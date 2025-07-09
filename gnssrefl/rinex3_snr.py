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
    Does not overwrite existing SNR files. It would be nice if someone would
    add that - plus utilize the libraries for boolean inputs.

    Parameters
    ----------
    rinex3 : str
        name of RINEX3 file
    orb : str
        optional orbit choice.  default is gbm
    snr : int
        snr file choice. default is 66

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinex3", help="rinex3 filename", type=str)
    parser.add_argument("-orb", help="orbit choice", default='gbm',type=str)
    parser.add_argument("-dec", help="decimation, in seconds", default=None,type=int)
    parser.add_argument("-snr", help="SNR file ending (default is 66)", default=None,type=int)
    parser.add_argument("-name_fail", help="RINEX 3 files masquerading as RINEX 2.11 files (boolean)", default=None,type=str)


    args = parser.parse_args()
    if args.snr is None:
        isnr = 66
    else:
        isnr = args.snr

    if args.dec is None:
        dec_rate = 0; 
    else:
        dec_rate = args.dec

    r3=args.rinex3
    station4ch = r3[0:4].lower()
    year = int(r3[12:16])
    doy = int(r3[16:19] )
    snre = g.snr_exist(station4ch,year,doy,str(isnr))

    if snre : 
        print('Requested SNR file already exists. You need to delete ')
        print('it if you want a new one. Exiting.')
        sys.exit()

    #set logs  - this is also used by rinex2snr
    #log, errorlog, exedir,genlog = r.set_rinex2snr_logs(station4ch,year,doy)

    # universal location for the log directory
    logdir, logname = g.define_logdir(station4ch,year,doy)

    logname = logdir + '/' + logname + '.rinex3'


    if (args.name_fail == 'T') or (args.name_fail == 'True'):
        # this is an attempt to help those people impacted by this activity.
        illegal_file = args.rinex3
        print('Someone is using a RINEX 2.11 filename for RINEX 3 data:', illegal_file)

        station = illegal_file[0:4].lower()
        STATION = illegal_file[0:4].upper() + '00ANT'
        cdoy = illegal_file[4:7]
        year = '20' + illegal_file[9:11]
        idoy = int(cdoy) 
        rinex3 = STATION + '_R_' + year + cdoy + '0000_01D_30S_MO.rnx'
        # move the illegal file to its proper name
        subprocess.call(['mv','-f',illegal_file,rinex3])

    else:
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
    # need a log ... 

    if os.path.isfile(rinex3):
        print('Found version 3 input file \n')
        if (rinex3[-2::] == 'gz'):
            #print('Must gunzip version 3 rinex')
            subprocess.call(['gunzip', rinex3])
            rinex3 = rinex3[0:-3]
        gpsonly = False
        if orbtype == 'nav':
            gpsonly = True
        print('opening ', logname)
        log = open(logname, 'w+')
        g.new_rinex3_rinex2(rinex3,rinex2,dec_rate,gpsonly,log)
        log.close()

    else:
        print('ERROR: your input file does not exist: {0:s} \n'.format(rinex3))
        sys.exit()

    if os.path.isfile(rinex2):
        print('Found version 2.11 RINEX file : {0:s} \n'.format(rinex2))
        idoy = int(cdoy); iyear = int(year)

        # many of these are fake values because the file has already been translated to rinex2
        archive = 'unavco' ; fortran = False; translator = 'hybrid'
        year_list = [iyear]; doy_list = [idoy]; rate = 'low';   nol = True; 
        overwrite = False; srate = 30; mk = False; skipit = 1
        strip = False; stream = 'R'  ; bkg = 'IGS' 
        gzip = True
        timeout = 0
        screenstats = True
        # removed fortran and skipit inputs ...  and got rid of the year and doy lists
        # 2024 may 28
        # this should really call conv2snr ... 
        r.run_rinex2snr(station, iyear, idoy, isnr, orbtype, rate,dec_rate,archive,nol,
                overwrite,translator,srate,mk,stream,strip,bkg,screenstats,gzip,timeout)


if __name__ == "__main__":
    main()
