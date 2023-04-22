import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys


import gnssrefl.gps as g
import gnssrefl.read_snr_files as read_snr
from gnssrefl.utils import FileManagement, FileTypes
import gnssrefl.daily_avg_cl as da

from functools import partial
from scipy import optimize
from scipy.interpolate import interp1d
from datetime import datetime
from pathlib import Path

from gnssrefl.utils import str2bool, read_files_in_dir

xdir = Path(os.environ["REFL_CODE"])

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

def daily_phase_plot(station, fr,datetime_dates, tv,xdir,subdir):
    """
    makes a plot of daily averaged phase

    Parameters
    ----------
    station: str
        4 char station

    fr : int
        frequency

    datetime_dates : ...

    tv : list of results

    xdir : str
        location of the results (environment variable REFL_CODE)

    subdir : str
        subdirectory in Files

    """
    outdir = xdir + '/Files/' + subdir
    plt.figure(figsize=(10, 6))
    plt.plot(datetime_dates, tv[:, 2], 'b-')
    plt.ylabel('phase (degrees)')
    if fr == 1:
        plt.title(f"Daily L1 Phase Results: {station.upper()}")
    else:
        plt.title(f"Daily L2C Phase Results: {station.upper()}")
    plt.grid()
    plt.gcf().autofmt_xdate()

    # maybe this works.  Maybe not.
    plot_path = f'{outdir}/{station}_daily_phase.png'
    print(f"Saving figure to {plot_path}")
    plt.savefig(plot_path)



def make_snow_filter(station, medfilter, ReqTracks, year1, year2):
    """
    runs daily_avg code so you have some idea of when the soil moisture products are 
    contaminated by snow. make a file with these years and doys saved

    Parameters
    ----------
    station : str
        4 ch station name

    medfilter : float
        how much you allow the individual tracks to deviate from the daily median (meters)

    ReqTracks : integer
        number of tracks to compute trustworthy daily average

    year1 : integer
        starting year

    year2 : integer
        ending year

    Returns
    -------
    snowmask_exists : boolean

    creates output file into a file $REFL_CODE/Files/snowmask_{ssss}.txt

    """
    myxdir = os.environ['REFL_CODE']
    # l2c only
    txtfile = 'test_' + station + '.txt'; 
    pltit = False; extension = ''; fr = 20; csv = False

    # writes out a daily average file. woudl be better if it returned the values, but this works
    da.daily_avg(station, medfilter, ReqTracks, txtfile, pltit,
              extension, year1, year2, fr, csv) 

    avgf = myxdir + '/Files/' + station + '/' + txtfile
    x = np.loadtxt(avgf, comments='%')
    # delete the file!
    rh = x[:,2]
    medianvalue = np.median(rh);
    print('Median RH value ', medianvalue)
    # everything within 5 cm
    ii = (rh -medianvalue) < -0.05
    newx = x[ii,:] ; N=len(newx)
    if (N > 0):
        snowfile = myxdir + '/Files/' + station + 'snowmask_' + station + '.txt' 
        print('Suspect snow values stored in : ', snowfile)
        snow = open(snowfile, 'w+')
        for i in range(0,N):
            sv = -(newx[i,2]-medianvalue)
            print('Suspect Snow Day : ', int(newx[i,0]), int(newx[i,1]))
            snow.write("{0:4.0f}  {1:3.0f} {2:8.3f}  \n".format( newx[i,0], newx[i,1], sv))
        snow.close()
    # now that you saved what you need from daily average file, delete it.

        snowmask_exists = True
    else:
        snowmask_exists = False
    subprocess.call(['rm',avgf])

    return snowmask_exists

def vwc_plot(station,t_datetime, vwcdata, plot_path,circles):
    """
    makes a plot of volumetric water content

    Parameters
    ----------
    station : string
        4 ch station name

    t_datetime : datetime 
        observation times for measurements

    vwcdata : numpy array of floats (I think)
        volumetric water content

    plot_path : string
        full name of the plot file 

    circles: boolean
        circles in the plot. default is a line (really .-)

    Saves a plot to plot_path

    """
    # i think this would work???
    # data = [[1, 2, 3, 4], [0, 2, 3, 4], [0, 0 , 3, 4], [0, 0, 0, 4]] 
    # data = np.array(data)
    # data = np.where(data == 0, np.nan, data)
    for i in range(0,len(vwcdata)):
        if vwcdata[i] > 0.5:
            vwcdata[i] = np.nan
        if vwcdata[i] < 0:
            vwcdata[i] = np.nan

    plt.figure(figsize=(10, 6))
    if circles:
        plt.plot(t_datetime, vwcdata, 'bo')
    else:
        plt.plot(t_datetime, vwcdata, 'b-')
        plt.plot(t_datetime, vwcdata, 'b.')
    plt.title('GNSS Station ' + station.upper())
    plt.ylim(0, 0.5)
    plt.ylabel('Vol. Soil Moisture')
    plt.grid()
    plt.gcf().autofmt_xdate()


    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)

def read_apriori_rh(station,fr):
    """
    read the track dependent a priori reflector heights needed for
    phase & thus soil moisture.

    Parameters
    ----------
    station : str
        four character ID, lowercase

    fr : int
        frequency (e.g. 1,20)

    Returns
    -------
    results : numpy array 
        column 1 is just a number (1,2,3,4, etc)

        column 2 is RH in meters

        column 3 is satellite number 

        column 4 is azimuth of the track (degrees)

        column 5 is number of values used in average

        column 6 is minimum azimuth degrees for the quadrant

        column 7 is maximum azimuth degrees for the quadrant
    """
    result = []
    # do not have time to use this
    file_manager = FileManagement(station, FileTypes.apriori_rh_file)
    apriori_results = file_manager.read_file(comments='%')
    # for l2c
    myxdir = os.environ['REFL_CODE']
    apriori_path_f = myxdir + '/input/' + station + '_phaseRH.txt'

    if (fr == 1):
        apriori_path_f = myxdir + '/input/' + station + '_phaseRH_L1.txt'

    if os.path.exists(apriori_path_f):
        result = np.loadtxt(apriori_path_f, comments='%')
        print('Using: ', apriori_path_f) 
    else:
        print('Average RH file does not exist')
        sys.exit()

    # column 2 is RH, 3 is sat, 4 is azimuth, 5 is number of values
    #number_of_rhs = apriori_results[:, 4]
    #result = apriori_results
    # 50 is arbitrary - but assuming you have 365 values, not unreasonable
    # TODO make 50 a variable?
    # this is now taken care of in apriori.py
    #result = apriori_results[(number_of_rhs > 50)]


    return result


def test_func(x, a, b, rh_apriori):
    """
    This is least squares for estimating a sine wave given a fixed frequency, freqLS
    """
    freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL2
    return a * np.sin(freq_least_squares * x + b)

def test_func_new(x, a, b, rh_apriori,freq):
    """
    This is least squares for estimating a sine wave given a fixed frequency, freqLS
    now freq is input so it is not hardwired for L2

    Parameters
    ----------
    x : numpy array of floats
        sine(elevation angle) I think
    a : float
        amplitude  - estimated
    b : float
        phase  - estimated
    rh_apriori : float
        reflector height (m)
    freq : int 
        frequency

    """
    if (freq == 20) or (freq == 2):
        freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL2
    else:
        freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL1

    return a * np.sin(freq_least_squares * x + b)


def phase_tracks(station, year, doy, snr_type, fr_list, e1, e2, pele, plot, screenstats, compute_lsp,gzip):
    """
    This does the main work of estimating phase and other parameters from the SNR files
    it uses tracks that were predefined by the apriori.py code

    Parameters
    ----------
    station name : string
        4 char id, lowercase
    year : integer

    doy : integer
        day of year

    snr_type : integer
        is the file extension (i.e. 99, 66 etc)

    fr_list : list of integers
        frequency, [1], [20] or [1,20] 

    e1 : float
        min elevation angle (degrees)

    e2 : float 
        max elevation angle (degrees)

    pele : list of floats 
        elevation angle limits for the polynomial removal.  units: degrees

    screenstats : boolean
        whether statistics are printed to the screen

    compute_lsp : boolean
        this is always true

    gzip : boolean
        whether you want SNR files gzipped after running the code

    Only GPS frequencies are allowed because this relies on the repeating ground track.

    """

    min_amp = 3 # should be much higher - but this is primarily to catch L2P data that

    # various defaults - ones the user doesn't change in this quick Look code
    poly_v = 4 # polynomial order for the direct signal

    # this is arbitrary
    min_num_pts = 20


    # get the SNR filename
    obsfile, obsfilecmp, snrexist = g.define_and_xz_snr(station, year, doy, snr_type)

    # noise region - hardwired for normal sites ~ 2-3 meters tall
    noise_region = [0.5, 8]


    if not snrexist:
        print('No SNR file on this day.')
        pass

    else:
        header = "Year DOY Hour   Phase   Nv  Azimuth  Sat  Ampl emin emax  DelT aprioriRH  freq estRH  pk2noise LSPAmp\n(1)  (2)  (3)    (4)   (5)    (6)    (7)  (8)  (9)  (10)  (11)   (12)     (13)  (14)    (15)    (16)"
        file_manager = FileManagement(station, FileTypes.phase_file, year, doy, file_not_found_ok=True)
        print(f"Saving phase file to: {file_manager.get_file_path()}")
        with open(file_manager.get_file_path(), 'w') as my_file:
            np.savetxt(my_file, [], header=header, comments='%')
            # read the SNR file into memory
            sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snr_exists = read_snr.read_one_snr(obsfile, 1)

            for freq in fr_list:
            # read apriori reflector height results
                apriori_results = read_apriori_rh(station,freq)

                print('Analyzing Frequency ', freq, ' Year ', year, ' Day of Year ', doy)

                rows, columns = np.shape(apriori_results)

                for i in range(0, rows):
                    azim = apriori_results[i, 3]
                    sat_number = apriori_results[i, 2]
                    az1 = apriori_results[i, 5]
                    az2 = apriori_results[i, 6]
                    rh_apriori = apriori_results[i, 1]

                    x, y, nv, cf, utctime, avg_azim, avg_edot, edot2, del_t = g.window_data(s1, s2, s5, s6, s7, s8, sat, ele, azi,
                                                                                        t, edot, freq, az1, az2, e1, e2,
                                                                                        sat_number, poly_v, pele, screenstats)
                    if screenstats:
                        print(f'Track {i:2.0f} Sat {sat_number:3.0f} Azimuth {azim:5.1f} RH {rh_apriori:6.2f} {nv:5.0f}')

                    if compute_lsp and nv > min_num_pts:
                        min_height = 0.5
                        max_height = 8
                        desired_p = 0.01

                        max_f, max_amp, emin_obs, emax_obs, rise_set, px, pz = g.strip_compute(x, y, cf, max_height,
                                                                                           desired_p, poly_v, min_height)

                        nij = pz[(px > noise_region[0]) & (px < noise_region[1])]
                        noise = 0
                        if len(nij) > 0:
                            noise = np.mean(nij)
                            obs_pk2noise = max_amp/noise

                            if screenstats:
                                print(f'>> LSP RH {max_f:7.3f} m {obs_pk2noise:6.1f} Amp {max_amp:6.1f} {min_amp:6.1f} ')
                        else:
                            max_amp = 0  # so it will have a value

                    # http://scipy-lectures.org/intro/scipy/auto_examples/plot_curve_fit.html
                        if (nv > min_num_pts) and (max_amp > min_amp):
                            minmax = np.max(x) - np.min(x)
                            if (minmax > 22) and (del_t < 120):
                                x_data = np.sin(np.deg2rad(x))  # calculate sine(E)
                                y_data = y
                                test_function_apriori = partial(test_func_new, rh_apriori=rh_apriori,freq=freq)
                                #test_function_apriori = partial(test_func, rh_apriori=rh_apriori)
                                params, params_covariance = optimize.curve_fit(test_function_apriori, x_data, y_data, p0=[2, 2])
    

                                # change phase to degrees
                                phase = params[1]*180/np.pi
                                # calculate min and max elevation angle
                                min_el = min(x); max_el = max(x)
                                amp = np.absolute(params[0])
                                raw_amp = params[0]
                                if phase > 360:
                                    phase = phase - 360
                                    if phase > 360:
                                        phase = phase - 360

                                # do not allow negative amplitudes. 
                                if raw_amp < 0:
                                    phase = phase + 180

                                result = [[year, doy, utctime, phase, nv, avg_azim, sat_number, amp, min_el, max_el, del_t, rh_apriori, freq, max_f, obs_pk2noise, max_amp]]
                                np.savetxt(my_file, result, fmt="%4.0f %3.0f %6.2f %8.3f %5.0f %6.1f %3.0f %5.2f %5.2f %5.2f %6.2f %5.3f %2.0f %6.3f %6.2f %6.2f", comments="%")
        # gzip SNR file if requested
        if gzip:
            subprocess.call(['gzip', obsfile])


def low_pct(amp, basepercent):
    """
    emulated amp_normK code from PBO H2O
    inputs are the amplitudes  and a percentage
    used to define the bottom level. returns
    normalized amplitudes

    this is meant to be used by individual tracks (I think)
    in this case they are the top values, not the bottom ... ugh
    """
    n = len(amp)
    if n > 0:
        numx = int(np.round(n*basepercent) )
        if numx == 0:
            numx = n
        sort_a = np.sort(amp)
        lowval = np.mean(sort_a[0:numx])

    return lowval


def convert_phase(station, year, year_end=None, plt2screen=True,fr=20,tmin=0.05,tmax=0.5,polyorder=-99,circles=False,subdir=''):
    """
    Convert GPS phase to VWC. Using Clara Chew's algorithm from 
    Matlab write_vegcorrect_smc.m

    https://scipy-cookbook.readthedocs.io/items/SignalSmooth.html

    Parameters
    -----------
    station : str
        4 char station name
    year : int
        beginning year
    year_end : int
        last year
    plt2screen : boolean
        plots come to the screen
    fr : integer
        frequency
        default is L2C (20)
    polyorder : integer
        override on the polynomial order used in leveling
    circles : boolean
        final plot using circles (instead of line)
    subdir : str
        subdirector for $REFL_CODE/Files
    tmin : float
        soil texture minimum
    tmax : float
        soil texture maximum


    """

    if not year_end:
        year_end = year

    # read makejson
    station_file = FileManagement(station, 'make_json')
    json_data = station_file.read_file()

    if json_data['lat'] >= 0:
        print('northern hemisphere summer')
        southern = False
    elif json_data['lat'] < 0:
        print('southern hemisphere summer')
        southern = True

    else:
        print(f"the required json file created from the make_json step could not be found: {station_file.get_file_path()}")
        sys.exit()

    # for PBO H2O this was set using STATSGO. 5% is reasonable as a starting point for australia
    #tmin = 0.05  # for now
    print('minimum texture value', tmin)
    residval = 2  # for now

    # daily average file of phase results
    #file_manager = FileManagement(station, FileTypes.daily_avg_phase_results)
    #avg_phase_results = file_manager.read_file(comments='%')

    myxdir = os.environ['REFL_CODE']


    # begging for a function ...
    # overriding KE for now
    if (fr == 1):
        fileout = myxdir + '/Files/' + subdir + '/' + station + '_phase_L1.txt'
    else:
        fileout = myxdir + '/Files/' + subdir + '/' + station + '_phase.txt'

    if os.path.exists(fileout):
        avg_phase_results = np.loadtxt(fileout, comments='%')
    else:
        print('Average phase results not found')
        sys.exit()
    if (len(avg_phase_results) == 0):
        print('Empty results file')
        sys.exit()


    # get only the years requested - this matters if in previous steps more data was processed
    avg_phase_results_requested = np.array([v for v in avg_phase_results if v[0] in np.arange(year, year_end+1)])

    years = avg_phase_results_requested[:, 0]
    doys = avg_phase_results_requested[:, 1]
    ph = avg_phase_results_requested[:, 2]
    phsig = avg_phase_results_requested[:, 3] # TODO this is not used in the rest of the code
    amp = avg_phase_results_requested[:, 4]
    months = avg_phase_results_requested[:, 6]
    days = avg_phase_results_requested[:, 7]

    t = years + doys/365.25
    tspan = t[-1] - t[0]
    print('>>> Timespan in years: ', np.round(tspan,3))
    if tspan < 1.5:
        polyordernum = 0  # do nothing
    else:
        polyordernum =  int(np.floor(tspan - 0.5));
    print('>>> Polynomial Order ', polyordernum)

    # need to do a 30 day smoother on amp
    window_len = 30
    s = np.r_[amp[window_len - 1:0:-1], amp, amp[-2:-window_len - 1:-1]]
    w = np.ones(window_len, 'd')
    y = np.convolve(w / w.sum(), s, mode='valid')
    # NOTE: length(output) != length(input), to correct this: return y[(window_len/2-1):-(window_len/2)] instead of just y.
    y0 = int(window_len / 2 - 1);
    y1 = -int(window_len / 2)
    smamp = y[y0:y1]

    # TODO do we want this plot as an option to display?
    # plt.figure() #plt.plot(t, smamp, '-', t, amp,'o') #plt.show()

    # original clara chew code
    # residval is the median of the lowest 10 % of the values
    wetwt = 10.6 * np.power(smamp, 4) - 34.9 * np.power(smamp, 3) + 41.8 * np.power(smamp, 2) - 22.6 * smamp + 5.24

    # TODO this variable (below) is never used in the code
    delphi = -5.65 * np.power(wetwt, 4) + 43.9 * np.power(wetwt, 3) - 101 * np.power(wetwt,
                                                                                     2) + 20.4 * wetwt - 2.37;
    # I think this is just changing the units by factor of 100
    delphi = (smamp - 1) * 50.25 / 1.48;  # % CR 17jan12
    newph = ph - delphi;
    # resid value should be min value of the actual data

    vwc = 100 * tmin + 1.48 * (ph - residval);
    # this is our "vegetation corrected" value - though needs leveling
    newvwc = 100 * tmin + 1.48 * (newph - residval);
    # acting on newvwc, year and doys
    nodes = np.empty(shape=[0, 3])

    if southern:
        for yr in np.arange(year, year_end+1):
            y1 = yr - 30/365.25  # dec previous year
            y2 = yr + 45/365.25  # mid feb
            print(yr, y1, y2)  # kristine's idea of summer in australia
            # summer_vwc = newvwc[(year == y) &   (doys >= 1) & (doys < 40)]
            summer_vwc = newvwc[(t > y1) & (t < y2)]
            # summer_vwc2 = newvwc[(year == (y-1))  &   (doys >= 334) & (doys < 365)]
            # new_summer = np.vstack((summer_vwc, summer_vwc2))
            if len(summer_vwc) > 0:
                basepercent = 0.15
                lval = low_pct(summer_vwc, basepercent)
                newl = [yr, 15, lval]
                #print(newl)
                nodes = np.append(nodes, [newl], axis=0)
                print('Level value:', yr, np.round(lval,2))
            else:
                print('No summer dates found to compute VWC for ', yr)
    else:
        # northern hemisphere
        for yr in np.arange(year, year_end+1):
            # put in amplitude criteria to keep out bad L2P results
            summer_vwc = newvwc[(years == yr) & (doys >= 190) & (doys < 273)]
            if len(summer_vwc) > 0:
                basepercent = 0.15
                lval = low_pct(summer_vwc, basepercent)
                newl = [yr, 213, lval]
                #print(newl)
                nodes = np.append(nodes, [newl], axis=0)
                print('Level value:',yr, np.round(lval,2))
            else:
                print('No summer dates found to compute VWC', yr)


    plt.figure(figsize=(10, 10))
    plt.subplots_adjust(hspace=0.2)
    plt.suptitle(f'Station: {station}', size=16)

    # list comprehension to make datetime objects from year, doy
    t_datetime = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(years, doys)]

    # create subplots: 2 rows 1 column, 1st subplot
    ax = plt.subplot(2, 1, 1)

    ax.plot(t_datetime, ph, 'b-',label='original')
    ax.plot(t_datetime, newph, 'r-',label='vegcorrected')
#    ax.plot(t_datetime, ph-newph, 'm-',label='subtracted')
    ax.set_title(f'With and Without Vegetation Correction ')
    ax.set_ylabel('phase (degrees)')
    ax.legend(loc='best')
    ax.grid()
    # ?? does not seem to be working.  sigh
    plt.gcf().autofmt_xdate()


    # More descriptive variable names would help 
    st = nodes[:, 0] + nodes[:, 1]/365.25
    st_datetime = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(nodes[:, 0], nodes[:, 1])]
    sp = nodes[:, 2]

    howmanynodes = len(sp)
    print('number of nodes', howmanynodes)
    if howmanynodes == 0:
        print('No summer nodes found. Exiting.')
        if plt2screen:
            plt.show()
        sys.exit()
    
    else:
        polyordernum = howmanynodes - 1
    if polyorder >= 0: # default is -99
        print('>>> Using user override for polynomial order on leveling')
        polyordernum = polyorder

    anothermodel = np.polyfit(st, sp, polyordernum)
    new_level = np.polyval(anothermodel, t)

    # this is applying the level and the tmin values
    nv = tmin + (newvwc - new_level) / 100

    ax = plt.subplot(2, 1, 2)
    ax.plot(t_datetime, newvwc, 'b-', label='new vwc')

    ax.plot(st_datetime, sp, 'ro', label='nodes')
    ax.plot(t_datetime, new_level, 'r-', label='level')
    ax.set_ylabel('VWC')
    ax.set_title('Volumetric Water Content')
    ax.legend(loc='best')
    ax.grid()
    plt.gcf().autofmt_xdate()

    outdir = f'{xdir}/Files/{subdir}'

    plot_path = f'{outdir}/{station}_phase_vwc_result.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)


    plot_path = f'{outdir}/{station}_vol_soil_moisture.png'
    vwc_plot(station,t_datetime, nv, plot_path,circles) 

    if plt2screen:
        plt.show()

    vwcfile = FileManagement(station, FileTypes.volumetric_water_content).get_file_path()

    vwcfile = f'{outdir}/{station}_vwc.txt'
    print('>>> VWC results being written to ', vwcfile)
    with open(vwcfile, 'w') as w:
        N = len(nv)
        w.write("% Soil Moisture Results for GPS Station {0:4s} \n".format(station))
        w.write("% {0:s} \n".format('https://github.com/kristinemlarson/gnssrefl'))
        w.write("% FracYr Year  DOY  VWC Month Day \n")
        for iw in range(0, N):
            whydoys = np.round(365.25 * (t[iw] - years))

            fdate = t[iw]
            myyear = years[iw]
            mm = months[iw]
            dd = days[iw]
            mydoy = doys[iw]
            watercontent = nv[iw]
            # we do not allow negative soil moisture in my world.
            if (watercontent> 0 and watercontent < 0.5):
                w.write(f"{fdate:10.4f} {myyear:4.0f} {mydoy:4.0f} {watercontent:8.3f} {mm:3.0f} {dd:3.0f} \n")


def write_avg_phase(station, phase, fr,year,year_end,minvalperday,vxyz,subdir):

    """
    creates output file for average phase results

    Parameters
    ----------
    station : string

    phase : numpy list  (float)
         phase values 

    fr : int
        frequency

    year: int
        first year evaluated

    year_end : int
        last year evaluated

    minvalperday : int
        required number of satellite tracks to trust the daily average 

    vxyz is from some other compilation

    subdir : str
        subdirectory for results

    Returns
    -------
    tv : numpy array with elements
        year 
        doy  - day of year
        meanph - mean phase value in degrees
        nvals - number of values that went into the average

    """
    myxdir = os.environ['REFL_CODE']
    y1 = vxyz[:, 0]
    d1 = vxyz[:, 1]
    phase = vxyz[:, 2]
    sat = vxyz[:, 3] # this is not used
    az = vxyz[:, 4] # this is not used
    rh = vxyz[:, 5] # this is not used
    amp = vxyz[:, 6]

    tv = np.empty(shape=[0, 4])

    # ultimately would like to use kelly's code here
    if (fr == 1):
        fileout = myxdir + '/Files/'  + subdir + '/' + station + '_phase_L1.txt'
    else:
        fileout = myxdir + '/Files/' + subdir + '/' + station + '_phase.txt'

    print('Daily averaged phases will be written to : ', fileout)
    with open(fileout, 'w') as fout:
        fout.write("% Year DOY Ph Phsig NormA MM DD \n")
        for requested_year in range(year, year_end + 1):
            for doy in range(1, 367):
            # put in amplitude criteria to keep out bad L2P results
                ph1 = phase[(y1 == requested_year) & (d1 == doy) & (phase > -10) & (amp > 0.65)]
                amp1 = amp[(y1 == requested_year) & (d1 == doy) & (phase > -10) & (amp > 0.65)]
                if (len(ph1) > minvalperday):
                    newl = [requested_year, doy, np.mean(ph1), len(ph1)]
                # i think you normalize the individual satellites before this step
                #namp = qp.normAmp(amp1,0.15)
                    tv = np.append(tv, [newl], axis=0)
                    rph1 = np.round(np.mean(ph1), 2)
                    meanA = np.mean(amp1)
                    rph1_std = np.std(ph1)
                    yy, mm, dd, cyyyy, cdoy, YMD = g.ydoy2useful(requested_year, doy)
                    fout.write(f" {requested_year:4.0f} {doy:3.0f} {rph1:6.2f} {rph1_std:6.2f} {meanA:6.3f} {0.0:5.2f}   {mm:2.0f} {dd:2.0f} \n")

        fout.close()
    return tv

def apriori_file_exist(station,fr):
    """
    reads in the a priori RH results

    Parameters
    ----------
    station : string
        station name

    fr : integer
        frequency
        
    Returns
    -------
    boolean as to whether the apriori file exists

    """
    # do not have time to use this
    file_manager = FileManagement(station, FileTypes.apriori_rh_file)
    # for l2c
    myxdir = os.environ['REFL_CODE']
    apriori_path_f = myxdir + '/input/' + station + '_phaseRH.txt'

    if (fr == 1):
        apriori_path_f = myxdir + '/input/' + station + '_phaseRH_L1.txt'
    
    return os.path.exists(apriori_path_f) 

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
        frequency, i.e. 1 or 20
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
    xdir = os.environ['REFL_CODE']
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
