import argparse
import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from pathlib import Path

import gnssrefl.phase_functions as qp
import gnssrefl.gps as g
from gnssrefl.utils import str2bool, read_files_in_dir

xdir = os.environ['REFL_CODE']


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year_end", type=int)
    parser.add_argument("-fr", help="frequency", type=int)
    parser.add_argument("-plt2screen", default=None, type=str, help="boolean for plotting to screen")
    parser.add_argument("-screenstats", default=None, type=str, help="boolean for plotting statistics to screen")
    parser.add_argument("-min_req_pts_track", default=None, type=int, help="minimum number of points for a track to be kept. Default is 50")
    parser.add_argument("-polyorder", default=None, type=int, help="override on polynomial order")
    parser.add_argument("-minvalperday", default=None, type=int, help="minimum number of satellite tracks needed each day. Default is 10")
    parser.add_argument("-snow_filter", default=None, type=str, help="boolean for attempting to remove days contaminated by snow")
    parser.add_argument("-circles", default=None, type=str, help="circles instead of lines for the final VWC plot ")
    parser.add_argument("-subdir", default=None, type=str, help="use non-default subdirectory for output files")

    args = parser.parse_args().__dict__

    boolean_args = ['plt2screen','screenstats','snow_filter','circles']
    args = str2bool(args, boolean_args)
    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def filter_out_snow(station, year1, year2, fr,snowmask):
    """
    attempt to remove outliers from snow. only called if the snow filter file exists

    Parameters
    ----------
    station : str
        four character station name

    year1 : integer
        starting year

    year2 : integer
        ending year

    fr : integer
        frequency

    snowmask : str
        name/location of the snow mask file

    """
    xdir = os.environ['REFL_CODE']
    found_override = False
    if os.path.exists(snowmask):
        print('found snow file')
        override = np.loadtxt(snowmask, comments='%')
        found_override = True

#   now load the phase data
    newresults = []
    results_trans = []
    #vquad = np.vstack((vquad, newl))
    vquad = np.empty(shape=[0, 16])

    if found_override:
        dataexist, year, doy, hr, ph, azdata, ssat, rh, amp,results = load_sat_phase(station, year1,year2, fr)
        # results were originally transposed - so untransposing them 
        results = results.T
        for year in range(year1,year2+1):
            ii = (results[:,0] == year) & (results[:,12] == fr)
        # it is easier for me to do this year by year
            y = results[ii,0];
            d = results[ii,1]
            ph = results[ii,3]
            thisyear_results = results[ii,:]
        # the goal is to find all the results that do not appear in the override list
            jj = (override[:,0] == year) # find days when there are suspects points
            targetdoys = override[jj,1]
            #print(year, ' length of d', len(d))
            # the mask asks when is d distinct from targetdoys
            mask=np.logical_not(np.isin(d,targetdoys))
            #print(year, ' length of dmasked', len(d[mask]))
            masked_results = thisyear_results[mask]
            newresults = np.append(newresults, masked_results)
            #vquad = np.vstack((vquad, thisyear_results[mask] ) )
            vquad = np.append(vquad, masked_results,axis=0)

    # change to numpy?
    nr,nc = np.shape(vquad)
    print('Number of rows and columns now ', nr,nc)

    # 
    results_trans= np.transpose(vquad)

    print(np.shape(results_trans))

    if len(results_trans) == 0:
        print('no data ')
        dataexist = False
        year = []; doy = []; hr = []; ph = []; azdata = []; ssat = []
        rh = []; amp = []
    else:
        dataexist = True
        # save with new variable names
        year = results_trans[0]
        doy = results_trans[1]
        hr = results_trans[2]
        ph = results_trans[3]
        azdata = results_trans[5]
        ssat = results_trans[6]
        rh = results_trans[13]
        amp = results_trans[15]

# use same return command as in the original function
    return dataexist, year, doy, hr, ph, azdata, ssat, rh, amp, results_trans


def load_avg_phase(station,fr):
    """
    loads a previously computed daily average phase solution.
    this is NOT the same as the multi-track phase results.
    This file is now stored in station subdirectory in $REFL_CODE/Files/

    Parameters
    ----------
    station : str
        4 character station ID, lowercase

    Returns
    -------
    avg_exist : boolean

    avg_date : ??

    avg_phase : ??

    """


    avg_date = []
    avg_phase = []
    avg_exist = False

    if fr == 1:
        xfile = f'{xdir}/Files/{station}/{station}_phase_L1.txt'
    else:
        xfile = f'{xdir}/Files/{station}/{station}_phase.txt'

    if os.path.exists(xfile):
        result = np.loadtxt(xfile, comments='%')
        if len(result) > 0:
            year = result[:, 0]
            day = result[:, 1].astype(int)
            phase = result[:, 2]
            # change to integers from float, though not necessary since i'm using float date...
            avg_date = year + day/365.25
            avg_phase = phase
            avg_exist = True

    return avg_exist, avg_date, avg_phase


def load_sat_phase(station, year, year_end, freq):
    """
    Picks up the phase data from local results section
    return to main code whether dataexist, and np arrays of year, doy, hr, phase, azdata, ssat

    Parameters
    ----------
    station : str
        four character station name
    year : integer
        beginning year
    year_end : integer
        ending year
    freq : integer
        GPS frequency (1,20 allowed)

    Returns
    -------
    dataexist : bool
        whether data found?
    year : numpy array of int
        full years
    doy : numpy array of int
        days of year
    hr : float
        fractional day (UTC)
    ph : float
        phases (deg)
    azdata : float
        azimuths (deg)
    ssat : int
        satellites (deg)
    rh : float
        reflector height (m)
    amp : float
        amplitudes of peak LSP 

    results : ??

    """
    print('Requested frequency: ', freq)
    dataexist = False

    xfile = xdir + '/input/override/' + station + '_vwc' 
    found_override = False
    # not implementing this yet
    if os.path.exists(xfile):
        print('found override file but not implementing at this time')
    #    override = np.loadtxt(xfile, comments='%')
    #    found_override = True

    thedir = Path(os.environ["REFL_CODE"])

    if not year_end:
        year_end = year

    results = []
    for year in np.arange(year, year_end+1):
        # where the results are stored
        data_dir = thedir / str(year) / 'phase' / station
        local_results = read_files_in_dir(data_dir)
        if local_results:
            results.extend(local_results)

    if not results:
        print(f"No results were found for the year range you requested: ({year}-{year_end})")
        sys.exit()

    results = np.array(results)
    freq_list = results[:, 12]
    ii = (freq_list == freq)
    results = results[ii, :]
    print('Total phase measurements for this frequency: ', len(results))
#    common_elements, ar1_i, ar2_i = np.intersect1d(ar1, ar2, return_indices=True)
    minyear = np.min(np.unique(results[:,0]))
    maxyear = np.max(np.unique(results[:,0]))
    #print(minyear,maxyear)
    nr,nc = np.shape(results)
    print(nr, ' number of rows')

    results = results.T  # dumb, but i was using this convention.  easier to maintain

    if len(results) == 0:
        print('no data at that frequency')
        year = []; doy = []; hr = []; ph = []; azdata = []; ssat = []
        rh = []; amp = []
    else:
        dataexist = True
        # save with new variable names 
        year = results[0]
        doy = results[1]
        hr = results[2]
        ph = results[3]
        azdata = results[5]
        ssat = results[6]
        rh = results[13]
        amp = results[15]

    return dataexist, year, doy, hr, ph, azdata, ssat, rh, amp, results


def normAmp(amp, basepercent):
    """
    emulated amp_normK code from PBO H2O
    inputs are the amplitudes  and a percentage
    used to define the bottom level. returns
    normalized amplitudes
    this is meant to be used by individual tracks (I think)
    in this case they are the top values, not the bottom ... ugh
    """
    Namp = amp
    N=len(amp)
    if (N > 0):
        numx = int(np.round(N*basepercent) )

        if (numx==0):
            numx = N

        sortA = -np.sort(-amp)
        topavg = np.mean(sortA[0:numx])

        # this comes from Clara's Recommendations, amp_normK.m
        Namp = amp/topavg

    return Namp


def vwc(station: str, year: int, year_end: int = None, fr: int = 20, plt2screen: bool = True, screenstats: bool = False, 
        min_req_pts_track: int = 50, polyorder: int = -99, minvalperday: int = 10, 
        snow_filter: bool = False, circles: bool=False, subdir: str=None):
    """
    Code to pick up phase results, make quadrant plots, daily average files and converts to volumetric water content (VWC).

    Parameters
    ----------
    station : st
        4 character ID of the station

    year : integer
        Year

    year_end : integer
        Day of year

    fr : integer, optional
        GNSS frequency. Currently only supports l2c.
        Default is 20 (l2c)

    plt2screen: boolean, optional
        Whether to produce plots to the screen.
        Default is True

    min_req_pts_track : integer
        how many points needed to keep a satellite track
        default is 50

    polyorder : integer
        This is used for leveling.  Usually the code picks it but this allows to users to override. 
        Default is -99 which means let the code decide

    minvalperday: integer
        how many phase measurements are needed for each daily measurement
        default is 10

    snow_filter: boolean 
        whether you want to attempt to remove points contaminated by snow
        default is False

    circles : boolean
        whether you want circles in the final plot (lines are default)

    subdir: str
        subdirectory in $REFL_CODE/Files for plots and text file outputs

    Returns
    -------

    Returns daily phase results in a file at $REFL_CODE/<year>/phase/<station>_phase.txt
        with columns: Year DOY Ph Phsig NormA MM DD

    Returns the VWC results in a file at $$REFL_CODE/<year>/phase/<station>_vwc.txt
        with columns: FracYr Year DOY  VWC Month Day
    """
    if (len(station) != 4):
        print('station name must be four characters')
        sys.exit()

    if (len(str(year)) != 4):
        print('Year must be four characters')
        sys.exit()

    freq = fr # KE kept the other variable

    if not year_end:
        year_end = year

    # default is station name
    if subdir == None:
        subdir = station 

    # make sure subdirectory exists
    g.set_subdir(subdir)

    if not plt2screen:
        print('no plots will come to screen. Will only be saved.')

    # this is leftover from the old code
    writeout = True

    snow_file = xdir + '/Files/snowmask_' + station + '.txt'
    snowfileexists = False
    if snow_filter:
        medf = 0.2 # this is meters
        ReqTracks = 10 # have a pretty small number here
        snowfileexists = qp.make_snow_filter(station, medf, ReqTracks, year, year_end)
        plt.close ('all')# we do not want the plots to come to the screen for the daily average

    # azimuth list
    azlist = [270, 0, 180,90 ]

    # load past analysis  for QC
    avg_exist, avg_date, avg_phase = load_avg_phase(station,freq)
    if not avg_exist:
        print('WARNING: the average phase file from a previous run does not exist as yet')

    if snowfileexists and snow_filter :
        print('using snow filter code')
        # use same variables as existing code
        data_exist, year_sat_phase, doy, hr, phase, azdata, ssat, rh, amp,ext = filter_out_snow(station, year, year_end, fr,snow_file)
    else:
        data_exist, year_sat_phase, doy, hr, phase, azdata, ssat, rh, amp,ext = load_sat_phase(station, year, year_end=year_end, freq=freq)

    if not data_exist:
        print('No data were found. Check your frequency request or station name')
        sys.exit()

    
    tracks = qp.read_apriori_rh(station,freq)
    nr = len(tracks[:,1])

    if (minvalperday > nr ):
        print('The code thinks you are using ', nr, ' satellite tracks but you are requiring', minvalperday, ' for each VWC point.')
        print('Try lowering minvalperday at the command line')
        sys.exit()
    if (nr < 15 ) and (minvalperday==10):
        print('The code thinks you are using ', nr, ' satellite tracks but that is pretty close to the default (', minvalperday, ')')
        print('This could be problematic. Try lowering minvalperday at the command line')
        sys.exit()

    atracks = tracks[:, 5]  # min azimuth values
    stracks = tracks[:, 2]  # satellite names

    # column 3 is sat, 4 is azimuth, npoints is 5, azim is 6 and 7
    k = 1
    vxyz = np.empty(shape=[0, 7]) 

    # try removing these
    fig = plt.figure(figsize=(13, 10))
    ax=plt.subplots_adjust(hspace=0.2)
    plt.suptitle(f"Station: {station}", size=16)

    # this is the number of points for a given satellite track
    reqNumpts = min_req_pts_track

    # checking each geographic quadrant
    for index, az in enumerate(azlist):
        b = 0
        k += 1
        amin = az
        amax = az + 90
        # make a quadrant average for plotting purposes
        vquad = np.empty(shape=[0, 4])
        # pick up the sat list from the actual list
        satlist = stracks[atracks == amin]

        ax = plt.subplot(2, 2, index + 1)
        ax.set_title(f'Azimuth {str(amin)}-{str(amax)} deg.')
        ax.grid()
        #ax.autofmt_xdate()

        # this satellite list is really satellite TRACKS
        for satellite in satlist:
            if screenstats:
                print(satellite, amin, amax)
            # indices for the track you want to look at here
            ii = (ssat == satellite) & (azdata > amin) & (azdata < amax) & (phase < 360)
            x = phase[ii]
            t = doy[ii]
            h = hr[ii] # TODO this is never used
            y = year_sat_phase[ii]
            azd = azdata[ii]
            s = ssat[ii]
            amps = amp[ii]
            rhs = rh[ii]

            if len(x) > reqNumpts:
                b += 1
                sortY = np.sort(x)

                N = len(sortY)
                NN = int(np.round(0.20*N))

                # use median value instead
                medv = np.median(sortY[(N-NN):(N-1)])
                new_phase = -(x-medv)
                ii = (new_phase > -20)
                t = t[ii]
                y = y[ii]
                new_phase = new_phase[ii]
                azd = azd[ii]
                s = s[ii]
                amps = amps[ii]
                rhs = rhs[ii]
                if len(t) == 0:
                    print('you should consider removing this satellite track', sat, amin)

                if (len(t) > reqNumpts):
                    for l in range(0, len(t)-1):
                        if new_phase[l] > 340:
                            new_phase[l] = new_phase[l] - 360
                    ii = (new_phase > -20) & (new_phase < 60)
                    t = t[ii]
                    y = y[ii]
                    new_phase = new_phase[ii]
                    azd = azd[ii]
                    s = s[ii]
                    amps = amps[ii]
                    rhs = rhs[ii]
                    sortY = np.sort(new_phase)
                    # bottom 20% ???
                    NN = int(np.round(0.2*len(sortY)))
                    mv = np.median(sortY[0:NN])
                    new_phase = new_phase - mv
                    # probably should take out median value again

                    newl = np.vstack((y, t, new_phase, azd)).T
                    vquad = np.vstack((vquad, newl))

                    basepercent = 0.15
                    normAmps = normAmp(amps, basepercent)
                    newl = np.vstack((y, t, new_phase, azd, s, rhs, normAmps)).T

                    if (len(newl) > 0) and (avg_exist):
                        # quadrant results for this satellite track
                        satdate = y + t/365.25
                        satphase = new_phase

                        # figure out intersetion with "good" results
                        inter, id1, id2 = np.intersect1d(avg_date, satdate, assume_unique=True, return_indices=True)
                        aa = avg_phase[id1]
                        bb = satphase[id2]
                        if len(aa) > 0:
                            res = np.round(np.std(aa - bb), 2)
                            addit = ''
                            if res > 5.5:
                                addit = '>>>>>  Consider Removing This Track <<<<<'
                            print(f"Npts {len(aa):4.0f} SatNu {satellite:2.0f} Residual {res:6.2f} Azims {amin:3.0f} {amax:3.0f} Amp {max(normAmps):4.2f} {addit:20s} ")
                        else:
                            print('No QC assessment could be made for this satellite track')
                    else:
                        print('No average , so no QC. You should iterate.')


                    # cumulative values
                    vxyz = np.vstack((vxyz, newl))
                    datetime_dates = []
                    for yr, d in zip(y, t):
                        datetime_dates.append(datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j'))

                    ax.plot(datetime_dates, new_phase, 'o', markersize=3)
                    ax.set_ylabel('Phase')
                    #ax.set_ylimit((-20,60))
                    plt.ylim((-20,60))
                    # ???
                    plt.gcf().autofmt_xdate()


    plot_path = f'{xdir}/Files/{subdir}/{station}_az_phase.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)

    # this is now done in a function. i believe this can be commented out
    #tv = np.empty(shape=[0, 4])
    # year, day of year, phase, satellite, azimuth, RH, and RH amplitude
    y1 = vxyz[:, 0]
    d1 = vxyz[:, 1]
    phase = vxyz[:, 2]
    #sat = vxyz[:, 3] # TODO this is not used
    #az = vxyz[:, 4] # TODO this is not used
    #rh = vxyz[:, 5] # TODO this is not used
    amp = vxyz[:, 6]

    # this is the number of tracks per day you need to trust the daily average
    #minvalperday = 10 - now an input
    if writeout:

        tv = qp.write_avg_phase(station, phase, fr,year,year_end,minvalperday,vxyz,subdir)
        print('Number of daily phase measurements ', len(tv))
        if len(tv) < 1:
            print('No results - perhaps minvalperday or min_req_pts_track are too stringent')
            sys.exit()

        # make datetime date array
        datetime_dates = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(tv[:, 0], tv[:, 1])]

        qp.daily_phase_plot(station, fr,datetime_dates, tv,xdir,subdir)

        qp.convert_phase(station, year, year_end, plt2screen,fr,polyorder,circles,subdir)


def main():
    args = parse_arguments()
    vwc(**args)


if __name__ == "__main__":
    main()
