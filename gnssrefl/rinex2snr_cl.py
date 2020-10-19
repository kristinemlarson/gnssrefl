# -*- coding: utf-8 -*-
"""
command line tool for the rinex2snr module
pretty much what it sounds like - it translates rinex files and makes SNR files
kristine larson
"""

import argparse
import datetime
import os
import sys
import subprocess

import numpy as np

import gnssrefl.gps as g
import gnssrefl.rinex2snr as rnx
 
def main():
#
    # 
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="start day of year", type=int)
# optional arguments
    parser.add_argument("-snr", default=66, help="snr file ending", type=str)
    parser.add_argument("-orb", default='nav', type=str, help="orbit type, gps, gps+glo, gnss or you can specify nav,igs,igr,jax,gbm,grg,wum")
    parser.add_argument("-rate", default='low', metavar='low',type=str, help="sample rate: low or high, only unavco")
    parser.add_argument("-dec", default=0, type=int, help="decimate (seconds)")
    parser.add_argument("-nolook", default='False', metavar='False', type=str, help="True means only use RINEX files on local machine")
    parser.add_argument("-fortran", default='True', metavar='True',type=str, help="True means use Fortran RINEX translators ")
    parser.add_argument("-archive", default=None, metavar='all',help="archive (unavco,sopac,cddis,sonel,nz,ga,ngs,bkg)", type=str)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)

    args = parser.parse_args()
#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()
#
# rename the user inputs as variables
#
    station = args.station; NS = len(station)
    if (NS == 4) or (NS == 9):
        print('You have submitted a nominally valid station name')
    else:
        print('Illegal input - Station name must have 4 or 9 characters')
        sys.exit()
    year = args.year


    if len(str(year)) != 4:
        print('Year must be four characters long: ', year)
        sys.exit()

    doy1= args.doy
    isnr = args.snr # defined as an integer
    #snrt = args.snrEnd # 
    #isnr = int(snrt)
    orbtype = args.orb
# currently allowed orbit types - shanghai removed 2020sep08
    orbit_list = ['gps','gps+glo','gnss','nav', 'igs','igr','jax','gbm','grg','wum']
    if orbtype not in orbit_list:
        print('You picked an orbit type I do not recognize. Here are the ones I allow')
        print(orbit_list)
        sys.exit()
    # if you choose GPS, you get the nav message
    if orbtype == 'gps':
        orbtype = 'nav'

    # if you choose GNSS, you get the GFZ sp3 file 
    if orbtype == 'gnss':
        orbtype = 'gbm'

    # if you choose GPS+GLO, you get the JAXA sp3 file 
    if orbtype == 'gps+glo':
        orbtype = 'jax'

    print('Orbit type:', orbtype)
    if args.fortran == 'True':
        fortran = True
    else:
        fortran = False

# if true ony use local RINEX files, which speeds up analysis of local datasets
    nolook = args.nolook
    if nolook == 'True':
        nol = True
    else:
        nol = False

    # default is set to low.  pick high for 1sec files from unavco
    rate = args.rate

    if args.doy_end == None:
        doy2 = doy1
    else:
        doy2 = args.doy_end


# currently allowed archives 
    archive_list = ['sopac', 'unavco','sonel','cddis','nz','ga','bkg','jeff','ngs']
    if args.archive == None:
        archive = 'all'
    else:
        archive = args.archive.lower()
        if archive not in archive_list:
            print('You picked an archive that does not exist')
            print('I am going to check the main ones (unavco,sopac,sonel,cddis)')
            print('For future reference: I allow these archives:') 
            print(archive_list)

    year1=year
    if args.year_end == None:
        year2 = year 
    else:
        year2 = args.year_end

# decimation rate
    dec_rate = args.dec

    doy_list = list(range(doy1, doy2+1))
    year_list = list(range(year1, year2+1))

# this sets up the loops
    rnx.run_rinex2snr(station, year_list, doy_list, isnr, orbtype, rate,dec_rate,archive,fortran,nol)


if __name__ == "__main__":
    main()
