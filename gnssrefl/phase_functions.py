import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys


import gnssrefl.gps as g
import gnssrefl.read_snr_files as read_snr
from gnssrefl.utils import FileManagement, FileTypes
import gnssrefl.daily_avg_cl as da
import gnssrefl.gnssir_v2 as gnssir

from functools import partial
from scipy import optimize
from scipy.interpolate import interp1d
from datetime import datetime
from pathlib import Path

from gnssrefl.utils import str2bool, read_files_in_dir

xdir = Path(os.environ["REFL_CODE"])

def get_temporal_suffix(fr, bin_hours=24, bin_offset=0):
    """
    Generate consistent suffix for all output files with temporal resolution and offset
    
    Parameters
    ----------
    fr : int
        Frequency (1, 5, 20, etc.)
    bin_hours : int, optional
        Time bin size in hours. Default is 24 (daily)
    bin_offset : int, optional
        Bin timing offset in hours. Default is 0
        
    Returns
    -------
    str
        Suffix string like "_L1_6hr+0", "_L2_24hr+1", etc.
    """
    # Generate frequency suffix
    if fr == 1:
        freq_suffix = "_L1"
    elif fr == 2 or fr == 20:
        freq_suffix = "_L2"  # Both L2 (fr=2) and L2C (fr=20) use L2 
    elif fr == 5:
        freq_suffix = "_L5"  
    else:
        freq_suffix = f"_freq{fr}"
    
    # Generate temporal suffix with offset
    time_suffix = f"_{bin_hours}hr+{bin_offset}"
    
    return freq_suffix + time_suffix

def get_bin_schedule_info(bin_hours, bin_offset=0):
    """
    Helper function to generate bin schedule information strings
    
    Parameters
    ----------
    bin_hours : int
        Time bin size in hours
    bin_offset : int, optional
        Bin timing offset in hours. Default is 0
        
    Returns
    -------
    str
        Bin schedule description line
    """
    bins_per_day = 24 // bin_hours
    schedule_parts = []
    for i in range(bins_per_day):
        start_hour = (i * bin_hours + bin_offset) % 24
        end_hour = ((i + 1) * bin_hours + bin_offset) % 24
        if end_hour == 0:
            end_hour = 24
        schedule_parts.append(f"Bin{i}: {start_hour:02d}-{end_hour:02d}h")
    return "% Bin schedule: " + "  ".join(schedule_parts)

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

def subdaily_phase_plot(station, fr,datetime_dates, tv,xdir,subdir,hires_figs,bin_hours=24,bin_offset=0,plt2screen=True):
    """
    makes a plot of daily averaged phase for vwc code

    Parameters
    ----------
    station: str
        4 char station name
    fr : int
        frequency of signal
    datetime_dates : ...
        datetime values for phase points
    tv : list of results
        cannot remember the format
    xdir : str
        location of the results (environment variable REFL_CODE)
    subdir : str
        subdirectory in Files
    hires_figs: bool
        whether you want eps instead of png files

    """
    outdir = Path(xdir) / 'Files' / subdir
    plt.figure(figsize=(10, 6))
    plt.plot(datetime_dates, tv[:, 2], 'b-')
    plt.ylabel('phase (degrees)')
    freq_name = {1: "L1", 2: "L2", 20: "L2C", 5: "L5"}.get(fr, f"freq{fr}")
    if bin_hours < 24:
        plt.title(f"{bin_hours}-hour {freq_name} Phase Results: {station.upper()}")
    else:
        plt.title(f"Daily {freq_name} Phase Results: {station.upper()}")
    plt.grid()
    plt.gcf().autofmt_xdate()

    # Generate filename with temporal suffix
    suffix = get_temporal_suffix(fr, bin_hours, bin_offset)
    if hires_figs:
        plot_path = f'{outdir}/{station}_phase{suffix}.eps'
    else:
        plot_path = f'{outdir}/{station}_phase{suffix}.png'
    print(f"Saving figure to {plot_path}")

    plt.savefig(plot_path)
    if not plt2screen:
        plt.close()  # Close figure only when not displaying to screen



def make_snow_filter(station, medfilter, ReqTracks, year1, year2):
    """
    Runs daily_avg code to make a snow mask file.  This is 
    so you have some idea of when the soil moisture products are 
    contaminated by snow. Make a file with these years and doys saved. The user can
    edit if they feel the suggestsions are poor (i.e. days in the summer might show up
    as "snow")

    If snow mask file exists, it does not overwrite it.

    Parameters
    ----------
    station : str
        4 ch station name
    medfilter : float
        how much you allow the individual tracks to deviate from the daily median (meters)
    ReqTracks : int
        number of tracks to compute trustworthy daily average
    year1 : int
        starting year
    year2 : int
        ending year

    Returns
    -------
    snowmask_exists : bool
        whether file was created
    snow_file : str
        name of the snow mask file

    Creates output file into a file $REFL_CODE/Files/{ssss}/snowmask_{ssss}.txt
    where ssss is the station name

    """
    snowmask_exists = False
    myxdir = os.environ['REFL_CODE']
    # Use consistent path structure for snow mask file
    snowfile = Path(myxdir) / 'Files' / station / f'snowmask_{station}.txt' 
    if os.path.exists(snowfile):
        print('Using existing snow mask file, ', snowfile)
        snowmask_exists = True
        return snowmask_exists,snowfile

    # l2c only
    txtfile = station + '_allRH.txt'; 
    pltit = False; extension = ''; fr = 20; csv = False

    # writes out a daily average file. woudl be better if it returned the values, but this works
    da.daily_avg(station, medfilter, ReqTracks, txtfile, pltit,
              extension, year1, year2, fr, csv) 
    avgf = Path(myxdir) / 'Files' / station / txtfile
    print('Looking in ', avgf)
    x = np.loadtxt(avgf, comments='%')
    # delete the file!
    rh = x[:,2]
    medianvalue = np.median(rh);
    print('Median RH value ', medianvalue)
    # everything within 5 cm
    ii = (rh -medianvalue) < -0.05
    newx = x[ii,:] ; N=len(newx)
    if (N > 0):
        print('Suspect snow values stored in : ', snowfile)
        snow = open(snowfile, 'w+')
        for i in range(0,N):
            sv = -(newx[i,2]-medianvalue)
            print('Suspect Snow Day : ', int(newx[i,0]), int(newx[i,1]))
            snow.write("{0:4.0f}  {1:3.0f} {2:8.3f}  \n".format( newx[i,0], newx[i,1], sv))
        snow.close()
    subprocess.call(['rm','-f',avgf])
    if os.path.exists(snowfile):
        snowmask_exists = True
    else:
        print('I tried to make a snow mask file for you - but it did not work. This is most likely because ')
        print('this is a limited site, i.e. fewer tracks than the code wants. Go ahead and make one by hand,')
        print('plain text of year,doy is all you need ', snowfile)
        snowfile = None

    return snowmask_exists, snowfile

def vwc_plot(station,t_datetime, vwcdata, plot_path,circles,plt2screen=True):
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
    plt.title('GNSS-IR Soil Moisture Station ' + station.upper())
    plt.ylim(0, 0.5)
    plt.ylabel('Volumetric Soil Moisture')
    plt.grid()
    plt.gcf().autofmt_xdate()


    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)
    if not plt2screen:
        plt.close()  # Close figure only when not displaying to screen

def read_apriori_rh(station, fr, extension=''):
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
    file_manager = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
    apriori_path_f, format_type = file_manager.find_apriori_rh_file()

    if apriori_path_f.exists():
        result = np.loadtxt(apriori_path_f, comments='%', ndmin=2)
        if format_type == 'legacy':
            print(f'Using RH file (legacy directory): {apriori_path_f}')
        else:
            print(f'Using RH file: {apriori_path_f}')
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
    elif freq == 5:
        freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL5
    else:
        freq_least_squares = 2*np.pi*2*rh_apriori/g.constants.wL1

    return a * np.sin(freq_least_squares * x + b)

def get_vwc_frequency(station: str, extension: str, fr_cmd: str = None):
    """
    Determines the frequency to use for VWC workflows.
    Priority is: command line -> json file -> default (20).

    Parameters
    ----------
    station : str
        4-character station name.
    extension : str
        Analysis extension name.
    fr_cmd : str, optional
        Frequency provided from the command line (e.g., '1', '20', or 'all'), by default None.

    Returns
    -------
    list
        A list of frequencies to be used for analysis.
    """
    # Handle the 'all' case first, which overrides everything else.
    if fr_cmd == 'all':
        print("Processing all supported frequencies: L1 (1), L2C (20), and L5 (5).")
        print("Note: L1 and L5 are experimental - only L2C is officially supported.")
        return [1, 20, 5]

    final_fr = None
    # Use command line frequency if provided (and it's not 'all')
    if fr_cmd is not None:
        try:
            final_fr = int(fr_cmd)
            print(f"Using frequency from command line: {final_fr}")
        except ValueError:
            print(f"Error: Invalid frequency '{fr_cmd}'. Must be an integer or 'all'.")
            sys.exit()
    else:
        # Otherwise, try to read from the json file
        lsp = gnssir.read_json_file(station, extension, noexit=True)
        if 'freqs' in lsp and lsp.get('freqs'):
            if len(lsp['freqs']) == 1:
                final_fr = lsp['freqs'][0]
                print(f"Frequency read from JSON file: {final_fr}")
            else:
                print("Error: 'freqs' in JSON must be a list with a single value. Exiting.")
                sys.exit()
        else:
            # Default to L2C if not specified anywhere
            final_fr = 20
            print("No frequency specified. Defaulting to L2C (20).")

    # Warn if not using the standard L2C frequency
    if final_fr not in [1, 20, 5]:
        print(f"Error: Frequency {final_fr} is not supported. Supported frequencies: 1 (L1), 20 (L2C), 5 (L5).")
        sys.exit()
    elif final_fr == 1:
        print(f"Warning: Using L1 frequency ({final_fr}) - EXPERIMENTAL. Only L2C (20) is officially supported.")
    elif final_fr == 5:
        print(f"Warning: Using L5 frequency ({final_fr}) - EXPERIMENTAL. Only L2C (20) is officially supported.")

    # Always return a list
    return [final_fr]

def phase_tracks(station, year, doy, snr_type, fr_list, e1, e2, pele, plot, screenstats, compute_lsp,gzip, extension=''):
    """
    This does the main work of estimating phase and other parameters from the SNR files
    it uses tracks that were predefined by the apriori.py code

    Parameters
    ----------
    station name : string
        4 char id, lowercase
    year : int
        calendar year
    doy : int
        day of year
    snr_type : int
        SNR file extension (i.e. 99, 66 etc)
    fr_list : list of integers
        frequency, [1], [20] or [1,20] 
    e1 : float
        min elevation angle (degrees)
    e2 : float 
        max elevation angle (degrees)
    pele : list of floats 
        elevation angle limits for the polynomial removal.  units: degrees
    screenstats : bool
        whether statistics are printed to the screen
    compute_lsp : bool
        this is always true for now
    gzip : bool
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

    l2c_list, l5_list = g.l2c_l5_list(year,doy)

    if not snrexist:
        print('No SNR file on this day.')
        pass

    else:
        header = "Year DOY Hour   Phase   Nv  Azimuth  Sat  Ampl emin emax  DelT aprioriRH  freq estRH  pk2noise LSPAmp\n(1)  (2)  (3)    (4)   (5)    (6)    (7)  (8)  (9)  (10)  (11)   (12)     (13)  (14)    (15)    (16)"
        output_path = FileManagement(station, 'phase_file', year, doy, extension=extension).get_file_path()

        print(f"Saving phase file to: {output_path}")
        with open(output_path, 'w') as my_file:
            np.savetxt(my_file, [], header=header, comments='%')
            # read the SNR file into memory
            sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snr_exists = read_snr.read_one_snr(obsfile, 1)

            for freq in fr_list:
            # read apriori reflector height results
                apriori_results = read_apriori_rh(station, freq, extension)

                print('Analyzing Frequency ', freq, ' Year ', year, ' Day of Year ', doy)

                rows, columns = np.shape(apriori_results)

                for i in range(0, rows):
                    compute_lsp = True # will set to false for non-compliant L2C requests
                    azim = apriori_results[i, 3]
                    # this will be the satellite number you are working on 
                    sat_number = apriori_results[i, 2]
                    az1 = apriori_results[i, 5]
                    az2 = apriori_results[i, 6]
                    rh_apriori = apriori_results[i, 1]

                    # this uses the old way of resolving arcs - but I think that is ok because we only want
                    # one arc per quadrant anyway when doing soil moisture. And soil moisture doesn't really
                    # work unless you have most of the field (i.e. 180 degrees of azimuth)
                    x, y, nv, cf, utctime, avg_azim, avg_edot, edot2, del_t = g.window_data(s1, s2, s5, s6, s7, s8, sat, ele, azi,
                                                                                        t, edot, freq, az1, az2, e1, e2,
                                                                                        sat_number, poly_v, pele, screenstats)
                    if (freq == 20) and (sat_number not in l2c_list) :
                        if screenstats: 
                            print('Asked for L2C but this is not L2C transmitting on this day: ', int(sat_number))
                        compute_lsp = False
                    
                    if (freq == 5) and (sat_number not in l5_list):
                        if screenstats: 
                            print('Asked for L5 but this is not L5 transmitting on this day: ', int(sat_number))
                        compute_lsp = False

                    if screenstats:
                        print(f'Track {i:2.0f} Sat {sat_number:3.0f} Azimuth {azim:5.1f} RH {rh_apriori:6.2f} {nv:5.0f}')

                    if compute_lsp and (nv > min_num_pts):
                        # this is the same every track, so no reason to be in the loop
                        min_height = 0.5 ; max_height = 8 ; desired_p = 0.01

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


def convert_phase(station, year, year_end=None, plt2screen=True,fr=20,tmin=0.05,tmax=0.5,polyorder=-99,circles=False,
        subdir='',hires_figs=False, extension='', bin_hours=24, bin_offset=0):
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
    tmin : float
        soil texture minimum
    tmax : float
        soil texture maximum
    polyorder : integer
        override on the polynomial order used in leveling
    circles : boolean
        final plot using circles (instead of line)
    subdir : str
        subdirectory for $REFL_CODE/Files
    hires_figs : bool
        whether you want eps instead of png files created

    """

    if not year_end:
        year_end = year

    # read makejson
    station_file = FileManagement(station, 'make_json')
    json_data = gnssir.read_json_file(station, extension, silent=True)

    if json_data['lat'] >= 0:
        print('Northern hemisphere summer')
        southern = False
    elif json_data['lat'] < 0:
        print('Southern hemisphere summer')
        southern = True

    else:
        print(f"The required json file could not be found or is invalid: {station_file.get_file_path()}")
        sys.exit()

    # for PBO H2O this was set using STATSGO. 5% is reasonable as a starting point for australia
    #tmin = 0.05  # for now
    #print('minimum texture value', tmin)
    residval = 2  # for now

    # daily average file of phase results
    #file_manager = FileManagement(station, FileTypes.daily_avg_phase_results)
    #avg_phase_results = file_manager.read_file(comments='%')

    myxdir = os.environ['REFL_CODE']


    # Use FileManagement for consistent phase file paths
    file_manager = FileManagement(station, 'daily_avg_phase_results', extension=extension)
    base_fileout = file_manager.get_file_path()
    
    # Generate consistent filename using temporal resolution
    suffix = get_temporal_suffix(fr, bin_hours, bin_offset)
    fileout = base_fileout.parent / f"{station}_phase{suffix}.txt"
    
    if os.path.exists(fileout):
        avg_phase_results = np.loadtxt(fileout, comments='%')
        if bin_hours < 24:
            print(f'Found {bin_hours}-hour phase file: {fileout}')
        else:
            print(f'Found daily phase file: {fileout}')
    else:
        if bin_hours < 24:
            print(f'No {bin_hours}-hour phase file found: {fileout}')
        else:
            print('Average phase results not found')
        sys.exit()
    if (len(avg_phase_results) == 0):
        print('Empty results file')
        sys.exit()
        
    # Auto-detect file format based on number of columns
    if avg_phase_results.ndim == 1:
        # Single row, reshape for consistency
        avg_phase_results = avg_phase_results.reshape(1, -1)
    
    num_columns = avg_phase_results.shape[1]
    if num_columns == 9:
        is_subdaily = True
        print('Detected 9-column subdaily format from file')
    elif num_columns == 8:
        is_subdaily = False  
        print('Detected 8-column daily format from file')
    else:
        print(f'Unexpected file format: {num_columns} columns. Expected 8 (daily) or 9 (subdaily)')
        sys.exit()


    # get only the years requested - this matters if in previous steps more data was processed
    avg_phase_results_requested = np.array([v for v in avg_phase_results if v[0] in np.arange(year, year_end+1)])

    # Extract columns based on file format (8 vs 9 columns)
    years = avg_phase_results_requested[:, 0]
    doys = avg_phase_results_requested[:, 1]
    ph = avg_phase_results_requested[:, 2]
    phsig = avg_phase_results_requested[:, 3] # TODO this is not used in the rest of the code
    amp = avg_phase_results_requested[:, 4]
    months = avg_phase_results_requested[:, 6]
    days = avg_phase_results_requested[:, 7]
    
    # For subdaily files, we have an additional BinStart column
    if is_subdaily:
        bin_start_hours = avg_phase_results_requested[:, 8]
        print(f'Processing {len(avg_phase_results_requested)} subdaily measurements')
    else:
        print(f'Processing {len(avg_phase_results_requested)} daily measurements')

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

    # Create datetime objects with hour information for subdaily data  
    if is_subdaily:
        from datetime import timedelta
        t_datetime = []
        for yr, d, h in zip(years, doys, bin_start_hours):
            base_dt = datetime.strptime(f'{int(yr)} {int(d)}', '%Y %j')
            dt_with_hours = base_dt + timedelta(hours=int(h))
            t_datetime.append(dt_with_hours)
    else:
        # Daily data: use existing logic
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
        else:
            plt.close('all')
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

    outdir = Path(xdir) / 'Files' / subdir

    suffix = get_temporal_suffix(fr, bin_hours, bin_offset)
    if hires_figs:
        plot_path = f'{outdir}/{station}_phase_vwc_result{suffix}.eps'
    else:
        plot_path = f'{outdir}/{station}_phase_vwc_result{suffix}.png'
    print(f"Saving to {plot_path}")
    plt.savefig(plot_path)


    if hires_figs:
        plot_path = f'{outdir}/{station}_vol_soil_moisture{suffix}.eps'
    else:
        plot_path = f'{outdir}/{station}_vol_soil_moisture{suffix}.png'

    vwc_plot(station,t_datetime, nv, plot_path,circles,plt2screen) 

    if plt2screen:
        plt.show()
    else:
        # Close all figures to prevent them from displaying when plt2screen=False
        plt.close('all')

    # Use FileManagement with extension support for consistent directory structure
    file_manager = FileManagement(station, 'volumetric_water_content', extension=extension)
    base_vwcfile = file_manager.get_file_path()
    
    # Generate VWC filename using consistent suffix
    suffix = get_temporal_suffix(fr, bin_hours, bin_offset) 
    vwcfile = base_vwcfile.parent / f"{station}_vwc{suffix}.txt"
    print('>>> VWC results being written to ', vwcfile)
    with open(vwcfile, 'w') as w:
        N = len(nv)
        freq_map = {1: "L1", 2: "L2C", 20: "L2C", 5: "L5"}
        freq_name = freq_map.get(fr, f"Frequency {fr}")
        w.write("% Soil Moisture Results for GNSS Station {0:4s} \n".format(station))
        w.write("% Frequency used: {0} \n".format(freq_name))
        w.write("% {0:s} \n".format('https://github.com/kristinemlarson/gnssrefl'))
        if is_subdaily:
            w.write(f"% Subdaily VWC with {bin_hours}-hour bins (offset: {bin_offset}h)\n")
            w.write(get_bin_schedule_info(bin_hours, bin_offset) + "\n")
            w.write("% FracYr    Year   DOY   VWC Month Day BinStart \n")
        else:
            w.write("% FracYr    Year   DOY   VWC Month Day \n")
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
                if is_subdaily:
                    bin_start = bin_start_hours[iw]
                    w.write(f"{fdate:10.4f} {myyear:4.0f} {mydoy:4.0f} {watercontent:8.3f} {mm:3.0f} {dd:3.0f} {bin_start:3.0f} \n")
                else:
                    w.write(f"{fdate:10.4f} {myyear:4.0f} {mydoy:4.0f} {watercontent:8.3f} {mm:3.0f} {dd:3.0f} \n")


def write_avg_phase(station, phase, fr,year,year_end,minvalperday,vxyz,subdir,extension='',
                   bin_hours=24, minvalperbin=10, bin_offset=0):

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
    
    extension : str, optional
        analysis extension for directory organization

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
    hour = vxyz[:, 8] # hour of day, UTC
    
    # For subdaily mode, we need an extra column for hour bin
    if bin_hours < 24:
        tv = np.empty(shape=[0, 5])  # year, doy, meanph, nvals, bin_start_hour
    else:
        tv = np.empty(shape=[0, 4])  # year, doy, meanph, nvals (backwards compatibility)

    # Use FileManagement for consistent phase file paths
    file_manager = FileManagement(station, 'daily_avg_phase_results', extension=extension)
    base_fileout = file_manager.get_file_path()
    
    # Generate consistent filename with temporal resolution
    suffix = get_temporal_suffix(fr, bin_hours, bin_offset)
    fileout = base_fileout.parent / f"{station}_phase{suffix}.txt"

    if bin_hours < 24:
        print(f'{bin_hours}-hour averaged phases will be written to : ', fileout)
    else:
        print('Daily averaged phases will be written to : ', fileout)
    with open(fileout, 'w') as fout:
        # Write frequency information
        if fr == 1:
            freq_name = "L1"
        elif fr == 2 or fr == 20:
            freq_name = "L2"
        elif fr == 5:
            freq_name = "L5"  
        else:
            freq_name = f"freq{fr}"
        fout.write(f"% {freq_name} phase results for station {station.upper()}\n")
        
        # Write header based on mode
        if bin_hours < 24:
            # Subdaily mode: add bin info and BinStart column
            fout.write(f"% Subdaily phase averaging with {bin_hours}-hour bins (offset: {bin_offset}h)\n")
            fout.write(get_bin_schedule_info(bin_hours, bin_offset) + "\n")
            fout.write("% Year DOY   Ph    Phsig NormA  empty  Mon Day BinStart\n")
        else:
            # Daily mode: keep existing header for backwards compatibility  
            fout.write("% Year DOY   Ph    Phsig NormA  empty  Mon Day \n")
            
        # Calculate number of bins per day
        bins_per_day = 24 // bin_hours
        
        for requested_year in range(year, year_end + 1):
            for doy in range(1, 367):
                if bin_hours < 24:
                    # Subdaily binning: process each time bin separately
                    for bin_idx in range(bins_per_day):
                        # Calculate bin boundaries with offset
                        bin_start = (bin_idx * bin_hours + bin_offset) % 24
                        bin_end = ((bin_idx + 1) * bin_hours + bin_offset) % 24
                        
                        # Handle midnight wraparound - collect data from both days for cross-midnight bins
                        if bin_end <= bin_start:  # bin crosses midnight
                            # Current day: late hours (e.g., 22:00-24:00)
                            current_day_mask = (y1 == requested_year) & (d1 == doy) & (hour >= bin_start)
                            # Next day: early hours (e.g., 00:00-02:00)
                            next_day_mask = (y1 == requested_year) & (d1 == doy + 1) & (hour < bin_end)
                            time_mask = (current_day_mask | next_day_mask) & (phase > -10) & (amp > 0.65)
                        else:
                            # Normal case: bin doesn't cross midnight
                            time_mask = (y1 == requested_year) & (d1 == doy) & (hour >= bin_start) & (hour < bin_end) & (phase > -10) & (amp > 0.65)
                        ph1 = phase[time_mask]
                        amp1 = amp[time_mask]
                        
                        if len(ph1) >= minvalperbin:
                            # Calculate statistics
                            rph1 = np.round(np.mean(ph1), 2)
                            meanA = np.mean(amp1)
                            rph1_std = np.std(ph1)
                            yy, mm, dd, cyyyy, cdoy, YMD = g.ydoy2useful(requested_year, doy)
                            bin_start_hour = (bin_idx * bin_hours + bin_offset) % 24
                            
                            # Create data entry for tv array and write to file
                            newl = [requested_year, doy, np.mean(ph1), len(ph1), bin_start_hour]
                            fout.write(f" {requested_year:4.0f} {doy:3.0f} {rph1:6.2f} {rph1_std:6.2f} {meanA:6.3f} {0.0:5.2f}   {mm:2.0f} {dd:2.0f}   {bin_start_hour:2.0f}\n")
                            tv = np.append(tv, [newl], axis=0)
                else:
                    # Daily binning: use existing logic for backwards compatibility
                    time_mask = (y1 == requested_year) & (d1 == doy) & (phase > -10) & (amp > 0.65)
                    ph1 = phase[time_mask]
                    amp1 = amp[time_mask]
                    
                    if len(ph1) >= minvalperday:
                        newl = [requested_year, doy, np.mean(ph1), len(ph1)]
                        tv = np.append(tv, [newl], axis=0)
                        rph1 = np.round(np.mean(ph1), 2)
                        meanA = np.mean(amp1)
                        rph1_std = np.std(ph1)
                        yy, mm, dd, cyyyy, cdoy, YMD = g.ydoy2useful(requested_year, doy)
                        fout.write(f" {requested_year:4.0f} {doy:3.0f} {rph1:6.2f} {rph1_std:6.2f} {meanA:6.3f} {0.0:5.2f}   {mm:2.0f} {dd:2.0f} \n")
    return tv

def apriori_file_exist(station, fr, extension=''):
    """
    reads in the a priori RH results

    Parameters
    ----------
    station : string
        station name

    fr : integer
        frequency
        
    extension : str, optional
        analysis extension for finding files
        
    Returns
    -------
    boolean as to whether the apriori file exists

    """
    file_manager = FileManagement(station, 'apriori_rh_file', frequency=fr, extension=extension)
    apriori_path_f, format_type = file_manager.find_apriori_rh_file()
    
    return apriori_path_f.exists() 

def load_phase_filter_out_snow(station, year1, year2, fr, snowmask, extension = ''):
    """
    Load all phase data and attempt to remove outliers from snow if snowmask provided. 

    Parameters
    ----------
    station : str
        four character station name

    year1 : int
        starting year
    year2 : int
        ending year
    fr : int
        frequency, i.e. 1 or 20
    snowmask : str
        name/location of the snow mask file
        None if this value is not going to be used

    Returns
    -------
    dataexist : bool
        whether phase data were found
    year : numpy array of int
        calendar years
    doy : numpy array of int
        day of year
    hr : numpy array of floats
        UTC hour of measurement
    ph : numpy array of floats
        LS phase estimates
    azdata : numpy array of floats
        average azimuth, degrees
    ssat  : numpy array of int
        satellite number
    rh : numpy array of floats
        reflector height, meters
    amp_lsp : numpy array of floats
        lomb scargle periodogram amplitude
    amp_ls : numpy array of floats
        least squares amplitude
    ap_rh : numpy array of floats
        apriori rh
    results_trans : numpy array
        all phase results concatenated into numpy array
        plus column for quadrant and unwrapped phase

    """
#   now load the phase data
    newresults = []
    results_trans = []
    vquad = np.empty(shape=[0, 16])
    # output will go to 
    output_dir = Path(os.environ['REFL_CODE']) / 'Files' / station
    if extension:
        output_dir = output_dir / extension

    # Ensure the directory exists before trying to save to it
    fname = output_dir / 'raw.phase'

    dataexist, results = load_sat_phase(station, year1,year2, fr, extension)
    if not dataexist:
        print("No phase data was found to load.")
        # Return empty values to prevent a crash downstream
        return False, [], [], [], [], [], [], [], [], [], [], []

    results = results.T # backwards for consistency
    if snowmask == None:
        nr,nc = np.shape(results)
        if nr > 0:
            print('Number of rows and columns ', nr,nc)
            raw = write_out_raw_phase(results,fname)
    else:
        print('Snow mask should exist')
        override = np.loadtxt(snowmask, comments='%')
        # adding nonsense because it doesn't like having only one value
        #  which is a kluge i know
        blah = np.array([[1, 2], [3, 4]])
        override = np.vstack((override, blah))
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
    #  
        nr,nc = np.shape(vquad)
        if nr > 0:
            print('Number of rows and columns after snow filter ', nr,nc)
            raw = write_out_raw_phase(vquad,fname)

    rtrans= np.transpose(raw)

    if len(rtrans) == 0:
        print('no results ')
        dataexist = False
        year = []; doy = []; hr = []; ph = []; azdata = []; ssat = []
        rh = []; amp_lsp = []; amp_ls=[]; ap_rh = []
    else:
        dataexist = True
        # save with new variable names
        year = rtrans[0]
        doy = rtrans[1]
        hr = rtrans[2]
        ph = rtrans[3]
        azdata = rtrans[5]
        ssat = rtrans[6]
        amp_ls = rtrans[7]
        ap_rh = rtrans[11]
        rh = rtrans[13]
        amp_lsp = rtrans[15]

    return dataexist, year, doy, hr, ph, azdata, ssat, rh, amp_lsp, amp_ls, ap_rh, rtrans


def help_debug(rt,xdir, station):
    """
    Takes the input of phase files, read by other functions, and writes out a 
    file to help with debugging  (comparion of matlab and python codes)

    rt : numpy array of floats
        contents of the phase files stored in a numpy array 
    xdir : str
        where the otuput should be written
    station : str
        name of the station

    """
    fname = Path(xdir) / 'Files' / station / f'tmp.{station}'
    # don't have a priori rh values at this point
    rhtrack = 0
    #if True:
        # open the file
        #debug = write_all_phase(rt,fname,None,1,rhtrack)
        # write to the file
    #    debug = write_all_phase(rt,fname,debug,2,rhtrack)
    #    debug.close()


def load_avg_phase(station,fr,bin_hours=24,extension='',bin_offset=0):
    """
    loads a previously computed averaged phase solution with matching temporal resolution.
    this is NOT the same as the multi-track phase results.
    This file is now stored in station subdirectory in $REFL_CODE/Files/

    Parameters
    ----------
    station : str
        4 character station ID, lowercase
    fr : int
        frequency
    bin_hours : int, optional
        time bin size in hours (1,2,3,4,6,8,12,24). Default is 24 (daily).
        Only compares against files with exact same temporal resolution.
    extension : str, optional
        analysis extension for finding files, default is ''

    Returns
    -------
    avg_exist : bool
        whether the necessary file exists
    avg_date : list of floats
        fractional year, i.e. year + doy/365.25
    avg_phase : list of floats
        average phase for the given temporal resolution

    """

    avg_date = []
    avg_phase = []
    avg_exist = False

    # Use FileManagement for consistent phase file paths
    file_manager = FileManagement(station, 'daily_avg_phase_results', extension=extension)
    base_path = file_manager.get_file_path().parent
    
    # Generate consistent filename with exact temporal resolution matching
    suffix = get_temporal_suffix(fr, bin_hours, bin_offset)
    xfile = base_path / f"{station}_phase{suffix}.txt"

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

    if not avg_exist:
        if bin_hours < 24:
            print(f'WARNING: No previous {bin_hours}-hour phase file found for QC. File: {xfile}')
            print('You do not have a previous solution to compare to so I cannot compute QC stats. Rerun vwc')
        else:
            print('WARNING: The average phase file used from a previous run for QC does not exist as yet')
            print('You do not have a previous solution to compare to so I cannot compute QC stats. Rerun vwc')

    return avg_exist, avg_date, avg_phase


def load_sat_phase(station, year, year_end, freq, extension = ''):
    """
    Picks up the phase estimates from local (REFL_CODE) results section
    and returns most of the information from those files

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
    results : numpy array of floats
        basically one variable with everything in the original columns from the daily phase files

    """
    print('Requested frequency: ', freq)
    dataexist = False
    xdir = os.environ['REFL_CODE']
    xfile = Path(xdir) / 'input' / 'override' / f'{station}_vwc' 
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
    for yyyy in range(year, year_end+1):
        print('reading in year', yyyy)
        # where the results are stored
        data_dir = thedir / str(yyyy) / 'phase' / station
        if extension:
            data_dir = data_dir / extension
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
    #minyear = np.min(np.unique(results[:,0]))
    #maxyear = np.max(np.unique(results[:,0]))
    nr,nc = np.shape(results)
    print(nr, ' number of rows')

    results = results.T  # dumb, but i was using this convention.  easier to maintain

    if len(results) > 0:
        dataexist = True 

    return dataexist, results


def set_parameters(station, minvalperday,tmin,tmax,min_req_pts_track,fr, year, year_end,
                   subdir,plt,auto_removal,warning_value,extension,
                   bin_hours=None, minvalperbin=None, bin_offset=None):
    """
    the goal of this code is to pick up the relevant parameters used in vwc.

    Parameters
    ----------
    station : str
        4 character station name
    minvalperday : int
        number of phase values required each day
    tmin : float
        min soil texture
    tmax : float
        max soil texture
    min_req_pts_track: int 
        minimum number of phase values per year per track
    freq : int
        frequency to use (1,20 allowed)
    year : int 
        first year to analyze
    year_end : int
        last year to analyze
    subdir : str
        name for subdirectory used in subdirectory of REFL_CODE/Files
        this probably should go away and be repaced with extension
    plt : bool
        whether you want plots to come to the screen
    auto_removal : bool
        whther tracks should be removed when they fail QC
    warning_value : float
        phase RMS needed to trigger warning
    extension : str
        extension used for inputs and outputs (i.e. test1 in ssss.test1.json)

    Returns
    -------
    minvalperday : int
        number of phase values required to create a daily average
    tmin : float
        min soil texture
    tmax : float
        max soil texture
    min_req_pts_track: int 
        minimum number of phase values per year per track
    freq : int
        frequency to use (1,20 allowed)
    year_end : int
        last year to analyze
    subdir : str
        name for subdirectory used in subdirectory of REFL_CODE/Files
    plt : bool
        whether you want plots to come to the screen
    auto_removal : bool
        whther tracks should be removed when they fail QC
    warning_value : float
        phase RMS needed to trigger warning
    extension : str
        extra name for the json file

    """
    if (len(station) != 4):
        print('station name must be four characters. Exiting')
        sys.exit()

    if (len(str(year)) != 4):
        print('Year must be full year (4 char). Exiting')
        sys.exit()

    g.checkFiles(station, '')
    # should not crash if file does not exist...
    if extension is None:
        lsp = gnssir.read_json_file(station, '',noexit=True, silent=True)
    else:
        lsp = gnssir.read_json_file(station, extension,noexit=True, silent=True)

    # originally this was for command line interface ... 
    remove_bad_tracks = auto_removal # ??
    plot_legend = True # default is to use them
    circles = False

    if tmin is None:
        if 'vwc_min_soil_texture' in lsp:
            tmin = lsp['vwc_min_soil_texture']
        else:
            tmin = 0.05
    if tmax is None:
        if 'vwc_max_soil_texture' in lsp:
            tmax = lsp['vwc_max_soil_texture']
        else:
            tmax = 0.50
    if min_req_pts_track is None:
        if 'vwc_min_req_pts_track' in lsp:
            min_req_pts_track = lsp['vwc_min_req_pts_track']
        else:
            min_req_pts_track = 100
    # Always load minvalperday from JSON for transparency (even if not used)
    json_minvalperday = None
    if 'vwc_minvalperday' in lsp:
        json_minvalperday = lsp['vwc_minvalperday']

    if warning_value is None:    
        if 'vwc_warning_value' in lsp:
            warning_value = lsp['vwc_warning_value']
        else:
            warning_value = 5.5


    # not using extension
    # pick up values in json, if available
    if 'vwc_plot_legend' in lsp:
        plot_legend = lsp['vwc_plot_legend']
    if 'vwc_circles' in lsp:
        circles = lsp['vwc_circles']

    if 'vwc_min_norm_amp' in lsp:
        min_norm_amp = lsp['vwc_min_norm_amp']
    else:
        min_norm_amp = 0.5  # trying this out

    # Handle subdaily binning parameters with precedence: CLI > JSON > Defaults
    if bin_hours is None:
        if 'vwc_bin_hours' in lsp:
            bin_hours = lsp['vwc_bin_hours']
        else:
            bin_hours = 24  # Default to daily
    
    if bin_offset is None:
        if 'vwc_bin_offset' in lsp:
            bin_offset = lsp['vwc_bin_offset']
        else:
            bin_offset = 0  # Default offset
    
    # Store original parameters to detect CLI conflicts
    original_minvalperbin = minvalperbin
    original_minvalperday = minvalperday
    
    # Validate CLI parameter conflicts
    if original_minvalperbin is not None and original_minvalperday is not None:
        print("Error: Cannot specify both -minvalperbin and -minvalperday at the same time.")
        print("Use -minvalperbin for all time bin sizes, or -minvalperday only for 24hr bins.")
        sys.exit()
    
    if original_minvalperday is not None and bin_hours != 24:
        print(f"Error: -minvalperday is only valid for daily (24hr) analysis, got {bin_hours}hr bins.")
        print("Use -minvalperbin for subdaily analysis.")
        sys.exit()
    
    # Handle minvalperbin vs minvalperday parameter resolution
    if original_minvalperbin is not None:
        # Function called with minvalperbin - use it
        minvalperbin = original_minvalperbin
    elif original_minvalperday is not None:
        # Function called with minvalperday - use it (with warning)
        minvalperbin = original_minvalperday
        print("Warning: -minvalperday is deprecated for 24hr bins. Use -minvalperbin instead.")
    elif minvalperbin is None:
        # No CLI parameters - resolve from JSON with preference rules
        if bin_hours == 24:
            # For 24hr bins, prefer minvalperday over minvalperbin
            if json_minvalperday is not None:
                minvalperbin = json_minvalperday
            elif 'vwc_minvalperbin' in lsp:
                minvalperbin = lsp['vwc_minvalperbin']
            else:
                minvalperbin = 10  # Daily default
        else:
            # For subdaily bins, use minvalperbin or default
            if 'vwc_minvalperbin' in lsp:
                minvalperbin = lsp['vwc_minvalperbin']
            else:
                minvalperbin = 5   # Subdaily default

    freq = fr # KE kept the other variable

    if not year_end:
        year_end = year 

    # originally was making people input these on the command line
    # now first try to read from json.  if not there they will be set here

    if tmin is None:
        tmin = 0.05

    if tmax is None:
        tmax = 0.5

    # default is station name, but use extension if provided
    if subdir is None:
        if extension:
            subdir = f"{station}/{extension}"
        else:
            subdir = station

    # make sure subdirectory exists
    g.set_subdir(subdir)

    if not plt:
        print('no plots will come to screen. Will only be saved.')

    print('=== VWC Configuration ===')
    print(f'vwc_min_soil_texture: {tmin:.2f}')
    print(f'vwc_max_soil_texture: {tmax:.2f}')
    print(f'vwc_min_req_pts_track: {min_req_pts_track}')
    print(f'vwc_warning_value: {warning_value:.1f}')
    print(f'vwc_min_norm_amp: {min_norm_amp:.1f}')
    
    print('=== Time Binning ===')
    print(f'vwc_bin_hours: {bin_hours}')
    print(f'vwc_bin_offset: {bin_offset}') 
    # Show minvalperbin with source information
    minvalperbin_source = ""
    if original_minvalperbin is not None:
        minvalperbin_source = " (from CLI)"
    elif original_minvalperday is not None:
        minvalperbin_source = " (from CLI -minvalperday)"
    elif bin_hours == 24 and json_minvalperday is not None and 'vwc_minvalperbin' not in lsp:
        minvalperbin_source = " (from JSON vwc_minvalperday)"
    elif bin_hours == 24 and json_minvalperday is not None:
        minvalperbin_source = " (from JSON vwc_minvalperday, preferred for 24hr bins)"
    elif 'vwc_minvalperbin' in lsp:
        minvalperbin_source = " (from JSON)"
    else:
        minvalperbin_source = " (default)"
    
    print(f'vwc_minvalperbin: {minvalperbin}{minvalperbin_source}')
    
    # Warning for experimental subdaily features
    if bin_hours < 24:
        print('WARNING: Subdaily VWC analysis (bin_hours < 24) is EXPERIMENTAL.')
    
    if extension:
        print(f'extension: {extension}')

    return minvalperday, tmin, tmax, min_req_pts_track, freq, year_end, subdir, \
            plt, remove_bad_tracks, warning_value, min_norm_amp, plot_legend,circles, extension, \
            bin_hours, minvalperbin, bin_offset

def write_all_phase(v,fname):
    """
    writes out preliminary phase values and other metrics for advanced vegetation
    option.  This is in the hope that it can be used in clara chew's
    dissertation algorithm.

    File is written to $REFL_CODE/Files/station/station_all_phase.txt I think

    Parameters
    ----------
    v : numpy of floats as defined in vwc_cl
        TBD
        year, doy, phase, azimuth, satellite number
        estimated RH, LSP amplitude, LS amplitude, UTC hours
        raw LSP amp, raw LS amp
    fname : str
        name of the output file
    filestatus : int
        1, open the file
        2, write to file (well, really any value)
    rhtrack: float
        apriori reflector height for the given track, meters

    Returns
    -------
    allrh : fileID

    """

    #if filestatus == 1:
    if True:
        print('Writing interim phase values to ', fname)
        header1=  'Year DOY Hour   Phase   Nv  Azimuth  Sat  Ampl emin emax  DelT aprioriRH  freq estRH  pk2noise LSPAmp'
        header2 = '(1)  (2)  (3)    (4)   (5)    (6)    (7)  (8)  (9)  (10)  (11)   (12)     (13)  (14)    (15)    (16)'

        #allrh.write(" {0:s}  \n".format(header1))
        #allrh.write(" {0:s}  \n".format(header2))

        #return allrh

    nr,nc = v.shape
    # sort by time
    ii = np.argsort(v[:,0] + v[:,1]/365.25)
    v = v[ii,:]

    with open(fname, 'w') as my_file:
        np.savetxt(my_file, [], header=header1, comments='%')
        #np.savetxt(my_file, [], header=header2, comments='%')
    #result = [[year, doy, utctime, phase, nv, avg_azim, sat_number, amp, min_el, max_el, del_t, rh_apriori, freq, max_f, obs_pk2noise, max_amp]]
    #np.savetxt(my_file, result, fmt="%4.0f %3.0f %6.2f %8.3f %5.0f %6.1f %3.0f %5.2f %5.2f %5.2f %6.2f %5.3f %2.0f %6.3f %6.2f %6.2f", comments="%")


    #for i in range(0,nr):
    #    q = old_quad(v[i,3])
    #    a = v[i,5] ; sat = v[i,6]; amp_lsp = v[i,15]
    #    amp_ls = v[i,7] ; rh = v[i,13]
    #    allrh.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:7.1f} {4:2.0f} {5:7.3f} {6:7.3f} {7:7.3f} {8:2.0f} \
    #            {9:7.2f} {10:7.2f} {11:7.2f} {12:7.3f}\n".format(v[i,0], v[i,1], v[i,3],a, sat,rh,amp_lsp,amp_ls,\
    #            q, v[i,2],v[i,10], rhtrack ))


def old_quad(azim):
    """
    calculates oldstyle quadrants from PBO H2O

    Parameters
    ----------
    azim : float
        azimuth, dgrees
    q : int
        old quadrant system used in pboh2o
    """
    q = 1
    if azim < 90:
        q= 1
    elif (azim >= 90) and (azim < 180):
        q = 4 
    elif (azim >= 180) and (azim < 270):
        q = 3
    elif (azim >= 270) and (azim <= 360):
        q =2

    return q


def kinda_qc(satellite, rhtrack,meanaztrack,nvalstrack, amin,amax, y, t, new_phase, 
             avg_date,avg_phase,warning_value,ftmp,remove_bad_tracks,k4,avg_exist):
    """
    Parameters
    ----------
    satellite : int
        satellite number
    rhtrack: float
        a priori reflector height 
    meanaztrack : float
        I think it is the azimuth of the track, degrees
    nvalstrack : int
        not sure?
    amin : int
        min az of this quadrant
    amax : int
        max az of this quadrant
    y : numpy array of ints
        year
    t : numpy array of ints
        day of year
    new_phase : numpy array of floats
        phase values for a given satellite track ??
    avg_date : numpy array of floats
        y + doy/365.25 I think
    avg_phase : numpy array of floats
        average phase, in degrees
    warning_value : float
        phase noise value
    ftmp : file ID 
        for writing
    remove_bad_tracks : bool
        whether you write out new tracks with bad ones removed
    k4 : int
        number of tracks?
    avg_exist : bool
        whether you have previous solution to compare to
    
        
    """
    # this is a kind of quality control -use previous solution to have 
    # better feel for whether current solution works. defintely needs to go in a function
    if avg_exist:
        # quadrant results for this satellite track
        satdate = y + t/365.25
        satphase = new_phase
        keepit=False

        # figure out intersection with "good" results
        inter, id1, id2 = np.intersect1d(avg_date, satdate, return_indices=True)
        
        # Check for valid intersection and indices
        if len(inter) == 0:
            # No matching dates found - skip QC for this track
            return k4
        
        # Validate indices before accessing arrays
        if (np.any(id1 >= len(avg_phase)) or np.any(id2 >= len(satphase)) or 
            np.any(id1 < 0) or np.any(id2 < 0)):
            # Invalid indices - skip QC for this track  
            print(f'Warning: QC index mismatch for satellite {satellite}, skipping QC')
            return k4
            
        aa = avg_phase[id1]
        bb = satphase[id2]
        if len(aa) > 0:
            res = np.round(np.std(aa - bb), 2)
            addit = ''
            keepit = True
            if (res > warning_value ) :
                addit = '>>>>>  Consider Removing This Track <<<<<'
                if remove_bad_tracks:
                    addit = '>>>>>  Removing This Track - rerun to see effect <<<<<'
                    keepit = False
            if keepit:
                ftmp.write("{0:3.0f} {1:7.2f} {2:3.0f} {3:7.1f} {4:7.0f} {5:4.0f} {6:4.0f} \n".format(k4,rhtrack, 
                       satellite,meanaztrack,nvalstrack,amin,amax))
                k4 = k4 + 1
                print(f"Npts {len(aa):4.0f} SatNu {satellite:2.0f} Residual {res:6.2f} Azims {amin:3.0f} {amax:3.0f} {addit:20s} ")

    else:
        print('You do not have a previous solution to compare to so I cannot compute QC stats. Rerun vwc')

    return k4

def save_vwc_plot(fig, pngfile):
    """
    Parameters
    ----------
    fig : matplotlib figure
        the figure definition you define when you open a figure
    pngfile : str
        name of the png file to be saved
    """
    fig.savefig(pngfile,format="png")
    print('Saving to ', pngfile)

    return

def rename_vals(year_sat_phase, doy, hr, phase, azdata, ssat, amp_lsp, amp_ls, rh, ap_rh,ii):
    """
    this is just trying to clean up vwc.py  
    send indices ii - and return renamed variables.  

    Parameters
    ----------
    year_sat_sat
    doy : 
    hr : 
    phase : 
    azdata : 
    ssat : 
    amp_lsp : 
    amp_ls
    rh : 
    ap_rh :
    ii :

    Returns
    -------
    y : numpy array of int
        year
    t : numpy array of int
        day of year 
    h : numpy array of floats
        hour of the day (UTC)
    x : numpy array of floats
        phase, degrees
    azd: numpy array of floats
        azimuth for the track
    s : numpy array of int
    amps_lsp : numpy array of floats
        LSP amplitude
    amps_ls : numpy array of floats
        least squares amplitude
    rhs : numpy array of floats
        estimated RH (m)
    ap_rhs : numpy array of floats
        a priori RH (m)

    """
    y = year_sat_phase[ii]
    t = doy[ii]
    h = hr[ii] # this is fractional hour of the day, GPS time 
    x = phase[ii]
    # should be so we could do subdaily VWC
    azd = azdata[ii] # azimuth, in degrees
    s = ssat[ii] # array of satellites numbers
    amps_lsp = amp_lsp[ii] # this amplitude is RH amplitude 
    amps_ls = amp_ls[ii] # this amplitude is phase amplitude 
    rhs = rh[ii] # estimated RH
    ap_rhs = ap_rh[ii] # apriori RH

    return y,t,h,x,azd,s,amps_lsp,amps_ls,rhs, ap_rhs


def write_out_raw_phase(v,fname):
    """
    write daily phase values used in vwc to a new consolidated file
    I added columns for quadrant and unwrapped phase

    Parameters
    ----------
    v : numpy array
        phase results read for multiple years. 
        could be with snow filter applied
    fname : str
        filename for output

    Returns
    -------
    newv : numpy array
        original variable v with columns added for
        quadrant (1-4) and unwrapped phase 

    """

    print('Writing to ', fname)
    # make sure v is numpy 
    v = np.asarray(v)
    nr,nc = v.shape; 
# sort by time
    ii = np.argsort(v[:,0] + v[:,1]/365.25)
    v = v[ii,:]
# calculate quadrants cause it makes life easier
    q = np.zeros((nr,1)) #
    for i in range(nr):
        q[i] = old_quad(v[i,5])

    # make a column full of zeros to store unwrapped phase
    unwrapped = np.zeros((nr,1)) #

    # add quadrant column
    newv = np.hstack((v,q))
    # add unwrapped column
    newv = np.hstack((newv,unwrapped))

    # get a list of possible satellites
    sat_list = np.unique(v[:,6])
    # discontinuity used in phase wrapping
    discont = 270

    # make a variable to return
    tnewv = np.zeros((nr,18)) #
    for ql in [1,2,3,4]:
        for s in sat_list:
            iw = (newv[:,16] == ql) & (newv[:,6] == s)
            tnewv = newv[iw,:]
            if (len(tnewv) > 0):
                doy = tnewv[:,1]; phase = tnewv[:,3]
                unwrap_phase = np.unwrap(phase,period=360,discont=discont)
                newv[iw,17] = unwrap_phase

    # headers for output file
    h1 = "Year DOY Hour   Phase   Nv  Azim   Sat  Ampl emin emax   DelT aprRH  fr  estRH  pk2n  LSPAmp  quad  unphase\n"   
    h2 = "(1)  (2)  (3)    (4)   (5)   (6)   (7)  (8)  (9)  (10)  (11)   (12)  (13)  (14)   (15)   (16)  (17)  (18) "

    with open(fname, 'w') as my_file:
        np.savetxt(my_file, newv, fmt="%4.0f %3.0f %6.2f %8.3f %5.0f %6.1f %3.0f %5.2f %5.2f %5.2f %6.2f %5.3f %2.0f %6.3f %6.2f %6.2f %2.0f %8.3f ",header=h1+h2,comments='%')

    return newv

def write_phase_for_advanced(filename, vxyz):
    """
    Writes out a file of interim phase results for advanced models
    developed by Clara Chew

    File generally written to $REFL_CODE/Files/<station>/all_phase.txt

    Parameters
    ----------
    filename : str
        name for output file
    vxyz : numpy array of floats
        as defined in vwc_cl.py
    """
    # do a quick sort as they are likely quadrant sorted now
    ii = np.argsort(vxyz[:,0] + vxyz[:,1]/365.25)
    vxyz = vxyz[ii,:]
    #headers for output file - these are not correct BTW
    print('writing interim file for advanced model ', filename)
    h1 = "Year DOY Phase  Azim Sat    RH    nLSPA nLSA    Hour   LSPA   LS  apRH  quad  delRH  vegM\n"
    h2 = "(1)  (2)  (3)   (4)  (5)    (6)    (7)   (8)     (9)   (10)  (11)  (12)  (13)  (14)  (15) "
    #2012   1   9.19  315.6  1   1.850   0.97   0.98  0.59 19.80 19.79  1.85  2
    with open(filename, 'w') as my_file:
        np.savetxt(my_file, vxyz, fmt="%4.0f %3.0f %6.2f %6.1f %2.0f %7.3f %6.2f %6.2f %5.2f %6.2f %6.2f %6.3f %2.0f %6.3f %2.0f  ",header=h1+h2,comments='%')

    return
#                   if adhoc_snow:
#                        ii = (norm_ampLSP > 0.5)
#                        y,t,h,new_phase,azd,s,amp_lsps,amp_lss,rhs,ap_rhs = \
#                                qp.rename_vals(y, t, h, new_phase, azd, s, amp_lsps, amp_lss, rhs, ap_rhs,ii)
#                        norm_ampLSP = norm_ampLSP[ii]
#                        norm_ampLS = norm_ampLS[ii]
#                        fracyear = fracyear[ii]

