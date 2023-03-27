# I DO NOT THINK THIS IS USED. THIS SHOULD BE CONFIRMED AND IT SHOULD BE REMOVED
import sys
import os

import matplotlib.pyplot as plt
import numpy as np


import gnssrefl.gps as g
import gnssrefl.read_snr_files as read_snr
from gnssrefl.utils import FileManagement, FileTypes

from functools import partial
from scipy import optimize
from scipy.interpolate import interp1d
from datetime import datetime
from pathlib import Path

xdir = Path(os.environ["REFL_CODE"])

def vwc_plot(station,t_datetime, vwcdata, plot_path):
    """
    makes a final plot of volumetric water content

    Parameters
    ----------
    station : str
        4 ch station name

    t_datetime : array of datetime  
        times of the observations 

    vwcdata : numpy array of floats 
        volumetric water content (ranges from 0-1)

    plot_path : str
        where to put the plot
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
    read the track dependent a prori reflector heights needed for
    phase & thus soil moisture.

    Parameters
    ----------
    station : string
        four character ID, lowercase

    fr : integer
        frequency (e.g. 1,20)

    Returns
    ----------
    results : numpy array 
        column 2 is RH in meters
        column 3 is sat 
        column 4 is azimuth etc
        column 5 is number of values used in average
        column 6 is minimum azimuth degrees
        column 7 is maximum azimuth degrees
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
    """
    if (freq == 20) or (freq == 2):
        freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL2
    else:
        freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL1

    return a * np.sin(freq_least_squares * x + b)


def phase_tracks(station, year, doy, snr_type, fr_list, e1, e2, pele, plot, screenstats, compute_lsp):
    """
    This does the main work of estimating phase and other parameters from the SNR files
    it uses tracks that were predefined by the apriori.py code

    Parameters
    -------------
    station name : str
        4 char id, lowercase
    year : integer

    doy : int
        day of year

    snr_type : int
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

    only GPS frequencies are allowed

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
    
                                phase = params[1]*180/np.pi
                                min_el = min(x); max_el = max(x)
                                amp = np.absolute(params[0])
                                raw_amp = params[0]
                                if phase > 360:
                                    phase = phase - 360
                                    if phase > 360:
                                        phase = phase - 360

                                if raw_amp < 0:
                                    phase = phase + 180

                                result = [[year, doy, utctime, phase, nv, avg_azim, sat_number, amp, min_el, max_el, del_t, rh_apriori, freq, max_f, obs_pk2noise, max_amp]]
                                np.savetxt(my_file, result, fmt="%4.0f %3.0f %6.2f %8.3f %5.0f %6.1f %3.0f %5.2f %5.2f %5.2f %6.2f %5.3f %2.0f %6.3f %6.2f %6.2f", comments="%")



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


def convert_phase(station, year, year_end=None, plt2screen=True,fr=20,tmin,tmax,polyorder=-99,circles,subdir):
    """
    Conversion from estimated phase to VWC. Using Clara Chew algorithm
    from Matlab write_vegcorrect_smc.m

    qp.convert_phase(station, year, year_end, plt2screen,fr,tmin,tmax,polyorder,circles,subdir)

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        first year of analysis
    year_end : int
        last year of analysis
    plt2screen : bool
        whether plots come to the screen
    fr : int
        GNSS frequency used
    tmin : float
        soil texture minimum
    tmax : float
        soil texture maximum
    polyorder : int
        override on the polynomial order used in leveling
    circles : bool
        whether you want circles instead of dots?
    subdir: str
        directory to store files?

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
    # this i sset earlier now
    print(tmin)
    tmin = 0.05  # for now
    residval = 2  # for now

    # daily average file of phase results
    #file_manager = FileManagement(station, FileTypes.daily_avg_phase_results)
    #avg_phase_results = file_manager.read_file(comments='%')

    myxdir = os.environ['REFL_CODE']


    # begging for a function ...
    # overriding KE for now
    if (fr == 1):
        fileout = myxdir + '/Files/' + station + '_phase_L1.txt'
    else:
        fileout = myxdir + '/Files/' + station + '_phase.txt'

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

    plot_path = f'{xdir}/Files/{station}_phase_vwc_result.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)


    plot_path = f'{xdir}/Files/{station}_vol_soil_moisture.png'
    vwc_plot(station,t_datetime, nv, plot_path) 

    if plt2screen:
        plt.show()

    vwcfile = FileManagement(station, FileTypes.volumetric_water_content).get_file_path()
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

