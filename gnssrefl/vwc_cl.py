import argparse
import pickle
import matplotlib.pyplot as matplt
import numpy as np
import os
import scipy
import subprocess
import sys

from datetime import datetime
from pathlib import Path

import gnssrefl.phase_functions as qp
import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as gnssir

from gnssrefl.utils import str2bool, read_files_in_dir

xdir = os.environ['REFL_CODE']


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year_end", type=int)
    parser.add_argument("-fr", help="frequency", type=int)
    parser.add_argument("-plt", default=None, type=str, help="boolean for plotting to screen")
    parser.add_argument("-screenstats", default=None, type=str, help="boolean for plotting statistics to screen")
    parser.add_argument("-min_req_pts_track", default=None, type=int, help="min number of points for a track to be kept. Default is 50")
    parser.add_argument("-polyorder", default=None, type=int, help="override on polynomial order")
    parser.add_argument("-minvalperday", default=None, type=int, help="min number of satellite tracks needed each day. Default is 10")
    parser.add_argument("-snow_filter", default=None, type=str, help="boolean, try to remove snow contaminated points. Default is F")
    parser.add_argument("-subdir", default=None, type=str, help="use non-default subdirectory for output files")
    parser.add_argument("-tmin", default=None, type=float, help="minimum soil texture. Default is 0.05.")
    parser.add_argument("-tmax", default=None, type=float, help="maximum soil texture. Defafult is 0.50.")
    parser.add_argument("-warning_value", default=None, type=float, help="Phase RMS (deg) threshold for bad tracks, default is 5.5 degrees")
    parser.add_argument("-auto_removal", default=None, type=str, help="Whether you want to remove bad tracks automatically, default is False")
    parser.add_argument("-hires_figs", default=None, type=str, help="Whether you want eps instead of png files")
    parser.add_argument("-advanced", default=None, type=str, help="Whether you want to implement advanced veg model (in development)")

    args = parser.parse_args().__dict__

    boolean_args = ['plt','screenstats','snow_filter','auto_removal','hires_figs','advanced']
    args = str2bool(args, boolean_args)
    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def vwc(station: str, year: int, year_end: int = None, fr: int = 20, plt: bool = True, screenstats: bool = False, 
        min_req_pts_track: int = 150, polyorder: int = -99, minvalperday: int = 10, 
        snow_filter: bool = False, subdir: str=None, tmin: float=None, tmax: float=None, 
        warning_value : float=5.5, auto_removal : bool=False, hires_figs : bool=False, advanced : bool=False ):
    """
    The goal of this code is to compute volumetric water content (VWC) from GNSS-IR phase estimates. 
    It concatenates previously computed phase results, makes plots for the four geographic quadrants, computes daily 
    average phase files before converting to volumetric water content (VWC). It uses the simple vegetation model
    from Clara Chew's dissertation. For the more advanced vegetation model, we will need a volumteer to convert it from Matlab.
    It is not a difficult port - but it will require care be taken that it is checked carefully.


    Code now allows inputs (minvalperday, tmin, and tmax) to be stored in the gnssir analysis json file.
    To avoid confusion, in the json they are called vwc_minvalperday, vwc_min_soil_texture, and vwc_max_soil_texture.
    These values can also be overwritten on the command line ... 

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
        subdirectory in $REFL_CODE/Files for plots and text file outputs
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
         advanced veg model implmentation. Currently in testing

    Returns
    -------

    Daily phase results in a file at $REFL_CODE/Files/<station>/<station>_phase.txt
        with columns: Year DOY Ph Phsig NormA MM DD

    VWC results in a file at $$REFL_CODE/Files/<station>/<station>_vwc.txt
        with columns: FracYr Year DOY  VWC Month Day

    """
    fs =10 # fontsize
    snow_file = None
    colors = 'mrgbcykmrgbcykmrbcykmrgbcykmrgbcykmrbcyk'
    # plotting indices for phase data
    by=[0,1,0,1]; bx=[0,0,1,1]
    # azimuth list, starting point only (i.e. 270 means 270 thru 360)
    azlist = [270, 0, 180,90 ]
    # consistency with old adv vegetation code
    oldquads = [2, 1, 3, 4] # number system from pboh2o, only used for 

    # pick up the parameters used for this code
    minvalperday, tmin, tmax, min_req_pts_track, freq, year_end, subdir, plt, \
            remove_bad_tracks, warning_value,min_norm_amp,sat_legend,circles= \
            qp.set_parameters(station, minvalperday, tmin,tmax, min_req_pts_track, 
                              fr, year, year_end,subdir,plt, auto_removal,warning_value)

    # if you have requested snow filtering
    if snow_filter:
        medf = 0.2 # this is meters , so will only see big snow 
        ReqTracks = 10 # have a pretty small number here
        print('You have chosen the snow filter option')
        snowfileexists,snow_file = qp.make_snow_filter(station, medf, ReqTracks, year, year_end+1)
        matplt.close ('all')# we do not want the plots to come to the screen for the daily average

    # load past VWC analysis  for QC
    avg_exist, avg_date, avg_phase = qp.load_avg_phase(station,freq)

    # pick up all the phase data. unwrapped phase is stored in the results variable
    data_exist, year_sat_phase, doy, hr, phase, azdata, ssat, rh, amp_lsp,amp_ls,ap_rh, results = \
            qp.load_phase_filter_out_snow(station, year, year_end, fr,snow_file)


    if not data_exist:
        print('No data were found. Check your frequency request or station name')
        sys.exit()

    # using unwrapped phase instead of raw phase
    phase = results[17,:]
    
    # pick up the tracks you will use to compute phase.  THis was previously
    # created by vwc_input ...
    tracks = qp.read_apriori_rh(station,freq)
    nr = len(tracks[:,1])

    if (minvalperday > nr ):
        print('The code thinks you are using ', nr, ' satellite tracks but you are requiring', minvalperday, ' for each VWC point.')
        print('Try lowering minvalperday at the command line or in the gnssir analysis json (vwc_minvalperday)')
        sys.exit()
    if (nr < 15 ) and (minvalperday==10):
        print('The code thinks you are using ', nr, ' satellite tracks but that is pretty close to the default (', minvalperday, ')')
        print('This could be problematic. Try lowering minvalperday at the command line or in the gnssir analysis json (vwc_minvalperday)')
        sys.exit()

    atracks = tracks[:, 5]  # min azimuth values
    stracks = tracks[:, 2]  # satellite names

    k = 1
    # define the contents of this variable HERE
    vxyz = np.empty(shape=[0, 15]) 
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


    # this is the number of points for a given satellite track
    # just reassigning hte variable name
    reqNumpts = min_req_pts_track

    # KL disclosure
    # this code was written as a quick port between matlab and python
    # it does use many of the nice features of python variables. 
    
    # checking each geographic quadrant
    k4 = 1
    # two list of tracks - lets you compare an old run with a new run as a form of QC
    newlist = station + '_tmp.txt'
    oldlist = xdir + '/input/' + station + '_phaseRH.txt'

    ftmp = open(newlist,'w+')
    ftmp.write("{0:s} \n".format( '% station ' + station) )
    ftmp.write("{0:s} \n".format( '% TrackN  RefH SatNu MeanAz  Nval  Azimuths'))
    # open up a figure for the phase results by quadrant
    fig,ax = matplt.subplots(2, 2, figsize=(10,10))
    matplt.suptitle(f"Station: {station}", size=12)

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
            y,t,h,x,azd,s,amp_lsps,amp_lss,rhs,ap_rhs = \
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

                y,t,h,new_phase,azd,s,amp_lsps,amp_lss,rhs,ap_rhs = \
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
                    # just wondering
                    if advanced:
                        ii = (new_phase > -30) & (new_phase < 100)

                    y,t,h,new_phase,azd,s,amp_lsps,amp_lss,rhs,ap_rhs = \
                            qp.rename_vals(y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs, ii)

                    sortY = np.sort(new_phase)
                    # looks like I am using the bottom 20% 
                    NN = int(np.round(0.2*len(sortY)))
                    mv = np.median(sortY[0:NN])
                    new_phase = new_phase - mv
                    fracyear = y + t/365.25

                    newl = np.vstack((y, t, new_phase, azd)).T
                    vquad = np.vstack((vquad, newl))
                    if screenstats:
                        print('here0')

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

                    newl2 = np.vstack((y, t, new_phase, azd, s, rhs, norm_ampLSP,norm_ampLS,h,amp_lsps,amp_lss,ap_rhs,qs,delRH,vegMask.T)).T
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
                            print('some issue with the smoothing')
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

    qp.save_vwc_plot(fig,  f'{xdir}/Files/{subdir}/{station}_az_phase.png')

    if advanced:
        qp.save_vwc_plot(fig2,  f'{xdir}/Files/{subdir}/{station}_az_normamp.png')


    #Need to Define clearly the stored values in vxyz

    if advanced:
        print('Still working on the advanced option. Exiting.')
        fname_phase = f'{xdir}/Files/{subdir}/{station}_all_phase.txt'
        qp.write_phase_for_advanced(fname_phase, vxyz)

        if plt:
            matplt.show()
        sys.exit()
    else:
        # write out daily phase values
        tv = qp.write_avg_phase(station, phase, fr,year,year_end,minvalperday,vxyz,subdir)
        print('Number of daily phase measurements ', len(tv))
        if len(tv) < 1:
            print('No results - perhaps minvalperday or min_req_pts_track are too stringent')
            sys.exit()

        # make datetime date array
        datetime_dates = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(tv[:, 0], tv[:, 1])]

        # make a plot of daily phase values
        qp.daily_phase_plot(station, fr,datetime_dates, tv,xdir,subdir,hires_figs)

        # convert daily phase values to volumetric water content
        qp.convert_phase(station, year, year_end, plt,fr,tmin,tmax,polyorder,circles,subdir,hires_figs)


def main():
    args = parse_arguments()
    vwc(**args)


if __name__ == "__main__":
    main()
