# -*- coding: utf-8 -*-
"""
Translates rinex3 to rinex2. relies on gfzrnx
"""
import argparse
import os
import subprocess
import sys

import gnssrefl.gps as g

def main():
    """
    Converts a RINEX 3 file into a RINEX 2.11 file. Uses gfzrnx.

    Parameters
    ----------
    rinex3 : str
        filename for RINEX 3 file
    rinex2 : str, optional
        filename for RINEX 2.11 file
    dec : integer, optional
        decimation value (seconds)
    gpsonly : bool, optional
        whether to remove everything except GPS. Default is False

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("rinex3", help="rinex3 filename", type=str)
    parser.add_argument("-rinex2", help="rinex2 filename", type=str,default=None)
    parser.add_argument("-dec", help="decimation value (seconds)", type=int,default=None)
    parser.add_argument("-gpsonly", help="remove everything except GPS", type=str,default=None)

    args = parser.parse_args()
    rinex3 = args.rinex3

    gexe = g.gfz_version()

    # should use utils but don't have the time
    gpsonly = False
    if (args.gpsonly == 'True') or (args.gpsonly == 'T'):
        gpsonly = True

    if args.rinex2 is None:
        station = rinex3[0:4].lower()
        cyyyy = rinex3[12:16]
        cdoy = rinex3[16:19]
        rinex2 = station + cdoy + '0.' + cyyyy[2:4] + 'o'
        print('Output filename ', rinex2)
    else:
        rinex2 = args.rinex2

    if args.dec is None:
        dec = 1
    else:
        dec=args.dec

    if not os.path.exists(gexe):
        print('Required gfzrnx executable does not exist. Exiting.')
        sys.exit()


    if os.path.isfile(rinex3):
        print('Your RINEX input file does exist:', rinex3)
        if (rinex3[-2::] == 'gz'):
            print('Must gunzip version 3 rinex')
            subprocess.call(['gunzip', rinex3])
            rinex3 = rinex3[0:-3]
        g.new_rinex3_rinex2(rinex3,rinex2,dec,gpsonly)
    else:
        print('ERROR: your input file does not exist:', rinex3)
        sys.exit()

    if os.path.isfile(rinex2):
        print('SUCCESS: new file created', rinex2)

if __name__ == "__main__":
    main()
