# -*- coding: utf-8 -*-
"""
command line tool for the rinex2snr module
pretty much what it sounds like - it translates rinex files and makes SNR files
kristine larson
2021aug01 added mk option for uppercase file names

compile the fortran first
f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f

2022feb15 added karnak_sub for rinex3
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
    parser.add_argument("-orb", default='nav', type=str, help="orbit type, gps, gps+glo, gnss, rapid or you can specify nav,igs,igr,jax,gbm,grg,wum,gfr,ultra")
    parser.add_argument("-rate", default='low', metavar='low',type=str, help="sample rate: low or high")
    parser.add_argument("-dec", default=0, type=int, help="decimate (seconds)")
    parser.add_argument("-nolook", default='False', metavar='False', type=str, help="True means only use RINEX files on local machine")
    parser.add_argument("-fortran", default='False', metavar='False',type=str, help="True means use Fortran RINEX translators ")
    parser.add_argument("-archive", default=None, metavar='all',help="specify an archive or all. See documentation.", type=str)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)
    parser.add_argument("-overwrite", default=None, help="boolean", type=str)
    parser.add_argument("-translator", default=None, help="translator(fortran,hybrid,python)", type=str)
    parser.add_argument("-samplerate", default=None, help="sample rate in sec (RINEX 3 only)", type=int)
    parser.add_argument("-stream", default=None, help="Set to R or S (RINEX 3 only)", type=str)
    parser.add_argument("-mk", default=None, help="use True for uppercase station names ", type=str)
    parser.add_argument("-weekly", default=None, help="use True for weekly data translation", type=str)

    args = parser.parse_args()
#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()
#
# rename the user inputs as variables
#
    station = args.station; NS = len(station)
    if (NS == 4) or (NS == 6) or (NS == 9):
        okok = 1
    else:
        print('Illegal input - Station name must have 4 (RINEX 2), 6 (GSI), or 9 (RINEX 3) characters. Exiting.')
        sys.exit()

    year = args.year
    year_st = year

    if len(str(year)) != 4:
        print('Year must be four characters long. Exiting.', year)
        sys.exit()

    doy= args.doy
    doy_st = doy
    isnr = args.snr # defined as an integer
    #snrt = args.snrEnd # 
    #isnr = int(snrt)
    orb = args.orb
# currently allowed orbit types - shanghai removed 2020sep08
# added GFZ rapid, aka gfr 2021May19 but it does not work anymore.  point it to gbm
# 
# added ESA, thank you to Makan
    orbit_list = ['gps','gps+glo','gnss','nav', 'igs','igr','jax','gbm','grg','wum','gfr','esa','ultra','rapid','gnss2']
    if orb not in orbit_list:
        print('You picked an orbit type I do not recognize. Here are the ones I allow')
        print(orbit_list)
        print('Exiting')
        sys.exit()
    # if you choose GPS, you get the nav message
    if orb == 'gps':
        orb = 'nav'
    # if you choose ultra , you get the GFZ rapid 
    if orb == 'rapid':
        orb = 'gfr'

    # if you choose GNSS, you get the GFZ sp3 file  (precise)
    if orb == 'gnss':
        orb = 'gbm'

    if orb == 'gnss2':
        # this code wants year month day....
        year,month,day=g.ydoy2ymd(year, doy)
        filename,fdir,foundit = g.avoid_cddis(year,month,day)
        orb = 'gbm'
        if not foundit:
            print('You picked the backup multi-GNSS option.')
            print('I tried to get the file from IGN and failed. Exiting')
            sys.exit()
        else:
            print('found GFZ orbits at IGN - warning, only a single file at a time')



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

    # default is set to low.  pick high for 1sec files 
    rate = args.rate
    print(rate)

    if args.doy_end == None:
        doy2 = doy
    else:
        doy2 = args.doy_end


    archive = args.archive
    if archive == None:
        archive = 'all'

    archive_list_rinex3 = ['unavco','cddis','bev','bkg','ga','epn','all']
    archive_list = ['sopac', 'unavco','sonel','cddis','nz','ga','bkg','jeff','ngs','nrcan','special','bev','jp','all']

    highrate_list = ['unavco','nrcan','all']


    if (NS == 9):
        # rinex3
        if archive not in  archive_list_rinex3:
            print('You chose an archive not supported by my code.')
            print(archive_list_rinex3)
            sys.exit()
    else:
        # rinex2
        if (rate == 'high'):
            if archive not in highrate_list:
                print('You chose highrate and ', archive, ' but  I only allow unavco and nrcan. Exiting.')
                print('Please help code up access to additional archives')
                sys.exit()
        else:
            if archive not in archive_list:
                print('You picked an archive that is not allowed. Exiting')
                print(archive_list)
                sys.exit()
    year1=year
    if args.year_end == None:
        year2 = year 
    else:
        year2 = args.year_end

# decimation rate
    dec_rate = args.dec

# the weekly option
    skipit = 1
    if args.weekly == 'True':
        print('you have invoked the weekly option')
        skipit = 7

    # change skipit to be sent to rinex2snr.py
    #doy_list = list(range(doy, doy2+1))
    #doy_list = list(range(doy, doy2+1,skipit))
    # this makes the correct lists in the function
    doy_list = [doy_st, doy2]
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

    # this is for RINEX 3 only - default will be 30
    if args.samplerate == None:
        srate = 30
    else:
        srate = int(args.samplerate)

    # the Makan option
    mk = False
    if args.mk == 'True':
        print('you have invoked the Makan option')
        mk = True

    if args.stream == None:
        stream = 'R'
    else:
        stream = args.stream
    if stream not in ['R','S']:
        stream = 'R'

    rnx.run_rinex2snr(station, year_list, doy_list, isnr, orb, rate,dec_rate,
            archive,fortran,nol,overwrite,translator,srate,mk,skipit,stream=stream)
    print('Feedback written to subdirectory logs')


if __name__ == "__main__":
    main()




#    if translator == 'hybrid':
#        snrexe = g.gnssSNR_version()
#        if (orb == 'jax') or (orb == 'gbm') or (orb=='igr'):
#            print('The hybrid option does not currently work on multi-GNSS files')
#            print('I am currently testing this option')
#           if not os.path.isfile(snrexe):
#                print('setting to python in the interim')
                #translator = 'python'
    #        else:
    #            print('setting to fortran in the interim')
    #            translator = 'fortran'

