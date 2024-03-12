import warnings
import argparse
import os
import subprocess
import sys
import time
import wget
import multiprocessing
from functools import partial

#import gnssrefl.gnssir as guts
import gnssrefl.gnssir_v2 as guts2
import gnssrefl.gps as g

from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name (4 ch)", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)

    # optional inputs
    parser.add_argument("-snr", default=None, help="snr file ending, default is 66", type=int)
    parser.add_argument("-plt", default=None, help="plt to screen (True or False)", type=str)
    parser.add_argument("-fr", default=None, type=int, help="Frequency, 1 for GPS L1, 101 for Glonass L1 etc")
    parser.add_argument("-ampl", default=None, type=float, help="Min spectral amplitude ")
    parser.add_argument("-sat", default=None, type=int, help="Only look at this satellite")
    parser.add_argument("-doy_end", default=None, type=int, help="doy end")
    parser.add_argument("-year_end", default=None, type=int, help="year end")
    parser.add_argument("-azim1", default=None, type=int, help="lower limit azimuth (deg)")
    parser.add_argument("-azim2", default=None, type=int, help="upper limit azimuth (deg)")
    parser.add_argument("-nooverwrite", default=None, type=str, help="default is False, i.e. you will overwrite")
    parser.add_argument("-extension", type=str, help="extension for result file, useful for testing strategies")
    parser.add_argument("-compress", default=None, type=str, help="Boolean, xz compress SNR files after use")
    parser.add_argument("-gzip", default=None, type=str, help="Boolean, gzip SNR files after use. Default is True")
    parser.add_argument("-screenstats", default=None, type=str, help="Boolean, some stats printed to screen(default is False)")
    parser.add_argument("-delTmax", default=None, type=int, help="Allowed satellite arc length (minutes)")
    parser.add_argument("-e1", default=None, type=float, help="min elev angle (deg)")
    parser.add_argument("-e2", default=None, type=float, help="max elev angle (deg)")
    parser.add_argument("-mmdd", default=None, type=str, help="Boolean, add columns for month,day,hour,minute")
    parser.add_argument("-dec", default=1, type=int, help="decimate SNR file to this sampling rate before computing periodograms")
    parser.add_argument("-newarcs", default=None, type=str, help="This no longer has any meaning")
    parser.add_argument("-par", default=None, type=int, help="Number of processes ?")


    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'screenstats', 'nooverwrite', 'compress', 'screenstats', 'mmdd','gzip','newarcs']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def gnssir(station: str, year: int, doy: int, snr: int = 66, plt: bool = False, fr: int = None, 
        ampl: float = None, sat: int = None, doy_end: int = None, year_end: int = None, azim1: int = 0, 
        azim2: int = 360, nooverwrite: bool = False, extension: str = '', compress: bool = False, 
        screenstats: bool = False, delTmax: int = None, e1: float = None, e2: float = None, 
           mmdd: bool = False, gzip: bool = True, dec : int = 1, newarcs : bool = True, par : int = None ):
    """
    gnssir is the main driver for estimating reflector heights. The user is required to 
    have set up an analysis strategy using gnssir_input. 

        
    Examples
    --------
    gnssir p041 2021 15 
        analyzes the data for station p041, year 2021 and day of year 15.
    gnssir p041 2021 15  -snr 99
        uses SNR files with a 99 suffix
    gnssir p041 2021 15  -plt T
        plots of SNR data and periodograms come to the screen. Each frequency gets its own plot.
    gnssir p041 2021 15  -screenstats T
        sends debugging information to the screen
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

    Parameters
    ----------
    station : str
        lowercase 4 character ID of the station
    year : int
        full Year
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
        GNSS frequency. Value options:

            1,2,20,5 : GPS L1, L2, L2C, L5

            101,102 : GLONASS L1, L2

            201, 205,206,207,208 : GALILEO E1, E5a,E6,E5b,E5

            302,306,307 : BEIDOU B1, B3, B2 (not sure we do 307)

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
        If the azimuth angles are changed in the json (using 'azval' key) and not here, then the json overrides these.
        If changed here, then it overrides what you requested in the json. default is 0.
    azim2 : int, optional
        upper limit azimuth.
        If the azimuth angles are changed in the json (using 'azval' key) and not changed here, then the json overrides these.
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
    newarcs : bool, optional
        this input no longer has any meaning 

    """

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    exitS = g.check_inputs(station, year, doy, snr)

    if exitS:
        sys.exit()

    lsp = guts2.read_json_file(station, extension)
    # now check the overrides to the json instructions

    # requiring people use the new code
    if 'azval2' not in lsp:
        print('An azval2 variable was not found in your json input file. Fix your json ')
        print('and/or use gnssir_input to make a new one. Exiting')
        sys.exit()



    # plt is False unless user changes
    lsp['plt_screen'] = plt

    if delTmax is not None:
        lsp['delTmax'] = delTmax

    if ((lsp['maxH'] - lsp['minH']) < 5):
        print('Requested reflector heights (', lsp['minH'], ',', lsp['maxH'], ') are too close together. Exiting.')
        print('They must be at least 5 meters apart - and preferably further than that.')
        sys.exit()

    # compress is False unless user changes
    lsp['wantCompression'] = compress

    # screenstats is True unless user changes
    lsp['screenstats'] = screenstats

    # added this for people that have 1 sec files that do not need this resolution
    # decimation is a bit slow but way faster than doing a gazillion periodograms with 
    # 1 sec data

    lsp['dec'] = dec

    # in case you want to analyze multiple days of data
    if doy_end is None:
        doy_end = doy

    # mmdd is False unless user changes
    add_mmddhhss = mmdd


    # in case you want to analyze only data within one year
    year_st = year  # renaming for confusing variable naming when dealing with year calculations below
    if year_end is None:
        year_end = year_st

    # default will be to overwrite
    #if nooverwrite is None:
    lsp['nooverwrite'] = nooverwrite
    #else:
    #    lsp['overwriteResults'] = False

    if e1 is not None:
        lsp['e1'] = e1
    if e2 is not None:
        lsp['e2'] = e2

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
        lsp['azval'] = [azim1,  azim2]

    # this is for when you want to run the code with just a single frequency, i.e. input at the console
    # rather than using the input restrictions
    if fr is not None:
        lsp['freqs'] = [fr]
    if ampl is not None:
        # this is not elegant - but allows people to set ampl on the command line
        # but use the frequency list from their json ...  which i think has max of 12
        # but use 14 to be sure
        lsp['reqAmp'] = [ampl for i in range(14)]

    if sat is not None:
        lsp['onesat'] = [sat]

    lsp['mmdd'] = add_mmddhhss
    # added 2022apr15
    lsp['gzip'] = gzip

    # if refraction model is not assigned, set it to 1
    if 'refr_model' not in lsp.keys():
        lsp['refr_model'] = 1

    xdir = str(os.environ['REFL_CODE'])
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

    args = {'station': station.lower(), 'year': year, 'doy': doy, 'snr_type': snr, 'extension': extension, 'lsp': lsp}

    print(lsp['pele'], ' direct signal elevation angle limits')
    print(lsp['e1'], lsp['e2'], ' min and max elevation angles')
    # added this because ellist is a new option and was not necessarily created in old json files
    if 'ellist' not in lsp:
        print('did not find ellist')
        if float(lsp['e1']) < float(lsp['pele'][0]):
            print('emin is smaller than the minimum eangle (pele) used for direct signal removed.')
            print('This is Forbidden. Fix the records set in the json created by gnssir_analysis')
            sys.exit()
    else:
        if float(lsp['e1']) < float(lsp['pele'][0]):
            print('Your requested emin is lower than the minimum elevation angle used ')
            print('for direct signal removal. This is stored in the variable pele.')
            print('This is Forbidden. Fix the pele records set in the json created by gnssir_analysis')
            sys.exit()
        if float(lsp['e2']) > float(lsp['pele'][1]):
            print('Your requested emax is higher than the maximum elevation angle used ')
            print('for direct signal removal. This is stored in the variable pele.')
            print('This is Forbidden. Fix the pele records set in the json created by gnssir_analysis')
            sys.exit()

    # should make sure there are directories for the results ... 
    g.checkFiles(station.lower(), extension)

    year_list = list(range(year_st, year_end+1))
    # changed to better describe year and doy start/end

    print('Requested frequencies ', lsp['freqs'])
    additional_args = { "year_end": year_end, "year_st": year_st, "doy": doy, "doy_end": doy_end, "args": args }


    t1 = time.time()
    if not par: 
        # analyze one year at a time in the current code
        for year in year_list:
            process_year(year, **additional_args)
    else:
        print('Using process year with pools')
        pool = multiprocessing.Pool(processes=par) 
        partial_process_year = partial(process_year, **additional_args)

        pool.map(partial_process_year, year_list)
        pool.close()
        pool.join()

    t2 = time.time()
    print('Time to compute ', round(t2-t1,2))

def process_year(year, year_end, year_st, doy, doy_end, args):
    """
    Code that does the processing for a specific year. Refactored to separate 
    function to allow for parallel processes

    Parameters
    ----------
    year : int
        the year you are currently analyzing
    year_end : int
        end year. This was the last year you plan to analyze
    year_st: int 
        This is starting year you were planning to analyze
    doy : integer
        Day of year
        POOR VARIABLE NAME. SHOULD BE CHANGED. i believe it is the start doy on the start year.
    doy_end : int
        end day of year on the last year you plan to analyze
        Default is None. 
    args : dict
        arguments passed into gnssir through commandline (or python)

    """
    if year != year_end:
        doy_en = 366
    else:
        doy_en = doy_end

    if year == year_st:
        doy_list = list(range(doy, doy_en+1))
    else:
        doy_list = list(range(1, doy_en+1))

    # so really this is looking at only a single year
    # looping through day of year. I think? 
    args['year'] = year
    for doy in doy_list:
        args['doy'] = doy
        try:
            guts2.gnssir_guts_v2(**args)
        except:
            warnings.warn(f'error processing {year} {doy}');                



def main():
    args = parse_arguments()
    gnssir(**args)


if __name__ == "__main__":
    main()


