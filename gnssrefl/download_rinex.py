# -*- coding: utf-8 -*-
"""
downloads RINEX files
kristine larson
2020sep03 - modified environment variable requirement
2022feb15 - updated rinex3 to use karnak.py
"""
import argparse
import gnssrefl.gps as g
import gnssrefl.karnak_libraries as k
import gnssrefl.cddis_highrate as ch
import gnssrefl.rinex2snr as r
import os
import subprocess
import sys

def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day",   help="day (zero if you use day of year earlier)", type=int)
# optional arguments
    parser.add_argument("-rate", default='low', metavar='low',type=str, help="sample rate: low or high")
    parser.add_argument("-archive", default=None, metavar='cddis',help="archive (unavco,sopac,cddis,sonel,nz,ga,ngs,bkg,nrcan)", type=str)
    parser.add_argument("-version", default=None, metavar=2,type=int, help="rinex version (2 or 3)")
    parser.add_argument("-strip", default=None, type=str, help="set to True to strip to only SNR observables, teqc used")
    parser.add_argument("-doy_end", default=None, type=int, help="last day of year to be downloaded")
    parser.add_argument("-stream", default=None, type=str, help="set to True to get stream defined filename. I know. I know. It is annoying.")
    parser.add_argument("-samplerate", default=None, type=str, help="Sample rate in seconds for RINEX3 only.")
    parser.add_argument("-strip_snr", default=None, type=str, help="Uses gfzrnx to strip out non-SNR data/default is False")

    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

#   assign to normal variables
    station = args.station
    year = args.year
    month = args.month
    day = args.day

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

    if (day == 0):
        # then you are using day of year as input
        doy = month
        year,month,day=g.ydoy2ymd(year, doy) 
    else:
        doy,cdoy,cyyyy,cyy = g.ymd2doy(year,month,day)

    # default is low
    rate = args.rate

    # set archive variable
    archive = args.archive


    archive_list = ['sopac', 'unavco','sonel','cddis','nz','ga','bkg','jeff','ngs','nrcan','special','bev','all']

    archive_list_high = ['unavco','nrcan','ga']
    # removed all
    archive_list_high = ['unavco','nrcan','cddis'] # removed GA, added Cddis for v2

    archive_list_rinex3 = ['unavco','cddis','ga','bev','bkg','ign','epn','all']

    if args.version == None:
        version = 2
    else:
        version = args.version

    # this is only for high-rate rinex2 for now
    if args.strip_snr == None:
        strip_snr = False
    else:
        if args.strip_snr == 'True':
            strip_snr = True
        else:
            strip_snr = False

    if args.doy_end == None:
        doy_end = doy
    else:
        doy_end = args.doy_end

    NS = len(station)

    if NS == 9:
        version = 3 # even if you don't choose version 3 .... 
    
    # this is for version 2
    # not going to allow GSI for now
    if (version == 2) and (rate == 'low'):
        if (NS != 4):
            if not (args.archive == 'jp'):
                print('exiting: RINEX 2.11 station names must have 4 characters, lowercase please')
                sys.exit()
        if args.archive == None:
            archive = 'all'
        else:
            archive = args.archive.lower()
            if archive not in archive_list:
                print('You picked an archive that does not exist. To be nice, ')
                print('I am going to check the main ones (unavco,sopac,sonel) for you')
                print('For future reference: I allow these archives:')
                print(archive_list)
                archive = 'all'

    #print('archive selected: ' , archive)
    # default archive wil be CDDIS for version 3
    if (version == 3):
        if (NS != 9):
            print('exiting: RINEX 3+ station names must have 9 characters')
            sys.exit()
        if (args.archive == None):
            archive = 'cddis'
        else:
            archive = args.archive

        if args.samplerate== None:
            srate = 30
        else:
            srate = int(args.samplerate)

        if args.stream == None:
            stream = 'R'
        else:
            stream = args.stream
            # make sure people don't use goofy inputs
            if stream not in ['R','S']:
                stream = 'R'
        if archive == 'unavco':
            # override the sample rate here
            srate = 15
        if archive not in archive_list_rinex3:
            print('You picked an archive that is not supported by my code. Exiting')
            print(archive_list_rinex3)
            sys.exit()

    if (rate == 'high') and (version == 2):
        if args.archive == None:
            archive = 'unavco'
        else:
            archive = args.archive

        if archive not in archive_list_high:
            print('You picked an archive that is not supported by my code. Exiting')
            sys.exit()

    if (rate == 'high') and (version == 3):
        if (archive == 'cddis'):
            print('Highrate RINEX 3 from CDDIS is supported - but it is very slow')
        else:
            print('I only support high-rate RINEX 3 files from CDDIS')
            print('Not a fan of the 96 file thing ...')
            sys.exit()

    for d in range(doy, doy_end+1):
        # RINEX Version 3
        if version == 3:
            print(station,year,d,archive,srate,stream)
            if rate == 'high':
                print('seek highrate data at CDDIS')
                ch.cddis_highrate(station, year, doy, 0,stream,1)
            else:
                if archive == 'all':
                    file_name,foundit = k.universal_all(station, year, doy, srate,stream)
                    if (not foundit):
                        file_name,foundit = k.universal_all(station, year, doy, srate,k.swapRS(stream))
                else:
                    file_name,foundit = k.universal(station, year, doy, archive,srate,stream)
                    if (not foundit):
                        file_name,foundit = k.universal(station, year, doy, archive,srate,k.swapRS(stream))
                if foundit: 
                    print('\n SUCCESS 1: ', file_name)
                    translated, new_file_name = r.go_from_crxgz_to_rnx(file_name)
                    if translated:
                        subprocess.call(['rm','-f',new_file_name.replace('rnx','crx')]) # delete crx file
                        print('\n SUCCESS 2: ', new_file_name)
        else: # RINEX VERSION 2
            # using new karnak code
            rinexfile,rinexfiled = g.rinex_name(station, year, d, 0)
            if rate == 'high':
                rinexfile, foundit = k.rinex2_highrate(station, year, doy,archive,strip_snr)
            else:
                if archive == 'all':
                    foundit = False
                    print('cycle thru unavco,sopac,sonel archives')
                    for archiveinput in ['unavco','sopac','sonel']:
                        if (not foundit):
                            file_name,foundit = k.universal_rinex2(station, year, doy, archiveinput)
                else:
                    file_name,foundit = k.universal_rinex2(station, year, doy, archive)
                if foundit: # uncompress and make o files ... 
                    rinexfile, foundit = k.make_rinex2_ofiles(file_name) # translate

            if foundit: 
                 print('SUCCESS:', rinexfile, ' was found')
            else:
                 print('FAILURE:', rinexfile, ' was not found')
            #g.go_get_rinex_flex(station,year,d,0,rate,archive)
            # a bit redundant ... but life is short 
            if os.path.isfile(rinexfile) and (args.strip == 'True'):
                k.strip_rinexfile(rinexfile)

if __name__ == "__main__":
    main()
