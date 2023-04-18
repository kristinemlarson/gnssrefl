
import argparse
import os
import subprocess
import sys
import wget

import gnssrefl.gnssir as guts
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
    parser.add_argument("-gzip", default=None, type=str, help="Boolean, gzip SNR files after use")
    parser.add_argument("-screenstats", default=None, type=str, help="Boolean, some stats printed to screen(default is False)")
    parser.add_argument("-delTmax", default=None, type=int, help="Allowed satellite arc length (minutes)")
    parser.add_argument("-e1", default=None, type=float, help="min elev angle (deg)")
    parser.add_argument("-e2", default=None, type=float, help="max elev angle (deg)")
    parser.add_argument("-mmdd", default=None, type=str, help="Boolean, add columns for month,day,hour,minute")
    parser.add_argument("-dec", default=1, type=int, help="decimate SNR file to this sampling rate before computing periodograms")


    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt', 'screenstats', 'nooverwrite', 'compress', 'screenstats', 'mmdd','gzip']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def gnssir(station: str, year: int, doy: int, snr: int = 66, plt: bool = False, fr: int = None,
           ampl: float = None, sat: int = None, doy_end: int = None, year_end: int = None,
           azim1: int = 0, azim2: int = 360, nooverwrite: bool = False, extension: str = '',
           compress: bool = False, screenstats: bool = False, delTmax: int = None,
           e1: float = None, e2: float = None, mmdd: bool = False, gzip: bool = False, dec : int = 1):
    """
        gnssir is the main driver for estimating Reflector Heights
        The user is required to have set up an analysis strategy using "make_json_input" 
        
        Examples
        --------
        gnssir p041 2021 15 
            analyzes the data for station p041, year 2021 and day of year 15.
        gnssir p041 2021 15  -snr 99
            uses SNR files with a 99 suffix
        gnssir p041 2021 15  -snr 99 -screenstats T
            sends debugging information to the screen
        gnssir p041 2021 15  -nooverwrite T 
            only runs gnssir if there isn't a previous solution
        gnssir p041 2021 15  -doy_end 20 
            Analyzes data from day of year 15 to day of year 20

        Parameters
        ----------
        station : str
            lowercase 4 character ID of the station
        year : int
            full Year
        doy : integer
            Day of year
        snr : int, optional
            SNR format. This tells the code what elevation angles to save data for. Will be the snr file ending.
            value options:
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

                302,306,307 : BEIDOU B1, B3, B2

        ampl : float, optional
            minimum spectral peak amplitude.
            default is None

        sat : int, optional
            satellite number to only look at that single satellite.
            default is None.

        doy_end : int, optional
            end day of year. This is to create a range from doy to doy_end of days.
            If year_end parameter is used - then day_end will end in the day of the year_end.
            Default is None. (meaning only a single day using the doy parameter)

        year_end : int, optional
            end year. This is to create a range from year to year_end to get the snr files for more than one year.
            doy_end will be for year_end.
            Default is None.

        azim1 : int, optional
            lower limit azimuth.
            If the azimuth angles are changed in the json (using 'azval' key) and not here, then the json overrides these.
            If changed here, then it overrides what you requested in the json.
            default is 0.
        azim2 : int, optional
            upper limit azimuth.
            If the azimuth angles are changed in the json (using 'azval' key) and not changed here, then the json overrides these.
            If changed here, then it overrides what you requested in the json.
            default is 360.
        nooverwrite : bool, optional
            Use to overwrite lomb scargle result files or not.
            Default is True (do not overwrite files).
        extension : string, optional
            extension for result file, useful for testing strategies.
            default is ''. (empty string)
        compress : boolean, optional
            xz compress SNR files after use.
            default is False.
        screenstats : bool, optional
            whether to print stats to the screen or not.
            default is True.
        delTmax : int, optional
            maximum satellite arc length in minutes. Set in make_json_input
        e1 : float, optional
            use to override the minimum elevation angle.
        e2 : float, optional
            use to override the maximum elevation angle.
        mmdd : boolean, optional
            adds columns in results for month, day, hour, and minute.
            default is False.
        gzip : boolean, optional
            gzip compress SNR files after use.
            default is False.
        dec : int, optional
            decimate SNR file to this sampling period before the 
            periodograms are computed. 1 sec is default (i.e. no decimating)

    """

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    exitS = g.check_inputs(station, year, doy, snr)

    if exitS:
        sys.exit()

    lsp = guts.read_json_file(station, extension)
    # now check the overrides to the json instructions

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

    xdir = str(os.environ['REFL_CODE'])
    picklefile = 'gpt_1wA.pickle'
    pname = xdir + '/input/' + picklefile

    if os.path.isfile(pname):
        print('refraction file exists')
    else:
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

    year_list = list(range(year_st, year_end+1))
    # changed to better describe year and doy start/end

    print('requested frequencies ', lsp['freqs'])

    for year in year_list:
        # edits made 2021Sep10 by Makan karegar
        if year != year_end:
            doy_en = 366
        else:
            doy_en = doy_end

        # edits made 2021Sep10 by Makan karegar
        if year == year_st:
            doy_list = list(range(doy, doy_en+1))
        else:
            doy_list = list(range(1, doy_en+1))

        args['year'] = year
        for doy in doy_list:
            args['doy'] = doy
            guts.gnssir_guts(**args)


def main():
    args = parse_arguments()
    gnssir(**args)


if __name__ == "__main__":
    main()


