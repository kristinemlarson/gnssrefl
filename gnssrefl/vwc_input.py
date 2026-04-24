import argparse
import copy
import json
import numpy as np
import os
import sys
from pathlib import Path

from scipy.stats import skew, kurtosis as scipy_kurtosis

from gnssrefl.gps import l2c_l5_list
from gnssrefl.extract_arcs import load_gnssir_results_from_tracks
from gnssrefl.tracks import build_tracks, load_tracks_json
from gnssrefl.tracks_qc import deactivate_epoch, delete_track, save_tracks
from gnssrefl.utils import (read_files_in_dir, FileManagement,
                            circular_mean_deg, circular_distance_deg, str2bool)
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.phase_functions as qp
from gnssrefl.phase_functions import get_vwc_frequency


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-min_req_pts_track", default=None, type=int,
                        help="min arcs per (track_id, track_epoch) bucket to keep that epoch. "
                             "Default 30, or the station JSON value of vwc_min_req_pts_track if present. "
                             "The resolved value is persisted back to the station JSON.")
    parser.add_argument("-minvalperday", default=None, help="min number of tracks needed on one day to compute VWC (default is 10)", type=int)
    parser.add_argument("-bin_hours", default=None, type=int, help="time bin size in hours (1,2,3,4,6,8,12,24). Default is 24 (daily)")
    parser.add_argument("-minvalperbin", default=None, type=int, help="min number of satellite tracks needed per time bin. Default is 5")
    parser.add_argument("-bin_offset", default=None, type=int, help="bin timing offset in hours (0 <= offset < bin_hours). Default is 0")
    parser.add_argument("-fr", default=None, nargs="*", type=int,
                        help="frequency filter, e.g. 20 5 to keep only L2C and L5 in vwc_tracks.json "
                             "(default: all frequencies in tracks.json). GPS (especially L2C) is widely "
                             "validated; support for other constellations and signals is in testing and, "
                             "with this caveat, available for research. Legacy path (-legacy T) accepts "
                             "a single value: 1 (L1), 20 (L2C), or 5 (L5).")
    parser.add_argument("-extension", default='', help="analysis extension parameter", type=str)
    parser.add_argument("-tmin", default=None, help="min soil texture (default 0.05)", type=float)
    parser.add_argument("-tmax", default=None, help="max soil texture (default 0.5)", type=float)
    parser.add_argument("-warning_value", default=None, help="warning value, degrees, phaseRMS (default 5.5)", type=float)
    parser.add_argument("-year_end", default=None, type=int,
                        help="end year (inclusive). Not supported with -legacy T.")
    parser.add_argument("-apriori_rh_ndays", default=None, type=int,
                        help="window (in days, counting back from the end of the date range) "
                             "over which apriori_RH and RH_std are averaged. Default 365.")
    parser.add_argument("-legacy", default=None, type=str,
                        help="use the legacy GPS-only apriori_RH flow (default False). "
                             "Deprecated; may be removed after 2027-01-01.")

    args = parser.parse_args().__dict__

    boolean_args = ['legacy']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def build_vwc_tracks(tracks, arcs_df, min_req_pts_track, fr_list,
                     apriori_rh_ndays):
    """Build a vwc_tracks dict from a (comprehensive) tracks dict.

    Works on a copy of tracks: drops tracks whose freq is not in fr_list
    via delete_track; deactivates (track_id, epoch_id) buckets with fewer
    than min_req_pts_track QC-passing arcs in arcs_df via deactivate_epoch;
    drops tracks left with no active epochs. Sets
    metadata['file_type'] = 'vwc_tracks' and metadata['apriori_rh_ndays'].
    Per-epoch derived fields (apriori_RH, RH_std, n_arcs, n_qc_arcs) are
    populated by save_tracks.

    The input tracks dict is not mutated.
    """
    vwc_tracks = copy.deepcopy(tracks)
    vwc_tracks['metadata']['file_type'] = 'vwc_tracks'
    vwc_tracks['metadata']['apriori_rh_ndays'] = int(apriori_rh_ndays)

    for tid_str in list(vwc_tracks['tracks'].keys()):
        tid = int(tid_str)
        track = vwc_tracks['tracks'][tid_str]
        if fr_list is not None and int(track['freq']) not in fr_list:
            delete_track(vwc_tracks, tid)

    bucket_sizes_qc = arcs_df.dropna(subset=['RH']).groupby(['track_id', 'track_epoch']).size().to_dict()

    for tid_str in list(vwc_tracks['tracks'].keys()):
        tid = int(tid_str)
        track = vwc_tracks['tracks'][tid_str]

        for ep in track['epochs']:
            if ep['epoch_type'] != 'active':
                continue
            if bucket_sizes_qc.get((tid, int(ep['epoch_id'])), 0) < min_req_pts_track:
                deactivate_epoch(vwc_tracks, tid, int(ep['epoch_id']))

        if not any(ep['epoch_type'] == 'active'
                   for ep in track['epochs']):
            delete_track(vwc_tracks, tid)

    return vwc_tracks


def vwc_input(station: str, year: int, fr=None, min_req_pts_track: int = None, minvalperday: int = None,
              bin_hours: int = None, minvalperbin: int = None, bin_offset: int = None,
              extension : str='', tmin: float = None, tmax: float = None, warning_value: float = None,
              year_end: int = None, apriori_rh_ndays: int = None, legacy: bool = False,
              vwc_tracks_builder=None):
    """
    Sets inputs for the estimation of VWC (volumetric water content).

    Auto-builds tracks.json for the station if it doesn't already exist,
    walks every day in [year, year_end] calling extract_arcs with that
    tracks.json so each arc is tagged with its (track_id, track_epoch)
    and gnssir QC result, aggregates per (track_id, track_epoch), and writes
    the VWC-eligible subset as vwc_tracks.json. That file has the same
    schema as tracks.json with two added per-epoch fields: apriori_RH
    (the mean RH across QC-passing arcs in the last apriori_rh_ndays days
    of the range, default 365) and RH_std (the standard deviation over
    the same sample, or null when fewer than 3 samples are available).

    Downstream phase and vwc commands consume vwc_tracks.json directly
    to get each arc's apriori RH and track-mean azimuth.

    Pass -legacy T to fall back to the old GPS-only flow that produces
    apriori_rh_{fr}.txt from per-day gnssir result files. -year_end
    is not supported with -legacy T.

    Parameters
    ----------
    station : str
        4 character ID of the station
    year : int
        full year
    fr : int or list of int, optional
        Default path: frequency filter. Only tracks whose freq is in this list
        are written to vwc_tracks.json. When None (default), all frequencies
        present in tracks.json are kept.
        Legacy path: single frequency (1 L1, 20 L2C, 5 L5). Only L2C is
        officially supported; passing a list of length > 1 with legacy=True
        is an error.
    min_req_pts_track : int, optional
        Minimum number of arcs per (track_id, track_epoch) bucket required to
        keep that epoch. When None, the station JSON value of
        vwc_min_req_pts_track is used if present, otherwise 30. The
        resolved value is persisted back to the station JSON.
    minvalperday : int, optional
        how many unique tracks are needed to compute a valid VWC measurement for a given day
    extension : str, optional
        strategy extension value (same as used in gnssir, subdaily etc)
    tmin : float, optional
        minimum soil moisture value
    tmax : float, optional
        maximum soil moisture value
    warning_value : float, optional
        for removing low quality satellite tracks when running vwc
        phase units, degrees
    year_end : int, optional
        End year (inclusive). Defaults to year. Not supported with
        legacy=True.
    apriori_rh_ndays : int, optional
        Window size, in days, counted backwards from the end of the date
        range, over which apriori_RH and RH_std are averaged.
        Default 365.
    legacy : bool, optional
        When True, use the legacy GPS-only apriori_RH flow (writes
        apriori_rh_{fr}.txt from gnssir result files). Default: False.

    Returns
    -------
    Default path:
        Files/{station}/{extension}/vwc_tracks.json

    Legacy path:
        $REFL_CODE/input/<station>/[<extension>/]<station>_phaseRH_<C>_<label>.txt
        (the per-freq apriori_rh_{fr}.txt consumed by legacy phase/vwc;
        <C> is the constellation char and <label> the signal label, e.g. _G_L2C)

    Both paths also persist the VWC-specific parameters (vwc_minvalperday,
    vwc_min_soil_texture, vwc_max_soil_texture, vwc_min_req_pts_track,
    vwc_warning_value) into the gnssir analysis JSON.
    """
    if len(station) != 4:
        print('station name must be four characters. Exiting.')
        sys.exit()
    if len(str(year)) != 4:
        print('Year must be four characters. Exiting.')
        sys.exit()

    # Normalize -fr to a list[int] or None. argparse (nargs="*") yields a list;
    # callers from Python may pass int, str, list, or None.
    if fr is None:
        fr_list = None
    elif isinstance(fr, (list, tuple)):
        fr_list = [int(f) for f in fr] or None
    else:
        fr_list = [int(fr)]

    if legacy:
        print('Note: -legacy T is deprecated and may be removed after 2027-01-01.')
        if year_end is not None:
            print('Error: -year_end is not supported with -legacy T.')
            sys.exit()
        if fr_list is not None and len(fr_list) > 1:
            print(f'Error: -legacy T accepts a single frequency only; got {fr_list}.')
            sys.exit()
        if apriori_rh_ndays is not None:
            print('Error: -apriori_rh_ndays is not supported with -legacy T.')
            sys.exit()
        legacy_fr = fr_list[0] if fr_list else None
        vwc_input_legacy(
            station=station, year=year, fr=legacy_fr, min_req_pts_track=min_req_pts_track,
            minvalperday=minvalperday, bin_hours=bin_hours,
            minvalperbin=minvalperbin, bin_offset=bin_offset,
            extension=extension, tmin=tmin, tmax=tmax,
            warning_value=warning_value,
        )
        return

    if year_end is None:
        year_end = year

    if apriori_rh_ndays is None:
        apriori_rh_ndays = 365
    if apriori_rh_ndays <= 0:
        print(f'Error: -apriori_rh_ndays must be positive; got {apriori_rh_ndays}.')
        sys.exit()

    # Resolve and (if needed) auto-build tracks.json
    tracks_fm = FileManagement(station, 'tracks_file', extension=extension)
    tracks_path = tracks_fm.get_file_path(ensure_directory=True)
    if tracks_path.exists():
        print(f'using tracks file: {tracks_path}')
        tracks_json = load_tracks_json(tracks_path)
        arcs_df = None
    else:
        print(f'tracks.json not found at {tracks_path}, auto-building...')
        try:
            tracks_json, arcs_df = build_tracks(station, year, year_end=year_end, extension=extension)
        except RuntimeError as e:
            print(f'cannot build tracks.json: {e}')
            sys.exit()

    # Read station config so refraction etc. matches gnssir
    station_config = guts2.read_json_file(station, extension)

    if arcs_df is None:
        print('loading gnssir results + failQC...')
        arcs_df = load_gnssir_results_from_tracks(tracks_json)

    n_gnssir_attached = int(arcs_df['RH'].notna().sum())
    n_failqc = int(arcs_df['RH'].isna().sum())
    print(f'{n_gnssir_attached} arcs passed QC, {n_failqc} in failQC '
          f'({n_gnssir_attached + n_failqc} total)')
    print(f'apriori RH computed from last {apriori_rh_ndays} days of date range')

    # Resolve min_req_pts_track: CLI > station JSON > default 30.
    if min_req_pts_track is not None:
        threshold = min_req_pts_track
    elif 'vwc_min_req_pts_track' in station_config:
        threshold = int(station_config['vwc_min_req_pts_track'])
    else:
        threshold = 30
    print(f'using min_req_pts_track={threshold}')

    if fr_list is not None:
        print(f'filtering vwc_tracks to frequencies: {fr_list}')

    if vwc_tracks_builder is None:
        vwc_tracks_builder = build_vwc_tracks

    vwc_tracks = vwc_tracks_builder(tracks_json, arcs_df, min_req_pts_track=threshold, fr_list=fr_list, apriori_rh_ndays=apriori_rh_ndays)

    out_tracks = vwc_tracks['tracks']
    kept_epochs = sum(1 for track in out_tracks.values() for ep in track['epochs'] if ep['epoch_type'] == 'active')
    in_tracks = tracks_json.get('tracks', {})
    in_epoch_count = sum(1 for track in in_tracks.values() for ep in track['epochs'] if ep['epoch_type'] == 'active')
    removed_tracks = len(in_tracks) - len(out_tracks)
    removed_epochs = in_epoch_count - kept_epochs
    print(f'removed {removed_tracks} tracks / {removed_epochs} epochs, '
          f'kept {len(out_tracks)} tracks / {kept_epochs} epochs')

    if not out_tracks:
        print('No surviving tracks. Likely causes:')
        if n_gnssir_attached == 0:
            print(f'  - gnssir has not been run for [{year}..{year_end}] (0 arcs had gnssir results attached)')
        print(f'  - -min_req_pts_track too strict (current: {threshold})')
        print('  - tracks.json coverage does not match the date range')
        sys.exit()

    out_fm = FileManagement(station, 'vwc_tracks_file', extension=extension)
    out_path = out_fm.get_file_path(ensure_directory=True)
    save_tracks(vwc_tracks, out_path, tool='vwc_input', arcs_df=arcs_df)
    print(f'vwc tracks written to {out_path}')

    # Persist VWC-specific parameters into the gnssir analysis JSON (same
    # behaviour as the legacy path, for downstream consumers).
    station_config['vwc_min_norm_amp'] = 0.5
    if warning_value is not None:
        station_config['vwc_warning_value'] = warning_value
    if tmin is not None:
        station_config['vwc_min_soil_texture'] = tmin
    if tmax is not None:
        station_config['vwc_max_soil_texture'] = tmax
    if minvalperday is not None:
        station_config['vwc_minvalperday'] = minvalperday
    if minvalperbin is not None:
        station_config['vwc_minvalperbin'] = minvalperbin
    # Persist in lockstep with vwc's own threshold, since both gate the same
    # quantity (arcs per epoch) at different pipeline stages.
    station_config['vwc_min_req_pts_track'] = threshold
    if bin_hours is not None:
        station_config['vwc_bin_hours'] = bin_hours
    if bin_offset is not None:
        station_config['vwc_bin_offset'] = bin_offset

    json_manager = FileManagement(station, 'make_json', extension=extension)
    json_path = json_manager.get_file_path()
    with open(json_path, 'w+') as outfile:
        json.dump(station_config, outfile, indent=4)


def vwc_input_legacy(station, year, fr, min_req_pts_track, minvalperday, bin_hours,
                     minvalperbin, bin_offset, extension, tmin, tmax,
                     warning_value):
    """Legacy GPS-only VWC input pipeline.

    Loads the per-day gnssir result files for year, clusters arcs into
    tracks by satellite + azimuth, and writes the selected tracks to
    apriori_rh_{fr}.txt (the file name depends on the single requested
    frequency). Downstream phase -legacy T / vwc -legacy T consume
    that file to get each arc's apriori RH.
    """
    xdir = Path(os.environ["REFL_CODE"])  # for kelly enloe

    # Use the new helper function to determine the frequency.
    fr_list = get_vwc_frequency(station, extension, fr)
    if len(fr_list) > 1:
        print("Error: vwc_input can only process one frequency at a time.")
        print("Please specify a single frequency with -fr or in the json file.")
        sys.exit()
    fr = fr_list[0]

    station_config = guts2.read_json_file(station, extension)
    ellist = station_config.get('ellist', [])
    if len(ellist) > 0:
        print('vwc_input does not support ellist. Please remove ellist from your json')
        print('and rerun gnssir_input with a single e1/e2 range before using vwc_input.')
        sys.exit()

    # Resolve min_req_pts_track: CLI > station JSON > default 30.
    if min_req_pts_track is not None:
        threshold = min_req_pts_track
    elif 'vwc_min_req_pts_track' in station_config:
        threshold = int(station_config['vwc_min_req_pts_track'])
    else:
        threshold = 30
    print('Minimum number of arcs required to save a series ', threshold)

    data_dir = xdir / str(year) / 'results' / station
    if extension:
        data_dir = data_dir / extension
    result_files = read_files_in_dir(data_dir)
    if result_files is None:
        print('Exiting.')
        sys.exit()

    gnssir_results = np.asarray(result_files)
    gnssir_results = np.transpose(gnssir_results)

    # get the satellites for the requested frequency and most recent year
    if fr == 1:
        l1_satellite_list = np.arange(1, 33)
        satellite_list = l1_satellite_list
    elif fr == 5:
        print('Using L5 satellite list for December 31 on ', year)
        l2c_sat, l5_sat = l2c_l5_list(year, 365)
        satellite_list = l5_sat
    else:  # fr == 20 (L2C)
        print('Using L2C satellite list for December 31 on ', year)
        l2c_sat, l5_sat = l2c_l5_list(year, 365)
        satellite_list = l2c_sat

    if len(gnssir_results) == 0:
        print('Found no results - perhaps wrong year? Please run gnssir first.')
        sys.exit()

    frequency_indices = np.where(gnssir_results[10] == fr)
    reflector_height_gnssir_results = gnssir_results[2][frequency_indices]
    satellite_gnssir_results = gnssir_results[3][frequency_indices]
    azimuth_gnssir_results = gnssir_results[5][frequency_indices]

    b = 0
    apriori_array = []
    for satellite in satellite_list:
        sat_mask = satellite_gnssir_results == satellite
        sat_azimuths = azimuth_gnssir_results[sat_mask]
        if len(sat_azimuths) == 0:
            continue
        clusters = define_track_clusters(sat_azimuths)
        for cluster in clusters:
            track_avg_az = circular_mean_deg(cluster)
            mask = sat_mask & (circular_distance_deg(azimuth_gnssir_results, track_avg_az) <= 3)
            reflector_heights = reflector_height_gnssir_results[mask]
            azimuths = azimuth_gnssir_results[mask]
            if len(reflector_heights) > threshold:
                # Exclude bimodal RH distributions (high BC + low kurtosis)
                kurt = scipy_kurtosis(reflector_heights, fisher=False)
                bc = (skew(reflector_heights)**2 + 1) / kurt if kurt > 0 else 0
                if bc > 0.9 and kurt < 3:
                    print(f'  Excluding bimodal track: sat {satellite:2.0f} avgAz {track_avg_az:5.1f} (BC={bc:.3f}, n={len(reflector_heights)})')
                    continue

                b += 1
                average_azimuth = circular_mean_deg(azimuths)
                az_min = (average_azimuth - 3) % 360
                az_max = (average_azimuth + 3) % 360
                apriori_array.append([b, np.mean(reflector_heights), satellite, average_azimuth, len(reflector_heights), az_min, az_max])

    file_manager = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
    apriori_path_f = file_manager.get_file_path()

    if len(apriori_array) == 0:
        print('Found no results - perhaps wrong year?')
        sys.exit()

    qp.write_apriori_rh(apriori_path_f, apriori_array, station, year,
                        0.05 if tmin is None else tmin,
                        0.5 if tmax is None else tmax)
    print('Apriori RH file written to ', apriori_path_f)

    station_config = guts2.read_json_file(station, extension)

    station_config['vwc_min_norm_amp'] = 0.5
    if warning_value is not None:
        station_config['vwc_warning_value'] = warning_value
    if tmin is not None:
        station_config['vwc_min_soil_texture'] = tmin
    if tmax is not None:
        station_config['vwc_max_soil_texture'] = tmax
    if minvalperday is not None:
        station_config['vwc_minvalperday'] = minvalperday
    if minvalperbin is not None:
        station_config['vwc_minvalperbin'] = minvalperbin
    station_config['vwc_min_req_pts_track'] = threshold
    if bin_hours is not None:
        station_config['vwc_bin_hours'] = bin_hours
    if bin_offset is not None:
        station_config['vwc_bin_offset'] = bin_offset

    json_manager = FileManagement(station, 'make_json', extension=extension)
    json_path = json_manager.get_file_path()
    with open(json_path, 'w+') as outfile:
        json.dump(station_config, outfile, indent=4)


def define_track_clusters(azimuths, gap_threshold=10):
    """Define satellite track clusters from observed azimuths.

    Groups azimuths into distinct tracks by sorting them on the circle,
    finding the largest gap (natural break), then splitting at any gap
    exceeding the threshold. Handles 0/360 wrap.

    Parameters
    ----------
    azimuths : array-like
        Observed azimuth values in degrees for a single satellite
    gap_threshold : float
        Minimum azimuth gap in degrees to split into separate tracks. Default 10.

    Returns
    -------
    list of numpy arrays
        Each array contains the azimuths belonging to one track.
    """
    az = np.sort(np.asarray(azimuths, dtype=float) % 360)
    n = len(az)
    if n == 0:
        return []
    if n == 1:
        return [az]

    gaps = np.empty(n)
    gaps[:-1] = np.diff(az)
    gaps[-1] = (az[0] + 360) - az[-1]

    start = (np.argmax(gaps) + 1) % n
    ordered_az = np.roll(az, -start)

    ordered_gaps = np.diff(ordered_az)
    ordered_gaps[ordered_gaps < 0] += 360

    clusters = []
    current = [ordered_az[0]]
    for i in range(1, n):
        if ordered_gaps[i - 1] > gap_threshold:
            clusters.append(np.array(current))
            current = []
        current.append(ordered_az[i])
    clusters.append(np.array(current))

    return clusters


def main():
    args = parse_arguments()
    vwc_input(**args)


if __name__ == "__main__":
    main()
