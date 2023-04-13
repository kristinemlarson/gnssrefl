# -*- coding: utf-8 -*-
"""
"""
import argparse
import os
import subprocess 
import sys

import gnssrefl.gps as g
import gnssrefl.rinex2snr as r

def main():
    """

    Creates SNR file from RINEX 3 file that is stored locally
    Requires the gfzrnx executable to be available.

    Parameters
    ----------
    rinex3 : str
        name of filename

    orb : str
        optional orbit choice.  default is gbm
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinex3", help="rinex3 filename", type=str)
    parser.add_argument("-orb", help="orbit choice", default='gbm',type=str)
    parser.add_argument("-snr", help="SNR file ending (default is 66)", default=None,type=str)


    args = parser.parse_args()
    if args.snr is None:
        snr = '66'
    else:
        snr = int(args.snr)

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
        print('Found version 3 input file ')
        if (rinex3[-2::] == 'gz'):
            print('Must gunzip version 3 rinex')
            subprocess.call(['gunzip', rinex3])
            rinex3 = rinex3[0:-3]
        g.new_rinex3_rinex2(rinex3,rinex2)
    else:
        print('ERROR: your input file does not exist:', rinex3)
        sys.exit()
    if os.path.isfile(rinex2):
        print('found version 2 rinex')
        isnr = 66;  rate = 30; idoy = int(cdoy); iyear = int(year)
        rate = '30'; dec_rate = 0; archive = 'unavco' ; fortran = False; translator = 'hybrid'
        year_list = [iyear]; doy_list = [idoy]; rate = 'low';   nol = True; overwrite = False; srate = 30; mk = False; skipit = 1
        strip = False; stream = 'S'  ; bkg = 'IGS' # many of these are fake values because the file has already been translated to rinex2
        r.run_rinex2snr(station, year_list, doy_list, isnr, orbtype, rate,dec_rate,archive,fortran,nol,
                overwrite,translator,srate,mk,skipit,stream,strip,bkg)


if __name__ == "__main__":
    main()
