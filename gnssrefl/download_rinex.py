# -*- coding: utf-8 -*-
"""
downloads RINEX files
kristine larson
2020sep03 - modified environment variable requirement
"""
import argparse
import gnssrefl.gps as g
import sys

def version3(station,year,doy,NS,archive):
    """
    subroutine to take care of RINEX version 3
    """
    fexist = False
    if NS == 9:
        if archive == 'cddis':
            srate = 30 # rate supported by CDDIS
            fexist = g.cddis3(station, year, doy,srate)
        if archive == 'unavco':
            srate = 15
            fexist = g.unavco3(station, year, doy,srate)
        if archive == 'bkg':
            srate = 30
            fexist = g.bkg_rinex3(station, year, doy,srate)
        if archive == 'ign':
            srate = 30
            fexist = g.ign_rinex3(station, year, doy,srate)
        if archive == 'ga':
            srate = 30
            fexist = g.ga_rinex3(station, year, doy,srate)
        if fexist:
            print('RINEX 3 DOWNLOAD SUCCESSFUL from ', archive)
        else:
            print('could not find the RINEX 3 file')
    else:
        print('exiting: station names must have 9 characters')

def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("month", help="month (or day of year)", type=int)
    parser.add_argument("day", help="day (zero if you use day of year earlier)", type=int)
# optional arguments
    parser.add_argument("-rate", default='low', metavar='low',type=str, help="sample rate: low or high")
    parser.add_argument("-archive", default=None, metavar='cddis',help="archive (unavco,sopac,cddis,sonel,nz,ga,ngs,bkg)", type=str)
    parser.add_argument("-version", default=None, metavar=2,type=int, help="rinex version (2 or 3)")
    parser.add_argument("-doy_end", default=None, type=int, help="last day of year to be downloaded")

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

    archive_list = ['sopac', 'unavco','sonel','cddis','nz','ga','bkg','jeff','ngs']

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
    if (version == 2):
        if (NS != 4):
            print('exiting: RINEX 2.11 station names must have 4 characters, lowercase please')
            sys.exit()
        if args.archive == None:
            archive = 'all'
        else:
            archive = args.archive.lower()
            if archive not in archive_list:
                print('You picked an archive that does not exist')
                print('I am going to check the main ones (unavco,sopac,sonel,cddis)')
                print('For future reference: I allow these archives:')
                print(archive_list)
                archive = 'all'

    print('archive selected: ' , archive)
    # default archive wil be CDDIS for version 3
    if (version == 3):
        if (args.archive == None):
            archive = 'cddis'
            print('no archive was specified, so looking for it at CDDIS')
        else:
            archive = args.archive

    # currently only search unavco for 1 sec data
    print('data rate', rate)
    if rate == 'high':
        archive = 'unavco'

    for d in range(doy, doy_end+1):
        print('working on year, day of year:', year, d)
        if version == 3:
            version3(station,year,d,NS,archive)
        else: # RINEX VERSION 2
            g.go_get_rinex_flex(station,year,d,0,rate,archive)

if __name__ == "__main__":
    main()
