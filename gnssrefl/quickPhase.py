import argparse
import numpy as np
import sys
import time
import multiprocessing
from functools import partial

import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.phase_functions as qp
from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="doy", type=int)
    parser.add_argument("-snr", default=None, help="snr file ending", type=int)
    parser.add_argument("-fr", default=None, help="frequency: 1 (L1), 20 (L2C), 5 (L5), or 'all'. Only L2C officially supported.", type=str)
    parser.add_argument("-doy_end", "-doy_end", default=None, type=int, help="doy end")
    parser.add_argument("-year_end", "-year_end", default=None, type=int, help="year end")
    parser.add_argument("-extension", default='', help="analysis extension for json file", type=str)
    parser.add_argument("-e1", default=None, type=float),
    parser.add_argument("-e2", default=None, type=float),
    parser.add_argument("-plt", default=None, type=str, help="plots come to the screen - which you do not want!")
    parser.add_argument("-screenstats", default=None, type=str, help="stats come to the screen")
    parser.add_argument("-gzip", default=None, type=str, help="gzip SNR files after use, default is True" )
    parser.add_argument("-par", default=None, type=int, help="Number of processes to spawn (up to 10)")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'screenstats', 'gzip']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def quickphase(station: str, year: int, doy: int, year_end: int = None, doy_end: int = None, snr: int = 66,
        fr: str = None, e1: float = 5, e2: float = 30, plt: bool = False, screenstats: bool = False, gzip: bool = True, extension: str = '', par: int = None):
    """
    quickphase computes phase, which are subquently used in vwc. The command line call is phase
    (which maybe we should change).
    
    Examples
    --------
    phase p038 2021 4
        analyzes data for year 2021 and day of year 4

    phase p038 2021 1 -doy_end 365 
        analyzes data for the whole year

    phase p038 2021 1 -doy_end 365 -par 5
        analyzes data for the whole year using 5 parallel processes

    Parameters
    ----------
    station: str
        4 character ID of the station.
    year: int
        full Year to evaluate.
    doy: int
        day of year to evaluate.
    year_end: int, optional
        year to end analysis. Using this option will create a range from year-year_end.
        Default is None.
    doy_end: int, optional
        Day of year to end analysis. Using this option will create a range of doy-doy_end.
        If also using year_end, then this will be the day to end analysis in the year_end requested.
        Default is None.
    snr : int, optional
        SNR format. This tells the code what elevation angles are in the SNR file
        value options:

            66 (default) : data with elevation angles less than 30 degrees

            99 : data with elevation angles between 5 and 30 degrees

            88 : data with all elevation angles 

            50 : data with elevation angles less than 10 degrees

    fr : str, optional
        GNSS frequency. Currently only supports L2C. Default is 20 (l2c)
    e1 : float, optional
        Elevation angle lower limit in degrees for the LSP. default is 5
    e2: float, optional
        Elevation angle upper limit in degrees for the LSP. default is 30
    plt: bool, optional
        Whether to plot results. Default is False
    screenstats: bool, optional
        Whether to print stats to the screen. Default is False
    gzip : bool, optional
        gzip the SNR file after use.  Default is True
    par : int, optional
        Number of parallel processes to spawn (up to 10). Default is 1 (single process).

    Returns
    -------
    Saves a file for each day in the doy-doy_end range: $REFL_CODE/<year>/phase/<station>/<doy>.txt

    columns in files:
        year doy hour phase nv azimuth sat ampl emin emax delT aprioriRH freq estRH pk2noise LSPAmp

    """

    compute_lsp = True # used to be an optional input
    if len(station) != 4:
        print('Station name must be four characters long. Exiting.')
        sys.exit()

    # Use the helper function to get the list of frequencies.
    fr_list = qp.get_vwc_frequency(station, extension, fr)

    # Check that an apriori file exists for each requested frequency.
    for f in fr_list:
        ex = qp.apriori_file_exist(station, f, extension)
        if not ex:
            print(f'No apriori RH file exists for frequency {f}. Please run vwc_input.')
            sys.exit()

    # in case you want to analyze multiple days of data
    if not doy_end:
        doy_end = doy
    
    # in case you want to analyze only data within one year
    if not year_end:
        year_end = year

    exitS = g.check_inputs(station, year, doy, snr)

    if exitS:
        sys.exit()

    g.result_directories(station, year, '')

    # this should really be read from the json
    pele = [5, 30]  # polynomial fit limits  for direct signal

    # Set up timing and parallel processing
    t1 = time.time()
    
    # Set default for par and validate
    if isinstance(par, type(None)):
        par = 1
    
    if not isinstance(par, int) or par <= 0 or par > 10:
        print('Number of processes must be between 1 and 10. Submit again. Exiting.')
        sys.exit()
    
    # Check for single day processing
    if (year == year_end) and (doy == doy_end):
        if par > 1:
            print('You are analyzing only one day of data - no reason to submit multiple processes')
            par = 1
    
    # Create args for worker function
    args = {
        'station': station, 'snr': snr, 'fr_list': fr_list, 'e1': e1, 'e2': e2,
        'pele': pele, 'plt': plt, 'screenstats': screenstats, 'compute_lsp': compute_lsp,
        'gzip': gzip, 'extension': extension
    }
    
    if par == 1:
        print('Sequential processing')
        process_phase_sequential(year, year_end, doy, doy_end, args)
    else:
        print('Parallel processing chosen')
        process_phase_parallel(year, year_end, doy, doy_end, args, par)
    
    t2 = time.time()
    print('Time to compute: ', round(t2-t1, 2), ' seconds')


def process_phase_day(year, doy, args, error_queue=None):
    """Process a single day - shared by both sequential and parallel processing"""
    try:
        print(f'Analyzing year/day of year {year}/{doy}')
        qp.phase_tracks(args['station'], year, doy, args['snr'], args['fr_list'], 
                       args['e1'], args['e2'], args['pele'], args['plt'], 
                       args['screenstats'], args['compute_lsp'], args['gzip'], args['extension'])
    except Exception as e:
        if error_queue:
            print('***********************************************************************')
            print('Error in phase processing: ', year, doy)
            print('***********************************************************************')
            error_queue.put(e)
        else:
            raise

def process_phase_sequential(year, year_end, doy, doy_end, args):
    """Sequential processing function"""
    # Original logic preserved
    if year_end != year:  # Multi-year processing
        year_range = np.arange(year, year_end+1)
        for y in np.arange(year, year_end+1):
            # If first year in multi-year range, then start on doy requested and finish year.
            if y == year_range[0]:
                date_range = np.arange(doy, 366)
            # If last year in multi-year range, then start on doy 1 finish on doy_end.
            elif y == year_range[-1]:
                date_range = np.arange(1, doy_end+1)
            # If year within multi-year range then do whole year start to finish.
            else:
                date_range = np.arange(1, 366)

            for d in date_range:
                process_phase_day(y, d, args)
    else:  # Single year processing
        for d in np.arange(doy, doy_end + 1):
            process_phase_day(year, d, args)

def process_phase_parallel(year, year_end, doy, doy_end, args, par):
    """Parallel processing setup and execution"""
    manager = multiprocessing.Manager()
    error_queue = manager.Queue()
    
    numproc = par
    print(year, doy, year_end, doy_end)
    # Get date ranges for parallel processing
    d, numproc = guts2.make_parallel_proc_lists_mjd(year, doy, year_end, doy_end, numproc)
    
    # Create list of (year, doy, args, error_queue) for each day to process
    day_list = []
    for index in range(numproc):
        d1 = d[index][0]
        d2 = d[index][1]
        for MJD in range(d1, d2+1):
            year_mjd, doy_mjd = g.modjul_to_ydoy(MJD)
            day_list.append((year_mjd, doy_mjd, args, error_queue))
    
    pool = multiprocessing.Pool(processes=numproc)
    pool.starmap(process_phase_day, day_list)
    pool.close()
    pool.join()
    
    # Check for errors
    if not error_queue.empty():
        print("One (or more) of the processes encountered errors. Will not proceed until errors are fixed.")
        i = 1
        while not error_queue.empty():
            e = error_queue.get()
            print(f"Error {i} type: {type(e)}. Error {i} message: {e}")
            i += 1
        sys.exit(1)

def main():
    args = parse_arguments()
    quickphase(**args)


if __name__ == "__main__":
    main()
