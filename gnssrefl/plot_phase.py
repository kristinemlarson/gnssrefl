import argparse
import os
import sys
import subprocess
import numpy as np
import matplotlib.pyplot as plt

from datetime import datetime
from pathlib import Path

import gnssrefl.quickPhase_function as qp
import gnssrefl.gps as g
from gnssrefl.utils import str2bool, read_files_in_dir

xdir = os.environ['REFL_CODE']


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("-year_end", default=None, help="year_end", type=int)
    parser.add_argument("-freq", help="frequency", type=int)
    parser.add_argument("-sat", default=None, type=int, help="satellite")
    parser.add_argument("-plt2screen", default=None, type=str, help="plot to screen")

    args = parser.parse_args().__dict__

    boolean_args = ['plt2screen']
    args = str2bool(args, boolean_args)
    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def load_avg_phase(station):
    """
    parameters
    -----------
    station : string
        4 character ID, lowercase

    returns
    --------
    avg_exist : boolean

    avg_date : ??

    avg_phase : ??

    """
    avg_date = []
    avg_phase = []
    avg_exist = False

    xfile = f'{xdir}/Files/{station}_phase.txt'

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
    given station name and frequency, pick up the phase data from local results section
    return to main code whether dataexist, and np arrays of year, doy, hr, phase, azdata, ssat

    return reflector heights and amplitudes
    """
    print('Requested frequency: ', freq)
    dataexist = False
    #subprocess.call(['rm', '-f', 'tmp.txt'])
    #txtdir = 'echo \%  > tmp.txt'
    #os.system(txtdir)

    dir = Path(os.environ["REFL_CODE"])

    if not year_end:
        year_end = year

    results = []
    for year in np.arange(year, year_end+1):
        # where the results are stored
        data_dir = dir / str(year) / 'phase' / station
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
    results = results.T  # dumb, but i was using this convention.  easier to maintain

    if len(results) == 0:
        print('no data at that frequency')
        year = []
        doy = []
        hr = []
        ph = []
        azdata = []
        ssat = []
        rh = []
        amp = []
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
    return dataexist, year, doy, hr, ph, azdata, ssat, rh, amp


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


def do_quad(vquad, year, year_end):
    """
    stacks all the phase results for a given quadrant
    returns 3 vector (year, doy, phase)
    requires 5 for an average

    """
    vout = np.empty(shape=[0, 3])
    y1 = vquad[:, 0]
    d1 = vquad[:, 1]
    phq = vquad[:, 2]
    for year in range(year, year_end+1):
        for doy in range(1, 367):
            ph1 = phq[(y1 == year) & (d1 == doy)]
            if len(ph1) > 3:
                meanphase = np.mean(ph1)
                newl = np.hstack((year, doy, meanphase))
                # in which kristine learns tha vertically stacking
                # the transpose is the same as horizontally stacking ;-)
                #newl = np.vstack((year,doy,meanphase)).T
                vout = np.vstack((vout, newl))
    return vout


def plot_phase(station: str, year: int, year_end: int = None, freq: int = 20, sat: int = None, plt2screen: bool = True):
    """
    Code to pick up phase results, make quadrant plots, daily average files and converts to volumetric water content (VWC).
    Parameters:
    ___________
    station : string
        4 character ID of the station

    year : integer
        Year

    year_end : integer
        Day of year

    freq : integer, optional
        GNSS frequency. Currently only supports l2c.
        Default is 20 (l2c)

    sat: integer, optional
        Satellite number.
        Default is None

    plt2screen: boolean, optional
        Whether to produce plots to the screen.
        Default is True

    Returns
    _______
    Returns two files:

    - Returns daily phase results in a file at $REFL_CODE/<year>/phase/<station>_phase.txt
        with columns: Year DOY Ph Phsig NormA MM DD

     - Returns the VWC results in a file at $$REFL_CODE/<year>/phase/<station>_vwc.txt
        with columns: FracYr Year DOY  VWC
    """

    if not year_end:
        year_end = year

    if not plt2screen:
        print('no plots will come to screen. Will only be saved.')

    # l2c list
    # if you don't ask for a special satellite, assume they want to write out the average
    if (sat is None) and (freq == 20):
        writeout = True
    else:
        writeout = False
        print('An average file will not be produced.')

    # azimuth list
    azlist = [270, 0, 180,90 ]

    # load past analysis  for QC
    avg_exist, avg_date, avg_phase = load_avg_phase(station)
    if not avg_exist:
        print('WARNING: the average phase file does not exist as yet')

    data_exist, year_sat_phase, doy, hr, phase, azdata, ssat, rh, amp = load_sat_phase(station, year, year_end=year_end, freq=freq)
    if not data_exist:
        print('No data were found. Check your frequency request or station name')
        sys.exit()

    
    tracks = qp.read_apriori_rh(station)
    atracks = tracks[:, 5]  # min azimuth values
    stracks = tracks[:, 2]  # satellite names

    # column 3 is sat, 4 is azimuth, npoints is 5, azim is 6 and 7
    k = 1
    vxyz = np.empty(shape=[0, 7])

    # try removing these
    plt.figure(figsize=(13, 10))
    ax=plt.subplots_adjust(hspace=0.2)
    #plt.suptitle(f"Station: {station}", size=16)

    for index, az in enumerate(azlist):
        b = 0
        k += 1
        amin = az
        amax = az + 90
        # make a quadrant average for plotting purposes
        vquad = np.empty(shape=[0, 4])
        # pick up the sat list from the actual list
        if sat is None:
            satlist = stracks[atracks == amin]
        else:
            satlist = [int(sat)]

        ax = plt.subplot(2, 2, index + 1)
        ax.set_title(f'Azimuth {str(amin)}-{str(amax)} deg.')
        ax.grid()

        #ax.autofmt_xdate()


        for satellite in satlist:
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

            # this is the number of points in a whole year for a given satellite ??? 
            reqNumpts = 50
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
                        res = np.round(np.std(aa - bb), 2)
                        addit = ''
                        if res > 5.5:
                            addit = '>>>>>  Consider Removing This Track <<<<<'
                        print(f"Npts {len(aa):4.0f} SatNu {satellite:2.0f} Residual {res:6.2f} Azims {amin:5.0f} {amax:5.0f} Amp {max(normAmps):4.2f} {addit:20s} ")
                    else:
                        print('No average , so no QC. You should iterate.')


                    # cumulative values
                    vxyz = np.vstack((vxyz, newl))
                    datetime_dates = []
                    for yr, d in zip(y, t):
                        datetime_dates.append(datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j'))

                    ax.plot(datetime_dates, new_phase, 'o', markersize=3)
                    ax.set_ylabel('Phase')


    plot_path = f'{xdir}/Files/{station}_az_phase.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)
    #if plt2screen:
    #    plt.show()

        # TODO is this used? (the line below)
        # vout = do_quad(vquad, year, year_end)
        #plt.plot(vout[:,0] + vout[:,1]/365.25, vout[:,2], 'ko')
        #plt.subplot(211)

    tv = np.empty(shape=[0, 4])
    # year, day of year, phase, satellite, azimuth, RH, and RH amplitude
    y1 = vxyz[:, 0]
    d1 = vxyz[:, 1]
    phase = vxyz[:, 2]
    sat = vxyz[:, 3] # TODO this is not used
    az = vxyz[:, 4] # TODO this is not used
    rh = vxyz[:, 5] # TODO this is not used
    amp = vxyz[:, 6]

    # 10 required for each day?
    if writeout:
        fileout = xdir + '/Files/' + station + '_phase.txt'
        print('Daily averaged phases: ', fileout)
        with open(fileout, 'w') as fout:
            fout.write("% Year DOY Ph Phsig NormA MM DD \n")
            for requested_year in range(year, year_end + 1):
                for doy in range(1, 367):
                    # put in amplitude criteria to keep out bad L2P results
                    ph1 = phase[(y1 == requested_year) & (d1 == doy) & (phase > -10) & (amp > 0.65)]
                    amp1 = amp[(y1 == requested_year) & (d1 == doy) & (phase > -10) & (amp > 0.65)]
                    if len(ph1) > 10:
                        newl = [requested_year, doy, np.mean(ph1), len(ph1)]
                        # i think you normalize the individual satellites before this step
                        #namp = qp.normAmp(amp1,0.15)
                        tv = np.append(tv, [newl], axis=0)
                        rph1 = np.round(np.mean(ph1), 2)
                        meanA = np.mean(amp1)
                        rph1_std = np.std(ph1)
                        yy, mm, dd, cyyyy, cdoy, YMD = g.ydoy2useful(requested_year, doy)
                        fout.write(f" {requested_year:4.0f} {doy:3.0f} {rph1:6.2f} {rph1_std:6.2f} {meanA:6.3f} {0.0:5.2f}   {mm:2.0f} {dd:2.0f} \n")

        datetime_dates = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(tv[:, 0], tv[:, 1])]

        plt.figure(figsize=(10, 6))
        plt.plot(datetime_dates, tv[:, 2], 'bo')
        plt.ylabel('phase (degrees)')
        plt.title(f"Daily Phase Results: {station.upper()}")
        plt.grid()
        plot_path = f'{xdir}/Files/{station}_daily_phase.png'
        print(f"Saving figure to {plot_path}")
        plt.savefig(plot_path)

        #now convert to vwc
        qp.convert_phase(station, year, year_end, plt2screen)


def main():
    args = parse_arguments()
    plot_phase(**args)


if __name__ == "__main__":
    main()
