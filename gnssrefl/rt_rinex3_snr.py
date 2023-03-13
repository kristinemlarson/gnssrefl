# -*- coding: utf-8 -*-
"""
"""
import argparse
import os
import subprocess
import sys

import gnssrefl.gps as g
import gnssrefl.rinex2snr as r
import gnssrefl.gnsssnrbigger as gnsssnrbigger


def main():
    """

    Creates SNR file from RINEX 3 file that is stored locally in makan folders
    It may allow crx - I am not sure.
    Only allows GFZ ultra orbit files

    Parameters
    ----------
    rinex3 : str
        name of filename

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinex3", help="rinex3 filename", type=str)
    parser.add_argument("-dec", help="decimation", default=None,type=str)


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
    print(xdir)


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
        g.new_rinex3_rinex2(full_rinex3,rinex2)
    else:
        print('ERROR: your input file does not exist:', rinex3)
        sys.exit()

    g.make_snrdir(year,STATION) # make sure output directory exists
    snrname = snrdir + rinex3[0:-3] + 'snr66'

    in1 = g.binary(rinex2)
    in2 = g.binary(snrname) 
    in3 = g.binary(orbfile)

    if (len(snrname) > 132) or (len(orbfile) > 132):
        print('The orbit or SNR file name is too long.')
        print('Make your environment variable names shorter.')
        sys.exit()
    option = 66
    in4 = g.binary(str(option))
    if (dec_rate > 0):
        decr = str(dec_rate)
    else:
        decr = '0'
    in5 = g.binary(decr) # decimation can be used in hybrid option
    message = 'None '
    errorlog = 'logs/' + station + '_hybrid_error.txt'
    in6 = g.binary(errorlog)
    gnsssnrbigger.foo(in1,in2,in3,in4,in5,in6)
    # clean up - remove the rinex2 file
    print('Output file written to: ', snrname)
    subprocess.call(['rm','-f',rinex2])

if __name__ == "__main__":
    main()
