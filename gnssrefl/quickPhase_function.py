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


def read_apriori_rh(station):
    """
    read the track dependent a prori reflector heights needed for
    phase & thus soil moisture.
    """
    file_manager = FileManagement(station, FileTypes.apriori_rh_file)
    apriori_results = file_manager.read_file(comments='%')

    # column 2 is RH, 3 is sat, 4 is azimuth, 5 is number of values
    number_of_rhs = apriori_results[:, 4]
    # 50 is arbitrary - but assuming you have 365 values, not unreasonable
    # TODO make 50 a variable?
    result = apriori_results[(number_of_rhs > 50)]

    return result


def test_func(x, a, b, rh_apriori):
    """
    This is least squares for estimating a sine wave given a fixed frequency, freqLS
    """
    freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL2
    return a * np.sin(freq_least_squares * x + b)


def phase_tracks(station, year, doy, snr_type, freq, e1, e2, pele, plot, screenstats, compute_lsp):
    """
    This does the main work of estimating phase and other parameters from the SNR files
    it uses tracks that were predefined by the apriori.py code

    parameters
    -------------
    station name : string
        4 char id, lowercase
    year : integer

    doy : integer
        day of year

    snr_type : integer
        is the file extension (i.e. 99, 66 etc)

    f : integer
        frequency (1, 2, 5), etc

    e1 : float
        min elevation angle (degrees)

    e2 : float 
        max elevation angle (degrees)

    pele : list of floats 
        elevation angle limits for the polynomial removal.  units: degrees

    only GPS frequencies are allowed

    """


    min_amp = 5 # should be much higher - but this is primarily to catch L2P data that

    # various defaults - ones the user doesn't change in this quick Look code
    poly_v = 4 # polynomial order for the direct signal

    min_num_pts = 20

    # read apriori reflector height results
    apriori_results = read_apriori_rh(station)

    # get the SNR filename
    obsfile, obsfilecmp, snrexist = g.define_and_xz_snr(station, year, doy, snr_type)

    # make a header for the phase/RH output
    # file_with_header = openfile_header(xdir, station, year, doy)

    # noise region - hardwired for normal sites ~ 2-3 meters tall
    noise_region = [0.5, 6]

    if not snrexist:
        print('No SNR file on this day.')
        pass

    else:
        sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snr_exists = read_snr.read_one_snr(obsfile, 1)

        print('<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('Analyzing Frequency ', freq, ' Year ', year, ' Day of Year ', doy)
        print('<<<<<<<<<<<<<<<<<<<<<<<<<>>>>>>>>>>>>>>>>>>>>>>>>>>')

        # find out how many tracks you have
        rows, columns = np.shape(apriori_results)

        header = "Year DOY Hour   Phase   Nv  Azimuth  Sat  Ampl emin emax  DelT aprioriRH  freq estRH  pk2noise LSPAmp\n(1)  (2)  (3)    (4)   (5)    (6)    (7)  (8)  (9)  (10)  (11)   (12)     (13)  (14)    (15)    (16)"
        file_manager = FileManagement(station, FileTypes.phase_file, year, doy, file_not_found_ok=True)
        print(f"Saving phase file to: {file_manager.get_file_path()}")
        with open(file_manager.get_file_path(), 'w') as my_file:
            np.savetxt(my_file, [], header=header, comments='%')
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
                    #TODO throw error/warning instead of use  noise=0

                    if screenstats:
                        print(f'>> LSP RH {max_f:7.3f} m {obs_pk2noise:6.1f} Amp {max_amp:6.1f} {min_amp:6.1f} ')
                    # added minAmp because of inadvertent use of L2P

                # TODO nothing above is set here with this else statement
                else:
                    max_amp = 0  # so it will have a value

                # TODO what do we want to happen if NOT?
                if (nv > min_num_pts) and (max_amp > min_amp):
                    # apparently x is elevation angle. So max is close to 30. Min is close to 5, thus 22 being used
                    # this would totally fail if i wasn't sure emax of 30..  poorly coded.
                    # TODO what should we do to change this? ^
                    minmax = np.max(x) - np.min(x)
                # two hours for now - just to avoid midnite crossovers
                    # TODO what to do if NOT?
                    if (minmax > 22) and (del_t < 120):
                    # http://scipy-lectures.org/intro/scipy/auto_examples/plot_curve_fit.html
                        x_data = np.sin(np.deg2rad(x))  # calculate sine(E)
                        y_data = y
                        test_function_apriori = partial(test_func, rh_apriori=rh_apriori)
                        params, params_covariance = optimize.curve_fit(test_function_apriori, x_data, y_data, p0=[2, 2])

                        phase = params[1]*180/np.pi
                        min_el = min(x)
                        max_el = max(x)
                        amp = np.absolute(params[0])
                        raw_amp = params[0]

                        # TODO should this happen more than once?
                        if phase > 360:
                            phase = phase - 360
                            if phase > 360:
                                phase = phase - 360

                        # TODO are we worried phase might be over 360 after next step?
                        if raw_amp < 0:
                            phase = phase + 180

                        result = [[year, doy, utctime, phase, nv, avg_azim, sat_number, amp, min_el, max_el, del_t, rh_apriori, freq, max_f, obs_pk2noise, max_amp]]
                        # print(f"Year {year:4.0f} DOY {doy:3.0f} Hour {utctime:6.2f} Phase {phase:8.3f} Nv {nv:5.0f}"
                        #       f" Azimuth {avg_azim:6.1f} Sat {sat_number:3.0f} Ampl {amp:5.2f} emin {min_el:5.2f} "
                        #       f"emax {max_el:5.2f} DelT {del_t:6.2f} aprioriRH {rh_apriori:5.3f} freq {freq:2.0f}"
                        #       f" estRH {max_f:6.3f} pk2noise {obs_pk2noise:6.2f} LSPAmp {max_amp:6.2f}")
                        np.savetxt(my_file, result, fmt="%4.0f %3.0f %6.2f %8.3f %5.0f %6.1f %3.0f %5.2f %5.2f %5.2f %6.2f %5.3f %2.0f %6.3f %6.2f %6.2f", comments="%")

                        if plot:
                            plt.plot(x_data, y_data, 'o', label='data')
                            plt.plot(x_data, test_func(x_data, params[0], params[1], rh_apriori), label='Fitted function')
                            plt.show()


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


def convert_phase(station, year, year_end=None, plt2screen=True):
    """
    conversion from phase to VWC. Using Clara Chew algorithm
    from Matlab write_vegcorrect_smc.m
    input is the station name

    https://scipy-cookbook.readthedocs.io/items/SignalSmooth.html
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

    # Code above is replacing this code below:
    # if station == 'p038':
    #     print('northern hemisphere summer')
    #     southern = False
    # else:
    #     print('southern hemisphere summer')
    #     southern = True

    #TODO will need to modify this to choose values based on station location?

    # for PBO H2O this was set using STATSGO. 5% is reasonable as a starting point for australia
    tmin = 0.05  # for now
    residval = 2  # for now

    # daily average file of phase results
    file_manager = FileManagement(station, FileTypes.daily_avg_phase_results)
    avg_phase_results = file_manager.read_file(comments='%')

    # get only the years requested - this matters if in previous steps more data was processed
    avg_phase_results_requested = np.array([v for v in avg_phase_results if v[0] in np.arange(year, year_end+1)])

    years = avg_phase_results_requested[:, 0]
    doys = avg_phase_results_requested[:, 1]
    ph = avg_phase_results_requested[:, 2]
    phsig = avg_phase_results_requested[:, 3] # TODO this is not used in the rest of the code
    amp = avg_phase_results_requested[:, 4]

    t = years + doys/365.25
    tspan = t[-1] - t[0]
    print('timespan', tspan)
    if tspan < 1.5:
        polyordernum = 0  # do nothing
    else:
        polyordernum = 1 + np.floor(tspan - 0.5);
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

    # TODO perhaps we should require users to pick their summer months as a param?
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
                print(yr, lval)
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
                print(yr, lval)
            else:
                print('No summer dates found to compute VWC', yr)

    # newl = [year[-1], doys[-1], newvwc[-1]]
    # nodes = np.append(nodes, [newl],axis=0)

    plt.figure(figsize=(10, 10))
    plt.subplots_adjust(hspace=0.2)
    plt.suptitle(f'Station: {station}', size=16)

    # list comprehension to make datetime objects from year, doy
    t_datetime = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(years, doys)]

    # create subplots: 2 rows 1 column, 1st subplot
    ax = plt.subplot(2, 1, 1)

    ax.plot(t_datetime, ph, label='original')
    ax.plot(t_datetime, newph, label='vegcorr')
    ax.set_title(f'With and Without Vegetation Correction ')
    ax.set_ylabel('phase (degrees)')
    ax.legend(loc='best')
    ax.grid()

    # More descriptive variable names would help :)
    st = nodes[:, 0] + nodes[:, 1]/365.25
    st_datetime = [datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j') for yr, d in zip(nodes[:, 0], nodes[:, 1])]

    sp = nodes[:, 2]

    # ‘zero’, ‘slinear’, ‘quadratic’ and ‘cubic’ refer to a spline interpolation of zeroth, first, second or third order
    # Choosing the kind of fit based on the number of years requested to process
    fit_kind = {1: 'zero', 2: 'slinear', 3: 'quadratic', 4: 'cubic'}
    num_years = len(st)
    if num_years > 4:
        num_years = 4
    kind = fit_kind[num_years]
    st_interp = interp1d(st, sp, kind=kind, fill_value='extrapolate')
    new_level = st_interp(t)

    nv = tmin + (newvwc - new_level) / 100

    ax = plt.subplot(2, 1, 2)
    # plt.plot(t,vwc,label='old vwc')
    ax.plot(t_datetime, newvwc, label='new vwc')
    ax.plot(st_datetime, sp, 'o', label='nodes')
    ax.plot(t_datetime, new_level, '-', label='level')
    ax.set_ylabel('VWC')
    ax.set_title('Volumetric Water Content')
    ax.legend(loc='best')
    ax.grid()

    plot_path = f'{xdir}/Files/{station}_phase_vwc_result.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)
    if plt2screen:
        plt.show()

    fig,ax=plt.subplots()
    plt.plot(t_datetime, nv, '.')
    params = {'mathtext.default': 'regular'}
    plt.rcParams.update(params)
    plt.title('Soil Moisture ' + station.upper())
    plt.ylim(0, 0.5)
    plt.ylabel('VWC')
    plt.grid()
    fig.autofmt_xdate()


    plot_path = f'{xdir}/Files/{station}_vol_soil_moisture.png'
    print(f"saving figure to {plot_path}")
    plt.savefig(plot_path)
    if plt2screen:
        plt.show()

    # TODO this is not used - polyordernum only gets set and then is here so is not used except with the commented-out code below.
    if polyordernum > 0:
        model = np.polyfit(t, vwc, polyordernum)
        fit = np.polyval(model, t)
        # plt.plot(t,fit,label='poly-vwc')
        # this doesn't really help
        # sm_vwc = seasonal_smoother(vwc, 90)
        # plt.plot(t,sm_vwc,label='90 smoother')


    vwcfile = FileManagement(station, FileTypes.volumetric_water_content).get_file_path()
    print('VWC results going to ', vwcfile)
    with open(vwcfile, 'w') as w:
        N = len(nv)
        w.write("% gnssrefl results for GPS Station {0:4s} \n".format(station))
        w.write("% FracYr Year DOY  VWC  \n")
        for iw in range(0, N):
            fdate = t[iw]
            years = np.floor(fdate)
            doys = np.round(365.25 * (t[iw] - years))
            w.write(f"{fdate:10.4f} {years:4.0f} {doys:3.0f} {nv[iw]:8.3f} \n")
