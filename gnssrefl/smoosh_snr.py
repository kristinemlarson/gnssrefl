# -*- coding: utf-8 -*-
import argparse
import numpy as np
import os
import subprocess
import sys

import gnssrefl.gps as g

def main():
    """
    decimates a SNR file

    Examples
    --------

    smoosh_snr p041 2015 175 5
        decimates an existing SNR file (year 2015 and day of year 175) to 5 seconds


    Parameters
    ----------
    station : str
        four ch station name
    year : int
        full year
    doy : int
        day of year 
    dec : int
        decimation value in seconds
    snr : int, optional
        snr file name, i.e. 99 or 10, default is 66
    doy_end : int, optional
        allows you to analyze data from doy to doy_end

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="4 ch station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)
    parser.add_argument("dec", help="decimate value, sec", type=int)
    parser.add_argument("-snr", help="snr value", type=int,default=None)
    parser.add_argument("-doy_end", help="decimation value, seconds", type=int,default=None)

    args = parser.parse_args()
    station = args.station
    year = args.year
    doy = args.doy
    dec = args.dec

    if (args.snr is None):
        snr = 66
    else:
        snr = args.snr

    csnr = str(snr)

    cyyyy, cyy, cdoy = g.ydoych(year,doy)
    myxdir = os.environ['REFL_CODE'] + '/' +  cyyyy +  '/snr/' + station + '/'
    if args.doy_end is None:
        doy_end = doy
    else:
        doy_end = args.doy_end

    for d in range(doy, doy_end+1):
        cyyyy, cyy, cdoy = g.ydoych(year,d)
        snrfile = myxdir +  station + cdoy + '0.' + cyy + '.snr' + csnr
        snrfilet = snrfile + 't'

        if not os.path.exists(snrfile):
            print('snrfile does not exist: ', snrfile)
        else:
            a=np.loadtxt(snrfile)
            i = (a[:,3] % dec) == 0 ; a=a[i,:]
            nr,nc = a.shape
            fout = open(snrfilet, 'w+')
            if (nc == 11):
                np.savetxt(fout, a, fmt="%3.0f %9.4f %9.4f %9.1f %11.6f %6.2f %6.2f %6.2f %6.2f %6.2f %6.2f")
            elif (nc == 9):
                np.savetxt(fout, a, fmt="%3.0f %9.4f %9.4f %9.1f %11.6f %6.2f %6.2f %6.2f %6.2f")
            else:
                print('Incorrect number of columns. Exiting without making new file')
                sys.exit()
            fout.close()
            print('new/decimated snrfile created')
            subprocess.call(['mv','-f',snrfilet,snrfile])

if __name__ == "__main__":
    main()
