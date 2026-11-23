import argparse
import datetime

import numpy as np
import os
import sys

import gnssrefl.sd_libs as sd
import gnssrefl.gps as g
import gnssrefl.spline_functions as spl

from gnssrefl.utils import str2bool

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", default=None, type=str)
    parser.add_argument("year", default=None, type=int, help="year")
    parser.add_argument("-extension", default=None, type=str, help="analysis strategy name")
    parser.add_argument("-doy1", default=None, type=int, help="optional minimum day of year")
    parser.add_argument("-doy2", default=None, type=int, help="optional maximum day of year")
    parser.add_argument("-screen", default=None, type=str, help="stats")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['screen']
    args = str2bool(args, boolean_args)

    return {key: value for key, value in args.items() if value is not None}

def imerge(station: str, year: int, extension: str=None, doy1: int=None, doy2: int=None, screen: bool=False):
    """
    Parameters
    ----------
    station : str
        4 character station name
    year : int
        full year
    extension : str
        analysis strategy name 
    doy1 : int
        day of year, starting
    doy2 : int
        day of year, ending

    """
    xdir = os.environ['REFL_CODE'] + '/Files/' + station + '/invsnr/' 
    cyear = str(year)
    if doy1 is None:
        doy1 = 1
    dec31 = g.dec31(year)
    if doy2 is None:
        doy2 = dec31

    mjd, rh,all_lines = read_invfile(station,year,extension, doy1,doy2,xdir)


def read_invfile(station,year,extension, doy1, doy2,xdirout):
    """
    pick up output of invsnr.  assume it is three days
    long but only use the middle part
    filename must be stored as {doy}.txt

    also writes the file now.
    Parameters
    ----------
    year : int
        calendar year
    extension : str
        analysis strategy name
    doy1 : int
        first day of year
    doy2 : int
        last day of year
    """
    cyear = str(year)
    if extension is None:
        xdir = os.environ['REFL_CODE'] + '/Files/' + station + '/invsnr/' + cyear + '/'
        outfile = xdirout + 'merge_' + station + '_' + cyear + '.txt'
    else:
        xdir = os.environ['REFL_CODE'] + '/Files/' + station + '/invsnr/' + cyear + '/' + extension + '/'
        outfile = xdirout + 'merge_' + station + '_' + extension + '_' + cyear + '.txt'
    allrh = []
    allmjd = []
    alll = []

    first = True
    for doy in range(doy1, doy2+1):
        cdoy = '{:03d}'.format(doy)
        ifilename = xdir + cdoy + '.txt'
        if os.path.exists(ifilename):
            xxx = np.loadtxt(ifilename, comments='%')
    # only use middle doy
            i = xxx[:,7] == doy; 
            xxx = xxx[i,:]

            mjd = xxx[:,8];
            rh = xxx[:,6]

            if first:
                alll = xxx
                first = False
            else:
                alll = np.vstack((alll, xxx)) 

            allrh = np.hstack((allrh,rh))
            allmjd = np.hstack((allmjd,mjd))


    # write to a file...in xdirout

    print('merged output goes to \n', outfile)
    head = getheader(station)
    fmt = '%4.0f %2.0f %2.0f %2.0f %2.0f %2.0f %8.3f %3.0f %13.6f %2.0f'
    # use this instead
    np.savetxt(outfile, alll, fmt=fmt, delimiter=' ', newline='\n',header=head, comments='%')


    return allmjd, allrh, alll


def getheader(station):
    """
    """
    xxx = str(datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
    line1 = ' Merged invsnr results for ' + station + ' calculated on {xxx} \n'
    line2 = ' gnssrefl, https://github.com/kristinemlarson \n'
    line3 = ' YYYY  MM  DD  HH  MM  SS   RH(m) doy  MJD  Nretrievals\n'
    line4 = '  (1) (2)  (3) (4) (5) (6)  (7)   (8)  (9)  (10) \n'


#   put all the lines together ....
    all_lines = line1 + line2 + line3 + line4 
    return all_lines



def main():
    args = parse_arguments()
    imerge(**args)


if __name__ == "__main__":
    main()


