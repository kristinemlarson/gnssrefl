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

    Creates SNR file from RINEX 3 file that is stored locally in makan type folders
    It may allow crx endings -  I am not sure. It only allows GFZ ultra orbit files
    That could be changed.

    This code could be improved - it would be great if the people that are using
    it would make those changes.

    Parameters
    ----------
    rinex3 : str
        name of RINEX 3 file

    dec : str, optional
        optional decimation value

    
    """ 
    parser = argparse.ArgumentParser() 
    parser.add_argument("rinex3", help="rinex3 filename - has to live in Makan directories", type=str)
    parser.add_argument("-dec", help="decimation value, seconds", default=None,type=str)

    args = parser.parse_args()
    rinex3 = args.rinex3

    station = rinex3[0:4].lower()
    STATION = rinex3[0:4]

    year = rinex3[12:16]
    iyear = int(year)
    cdoy = rinex3[16:19] 
    idoy = int(cdoy)
    iyear,month,day=g.ydoy2ymd(iyear, idoy)

    # where rinex data are
    xdir = os.environ['REFL_CODE'] + '/rinex/' + STATION + '/' + year + '/'
    # where snr data will go
    snrdir =  os.environ['REFL_CODE'] + '/' + year + '/snr/' + STATION + '/'

    # default keeps everything
    if args.dec is None:
        dec_rate = 1
    else:
        dec_rate = int(args.dec)

    # all lowercase in my world
    rinex2 = station + cdoy + '0.' + year[2:4] + 'o'

    # we only support GFZ ultra for now
    orbtype = 'ultra'
    hour = 0 # for now only download hour 0 for ultra products
    filename, fdir, foundit = g.ultra_gfz_orbits(iyear, month, day, hour)
    orbfile = fdir + '/' + filename
    if not os.path.exists(orbfile):
        print('Required orbitfile does not exist. Exiting.')
        sys.exit()


    gexe = g.gfz_version()

    if not os.path.exists(gexe):
        print('Required gfzrnx executable does not exist. Exiting.')
        sys.exit()


    # first step will be to translate to rinex2

    full_rinex3 = xdir + rinex3
    if os.path.isfile(full_rinex3):
        print('found version 3 rinex in the makan directories')
        # open log file(s)
        log, gen_log = r.set_rinex2snr_logs(station,iyear,idoy)
        dec=1; gpsonly=False
        g.new_rinex3_rinex2(full_rinex3,rinex2,dec,gpsonly,log)
        log.close()
    else:
        print('ERROR: your input file does not exist:', rinex3)
        sys.exit()

    g.make_snrdir(year,STATION) # make sure output directory exists
    snrname = snrdir + rinex3[0:-3] + 'snr66'
    option = 66

    log, gen_log2 = r.set_rinex2snr_logs(station,iyear,idoy)
    r.rnx2snr(rinex2, orbfile, snrname, option, iyear, month, day, dec_rate, log)
    log.close()

    # clean up - remove the rinex2 file
    print('SNR file written to: ', snrname)
    subprocess.call(['rm','-f',rinex2])

if __name__ == "__main__":
    main()
