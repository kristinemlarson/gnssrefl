# -*- coding: utf-8 -*-
"""
downloads RINEX files
"""
import argparse
import gnssrefl.gps as g
import gnssrefl.karnak_libraries as k
import gnssrefl.cddis_highrate as ch
import gnssrefl.rinex2snr as r
import os
import subprocess
import sys
from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day", help="day (zero if you use day of year earlier)", type=int)
    # optional arguments
    parser.add_argument("-rate", default='low', metavar='low', type=str, help="sample rate: low or high")
    parser.add_argument("-archive", default=None, 
                        help="archive (unavco,sopac,cddis,sonel,nz,ga,ngs,bkg,nrcan)", type=str)
    parser.add_argument("-version", default=None, metavar=2, type=int, help="rinex version (2 or 3)")
    parser.add_argument("-strip", default=None, type=str,
                        help="set to True to strip to only SNR observables, gfzrnx used")
    parser.add_argument("-doy_end", default=None, type=int, help="last day of year to be downloaded")
    parser.add_argument("-stream", default=None, type=str,
                        help="set to True to get stream-defined Rinex3 filename. I know. I know. It is annoying.")
    parser.add_argument("-samplerate", default=None, type=int, help="Sample rate in seconds. For RINEX3 only.")
    parser.add_argument("-debug", default=None, type=str, help="debugging flag for printout. default is False")
    parser.add_argument("-dec", default=None, type=int, help="decimation value (seconds). Only for RINEX 3.")
    parser.add_argument("-save_crx", default=None, type=str, help="Save crx version. Only for RINEX 3.")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['strip','debug','save_crx']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_rinex(station: str, year: int, month: int, day: int, rate: str = 'low', archive: str = None,
                   version: int = 2, strip: bool = False, doy_end: 
                   int = None, stream: str = 'R', samplerate: int = 30, 
                   debug: bool = False, dec: int = 1, save_crx: bool = False):
    """
    command line interface for download_rinex.

    Parameters
    ----------
    station : str
        4 or 9 character ID of the station.

    year : int
        Year

    month : int
        month

    day : int
        day

    rate : str, optional
        sample rate. value options:

            low (default) : standard rate data

            high : high rate data

    archive : str, optional
        Select which archive to get the files from.
        Default is redirected to all, as defined below. Value options:

            unavco : now earthscope

            sonel : (global sea level observing system)

            sopac : (Scripps Orbit and Permanent Array Center)

            cddis : (NASA's Archive of Space Geodesy Data)

            ngs : (National Geodetic Survey)

            nrcan : (Natural Resources Canada)

            bkg : (German Agency for Cartography and Geodesy)

            bfg : (German Agency for water research, only Rinex 3)

            nz : (GNS, New Zealand)

            ga : (Geoscience Australia)

            bev : (Austria Federal Office of Metrology and Surveying)

            jeff : Jeff Freymueller

            special : (reflectometry Rinex 2.11 files maintained by unavco)

            all : (searches unavco, sopac, and sonel in that order)

    version : int, optional
        Version of Rinex file. Default is 2.
        Value options  2 or 3 

    strip : bool, optional
        Whether to strip only SNR observables.  Uses teqc or gfzrnx.
        Default is False.


    doy_end : int, optional
        End day of year to be downloaded. 
        Default is None. (meaning only a single day using the doy parameter)

    stream : str, optional
        Whether to get stream 'S' defined filenames.
        Default is 'R'. 

    samplerate : int, optional
        Sample rate in seconds for RINEX3 only.
        Default is 30.

    debug : boolean, optional
        provides screen output helpful for debugging
        Default is False

    dec : integer, optional
        some highrate file downloads allow decimation. Default is 1 sec, i.e. no decimation

    save_crx : boolean, option
        saves crx version for Rinex3 downloads. Otherwise they are deleted.
    """

    #print('starting a new tag')

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

    month, day, doy, cyyyy, cyy, cdoy = g.ymd2ch(year,month,day)

    # allowed archives, rinex 2.11
    archive_list = ['sopac', 'unavco', 'sonel', 'cddis', 'nz', 'ga', 'bkg', 'jeff', 'ngs', 'nrcan', 'special', 'bev', 'all']


    # removed the all archive
    archive_list_high = ['unavco', 'nrcan', 'cddis','ga','bkg']  # though it is confusing because some are rinex 2.11 and others 3

    # archive list for rinex3 lowrate files
    archive_list_rinex3 = ['unavco', 'cddis', 'ga', 'bev', 'bkg', 'ign', 'epn', 'bfg','sonel','all']

    if doy_end is None:
        doy_end = doy

    NS = len(station)

    if NS == 9:
        version = 3 # even if you don't choose version 3 .... 
    
    # this is for version 2
    # not going to allow GSI for now
    if (version == 2) and (rate == 'low'):
        if NS != 4:
            if not archive == 'jp':
                print('exiting: RINEX 2.11 station names must have 4 characters, lowercase please')
                sys.exit()

        if archive is None:
            archive = 'all'
        else:
            archive = archive.lower()
            if archive not in archive_list:
                print('You picked an archive that does not exist. To be nice, ')
                print('I am going to check the main ones (unavco,sopac,sonel) for you')
                print('For future reference: I allow these archives:')
                print(archive_list)
                archive = 'all'

    #print('archive selected: ' , archive)
    # default archive wil be CDDIS for version 3
    if version == 3:
        if NS != 9:
            print('exiting: RINEX 3+ station names must have 9 characters')
            sys.exit()
        if archive is None:
            archive = 'cddis'

        if stream not in ['R', 'S']:
            stream = 'R'

        if archive == 'unavco':
            # override the sample rate here
            samplerate = 15

        if archive not in archive_list_rinex3:
            print('You picked an archive that is not supported by my code. Exiting')
            print(archive_list_rinex3)
            sys.exit()

    if (rate == 'high') and (version == 2):
        if archive is None:
            archive = 'unavco'

        if archive not in archive_list_high:
            print('You picked an archive that is not supported by my code. Exiting')
            sys.exit()

    if (rate == 'high') and (version == 3):
        if ((archive == 'cddis') or (archive == 'bkg')) or (archive == 'ga'):
            print('Highrate RINEX 3 is supported - but it is very slow. Pick up a cup of coffee.')
        else:
            print('I do not support RINEX 3 high rate downloads from your selected archive.')
            sys.exit()

    for d in range(doy, doy_end+1):
        # RINEX Version 3
        if version == 3:
            print(station, year, d, archive, samplerate, stream)
            if rate == 'high':
                if archive == 'cddis':
                    print('seek highrate data at CDDIS')
                    ch.cddis_highrate(station, year, d, 0, stream, 1)
                if archive == 'bkg':                               
                    print('seek highrate data at BKG')
                    rnx_filename,foundit = ch.bkg_highrate(station, year, d, 0,stream,dec)
                if archive == 'ga':
                    print('seek highrate data at GA')
                    deleteOld = True
                    r2, foundit = g.ga_highrate(station,year,d,dec,deleteOld)
            else:
                if archive == 'all':
                    file_name, foundit = k.universal_all(station, year, d, samplerate, stream)
                    if not foundit:
                        file_name, foundit = k.universal_all(station, year, d, samplerate, k.swapRS(stream))
                else:
                    file_name, foundit = k.universal(station, year, d, archive, samplerate, stream,debug)
                    if not foundit:
                        file_name, foundit = k.universal(station, year, d, archive, samplerate, k.swapRS(stream),debug)
                if foundit: 
                    print('\n SUCCESS 1: ', file_name)
                    deletecrx = not save_crx
                    translated, new_file_name = r.go_from_crxgz_to_rnx(file_name,deletecrx)
                    if translated:
                        # i do not think this was doing what we thought it was doing ....
                        #subprocess.call(['rm', '-f', new_file_name.replace('rnx', 'crx')])  # delete crx file
                        print('\n SUCCESS 2: ', new_file_name)
        else:  # RINEX VERSION 2
            # using new karnak code
            rinexfile, rinexfiled = g.rinex_name(station, year, d, 0)
            if rate == 'high':
                rinexfile, foundit = k.rinex2_highrate(station, year, d, archive, strip)
            else:
                if archive == 'all':
                    foundit = False
                    print('cycle thru unavco,sopac,sonel archives')
                    for archiveinput in ['unavco', 'sopac', 'sonel']:
                        if not foundit:
                            file_name, foundit = k.universal_rinex2(station, year, d, archiveinput)
                else:
                    file_name, foundit = k.universal_rinex2(station, year, d, archive)
                if foundit:  # uncompress and make o files ...
                    rinexfile, foundit = k.make_rinex2_ofiles(file_name)  # translate

            if foundit:
                print('SUCCESS:', rinexfile, ' was found')
            else:
                print('FAILURE:', rinexfile, ' was not found')

            if os.path.isfile(rinexfile) and (strip is True):
                k.strip_rinexfile(rinexfile)


def main():
    args = parse_arguments()
    download_rinex(**args)


if __name__ == "__main__":
    main()
