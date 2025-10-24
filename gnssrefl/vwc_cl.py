import argparse
import pickle
import matplotlib.pyplot as matplt
import numpy as np
import os
import scipy
import subprocess
import sys

from datetime import datetime, timedelta
from pathlib import Path

import gnssrefl.phase_functions as qp
import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as gnssir
import gnssrefl.advanced_vegetation_correction as avc
import gnssrefl.simple_vegetation_correction as svc

from gnssrefl.utils import str2bool, read_files_in_dir, FileManagement

xdir = os.environ['REFL_CODE']


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year_end", type=int)
    parser.add_argument("-fr", help="frequency: 1 (L1), 20 (L2C), 5 (L5). Only L2C officially supported.", type=str)
    parser.add_argument("-plt", default=None, type=str, help="boolean for plotting to screen")
    parser.add_argument("-screenstats", default=None, type=str, help="boolean for plotting statistics to screen")
    parser.add_argument("-min_req_pts_track", default=None, type=int, help="min number of points for a track to be kept. Default is 100")
    parser.add_argument("-polyorder", default=None, type=int, help="override on polynomial order")
    parser.add_argument("-minvalperday", default=None, type=int, help="min number of satellite tracks needed each day. Default is 10")
    parser.add_argument("-bin_hours", default=None, type=int, help="time bin size in hours (1,2,3,4,6,8,12,24). Default is 24 (daily)")
    parser.add_argument("-minvalperbin", default=None, type=int, help="min number of sat tracks needed per time bin. Default is 5")
    parser.add_argument("-bin_offset", default=None, type=int, help="bin timing offset in hours (0 <= offset < bin_hours). Default is 0")
    parser.add_argument("-snow_filter", default=None, type=str, help="boolean, try to remove snow contaminated points. Default is F")
    parser.add_argument("-subdir", default=None, type=str, help="DEPRECATED: use -extension instead")
    parser.add_argument("-tmin", default=None, type=float, help="minimum soil texture. Default is 0.05.")
    parser.add_argument("-tmax", default=None, type=float, help="maximum soil texture. Defafult is 0.50.")
    parser.add_argument("-warning_value", default=None, type=float, help="Phase RMS (deg) threshold for bad tracks, default is 5.5 degrees")
    parser.add_argument("-auto_removal", default=None, type=str, help="Remove bad tracks automatically (default is False)")
    parser.add_argument("-hires_figs", default=None, type=str, help="Whether you want eps instead of png files")
    parser.add_argument("-advanced", default=None, type=str, help="Shorthand for -vegetation_model 2 (advanced vegetation model)")
    parser.add_argument("-vegetation_model", default=None, type=str, help="Vegetation correction model: 1 (simple, default) or 2 (advanced)")
    parser.add_argument("-save_tracks", default=None, type=str, help="Save individual track VWC data (model 2 only)")
    parser.add_argument("-simple_level", default=None, type=str, help="Use simple global leveling instead of polynomial (default: False)")
    parser.add_argument("-extension", default='', type=str, help="which extension -if any - used in analysis json")
    parser.add_argument("-level_doys", nargs="*", help="doy limits to define level nodes",type=int) 


    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    boolean_args = ['plt','screenstats','snow_filter','auto_removal','hires_figs','advanced','save_tracks','simple_level']
    args = str2bool(args, boolean_args)
    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def vwc(station: str, year: int, year_end: int = None, fr: str = None, plt: bool = True, screenstats: bool = False,
        min_req_pts_track: int = None, polyorder: int = -99, minvalperday: int = None,
        bin_hours: int = None, minvalperbin: int = None, bin_offset: int = None,
        snow_filter: bool = False, subdir: str=None, tmin: float=None, tmax: float=None,
        warning_value : float=None, auto_removal : bool=False, hires_figs : bool=False,
        advanced : bool=False, vegetation_model: int=None, save_tracks: bool=False, simple_level: bool=False,
        extension:str=None, level_doys : list =[] ):
    """
    The goal of this code is to compute volumetric water content (VWC) from GNSS-IR phase estimates.
    It concatenates previously computed phase results, makes plots for the four geographic quadrants, bins the data
    (into daily or subdaily time bins), applies vegetation correction, and converts to volumetric water content.

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
        GNSS frequency. Currently only supports l2c.
        Default is 20 (l2c)
    plt: bool, optional
        Whether to produce plots to the screen.
        Default is True
    min_req_pts_track : int, optional
        how many points needed to keep a satellite track
        default is now set to 150 (was previously 50). This is an issue when a satellite has recently 
        been launched. You don't really have enough information to trust it for several months (and in some cases longer)
        this can now be set in the gnssir_input created analysis json (vwc_min_req_pts_track)
        As of version 3.10.9 it is set to 100.
    polyorder : int
        polynomial order used for leveling.  Usually the code picks it but this allows to users to override. 
        Default is -99 which means let the code decide
    minvalperday: integer
        how many phase measurements are needed for each daily measurement
        default is 10
    snow_filter: bool
        whether you want to attempt to remove points contaminated by snow
        default is False
    subdir: str
        DEPRECATED: use -extension instead. This parameter is ignored.
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
    simple_level : bool, optional
         use simple leveling instead of polynomial (default: False)
    save_tracks : bool, optional
         save individual track VWC data to files (advanced model only)
    extension : str
         extension used when you made the json analysis file
    level_doys : list
         pair of day of years that are used to define time period for "leveling"
         default is north american summer

    Returns
    -------

    Daily phase results in a file at $REFL_CODE/Files/<station>/<station>_phase.txt
        with columns: Year DOY Ph Phsig NormA MM DD

    VWC results in a file at $$REFL_CODE/Files/<station>/<station>_vwc.txt
        with columns: FracYr Year DOY  VWC Month Day

    """
    print('Requested level doys ', level_doys,len(level_doys))
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

    fs =10 # fontsize
    snow_file = None
    colors = 'mrgbcykmrgbcykmrbcykmrgbcykmrgbcykmrbcyk'
    # plotting indices for phase data
    by=[0,1,0,1]; bx=[0,0,1,1]
    # azimuth list, starting point only (i.e. 270 means 270 thru 360)
    azlist = [270, 0, 180,90 ]
    # consistency with old adv vegetation code
    oldquads = [2, 1, 3, 4] # number system from pboh2o, only used for

    # Default frequency selection logic (from json if none supplied by command line)
    fr_list = qp.get_vwc_frequency(station, extension, fr)
    if len(fr_list) > 1:
        print("Error: vwc can only process one frequency at a time.")
        sys.exit()
    # Get the single frequency from the list
    fr = fr_list[0]

    # Deprecation warning for subdir parameter
    if subdir is not None:
        print("Warning: -subdir is deprecated. Please use -extension instead.")
        print(f"  (subdir '{subdir}' will be ignored, using extension-based path)")

    # Compute subdirectory path from extension (for file operations)
    subdir_path = f"{station}/{extension}" if extension else station

    # pick up the parameters used for this code
    # Sep 4, 2025 added level_doys parameter
    minvalperday, tmin, tmax, min_req_pts_track, freq, year_end, \
            plt, remove_bad_tracks, warning_value,min_norm_amp,sat_legend,circles,extension, \
            bin_hours, minvalperbin, bin_offset, level_doys, json_vegetation_model = \
            qp.set_parameters(station, level_doys, minvalperday, tmin,tmax, min_req_pts_track,
                              fr, year, year_end, plt, auto_removal,warning_value,extension,
                              bin_hours, minvalperbin, bin_offset)

    # Finalize vegetation model: use JSON value if not set by CLI
    if veg_model is None:
        veg_model = json_vegetation_model  # Will be 1 or 2 from JSON, defaulting to 1

    # Validate model number
    if veg_model not in [1, 2]:
        print(f'Vegetation model {veg_model} is not supported. Use 1 (simple) or 2 (advanced). Exiting.')
        sys.exit()

    # Set advanced flag when using model 2 for backward compatibility
    if veg_model == 2:
        advanced = True

    # Print final resolved vegetation model (overrides the JSON printout from set_parameters)
    if veg_model != json_vegetation_model:
        print(f'Vegetation model overridden by CLI: {veg_model}')

    print(f'Using baseline leveling: {"simple" if simple_level else "polynomial"}')

    # if you have requested snow filtering
    if snow_filter:
        medf = 0.2 # this is meters , so will only see big snow 
        ReqTracks = 10 # have a pretty small number here
        print('You have chosen the snow filter option')
        snowfileexists,snow_file = qp.make_snow_filter(station, medf, ReqTracks, year, year_end+1)
        matplt.close ('all')# we do not want the plots to come to the screen for the daily average

    # load past VWC analysis  for QC
    avg_exist, avg_date, avg_phase = qp.load_avg_phase(station,freq,bin_hours,extension,bin_offset)

    # pick up all the phase data. unwrapped phase is stored in the results variable
    data_exist, year_sat_phase, doy, hr, phase, azdata, ssat, rh, amp_lsp,amp_ls,ap_rh, results = \
            qp.load_phase_filter_out_snow(station, year, year_end, fr,snow_file, extension)


    if not data_exist:
        print('No data were found. Check your frequency request or station name')
        sys.exit()

    # using unwrapped phase instead of raw phase
    phase = results[17,:]
    
    # pick up the tracks you will use to compute phase.  THis was previously
    # created by vwc_input ...
    tracks = qp.read_apriori_rh(station, freq, extension)
    nr = len(tracks[:,1])

    if (minvalperbin > nr ):
        print('The code thinks you are using ', nr, ' satellite tracks but you are requiring', minvalperbin, ' for each VWC point.')
        print('Try lowering minvalperbin at the command line or in the gnssir analysis json (vwc_minvalperbin)')
        sys.exit()
    if (nr < 15 ) and (minvalperbin==10):
        print('The code thinks you are using ', nr, ' satellite tracks but that is pretty close to the default (', minvalperbin, ')')
        print('This could be problematic. Try lowering minvalperbin at the command line or in the gnssir analysis json (vwc_minvalperbin)')
        sys.exit()

    atracks = tracks[:, 5]  # min azimuth values
    stracks = tracks[:, 2]  # satellite names

    k = 1
    # define the contents of this variable HERE
    vxyz = np.empty(shape=[0, 16]) 
    # newl = np.vstack((y, t, new_phase, azd, s, rhs, norm_ampLSP,norm_ampLS,h,amp_lsps,amp_lss,qs)).T
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
    # 12 quadrant (pboh2o style)
    # 13 delRH (for adv model)
    # 14 vegMask (for adv model)
    # 15 MJD for Kristine's sanity


    # this is the number of points for a given satellite track
    # just reassigning hte variable name
    reqNumpts = min_req_pts_track

    # KL disclosure
    # this code was written as a quick port between matlab and python
    # it does use many of the nice features of python variables. 
    
    # checking each geographic quadrant
    k4 = 1
    # two list of tracks - lets you compare an old run with a new run as a form of QC
    newlist = f'{station}_tmp.txt'
    file_manager = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
    oldlist = file_manager.get_file_path()

    ftmp = open(newlist,'w+')
    ftmp.write("{0:s} \n".format( '% station ' + station) )
    ftmp.write("{0:s} \n".format( '% TrackN  RefH SatNu MeanAz  Nval  Azimuths'))
    # open up a figure for the phase results by quadrant
    fig,ax = matplt.subplots(2, 2, figsize=(10,10))
    matplt.suptitle(f"Phase by Azimuth Quadrant: {station}", size=12)

    # open up a second plot for the amplitudes in the advanced option
    if advanced: 
        # opens the file , writes a header
        #fname_phase = f'{xdir}/Files/{subdir}/{station}_{str(year)}_all_phase.txt'

        fig2,ax2 = matplt.subplots(2, 2, figsize=(10,10))
        matplt.suptitle(f"Lomb Scargle Periodogram Amplitudes: {station}", size=12)

    for index, az in enumerate(azlist):
        b = 0
        k += 1
        ww = 0
        print('quadrant ' , oldquads[index])
        amin = az ; amax = az + 90
        # make a quadrant average for plotting purposes
        vquad = np.empty(shape=[0, 4])
        # pick up the sat list from the actual list
        satlist = stracks[atracks == amin]

        # set the titles for the two plots
        ax[bx[index],by[index]].set_title(f'Azimuth {str(amin)}-{str(amax)} deg.',fontsize=fs)
        if advanced:
            ax2[bx[index],by[index]].set_title(f'Azimuth {str(amin)}-{str(amax)} deg.',fontsize=fs)

        for satellite in satlist:
            # set the indices for the satellite and quadrant you want to look at here
            ii = (ssat == satellite) & (azdata > amin) & (azdata < amax) & (phase < 360)
            # added mjd as an output
            y,t,h,x,azd,s,amp_lsps,amp_lss,rhs,ap_rhs,mjds = \
                    qp.rename_vals(year_sat_phase, doy, hr, phase, azdata, ssat, amp_lsp, amp_ls, rh, ap_rh, ii)
            if screenstats:
                print('Looking at ', int(satellite), amin, amax,' Num vals', len(y))

            iikk  = (atracks == amin) & (stracks == satellite) 
            rhtrack = float(tracks[iikk,1]) # a priori RH
            meanaztrack = float(tracks[iikk,3])
            nvalstrack = float(tracks[iikk,4])

            if len(x) > reqNumpts:
                b += 1 # is b used?
                sortY = np.sort(x)
                N = len(sortY)
                NN = int(np.round(0.20*N))
                # use median value instead
                medv = np.median(sortY[(N-NN):(N-1)])
                new_phase = -(x-medv)
                # this might be a problem ???? maybe use -30?
                ii = (new_phase > -20)

                y,t,h,new_phase,azd,s,amp_lsps,amp_lss,rhs,ap_rhs,mjds = \
                        qp.rename_vals(y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs,ii)

                if len(t) == 0:
                    print('you should consider removing this satellite track as there are no results', satellite, amin)

                if (len(t) > reqNumpts):
                    ww = ww + 1 # index for plotting in a quadrant

                    # not sure why this is done in a loop - and why it is even here????
                    # and why with len(t) - 1
                    for l in range(0, len(t)-1):
                        if new_phase[l] > 340:
                            new_phase[l] = new_phase[l] - 360

                    # this is ok for regular model - not so good for big vegetation sites
                    ii = (new_phase > -20) & (new_phase < 60)
                    # Apply wider bounds for high vegetation model (model 2)
                    if veg_model == 2:
                        ii = (new_phase > -30) & (new_phase < 100)

                    y,t,h,new_phase,azd,s,amp_lsps,amp_lss,rhs,ap_rhs,mjds = \
                            qp.rename_vals(y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, ii)

                    sortY = np.sort(new_phase)
                    # looks like I am using the bottom 20% 
                    NN = int(np.round(0.2*len(sortY)))
                    mv = np.median(sortY[0:NN])
                    new_phase = new_phase - mv
                    fracyear = y + t/365.25

                    newl = np.vstack((y, t, new_phase, azd)).T
                    vquad = np.vstack((vquad, newl))

                    # this is to normalize the amplitudes. use base 15% to set it
                    basepercent = 0.15
                    # these are normalized LSP amplitudes
                    norm_ampLSP = qp.normAmp(amp_lsps, basepercent) ; 
                    # these are normalized LS amplitudes
                    norm_ampLS= qp.normAmp(amp_lss, basepercent)

                    # adding three new columns to use in Clara Chew algorithm
                    NN = len(amp_lsps)
                    qs = oldquads[index]*np.ones(shape=[1,NN])
                    delRH = rhs-ap_rhs
                    i = (norm_ampLSP < 0.8)
                    vegMask = np.zeros(shape=[NN,1])
                    vegMask[i] = 1

                    # Sep 8, 2025 add MJD
                    # this is for advanced ...
                    newl2 = np.vstack((y, t, new_phase, azd, s, rhs, norm_ampLSP,norm_ampLS,h,amp_lsps,amp_lss,ap_rhs,qs,delRH,vegMask.T,mjds)).T
                    #newl2 = np.vstack((y, t, new_phase, azd, s, rhs, norm_ampLSP,norm_ampLS,h,amp_lsps,amp_lss,ap_rhs,qs)).T

                    newl = np.vstack((y, t, new_phase, azd, s, rhs, norm_ampLSP,norm_ampLS,h,amp_lsps,amp_lss,ap_rhs)).T

                    # this is a kind of quality control -use previous solution to have 
                    # better feel for whether current solution works. defintely needs to go in a function

                    if (len(newl) > reqNumpts): 
                        k4= qp.kinda_qc(satellite, rhtrack,meanaztrack,nvalstrack, amin,amax, y, t, new_phase, 
                                         avg_date,avg_phase,warning_value,ftmp,remove_bad_tracks,k4,avg_exist )
                    else:
                        print('No previous solution or not enough points for this satellite.', int(satellite), amin, amax,len(newl))

                    adv_color = colors[ww:ww+1] # sets color for below
                    # stack this latest set of values to vxyz
                    #vxyz = np.vstack((vxyz, newl))
                    # try using version with quadrants
                    vxyz = np.vstack((vxyz, newl2))
                    datetime_dates = []
                    csat = str(int(satellite))
                    # make datetime dates for x-axis plots
                    for yr, d in zip(y, t):
                        datetime_dates.append(datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j'))

                    if advanced:
                        ax[bx[index],by[index]].plot(datetime_dates, new_phase, 'o', markersize=3,color=adv_color,label=csat)
                    else:
                        ax[bx[index],by[index]].plot(datetime_dates, new_phase, 'o', markersize=3,label=csat)

                    # per clara chew paper in GPS Solutions 2016
                    if advanced:
                        # sort for the smoothing ... cause ... you can imagine 
                        ik = np.argsort( fracyear)
                        try:
                            smoothAmps = scipy.signal.savgol_filter(norm_ampLSP[ik], window_length=31,polyorder=2 )
                            # turn off for now - changed x-axis to datetime instead of fractional year
                            #ax2[bx[index],by[index]].plot(fracyear[ik], smoothAmps, '-',color=adv_color)
                        except:
                            print('some issue with the smoothing in the function vwc')
                        # not sure this will work
                        ax2[bx[index],by[index]].plot(datetime_dates, norm_ampLSP, '.',color=adv_color,label=csat)
                        #ax2[bx[index],by[index]].plot(fracyear[ik], norm_ampLSP[ik], '.',color=adv_color,label=csat)


        # now add things to the plots for the whole quadrant, like labels and grid lines
        if (index == 0 ) or (index == 2):
            ax[bx[index],by[index]].set_ylabel('Phase')
            if advanced:
                ax2[bx[index],by[index]].set_ylabel('NormAmps')

        # for phase
        ax[bx[index],by[index]].set_ylim((-20,60))
        if advanced:
            ax[bx[index],by[index]].set_ylim((-30,90))

        ax[bx[index],by[index]].grid()
        if sat_legend and (ww > 0):
            ax[bx[index],by[index]].legend(loc='upper right',fontsize=fs-2)

        fig.autofmt_xdate() # set for datetime

        # for normalized amplitude plot, only triggered by advanced setting
        if advanced:
            fig2.autofmt_xdate() # set for datetime
            ax2[bx[index],by[index]].grid()
            if sat_legend and (ww > 0):
                ax2[bx[index],by[index]].legend(loc='upper right',fontsize=fs-2)

    ftmp.close()

    if remove_bad_tracks:
        print('Writing out a new list of good satellite tracks to ', oldlist)
        subprocess.call(['mv','-f', newlist, oldlist])
    else:
        subprocess.call(['rm','-f', newlist ])

    # Generate azimuth plot filename with temporal suffix
    suffix = qp.get_temporal_suffix(freq, bin_hours, bin_offset)
    qp.save_vwc_plot(fig,  f'{xdir}/Files/{subdir_path}/{station}_az_phase{suffix}.png')

    if advanced:
        qp.save_vwc_plot(fig2,  f'{xdir}/Files/{subdir_path}/{station}_az_normamp{suffix}.png')
    
    # Close figures to prevent them from showing on screen when plt=False
    if not plt:
        matplt.close(fig)
        if advanced:
            matplt.close(fig2)

    # Plot averaged phase data, from before vegetation correction
    if plt:
        qp.subdaily_phase_plot(station, fr, vxyz, xdir, subdir_path, hires_figs, bin_hours, bin_offset, minvalperbin, plt2screen=plt)

    # Write all_phase.txt file if requested
    if save_tracks:
        fname_phase = f'{xdir}/Files/{subdir_path}/{station}_all_phase.txt'
        qp.write_phase_for_advanced(fname_phase, vxyz)

    # ========================================================================
    # TRACK-LEVEL PHASE DATA (vxyz)
    # ========================================================================
    #
    # vxyz contains individual satellite track observations (N x 16 array):
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
    #       [12] quadrant (1-4)
    #       [13] delRH (RH - apriori_RH, meters)
    #       [14] vegMask (vegetation mask flag)
    #       [15] MJD (Modified Julian Day)
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
            station, vxyz, subdir_path,
            bin_hours, bin_offset, plt2screen=plt, fr=fr,
            minvalperbin=minvalperbin)
    elif veg_model == 2:
        print('Running advanced vegetation model (model 2)...')
        vwc_data = avc.advanced_vegetation_filter(
            station, vxyz, subdir_path,
            bin_hours, bin_offset, plt, fr, minvalperbin,
            save_tracks)
    else:
        print(f'Unknown vegetation model: {veg_model}. Use 1 (simple) or 2 (advanced).')
        sys.exit()

    # Check if vegetation correction produced results
    if not vwc_data or len(vwc_data.get('vwc', [])) == 0:
        print('No vegetation-corrected VWC values produced. Exiting.')
        sys.exit()

    # Apply baseline leveling
    print('\nApplying baseline leveling...')
    leveled_vwc, leveling_info = qp.apply_vwc_leveling(
        vwc_data['vwc'], tmin,
        simple=simple_level,
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
        suffix = qp.get_temporal_suffix(fr, bin_hours, bin_offset)
        plot_suffix = suffix.replace('.txt', '.png')

        if hires_figs:
            plot_path = f'{xdir}/Files/{subdir_path}/{station}_vol_soil_moisture{plot_suffix[:-4]}.eps'
        else:
            plot_path = f'{xdir}/Files/{subdir_path}/{station}_vol_soil_moisture{plot_suffix}'

        qp.vwc_plot(station, vwc_data['datetime'], leveled_vwc, plot_path, circles, plt2screen=plt)

        if plt:
            matplt.show()
        else:
            matplt.close('all')

    print(f'\n✓ VWC processing complete for {station}')




def main():
    args = parse_arguments()
    vwc(**args)


if __name__ == "__main__":
    main()
