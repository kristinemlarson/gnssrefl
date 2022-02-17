# -*- coding: utf-8 -*-
"""
downloads RINEX files
kristine larson
2020sep03 - modified environment variable requirement
2022feb15 - updated rinex3 to use karnak.py
"""
import argparse
import gnssrefl.gps as g
import gnssrefl.karnak_sub as k
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
    parser.add_argument("-strip", default=None, type=str, help="set to True to strip to only SNR observables")
    parser.add_argument("-doy_end", default=None, type=int, help="last day of year to be downloaded")
    parser.add_argument("-stream", default=None, type=str, help="set to True to get stream defined filename. I know. I know. It is annoying.")
    parser.add_argument("-samplerate", default=None, type=str, help="Sample rate in seconds for RINEX3 only.")

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


    archive_list = ['sopac', 'unavco','sonel','cddis','nz','ga','bkg','jeff','ngs','nrcan','special','bev']

    archive_list_high = ['unavco','nrcan','ga']

    archive_list_rinex3 = ['unavco','cddis','ga','bev','bkg','ign','epn','all']

    if args.version == None:
        version = 2
    else:
        version = args.version

    if args.doy_end == None:
        doy_end = doy
    else:
        doy_end = args.doy_end

    NS = len(station)

    if NS == 9:
        version = 3 # even if you don't choose version 3 .... 
    
    # this is for version 2
    if (version == 2) and (rate == 'low'):
        if (NS != 4):
            print('exiting: RINEX 2.11 station names must have 4 characters, lowercase please')
            sys.exit()
        if args.archive == None:
            archive = 'all'
        else:
            archive = args.archive.lower()
            if archive not in archive_list:
                print('You picked an archive that does not exist. To be nice, ')
                print('I am going to check the main ones (unavco,sopac,sonel,cddis) for you')
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

    for d in range(doy, doy_end+1):
        #print('working on year, day of year:', year, d)
        if version == 3:
            print(station,year,d,archive,srate,stream)
            # version3(station,year,d,NS,archive,stream) old version
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
            g.go_get_rinex_flex(station,year,d,0,rate,archive)
            rinexfile,rinexfiled = g.rinex_name(station, year, d, 0)
            print(rinexfile)
            if os.path.isfile(rinexfile):
                if args.strip == 'True':
                    print('use teqc to strip the RINEX file')
                    teqcv = g.teqc_version()
                    if os.path.isfile(teqcv):
                        foutname = 'tmp.' + rinexfile
                        fout = open(foutname,'w')
                        subprocess.call([teqcv, '-O.obs','S1+S2+S5+S6+S7+S8', rinexfile],stdout=fout)
                        fout.close()
                        subprocess.call(['rm','-f',rinexfile])
                        subprocess.call(['mv','-f',foutname, rinexfile])
                        print('\n SUCCESS: ', rinexfile)
                else:
                    print('\n SUCCESS: ', rinexfile)
            else:
                print(rinexfile, ' not found')

if __name__ == "__main__":
    main()
