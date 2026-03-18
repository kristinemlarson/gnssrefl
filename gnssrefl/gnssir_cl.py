import warnings
import argparse
import contextlib
import os
import subprocess
import sys
import time
import wget
import multiprocessing

from tqdm import tqdm

#import gnssrefl.gnssir as guts
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.gps as g
import gnssrefl.refraction as refr

from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name (4 ch)", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)

    #print('gnssrefl version ', str(g.version('gnssrefl')))

    # optional inputs
    parser.add_argument("-snr", default=None, help="snr file ending, default is 66", type=int)
    parser.add_argument("-plt", default=None, help="plt to screen (True or False)", type=str)
    parser.add_argument("-fr", default=None, nargs="*",type=int, help="Frequency override for json, e.g. 1 101 for GPS and Glonass L1")
    parser.add_argument("-ampl", default=None, type=float, help="Min spectral amplitude ")
    parser.add_argument("-sat", default=None, type=int, help="Only look at this satellite")
    parser.add_argument("-doy_end", default=None, type=int, help="doy end")
    parser.add_argument("-year_end", default=None, type=int, help="year end")
    parser.add_argument("-azim1", default=None, type=int, help="lower limit azimuth (deg)")
    parser.add_argument("-azim2", default=None, type=int, help="upper limit azimuth (deg)")
    parser.add_argument("-nooverwrite", default=None, type=str, help="default is False, i.e. you will overwrite")
    parser.add_argument("-screenstats", default=None, type=str, help="screenstats, always created ")
    parser.add_argument("-extension", type=str, help="extension for result file, useful for testing strategies")
    parser.add_argument("-compress", default=None, type=str, help="Boolean, xz compress SNR files after use")
    parser.add_argument("-gzip", default=None, type=str, help="Boolean, gzip SNR files after use. Default is True")
    parser.add_argument("-delTmax", default=None, type=int, help="Allowed satellite arc length (minutes)")
    parser.add_argument("-e1", default=None, type=float, help="min elev angle (deg)")
    parser.add_argument("-e2", default=None, type=float, help="max elev angle (deg)")
    parser.add_argument("-mmdd", default=None, type=str, help="Boolean, add columns for month,day,hour,minute")
    parser.add_argument("-dec", default=1, type=int, help="decimate SNR file to this sampling rate before computing periodograms")
    parser.add_argument("-savearcs", default=None, type=str, help="boolean, save individual arcs. default is false.")
    parser.add_argument("-savearcs_format", default=None, type=str, help="format of saved arcs (txt or pickle). default is txt")
    parser.add_argument("-par", default=None, type=int, help="Number of processes to spawn (up to 10)")
    parser.add_argument("-debug", default=None, type=str, help="remove try/except so that error messages are provided. Parallel processing turned off")
    parser.add_argument("-midnite", default=None, type=str, help="allow midnite crossings (default is true)")
    parser.add_argument("-dbhz", default=None, type=str, help="whether to keep SNR in db-hz (default is false)")
    parser.add_argument("-lsp_method", default=None, type=str, help="LSP backend: fast (default, astropy NFFT) or scipy (original)")

    g.print_version_to_screen()
    #print (sys.version)

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'nooverwrite', 'compress', 'mmdd','gzip','savearcs','debug','screenstats','midnite','dbhz']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def gnssir(station: str, year: int, doy: int, snr: int = 66, plt: bool = False, fr: list= [], 
        ampl: float = None, sat: int = None, doy_end: int = None, year_end: int = None, azim1: int = 0, 
        azim2: int = 360, nooverwrite: bool = False, extension: str = '', compress: bool = False, 
        screenstats: bool = True, delTmax: int = None, e1: float = None, e2: float = None, 
           mmdd: bool = False, gzip: bool = None, dec : int = 1, savearcs : bool = False, savearcs_format: str='txt',
           par : int = None, debug : bool=False, midnite : bool=True, dbhz : bool=False, lsp_method : str='fast'):
    """
    gnssir is the main driver for estimating reflector heights. The user is required to 
    have set up an analysis strategy using gnssir_input. 

    screenstats is always True now - and the information is written to a file. I have kept the optional parameter
    for backwards compatability, but it does not do anything.

    To improve screen output when your job crashes, try -debug T 

    "secret limits" : arcs must be at least one degree long (in elevation angle).  I can change that - but just a warning.

    Parallel processing is now available. If you set -par to an integer between 2 and 10,
    it should substantially speed up your processing. Big thank you to AaryanRampal for getting this up and running.
    If you are using the docker, you will need to experiment about how to use this - as they have 
    requirements for multiple processes that I do not know about.

    As of v3.6. there is a way to save individual rising and setting arcs to an external file.
    You can then use them as you wish. The default is plain text but only has elevation angles
    and deltaSNR (SNR with direct signal removed). You can also save more information in a pickle
    file.  Just say -savearcs_format pickle. Both require -savearcs T to set this option. The 
    location of the files is printed to the screen. If an arc does not pass QC, it is saved, but in a separate
    directory with the name failQC added to it. 

    If you are using the non-standard snr files (i.e. not 66), you have been required to provide an online parameter
    every time you run gnssir. As of v 3.6.6, you can now save a parameter called snr when you use gnssir_input.
    So that would automate it for you.  If you haven't done that then you should use snr on the command line
    and set it to the appropriate value.
        
    Examples
    --------
    gnssir p041 2021 15 
        analyzes the data for station p041, year 2021 and day of year 15.
    gnssir p041 2021 15 -savearcs T 
        prints out individual arcs to $REFL_CODE/2021/arcs/p041/015
    gnssir p041 2021 1 -doy_end 100 -par 10
        analyze 100 days of data - but spawn 10 processes at a time. Big cpu time savings.
    gnssir p041 2021 15  -snr 99
        uses SNR files with a 99 suffix
    gnssir p041 2021 15  -plt T
        plots of SNR data and periodograms come to the screen. Each frequency gets its own plot.
    gnssir p041 2021 15  -screenstats T
        sends more information to the screen
    gnssir p041 2021 15  -nooverwrite T 
        only runs gnssir if there isn't a previous solution
    gnssir p041 2021 15  -extension strategy1
        runs gnssir using json file called p041.strategy1.json
    gnssir p041 2021 15  -doy_end 20 
        Analyzes data from day of year 15 to day of year 20
    gnssir p041 2021 15 -dec 5
        before computing periodograms, decimates the SNR file contents to 5 seconds
    gnssir p041 2021 15 -gzip T
        gzips the SNR file after you run the code. Big space saver (now the default)
    gnssir p041 2021 15 -fr 1 101 
        ignore frequency list in your json and use frequencies 1 and 101 

    Parameters
    ----------
    station : str
        lowercase 4 character ID of the station
    year : int
        full year
    doy : integer
        Day of year

    snr : int, optional
        SNR format. This tells the code what elevation angles to save data for. Input is the snr file ending.
        Value options:

            66 (default) : saves all data with elevation angles less than 30 degress

            99 : saves all data with elevation angles between 5 and 30 degrees

            88 : saves all data 

            50 : saves all data with elevation angles less than 10 degrees

    plt : bool, optional
        Send plots to screen or not. Default is False.
    fr : int, optional
        As of version 3.5.9 you are allowed to enter more than one GNSS frequency.
        It overrides whatever was stored in your json. This is entered into
        a list so do not use commas, i.e. 1 101 102 
        allowed frequency names:

            1,2,20,5 : GPS L1, L2, L2C, L5

            101,102 : GLONASS L1, L2

            201, 205,206,207,208 : GALILEO E1, E5a,E6,E5b,E5

            301,302,305,306,307,308 : BEIDOU (See RINEX 3 format description for details)

    ampl : float, optional
        minimum spectral peak amplitude. default is None
    sat : int, optional
        satellite number to only look at that single satellite. default is None.
    doy_end : int, optional
        end day of year. This is to create a range from doy to doy_end of days.
        If year_end parameter is used - then day_end will end in the day of the year_end.
        Default is None. (meaning only a single day using the doy parameter)
    year_end : int, optional
        end year. This is to create a range from year to year_end to get the snr files for more than one year.
        doy_end will be for year_end. Default is None.
    azim1 : int, optional
        lower limit azimuth.
        If the azimuth angles are changed in the json (using 'azval2' key) and not here, then the json overrides these.
        If changed here, then it overrides what you requested in the json. default is 0.
    azim2 : int, optional
        upper limit azimuth.
        If the azimuth angles are changed in the json (using 'azval2' key) and not changed here, then the json overrides these.
        If changed here, then it overrides what you requested in the json. default is 360.
    nooverwrite : bool, optional
        Use to overwrite lomb scargle result files or not.
        Default is False, i.e., it will overwrite.
    extension : string, optional
        extension for result file, useful for testing strategies. default is empty string
    compress : boolean, optional
        xz compress SNR files after use. default is False.
    screenstats : bool, optional
        whether to print stats to the screen or not. default is True.
    delTmax : int, optional
        maximum satellite arc length in minutes. found in the json
    e1 : float, optional
        use to override the minimum elevation angle.
    e2 : float, optional
        use to override the maximum elevation angle.
    mmdd : boolean, optional
        adds columns in results for month, day, hour, and minute. default is False.
    gzip : boolean, optional
        gzip compress SNR files after use. default is True (as of 2023 Sep 17).
    dec : int, optional
        decimate SNR file to this sampling period before the 
        periodograms are computed. 1 sec is default (i.e. no decimating)
    savearcs : bool, optional
        save arcs in individual files (elevation angle and deltaSNR)
    savearcs_format : str, optional
        format of saved arc files, txt or pickle. default is txt
    par : int, optional
        number of parallel processing jobs. 
    debug : bool, optional
        remove the primary call from try/except so that you have a better idea of why the code
        might be crashing. No parallel processing in this mode
    midnite : bool
        whether arcs can cross midnite
    dbhz : bool
        whether to keep SNR data in db-hz. default (false) is to convert to linear scale

    """
    vers = 'gnssrefl version ' + str(g.version('gnssrefl'))
    #print('You are running ', vers)
    screenstats = True


    if (len(station) == 9):
        print('Going to assume you meant ', station[0:4], ' and not ', station)
        # being lazy
        station = station[0:4]


#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()
    xdir = str(os.environ['REFL_CODE'])

    exitS = g.check_inputs(station, year, doy, snr)

    if exitS:
        sys.exit()

    # check this now before spawning multi-processor jobs
    if year_end is None:
        g.result_directories(station,year,extension)
    else:
        for y in range(year, year_end+1):
            g.result_directories(station,y,extension)

    station_config = guts2.read_json_file(station, extension)
    # 
    if 'snr' in station_config:
        if station_config['snr'] is not None:
            snr = station_config['snr']
            if not par or par <= 1:
                print('Found a snr choice in the json:', snr)
    if not par or par <= 1:
        print('Using snr file type: ', snr)

    station_config['midnite'] = midnite

    # make a refraction file you will need later
    refr.readWrite_gpt2_1w(xdir, station, station_config['lat'], station_config['lon'])

    # now check the overrides to the json instructions

    # requiring people use the new code
    if 'azval2' not in station_config:
        print('An azval2 variable was not found in your gnssir json input file. Fix your json ')
        print('and/or use gnssir_input to make a new one. Exiting')
        sys.exit()

    # plt is False unless user changes
    station_config['plt_screen'] = plt

    if delTmax is not None:
        station_config['delTmax'] = delTmax

    if ((station_config['maxH'] - station_config['minH']) < 5):
        print('Requested reflector heights (', station_config['minH'], ',', station_config['maxH'], ') are too close together. Exiting.')
        print('They must be at least 5 meters apart - and preferably further than that.')
        sys.exit()

    # compress is False unless user changes
    station_config['wantCompression'] = compress

    # screenstats is True unless user changes
    station_config['screenstats'] = screenstats

    # added this for people that have 1 sec files that do not need this resolution
    # decimation is a bit slow but way faster than doing a gazillion periodograms with 
    # 1 sec data

    station_config['dec'] = dec

    station_config['dbhz'] = dbhz
    station_config['lsp_method'] = lsp_method if lsp_method is not None else 'fast'

    # in case you want to analyze multiple days of data
    if doy_end is None:
        doy_end = doy

    # mmdd is False unless user changes
    add_mmddhhss = mmdd


    # in case you want to analyze only data within one year
    year_st = year  # renaming for confusing variable naming when dealing with year calculations below
    if year_end is None:
        year_end = year

    station_config['nooverwrite'] = nooverwrite

    if e1 is not None:
        station_config['e1'] = e1
    if e2 is not None:
        station_config['e2'] = e2

    # in case you want to look at a restricted azimuth range from the command line
    setA = 0
    # if azim1 is not default (has been changed)
    if azim1 != 0:
        setA = 1

    # if azim2 is not default (has been changed)
    if azim2 != 360:
        setA = setA + 1

    # TODO figure out the goal here
    # this only sets the new azim values only if bother azim1 and azim2 changed?
    if setA == 2:
        station_config['azval2'] = [azim1,  azim2]

    # this is for when you want to run the code with just a single frequency, i.e. input at the console
    # rather than using the input restrictions

    if len(fr) > 0:
        station_config['freqs'] = fr
        # better make sure you have enough amplitudes
        ampl_from_json = station_config['reqAmp'][0]
        if ampl is None:
            station_config['reqAmp'] = [ampl_from_json for i in range(14)]

    if ampl is not None:
        # this is not elegant - but allows people to set ampl on the command line
        # but use the frequency list from their json ...  which i think has max of 12
        # but use 14 to be sure
        station_config['reqAmp'] = [ampl for i in range(14)]

    if sat is not None:
        station_config['onesat'] = [sat]

    station_config['mmdd'] = add_mmddhhss
    # only override JSON gzip setting if explicitly passed on command line
    if gzip is not None:
        station_config['gzip'] = gzip
    else:
        guts2.gzip_migration(station_config, station, extension)
    # added 2024aug01
    station_config['savearcs'] = savearcs

    # added 2024aug27
    station_config['savearcs_format'] = savearcs_format

    # if refraction model is not assigned, set it to 1
    if 'refr_model' not in station_config:
        station_config['refr_model'] = 1

    # default to fast (astropy NFFT) LSP; users can override with -lsp_method scipy
    if 'lsp_method' not in station_config:
        station_config['lsp_method'] = 'fast'

    # good lord - why is this here? surely a function can be called
    picklefile = 'gpt_1wA.pickle'
    pname = xdir + '/input/' + picklefile

    #    print('refraction file exists')
    if not os.path.isfile(pname):
        local_copy = 'gnssrefl/' + picklefile
        if os.path.isfile(local_copy):
            print('found local copy of refraction file')
            subprocess.call(['cp', '-f', local_copy, xdir + '/input/'])
        else:
            print('download and move refraction file')
            url='https://github.com/kristinemlarson/gnssrefl/raw/master/gnssrefl/gpt_1wA.pickle'
            wget.download(url, picklefile)
            subprocess.call(['mv', '-f', picklefile, xdir + '/input/'])

    # added debug aug 3/2024
    args = {'station': station.lower(), 'year': year, 'doy': doy, 'snr_type': snr, 'extension': extension, 'station_config': station_config, 'debug': debug}

    if not par or par <= 1:
        print(station_config['pele'], ' direct signal elevation angle limits')

    # added this because ellist is a new option and was not necessarily created in old json files
    if 'ellist' not in station_config:
        #print('did not find ellist')
        if float(station_config['e1']) < float(station_config['pele'][0]):
            print('emin is smaller than the minimum eangle (pele) used for direct signal removed.')
            print('This is Forbidden. Fix the records set in the json created by gnssir_analysis')
            sys.exit()
    else:
        if float(station_config['e1']) < float(station_config['pele'][0]):
            print('Your requested emin is lower than the minimum elevation angle used ')
            print('for direct signal removal. This is stored in the variable pele.')
            print('This is Forbidden. Fix the pele records set in the json created by gnssir_input')
            sys.exit()
        if float(station_config['e2']) > float(station_config['pele'][1]):
            print('Your requested emax is higher than the maximum elevation angle used ')
            print('for direct signal removal. This is stored in the variable pele.')
            print('This is Forbidden. Fix the pele records set in the json created by gnssir_input')
            sys.exit()

    # should make sure there are directories for the results ... 
    g.checkFiles(station.lower(), extension)

    print('Requested frequencies ', station_config['freqs'])


    if (par == 1):
        par = None

    t1 = time.time()
    if (year == year_end) & (doy == doy_end):
        if par:
            print('You are analyzing only one day of data - no reason to submit multiple processes')
            par = None

    if not par:
        print('Parallel processing not requested\n')
        additional_args = { "args": args }
        process_year(year,year_end,doy,doy_end, **additional_args)

    else:
        if par > 10:
            print('For now we will only allow ten simultaneous processes. Submit again. Exiting.')
            sys.exit()

        print('Per-day output suppressed in parallel mode. Run without -par to see detailed output.')

        # Build flat list of (year, doy) work units
        MJD1 = int(g.ydoy2mjd(year, doy))
        MJD2 = int(g.ydoy2mjd(year_end, doy_end))
        day_list = []
        for mjd in range(MJD1, MJD2 + 1):
            y, d = g.modjul_to_ydoy(mjd)
            day_list.append((y, d))

        manager = multiprocessing.Manager()
        error_queue = manager.Queue()
        pool = multiprocessing.Pool(processes=par)

        worker_args = [(y, d, args, error_queue) for y, d in day_list]
        total_arcs = 0
        with tqdm(pool.imap_unordered(process_day_worker, worker_args),
                  total=len(day_list),
                  desc=f"gnssir {station}",
                  unit="day") as pbar:
            for n_arcs in pbar:
                total_arcs += n_arcs
                elapsed = time.time() - t1
                ms_per_arc = elapsed / total_arcs * 1000 if total_arcs else 0
                pbar.set_postfix_str(f"{total_arcs} arcs, {ms_per_arc:.1f} ms/arc")

        pool.close()
        pool.join()

        if not error_queue.empty():
            print("One (or more) of the processes encountered errors. Will not proceed until errors are fixed.")
            i = 1
            while not error_queue.empty():
                e = error_queue.get()
                print(f"Error {i} type: {type(e)}. Error {i} message: {e}")
                i += 1
            sys.exit(1)

    t2 = time.time()
    elapsed = round(t2-t1, 2)
    ndays = int(g.ydoy2mjd(year_end, doy_end)) - int(g.ydoy2mjd(year, doy)) + 1
    if par and total_arcs:
        ms_per_arc = round(elapsed / total_arcs * 1000, 1)
        print(f'Processed {ndays} days, {total_arcs} arcs in {elapsed} s ({ms_per_arc} ms/arc)')
    else:
        print(f'Processed {ndays} days in {elapsed} s ({round(elapsed/ndays, 2)} s/day)')


def count_result_arcs(result_path):
    """Count non-comment lines in a result file."""
    try:
        with open(result_path) as f:
            return sum(1 for line in f if not line.startswith('%'))
    except FileNotFoundError:
        return 0


def process_year(year, year_end, doy, doy_end, args):
    """Sequential processing for gnssir."""
    debug = args['debug']

    MJD1 = int(g.ydoy2mjd(year,doy))
    MJD2 = int(g.ydoy2mjd(year_end,doy_end))
    for modjul in range(MJD1, MJD2+1):
        y, d = g.modjul_to_ydoy(modjul)
        args['year'] = y
        args['doy'] = d
        if debug:
            guts2.gnssir_guts_v2(**args)
        else:
            try:
                guts2.gnssir_guts_v2(**args)
            except:
                print('***********************************************************************')
                print('Try using -debug T to get better information about why the code crashed:  ',y,d)
                print('***********************************************************************')

    return


def process_day_worker(worker_args):
    """Worker for parallel gnssir processing. Returns arc count for progress bar."""
    year, doy, args, error_queue = worker_args
    try:
        args = dict(args)
        args['year'] = year
        args['doy'] = doy
        with contextlib.redirect_stdout(open(os.devnull, 'w')):
            guts2.gnssir_guts_v2(**args)
        xdir = str(os.environ['REFL_CODE'])
        station = args['station']
        result_path = os.path.join(xdir, str(year), 'results', station, f'{doy:03d}.txt')
        return count_result_arcs(result_path)
    except Exception as e:
        print('***********************************************************************')
        print('Try using -debug T to get better information about why the code crashed: ',year,doy)
        print('***********************************************************************')
        error_queue.put(e)
        return 0


def main():
    args = parse_arguments()
    gnssir(**args)


if __name__ == "__main__":
    main()


