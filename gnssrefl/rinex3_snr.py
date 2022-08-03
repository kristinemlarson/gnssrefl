# -*- coding: utf-8 -*-
"""
Translates rinex3 to rinex2 to snr - 
so saves some time .... 
this is only for people that HAVE the files on disk
author: kristine larson
Updated: November 14, 2021
This only works on a single file (no doy_end)
It also uses my convention for naming (lowercase) and it does not 
store the Rinex2 files

I think this has more or less been superceded by rinex3_rinex2
thought I guess it does have the extra step of making a SNR file ... 
but that should not matter since rinex2snr allows Rinex 3 files
"""
import argparse
import os
import gnssrefl.gps as g
import gnssrefl.rinex2snr as r
import sys

def main():

    parser = argparse.ArgumentParser()
    parser.add_argument("rinex3", help="rinex3 filename", type=str)
    parser.add_argument("-orb", help="orbit choice", default='gbm',type=str)


    args = parser.parse_args()
    rinex3 = args.rinex3
    station = rinex3[0:4].lower()
    STATION = rinex3[0:4]
    year = rinex3[12:16]
    cdoy = rinex3[16:19] 
    idoy = int(cdoy)

    #print(station, STATION, year, cdoy)
    # all lowercase in my world
    rinex2 = station + cdoy + '0.' + year[2:4] + 'o'
    orbtype = args.orb 
    if orbtype == 'gps':
        orbtype = 'nav'
    elif orbtype == 'gnss':
        orbtype = 'gbm'
    elif orbtype == 'gps+glo':
        orbtype = 'gbm'

    gexe = g.gfz_version()

    if not os.path.exists(gexe):
        print('Required gfzrnx executable does not exist. Exiting.')
        sys.exit()


    # first step will be to translate to rinex2

    if os.path.isfile(rinex3):
        #print('found version 3 rinex')
        g.new_rinex3_rinex2(rinex3,rinex2)
    else:
        print('ERROR: your input file does not exist:', rinex3)
        sys.exit()
    if os.path.isfile(rinex2):
        #print('found version 2 rinex')
        isnr = 66;  rate = 30; idoy = int(cdoy); iyear = int(year)
        rate = '30'; dec_rate = 0; archive = 'unavco' ; fortran = False; translator = 'hybrid'
        year_list = [iyear]; doy_list = [idoy]; rate = 'low';   nol = True; overwrite = False; srate = 30; mk = False; skipit = 1
        r.run_rinex2snr(station, year_list, doy_list, isnr, orbtype, rate,dec_rate,archive,fortran,nol,overwrite,translator,srate,mk,skipit)

if __name__ == "__main__":
    main()
