# -*- coding: utf-8 -*-
"""
command line tool for the rinex2snr module
pretty much what it sounds like - it translates rinex files and makes SNR files
kristine larson
"""

import argparse
import datetime
import numpy as np
import os
import sys
import subprocess
import time


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
    parser.add_argument("-archive", default=None, metavar='all',help="archive (unavco,sopac,cddis,sonel,nz,ga,ngs,bkg,nrcan)", type=str)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)
    parser.add_argument("-overwrite", default=None, help="boolean", type=str)
    parser.add_argument("-translator", default=None, help="translator(fortran,hybrid,python)", type=str)

    args = parser.parse_args()
#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()
#
# rename the user inputs as variables
#
    station = args.station; NS = len(station)
    if (NS == 4) or (NS == 9):
        #print('You have submitted a nominally valid station name')
        okok = 1
    else:
        print('Illegal input - Station name must have 4 or 9 characters. Exiting.')
        sys.exit()
    year = args.year


    if len(str(year)) != 4:
        print('Year must be four characters long. Exiting.', year)
        sys.exit()


    doy= args.doy
    isnr = args.snr # defined as an integer
    #snrt = args.snrEnd # 
    #isnr = int(snrt)
    orb = args.orb
# currently allowed orbit types - shanghai removed 2020sep08
    orbit_list = ['gps','gps+glo','gnss','nav', 'igs','igr','jax','gbm','grg','wum']
    if orb not in orbit_list:
        print('You picked an orbit type I do not recognize. Here are the ones I allow')
        print(orbit_list)
        print('Exiting')
        sys.exit()
    # if you choose GPS, you get the nav message
    if orb == 'gps':
        orb = 'nav'

    # if you choose GNSS, you get the GFZ sp3 file 
    if orb == 'gnss':
        orb = 'gbm'

    # if you choose GPS+GLO, you get the JAXA sp3 file 
    if orb == 'gps+glo':
        orb = 'jax'



    if args.fortran == 'True':
        fortran = True
    else:
        fortran = False

    # check that the fortran exe exist
    if fortran:
        if (orb == 'nav'):
            snrexe = g.gpsSNR_version()
            if not os.path.isfile(snrexe):
                print('You have selected the fortran and GPS only options.')
                print('However, the fortran translator gpsSNR.e has not been properly installed.')
                print('We are changing to the hybrid translator option.')
                fortran = False
                translator = 'hybrid'
        else:
            snrexe = g.gnssSNR_version()
            if not os.path.isfile(snrexe):
                print('You have selected the fortran and GNSS options.')
                print('However, the fortran translator gnssSNR.e has not been properly installed.')
                print('We are changing to the python translator option (the hybrid is not yet working).')
                fortran = False
                translator = 'python'


# if true ony use local RINEX files, which speeds up analysis of local datasets
    nolook = args.nolook
    if nolook == 'True':
        nol = True
    else:
        nol = False

    # default is set to low.  pick high for 1sec files from unavco
    rate = args.rate

    if args.doy_end == None:
        doy2 = doy
    else:
        doy2 = args.doy_end


# currently allowed archives 
    archive_list = ['sopac', 'unavco','sonel','cddis','nz','ga','bkg','jeff','ngs','nrcan']
    if args.archive == None:
        archive = 'all'
    else:
        archive = args.archive.lower()
        if archive not in archive_list:
            print('You picked an archive that does not exist')
            print('For future reference: I allow these archives:') 
            print(archive_list)
            print('Exiting')
            sys.exit()

    year1=year
    if args.year_end == None:
        year2 = year 
    else:
        year2 = args.year_end

# decimation rate
    dec_rate = args.dec

    doy_list = list(range(doy, doy2+1))
    year_list = list(range(year1, year2+1))

    overwrite = False
    if (args.overwrite == 'True'):
        overwrite = True

    # default is to use hybrid for RINEX translator
    if args.translator == None:
        translator = 'hybrid'
    else:
        translator = args.translator
        if translator == 'hybrid':
            fortran = False # override
        if translator == 'python':
            fortran = False # override - but this is sllllllooooowwww

    rnx.run_rinex2snr(station, year_list, doy_list, isnr, orb, rate,dec_rate,archive,fortran,nol,overwrite,translator)
    print('Feedback written to subdirectory logs')


if __name__ == "__main__":
    main()
