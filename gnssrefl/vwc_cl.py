import argparse
import json
import matplotlib.pyplot as matplt
import numpy as np
import scipy
import sys

from datetime import datetime

import gnssrefl.phase_functions as qp
import gnssrefl.gps as g
import gnssrefl.advanced_vegetation_correction as avc
import gnssrefl.simple_vegetation_correction as svc
import gnssrefl.tracks as tracks_mod
import gnssrefl.tracks_qc as tracks_qc

from gnssrefl.extract_arcs import load_gnssir_results_from_tracks
from gnssrefl.utils import str2bool, FileManagement, circular_distance_deg


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year_end", type=int)
    parser.add_argument("-fr", default=None, nargs="*", type=int,
                        help="frequency filter. Default path: omit to loop over every freq in "
                             "vwc_tracks.json, pass one value for a single-freq run, or pass "
                             "multiple values (e.g. -fr 20 5) to loop over that subset. GPS "
                             "(especially L2C) is widely validated; support for other "
                             "constellations and signals is in testing and, with this caveat, "
                             "available for research.")
    parser.add_argument("-plt", default=None, type=str,
                        help="boolean for plotting to screen. Default: True for single-frequency "
                             "runs; False when auto-looping over multiple frequencies. Pass -plt T "
                             "to force plots during an auto-loop.")
    parser.add_argument("-screenstats", default=None, type=str, help="boolean for plotting statistics to screen")
    parser.add_argument("-min_req_pts_track", default=None, type=int, help="min number of points for a track to be kept. Default is 30")
    parser.add_argument("-polyorder", default=None, type=int, help="override on polynomial order")
    parser.add_argument("-minvalperday", default=None, type=int, help="min number of satellite tracks needed each day. Default is 10")
    parser.add_argument("-bin_hours", default=None, type=int, help="time bin size in hours (1,2,3,4,6,8,12,24). Default is 24 (daily)")
    parser.add_argument("-minvalperbin", default=None, type=int, help="min number of sat tracks needed per time bin. Default is 5")
    parser.add_argument("-bin_offset", default=None, type=int, help="bin timing offset in hours (0 <= offset < bin_hours). Default is 0")
    parser.add_argument("-snow_filter", default=None, type=str, help="boolean, try to remove snow contaminated points. Default is F")
    parser.add_argument("-tmin", default=None, type=float, help="minimum soil texture. Default is 0.05.")
    parser.add_argument("-tmax", default=None, type=float, help="maximum soil texture. Defafult is 0.50.")
    parser.add_argument("-warning_value", default=None, type=float, help="Phase RMS (deg) threshold for bad tracks, default is 5.5 degrees")
    parser.add_argument("-auto_removal", default=None, type=str,
                        help="Remove bad tracks automatically (default is False). "
                             "Requires a prior vwc run to have completed so the daily-average "
                             "phase file exists; the first run with -auto_removal T writes that "
                             "file but does not drop any tracks, a second run performs the removal.")
    parser.add_argument("-hires_figs", default=None, type=str, help="Whether you want eps instead of png files")
    parser.add_argument("-advanced", default=None, type=str, help="Shorthand for -vegetation_model 2 (advanced vegetation model)")
    parser.add_argument("-vegetation_model", default=None, type=str, help="Vegetation correction model: 1 (simple, default) or 2 (advanced)")
    parser.add_argument("-save_tracks", default=None, type=str, help="Save individual track data")
    parser.add_argument("-extension", default='', type=str, help="which extension -if any - used in analysis json")
    parser.add_argument("-level_doys", nargs="*", help="doy limits to define level nodes", type=int)
    parser.add_argument("-legacy", default=None, type=str,
                        help="use the legacy GPS-only apriori_RH flow (default False). "
                             "Deprecated; may be removed after 2027-01-01.")

    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    boolean_args = ['plt', 'screenstats', 'snow_filter', 'auto_removal', 'hires_figs', 'advanced', 'save_tracks', 'legacy']
    args = str2bool(args, boolean_args)
    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def load_vwc_tracks(vwc_tracks_path):
    """Read a vwc_tracks.json document from disk."""
    with open(vwc_tracks_path) as f:
        return json.load(f)


def iter_vwc_epochs(vwc_tracks):
    """Yield (track_id, track_epoch, epoch, track) for every active epoch in a vwc_tracks.json document."""
    for tid_str, track in vwc_tracks['tracks'].items():
        tid = int(tid_str)
        for epoch in track['epochs']:
            if epoch['epoch_type'] != 'active':
                continue
            yield tid, int(epoch['epoch_id']), epoch, track


def vwc(station: str, year: int, year_end: int = None, fr: int = None, plt: bool = True, screenstats: bool = False,
        min_req_pts_track: int = None, polyorder: int = -99, minvalperday: int = None,
        bin_hours: int = None, minvalperbin: int = None, bin_offset: int = None,
        snow_filter: bool = False, tmin: float = None, tmax: float = None,
        warning_value: float = None, auto_removal: bool = False, hires_figs: bool = False,
        advanced: bool = False, vegetation_model: int = None, save_tracks: bool = False,
        extension: str = None, level_doys: list = [], skip_leveling: bool = False,
        legacy: bool = False):
    """
    Compute volumetric water content (VWC) from GNSS-IR phase estimates
    across all constellations/frequencies selected during vwc_input.

    Reads vwc_tracks.json to get each arc's apriori RH and track-mean
    azimuth, then concatenates the daily phase files, plots phase by azimuth
    quadrant, bins by time, applies vegetation correction, and converts to
    VWC. Pass -legacy T to use the old GPS-only flow that matches arcs
    against apriori_rh_{fr}.txt by satellite + azimuth.

    The code supports two vegetation correction models: Model 1 (simple, default) uses amplitude-based correction
    suitable for sites with bare soil or sparse vegetation. Model 2 (advanced) uses the Chew et al. (2016) GPS Solutions
    (DOI: 10.1007/s10291-015-0462-4) algorithm, and should be used for sites with dense or tall vegetation.

    Code now allows inputs (minvalperday, tmin, and tmax) to be stored in the gnssir analysis json file.
    To avoid confusion, in the json they are called vwc_minvalperday, vwc_min_soil_texture, and vwc_max_soil_texture.
    These values can also be overwritten on the command line ...

    Code now allows doy values for level nodes to be set in the json (variable name vwc_level_doys) and it
    is a list, i.e. [170,230] would be the input for summer months in NOAM.  This can be overriden by
    the command line -level_inputs 170 230. If no information is provided by the user, it has defaults
    based on the station being in the northern or southern hemisphere. However, this is a hack, and I have
    no idea if it works well for Australia, e.g.  It worked well for PBO H2O in the semi-arid western U.S.
    Those values are defined in set_parameters in phase_functions.py if you want to take a look
    If you want a time period that crosses the year boundary (i.e. you want all of december and january),
    you can input level_doys of 335 and 31, and the code will process accordingly.

    Examples
    --------
    vwc p038 2017
        one year for station p038
    vwc p038 2015 -year_end 2017
        three years of analysis for station p038
    vwc p038 2015 -year_end 2017 -warning_value 6
        warns you about tracks with phase RMS greater than 6 degrees rms
    vwc p038 2015 -year_end 2017 -warning_value 6 -auto_removal T
        makes new list of tracks based on your new warning value

    Parameters
    ----------
    station : str
        4 character ID of the station
    year : int
        full Year
    year_end : int, optional
        last year for analysis
    fr : int, optional
        Single GNSS frequency to process. main() handles the CLI
        -fr list (one/multiple/omitted) and calls this function once per
        freq; callers using vwc() directly must pass a single value.
        Only GPS is officially supported; other constellations are available
        for research/testing only.
    plt: bool, optional
        Whether to produce plots to the screen.
        Default is True
    min_req_pts_track : int, optional
        how many points needed to keep a satellite track.
        Default is 30. Can be set in the gnssir_input json (vwc_min_req_pts_track).
    polyorder : int
        polynomial order used for leveling.  Usually the code picks it but this allows to users to override.
        Default is -99 which means let the code decide
    minvalperday: integer
        how many phase measurements are needed for each daily measurement
        default is 10
    snow_filter: bool
        whether you want to attempt to remove points contaminated by snow
        default is False
    tmin: float
        minimum soil texture value, default 0.05. This can now be set in the gnssir_input json (with vwc_ added)
    tmax: float
        maximum soil texture value, default 0.5. This can now be set in the gnssir_input json (with vwc_ added)
    warning_value : float
         screen warning about bad tracks (phase rms, in degrees).
         default is 5.5
    auto_removal : bool, optional
         whether to automatically remove tracks that hit your bad track threshold
         default value is false
    hires_figs: bool, optional
         whether to make eps instead of png files
         default value is false
    advanced : bool, optional
         shorthand for vegetation_model=2
    vegetation_model : int, optional
         vegetation correction model: 1=simple (default), 2=advanced (Chew et al. 2016)
         can be set in gnssir analysis JSON as vwc_vegetation_model
    save_tracks : bool, optional
         save individual track VWC data to files (advanced model only)
    extension : str
         extension used when you made the json analysis file
    level_doys : list
         pair of day of years that are used to define time period for "leveling"
         default is north american summer
    skip_leveling : bool, optional
         internal use only - skip leveling and return percentage units for unified leveling
         in vwc_hourly. Default is False.
    legacy : bool, optional
        Use the legacy GPS-only apriori_RH flow. Default is False.
        Deprecated; may be removed after 2027-01-01.

    Returns
    -------

    Daily phase results in a file at
        $REFL_CODE/Files/<station>/[<extension>/]<station>_phase_<C>_<label>_<bin_hours>hr+<bin_offset>.txt
        with columns: Year DOY Ph Phsig NormA MM DD
        (<C> is the constellation char G/R/E/C and <label> the signal label L1/L2C/L5/...)

    VWC results in a file at
        $REFL_CODE/Files/<station>/[<extension>/]<station>_vwc_<C>_<label>_<bin_hours>hr+<bin_offset>.txt
        with columns: FracYr Year DOY  VWC Month Day

    """
    print('Requested level doys ', level_doys, len(level_doys))
    # Validate subdaily binning parameters
    if bin_hours is not None:
        valid_bin_hours = [1, 2, 3, 4, 6, 8, 12, 24]
        if bin_hours not in valid_bin_hours:
            print(f"Error: bin_hours must be one of {valid_bin_hours}")
            sys.exit()

    if bin_offset is not None and bin_hours is not None:
        if bin_offset < 0 or bin_offset >= bin_hours:
            print(f"Error: bin_offset must be 0 <= offset < bin_hours ({bin_hours})")
            sys.exit()

    # Handle vegetation model selection - do this BEFORE set_parameters for phase bounds
    # Precedence: CLI -advanced > CLI -vegetation_model > JSON vwc_vegetation_model > default (1)
    veg_model = None  # Will be finalized from JSON if not set by CLI
    if advanced:
        veg_model = 2
    elif vegetation_model:
        veg_model = int(vegetation_model)

    fs = 10  # fontsize
    snow_file = None
    colors = 'mrgbcykmrgbcykmrbcykmrgbcykmrgbcykmrbcyk'
    # subplot layout: NE=top-right, SE=bot-right, SW=bot-left, NW=top-left
    bx = [0, 1, 1, 0]
    by = [1, 1, 0, 0]

    if legacy:
        return vwc_legacy(
            station=station, year=year, year_end=year_end, fr=fr, plt=plt,
            screenstats=screenstats, min_req_pts_track=min_req_pts_track,
            polyorder=polyorder, minvalperday=minvalperday,
            bin_hours=bin_hours, minvalperbin=minvalperbin,
            bin_offset=bin_offset, snow_filter=snow_filter,
            tmin=tmin, tmax=tmax, warning_value=warning_value,
            auto_removal=auto_removal, hires_figs=hires_figs, advanced=advanced,
            veg_model=veg_model, save_tracks=save_tracks, extension=extension,
            level_doys=level_doys, skip_leveling=skip_leveling, colors=colors,
            bx=bx, by=by, fs=fs, snow_file=snow_file,
        )

    # Default path: read vwc_tracks.json
    vwc_tracks_path = FileManagement(station, 'vwc_tracks_file', extension=extension).get_file_path(ensure_directory=False)
    if not vwc_tracks_path.exists():
        tracks_mod.warn_legacy_apriori_and_exit(station, 'vwc_tracks.json', extension or '')
        print(f'vwc_tracks.json not found at {vwc_tracks_path}. Run `vwc_input` first.')
        sys.exit()

    vwc_tracks = load_vwc_tracks(vwc_tracks_path)

    # fr must be set, either by the user or by the auto-loop in main().
    if fr is None:
        unique_freqs = sorted({int(track['freq']) for track in vwc_tracks['tracks'].values()})
        print(f'Error: vwc_tracks.json contains frequencies {unique_freqs}.')
        print('Specify -fr <freq> or omit -fr to auto-loop over all frequencies.')
        sys.exit()
    fr = int(fr)

    # Build the (N, 7) tracks array, filtered to the requested frequency.
    # Cols: idx, RH, sat, track_azim, nvalstrack, track_id, track_epoch.
    # Arc matching is tag-based, so no per-track azimuth window is stored.
    rows = []
    n_skipped_no_apriori = 0
    for tid, track_epoch, epoch, track in iter_vwc_epochs(vwc_tracks):
        if int(track['freq']) != fr:
            continue
        if epoch['apriori_RH'] is None:
            n_skipped_no_apriori += 1
            continue
        mean_az = float(epoch['az_avg_minel']) % 360
        rows.append([
            0,                              # placeholder, renumbered below
            float(epoch['apriori_RH']),     # mean RH
            int(track['sat']),
            mean_az,
            int(epoch['n_arcs']),
            tid,
            track_epoch,
        ])
    if n_skipped_no_apriori:
        print(f'Skipped {n_skipped_no_apriori} epoch(s) with no arcs in the apriori_RH window (apriori_RH=None).')
    if not rows:
        available = sorted({int(track['freq']) for track in vwc_tracks['tracks'].values()})
        print(f'No tracks for freq {fr} in vwc_tracks.json. Available: {available}')
        sys.exit()
    tracks = np.asarray(rows, dtype=float)
    tracks[:, 0] = np.arange(1, len(tracks) + 1)
    print(f'Processing freq {fr}: {len(tracks)} tracks')

    return process_vwc_from_tracks(
        station=station, year=year, year_end=year_end, fr=fr, extension=extension,
        tracks=tracks, vwc_tracks=vwc_tracks,
        plt=plt, screenstats=screenstats,
        min_req_pts_track=min_req_pts_track, polyorder=polyorder,
        minvalperday=minvalperday, bin_hours=bin_hours,
        minvalperbin=minvalperbin, bin_offset=bin_offset,
        snow_filter=snow_filter,
        tmin=tmin, tmax=tmax, warning_value=warning_value,
        auto_removal=auto_removal, hires_figs=hires_figs,
        advanced=advanced, veg_model=veg_model, save_tracks=save_tracks,
        level_doys=level_doys, skip_leveling=skip_leveling,
        colors=colors, bx=bx, by=by, fs=fs, snow_file=snow_file,
    )


def process_vwc_from_tracks(
    station, year, year_end, fr, extension,
    tracks, vwc_tracks,
    plt, screenstats, min_req_pts_track, polyorder, minvalperday,
    bin_hours, minvalperbin, bin_offset,
    snow_filter, tmin, tmax, warning_value, auto_removal,
    hires_figs, advanced, veg_model, save_tracks,
    level_doys, skip_leveling, colors, bx, by, fs, snow_file,
):
    """Run the shared VWC pipeline on a prepared tracks array.

    Both the default multi-GNSS flow (vwc) and the GPS-only legacy flow
    (vwc_legacy) build a tracks array their own way and delegate the
    identical downstream work (set_parameters, snow filter, per-track phase
    fit, vegetation correction, leveling, output writing) to this function.

    Parameters
    ----------
    tracks : np.ndarray
        Track array with shape (N, 7). Cols 0-4 carry, in both paths:
        idx, mean RH (m), sat, track avg azimuth (deg), nvalstrack. Cols 5-6
        carry (az_min, az_max) for the legacy path and (track_id, track_epoch)
        for the default path; the choice is selected by vwc_tracks.
    vwc_tracks : dict or None
        Loaded vwc_tracks.json document for the default path (triggers
        tag-based arc matching via (track_id, track_epoch)), or None for the
        legacy path (triggers sat + azimuth-proximity matching).
    """
    if tracks.shape[1] != 7:
        raise ValueError(f'tracks must have shape (N, 7), got (N, {tracks.shape[1]})')

    minvalperday, tmin, tmax, min_req_pts_track, freq, year_end, \
            plt, remove_bad_tracks, warning_value, min_norm_amp, sat_legend, circles, extension, \
            bin_hours, minvalperbin, bin_offset, level_doys, json_vegetation_model = \
            qp.set_parameters(station, level_doys, minvalperday, tmin, tmax, min_req_pts_track,
                              fr, year, year_end, plt, auto_removal, warning_value, extension,
                              bin_hours, minvalperbin, bin_offset)

    if veg_model is None:
        veg_model = json_vegetation_model
    if veg_model not in [1, 2]:
        print(f'Vegetation model {veg_model} is not supported. Use 1 (simple) or 2 (advanced). Exiting.')
        sys.exit()
    if veg_model == 2:
        advanced = True
    if veg_model != json_vegetation_model:
        print(f'Vegetation model overridden by CLI: {veg_model}')

    if snow_filter:
        medf = 0.2  # this is meters, so will only see big snow
        ReqTracks = 10  # have a pretty small number here
        print('You have chosen the snow filter option')
        snowfileexists, snow_file = qp.make_snow_filter(station, medf, ReqTracks, year, year_end + 1)
        matplt.close('all')  # we do not want the plots to come to the screen for the daily average

    avg_exist, avg_date, avg_phase = qp.load_avg_phase(station, freq, bin_hours, extension)

    legacy_path = vwc_tracks is None
    data_exist, year_sat_phase, doy, hr, phase, azdata, ssat, rh, amp_lsp, amp_ls, ap_rh, results = \
            qp.load_phase(station, year, year_end, fr, snow_file, extension,
                          legacy=legacy_path)

    track_ids_arr = track_epochs_arr = None
    if data_exist:
        raw_columns = qp.PHASE_COLS_LEGACY if legacy_path else qp.PHASE_COLS
        phase = results[raw_columns.index('unphase'), :]
        if not legacy_path:
            track_ids_arr = results[raw_columns.index('TrackID'), :].astype(int)
            track_epochs_arr = results[raw_columns.index('TrackEpoch'), :].astype(int)

    if not data_exist:
        print('No data were found. Check your frequency request or station name')
        sys.exit()

    nr = len(tracks[:, 1])

    if (minvalperbin > nr):
        print('The code thinks you are using ', nr, ' satellite tracks but you are requiring', minvalperbin, ' for each VWC point.')
        print('Try lowering minvalperbin at the command line or in the gnssir analysis json (vwc_minvalperbin)')
        sys.exit()
    if (nr < 15) and (minvalperbin == 10):
        print('The code thinks you are using ', nr, ' satellite tracks but that is pretty close to the default (', minvalperbin, ')')
        print('This could be problematic. Try lowering minvalperbin at the command line or in the gnssir analysis json (vwc_minvalperbin)')
        sys.exit()

    k = 1
    # define the contents of this variable HERE
    vxyz = np.empty(shape=[0, 18])
    # column, contents of this variable
    # 0 year
    # 1 doy
    # 2 phase : degrees (unwrapped)
    # 3 azimuth
    # 4 satellite
    # 5 estimated reflector height
    # 6 normalized LSP amplitude
    # 7 normalized LS amplitude,
    # 8 hour of day, UTC
    # 9 raw LSP, for advanced setting
    # 10 raw LS amp, for advanced setting
    # 11 apriori RH
    # 12 track avg azimuth (degrees)
    # 13 delRH (for adv model)
    # 14 vegMask (for adv model)
    # 15 MJD for Kristine's sanity
    # 16 track_id (modern path; -1 sentinel on legacy path)
    # 17 track_epoch (modern path; -1 sentinel on legacy path)


    # this is the number of points for a given satellite track
    # just reassigning hte variable name
    reqNumpts = min_req_pts_track

    # KL disclosure
    # this code was written as a quick port between matlab and python
    # it does use many of the nice features of python variables.

    k4 = 1
    good_tracks = []
    good_track_keys = []  # default path only: (tid, track_epoch) for kept tracks
    # open up a figure for the phase results by quadrant
    fig, ax = matplt.subplots(2, 2, figsize=(10, 10))
    matplt.suptitle(f"Phase by Azimuth Quadrant: {station}", size=12)

    # open up a second plot for the amplitudes in the advanced option
    if advanced:
        fig2, ax2 = matplt.subplots(2, 2, figsize=(10, 10))
        matplt.suptitle(f"Lomb Scargle Periodogram Amplitudes: {station}", size=12)

    # Set up subplot titles for the four display quadrants
    quad_names = ['0-90', '90-180', '180-270', '270-360']
    for qi in range(4):
        ax[bx[qi], by[qi]].set_title(f'Azimuth {quad_names[qi]} deg.', fontsize=fs)
        if advanced:
            ax2[bx[qi], by[qi]].set_title(f'Azimuth {quad_names[qi]} deg.', fontsize=fs)

    ww_count = [0, 0, 0, 0]  # per-quadrant satellite counter for coloring

    # Iterate over each apriori track (satellite + avg azimuth)
    for ti in range(nr):
        satellite = int(tracks[ti, 2])
        track_avg_az = tracks[ti, 3]
        rhtrack = tracks[ti, 1]
        nvalstrack = tracks[ti, 4]
        display_quad = int(track_avg_az % 360 // 90)  # 0=NE, 1=SE, 2=SW, 3=NW

        # Arc-matching strategy is the only real divergence between the two
        # paths: default uses (track_id, track_epoch) tags carried on each arc;
        # legacy falls back to (satellite, azimuth within 3 deg) matching.
        tid = ep = None
        if vwc_tracks is not None:
            tid = int(tracks[ti, 5])
            ep = int(tracks[ti, 6])
            ii = (track_ids_arr == tid) & (track_epochs_arr == ep) & (phase < 360)
        else:
            ii = ((ssat == satellite)
                  & (circular_distance_deg(azdata, track_avg_az) <= 3)
                  & (phase < 360))
        y, t, h, x, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, mjds = \
                qp.rename_vals(year_sat_phase, doy, hr, phase, azdata, ssat, amp_lsp, amp_ls, rh, ap_rh, ii)
        if screenstats:
            print(f'Looking at sat {int(satellite)} avgAz {track_avg_az:.1f} Num vals {len(y)}')

        if len(x) > reqNumpts:
            sortY = np.sort(x)
            N = len(sortY)
            NN = int(np.round(0.20 * N))
            # use median value instead
            medv = np.median(sortY[(N - NN):(N - 1)])
            new_phase = -(x - medv)
            # this might be a problem ???? maybe use -30?
            ii = (new_phase > -20)

            y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, mjds = \
                    qp.rename_vals(y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, ii)

            if len(t) == 0:
                print(f'you should consider removing this satellite track as there are no results: sat {int(satellite)} avgAz {track_avg_az:.1f}')

            if (len(t) > reqNumpts):
                ww_count[display_quad] += 1
                ww = ww_count[display_quad]

                # not sure why this is done in a loop - and why it is even here????
                # and why with len(t) - 1
                for l in range(0, len(t) - 1):
                    if new_phase[l] > 340:
                        new_phase[l] = new_phase[l] - 360

                # this is ok for regular model - not so good for big vegetation sites
                ii = (new_phase > -20) & (new_phase < 60)
                # Apply wider bounds for high vegetation model (model 2)
                if veg_model == 2:
                    ii = (new_phase > -30) & (new_phase < 100)

                y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, mjds = \
                        qp.rename_vals(y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, ii)

                sortY = np.sort(new_phase)
                # looks like I am using the bottom 20%
                NN = int(np.round(0.2 * len(sortY)))
                mv = np.median(sortY[0:NN])
                new_phase = new_phase - mv
                fracyear = y + t / 365.25

                # this is to normalize the amplitudes. use base 15% to set it
                basepercent = 0.15
                # these are normalized LSP amplitudes
                norm_ampLSP = qp.normAmp(amp_lsps, basepercent)
                # these are normalized LS amplitudes
                norm_ampLS = qp.normAmp(amp_lss, basepercent)

                # adding three new columns to use in Clara Chew algorithm
                NN = len(amp_lsps)
                qs = track_avg_az * np.ones(shape=[1, NN])
                delRH = rhs - ap_rhs
                i = (norm_ampLSP < min_norm_amp)
                vegMask = np.zeros(shape=[NN, 1])
                vegMask[i] = 1

                tid_col = (tid if tid is not None else -1) * np.ones(shape=[1, NN])
                ep_col = (ep if ep is not None else -1) * np.ones(shape=[1, NN])
                newl2 = np.vstack((y, t, new_phase, azd, s, rhs, norm_ampLSP, norm_ampLS, h, amp_lsps, amp_lss, ap_rhs, qs, delRH, vegMask.T, mjds, tid_col, ep_col)).T

                # this is a kind of quality control -use previous solution to have
                # better feel for whether current solution works. defintely needs to go in a function

                if (len(newl2) > reqNumpts):
                    keepit = qp.kinda_qc(satellite, track_avg_az, y, t, new_phase,
                                     avg_date, avg_phase, warning_value, remove_bad_tracks, avg_exist)
                    if keepit:
                        if vwc_tracks is None:
                            # Legacy auto_removal rewrites apriori_rh_{fr}.txt,
                            # which carries az_min/az_max in its on-disk format.
                            az_min = (track_avg_az - 3) % 360
                            az_max = (track_avg_az + 3) % 360
                            good_tracks.append([k4, rhtrack, satellite, track_avg_az, nvalstrack, az_min, az_max])
                        else:
                            good_track_keys.append((tid, ep))
                        k4 += 1
                else:
                    print(f'No previous solution or not enough points for this satellite. sat {int(satellite)} avgAz {track_avg_az:.1f} n={len(newl2)}')

                adv_color = colors[ww % len(colors)]  # cycle when more tracks than palette entries
                # stack this latest set of values to vxyz
                vxyz = np.vstack((vxyz, newl2))
                datetime_dates = []
                csat = str(int(satellite))
                # make datetime dates for x-axis plots
                for yr, d in zip(y, t):
                    datetime_dates.append(datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j'))

                if advanced:
                    ax[bx[display_quad], by[display_quad]].plot(datetime_dates, new_phase, 'o', markersize=3, color=adv_color, label=csat)
                else:
                    ax[bx[display_quad], by[display_quad]].plot(datetime_dates, new_phase, 'o', markersize=3, label=csat)

                # per clara chew paper in GPS Solutions 2016
                if advanced:
                    # sort for the smoothing ... cause ... you can imagine
                    ik = np.argsort(fracyear)
                    try:
                        smoothAmps = scipy.signal.savgol_filter(norm_ampLSP[ik], window_length=31, polyorder=2)
                    except:
                        print('some issue with the smoothing in the function vwc')
                    ax2[bx[display_quad], by[display_quad]].plot(datetime_dates, norm_ampLSP, '.', color=adv_color, label=csat)

    # now add things to the plots for the whole quadrant, like labels and grid lines
    for qi in range(4):
        if qi == 0 or qi == 2:
            ax[bx[qi], by[qi]].set_ylabel('Phase')
            if advanced:
                ax2[bx[qi], by[qi]].set_ylabel('NormAmps')

        # for phase
        ax[bx[qi], by[qi]].set_ylim((-20, 60))
        if advanced:
            ax[bx[qi], by[qi]].set_ylim((-30, 90))

        ax[bx[qi], by[qi]].grid()
        if sat_legend and ww_count[qi] > 0:
            ax[bx[qi], by[qi]].legend(loc='upper right', fontsize=fs - 2)

        # for normalized amplitude plot, only triggered by advanced setting
        if advanced:
            ax2[bx[qi], by[qi]].grid()
            if sat_legend and ww_count[qi] > 0:
                ax2[bx[qi], by[qi]].legend(loc='upper right', fontsize=fs - 2)

    fig.autofmt_xdate()  # set for datetime
    if advanced:
        fig2.autofmt_xdate()  # set for datetime

    # auto_removal: legacy rewrites apriori_rh_{fr}.txt; default path mutates
    # vwc_tracks.json through the tracks_qc primitives, then save_tracks
    # appends a history entry and refits derived fields.
    if remove_bad_tracks and avg_exist:
        if vwc_tracks is None:
            file_manager = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
            oldlist = file_manager.get_file_path()
            print('Writing out a new list of good satellite tracks to ', oldlist)
            qp.write_apriori_rh(oldlist, good_tracks, station, year, tmin, tmax)
        else:
            counts = tracks_qc.apply_auto_removal(vwc_tracks, fr, set(good_track_keys))
            vwc_tracks_path = FileManagement(station, 'vwc_tracks_file', extension=extension).get_file_path(ensure_directory=False)
            arcs_df = load_gnssir_results_from_tracks(vwc_tracks)
            note = (f"freq={fr}, warning_value={warning_value}, "
                    f"tracks_removed={counts['tracks_removed']}/{counts['tracks_total']}, "
                    f"epochs_deactivated={counts['epochs_deactivated']}/{counts['epochs_total']}")
            tracks_qc.save_tracks(vwc_tracks, vwc_tracks_path,
                                  tool='vwc.auto_removal', note=note, arcs_df=arcs_df)
            print(f"auto_removal: freq {fr} - deactivated "
                  f"{counts['epochs_deactivated']}/{counts['epochs_total']} epochs "
                  f"({counts['tracks_removed']}/{counts['tracks_total']} tracks fully removed); "
                  f"history appended to {vwc_tracks_path.name}")

    suffix = qp.get_temporal_suffix(bin_hours)
    vwc_out_dir = FileManagement(station, 'vwc_outputs', frequency=fr, extension=extension).get_directory_path()

    # Skip saving plots when -plt F or skip_leveling (vwc_hourly two-pass mode)
    if plt and not skip_leveling:
        qp.save_vwc_plot(fig, f'{vwc_out_dir}/{station}_az_phase{suffix}.png')
        if advanced:
            qp.save_vwc_plot(fig2, f'{vwc_out_dir}/{station}_az_normamp{suffix}.png')

    # Close figures to prevent them from showing on screen when plt=False
    if not plt or skip_leveling:
        matplt.close(fig)
        if advanced:
            matplt.close(fig2)

    # Calculate averaged phase once (used by plot and file output)
    avg_phase = qp.calculate_avg_phase(vxyz, bin_hours, bin_offset, minvalperbin)

    # Plot averaged phase data, from before vegetation correction
    if plt:
        qp.subdaily_phase_plot(station, fr, vxyz, vwc_out_dir, hires_figs, bin_hours, bin_offset, minvalperbin, plt2screen=plt)

    # Write averaged phase file for QC on subsequent runs (needed by auto_removal)
    qp.write_avg_phase(station, fr, avg_phase, extension, bin_hours, bin_offset)

    # Write all_phase.txt QA file if requested
    if save_tracks:
        fname_phase = f'{vwc_out_dir}/{station}_all_phase.txt'
        qp.write_phase_for_advanced(fname_phase, vxyz, station, fr)

    # ========================================================================
    # TRACK-LEVEL PHASE DATA (vxyz)
    # ========================================================================
    #
    # vxyz contains individual satellite track observations (N x 18 array):
    #   - Each row = ONE observation from ONE satellite pass
    #   - Example: 10,000+ rows for a year of data
    #   - Columns:
    #       [0]  year
    #       [1]  doy (day of year)
    #       [2]  phase (unwrapped, degrees)
    #       [3]  azimuth (degrees)
    #       [4]  satellite number
    #       [5]  RH (reflector height, meters)
    #       [6]  norm_amp_LSP (normalized LSP amplitude)
    #       [7]  norm_amp_LS (normalized LS amplitude)
    #       [8]  hour (UTC)
    #       [9]  raw_LSP (raw LSP amplitude)
    #       [10] raw_LS (raw LS amplitude)
    #       [11] apriori_RH (a priori reflector height, meters)
    #       [12] track avg azimuth (degrees)
    #       [13] delRH (RH - apriori_RH, meters)
    #       [14] vegMask (vegetation mask flag)
    #       [15] MJD (Modified Julian Day)
    #       [16] track_id (modern path; -1 sentinel on legacy path)
    #       [17] track_epoch (modern path; -1 sentinel on legacy path)
    #
    # This track-level data is passed directly to vegetation filters and plotting functions.
    # ========================================================================

    # ========================================================================
    # VWC DATA STRUCTURE (vwc_data)
    # ========================================================================
    #
    # vwc_data is the standardized output from both vegetation models:
    #   - Dictionary with time-binned VWC estimates (after vegetation correction)
    #   - Keys:
    #       'mjd'        : list of Modified Julian Day values
    #       'vwc'        : list of VWC values (percentage units, not yet leveled)
    #       'datetime'   : list of datetime objects (for plotting)
    #       'bin_starts' : list of bin start hours (subdaily) or empty list (daily)
    #
    # This structure is returned by both simple_vegetation_filter() and
    # advanced_vegetation_filter(), then passed to leveling and output functions.
    # ========================================================================

    if veg_model == 1:
        print('Running simple vegetation model (model 1)...')
        vwc_data = svc.simple_vegetation_filter(
            station, vxyz, extension,
            bin_hours, bin_offset, plt2screen=plt, fr=fr,
            minvalperbin=minvalperbin, skip_plots=skip_leveling or not plt,
            save_tracks=save_tracks)
    elif veg_model == 2:
        print('Running advanced vegetation model (model 2)...')
        vwc_data = avc.advanced_vegetation_filter(
            station, vxyz, extension,
            bin_hours, bin_offset, plt, fr, minvalperbin,
            save_tracks)
    else:
        print(f'Unknown vegetation model: {veg_model}. Use 1 (simple) or 2 (advanced).')
        sys.exit()

    # Check if vegetation correction produced results
    if not vwc_data or len(vwc_data.get('vwc', [])) == 0:
        print('No vegetation-corrected VWC values produced. Exiting.')
        sys.exit()

    # Check if we should skip leveling (for vwc_hourly unified leveling)
    if skip_leveling:
        print('  Skipping leveling - returning unleveled data for unified processing')
        return vwc_data  # vwc_data['vwc'] is in PERCENTAGE units (0-60)

    # Apply baseline leveling
    print('\nApplying baseline leveling...')
    leveled_vwc, leveling_info = qp.apply_vwc_leveling(
        vwc_data['vwc'], tmin,
        mjd=vwc_data['mjd'],
        level_doys=level_doys,
        polyorder=polyorder,
        station=station, plot_debug=plt, plt2screen=plt,
        extension=extension, fr=fr, bin_hours=bin_hours, bin_offset=bin_offset
    )

    # Update vwc_data with leveled values
    vwc_data['vwc'] = leveled_vwc if isinstance(leveled_vwc, list) else leveled_vwc.tolist()

    # Write output files
    print('\nWriting VWC output file...')
    qp.write_vwc_output(station, vwc_data, year, fr, bin_hours, bin_offset, extension, veg_model)

    if plt:
        print('\nGenerating final VWC plot...')
        suffix = qp.get_temporal_suffix(bin_hours)

        if hires_figs:
            plot_path = f'{vwc_out_dir}/{station}_vol_soil_moisture{suffix}.eps'
        else:
            plot_path = f'{vwc_out_dir}/{station}_vol_soil_moisture{suffix}.png'

        qp.vwc_plot(station, vwc_data['datetime'], leveled_vwc, plot_path, circles, plt2screen=plt)

        matplt.show()

    print(f'\nVWC processing complete for {station}')


def vwc_legacy(station, year, year_end, fr, plt, screenstats, min_req_pts_track,
               polyorder, minvalperday, bin_hours, minvalperbin, bin_offset,
               snow_filter, tmin, tmax, warning_value, auto_removal,
               hires_figs, advanced, veg_model, save_tracks, extension,
               level_doys, skip_leveling, colors, bx, by, fs, snow_file):
    """Legacy GPS-only VWC flow.

    Reads apriori_rh_{fr}.txt (the legacy per-freq track list), then
    delegates the downstream pipeline to process_vwc_from_tracks, which
    matches each phase-file row to a track by (satellite, azimuth within
    3 deg) when no vwc_tracks.json doc is supplied.
    """
    fr_list = qp.get_vwc_frequency(station, extension, fr)
    if len(fr_list) > 1:
        print("Error: vwc can only process one frequency at a time.")
        sys.exit()
    fr = fr_list[0]

    tracks = qp.read_apriori_rh(station, fr, extension)

    return process_vwc_from_tracks(
        station=station, year=year, year_end=year_end, fr=fr, extension=extension,
        tracks=tracks, vwc_tracks=None,
        plt=plt, screenstats=screenstats,
        min_req_pts_track=min_req_pts_track, polyorder=polyorder,
        minvalperday=minvalperday, bin_hours=bin_hours,
        minvalperbin=minvalperbin, bin_offset=bin_offset,
        snow_filter=snow_filter,
        tmin=tmin, tmax=tmax, warning_value=warning_value,
        auto_removal=auto_removal, hires_figs=hires_figs,
        advanced=advanced, veg_model=veg_model, save_tracks=save_tracks,
        level_doys=level_doys, skip_leveling=skip_leveling,
        colors=colors, bx=bx, by=by, fs=fs, snow_file=snow_file,
    )


def get_vwc_tracks_freqs(station, extension=''):
    """Return sorted list of unique freq codes in vwc_tracks.json, or None if missing."""
    vwc_tracks_path = FileManagement(station, 'vwc_tracks_file', extension=extension).get_file_path(ensure_directory=False)
    if not vwc_tracks_path.exists():
        return None
    doc = load_vwc_tracks(vwc_tracks_path)
    return sorted({int(track['freq']) for track in doc['tracks'].values()})


def main():
    args = parse_arguments()

    legacy = args.get('legacy', False)
    fr_list = args.pop('fr', None)

    FileManagement(args['station'], 'raw_phase_file', extension=args.get('extension', '')).get_file_path().unlink(missing_ok=True)

    if legacy:
        print('Note: -legacy T is deprecated and may be removed after 2027-01-01.')
        # Legacy accepts a single frequency.
        if fr_list and len(fr_list) > 1:
            print(f'Error: -legacy T accepts a single frequency only; got {fr_list}.')
            sys.exit()
        args['fr'] = str(fr_list[0]) if fr_list else None
        vwc(**args)
        return

    # Default path: figure out which freqs to run.
    available = get_vwc_tracks_freqs(args['station'], args.get('extension', ''))
    if available is None:
        tracks_mod.warn_legacy_apriori_and_exit(args['station'], 'vwc_tracks.json', args.get('extension', '') or '')
        print('vwc_tracks.json not found. Run `vwc_input` first.')
        sys.exit()
    if not available:
        print('vwc_tracks.json is empty.')
        sys.exit()

    if fr_list:
        missing = [f for f in fr_list if f not in available]
        if missing:
            print(f'Error: requested frequencies {missing} are not in vwc_tracks.json.')
            print(f'Available: {available}')
            sys.exit()
        freqs = fr_list
    else:
        freqs = available

    if len(freqs) == 1:
        args['fr'] = freqs[0]
        vwc(**args)
    else:
        print(f'Auto-looping over {len(freqs)} frequencies: {freqs}\n')
        if 'plt' in args:
            plt_default_for_loop = args['plt']
        else:
            # User omitted -plt during an auto-loop: save per-freq plots but
            # don't pop 15 windows. Switching to a non-interactive backend
            # makes plt.show() a no-op while savefig still works.
            matplt.switch_backend('Agg')
            plt_default_for_loop = True
        for fr in freqs:
            print(f'\n{"=" * 60}')
            print(f'  vwc -fr {fr}')
            print(f'{"=" * 60}\n')
            run_args = {**args, 'fr': fr, 'plt': plt_default_for_loop}
            vwc(**run_args)


if __name__ == "__main__":
    main()
