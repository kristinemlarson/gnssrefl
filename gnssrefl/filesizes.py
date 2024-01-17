import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from datetime import date

import gnssrefl.gps as g

def main():
    """
    very simple code to pick up all the file sizes for SNR files in a given year
    only checks for snr66 files.  

    this is too slow - instead of using numpy array - use a list - and then change to
    numpy array at the end

    It makes a plot - not very useful now that files are nominal gzipped.

    Parameters
    ----------
    station : str
        4 character station name
    year1 : int, optional
        beginning year
    year2 : int, optional
        ending year
    doy1 : int, optional
        beginning day of year
    doy2 : int, optional
        ending day of year
    gz : bool, optional
        say T or True to search for gzipped files

    """
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE'] 

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("-year1", default=None, type=str, help="restrict to years starting with")
    parser.add_argument("-year2", default=None, type=str, help="restrict to years ending with")
    parser.add_argument("-doy1", default=None, type=str, help="restrict to after doy in year1")
    parser.add_argument("-doy2", default=None, type=str, help="restrict to before doy in year2")
    parser.add_argument("-gz", default=None, type=str, help="Boolean to search for gz files")
    args = parser.parse_args()
#   these are required
    station = args.station
    gz = args.gz

    if args.year1 == None:
        year1 = 2005
    else:
        year1=int(args.year1)

    if args.year2 == None:
        year2 = 2030
    else:
        year2=int(args.year2)

    if args.doy1== None:
        doy1=1
    else:
        doy1 = int(args.doy1)

    if args.doy2== None:
        doy2=366
    else:
        doy2 = int(args.doy2)

    tstart = year1+ doy1/365.25
    tend   = year2+ doy2/365.25

    gzadd = ''
    if (gz == 'T') or (gz == 'True'):
        gzadd = '.gz'

    k=0
# added standard deviation 2020 feb 14, changed n=6
# now require it as an input
# you can change this - trying out 80 for now
#ReqTracks = 80
# putting the results in a np.array, year, doy, RH, Nvalues, month, day
    n=3
    tv = np.empty(shape=[0, n])
    obstimes = []; 
    year_list = np.arange(year1, year2+1, 1)
    for yr in year_list:
        direc = xdir + '/' + str(yr) + '/snr/' + station + '/' 
        for doy in range(0,367):
            year, month, day, cyyyy,cdoy, YMD = g.ydoy2useful(yr,doy)

            fname = direc + station + cdoy + '0.' + cyyyy[2:4]  + '.snr66' + gzadd
            #print(fname)
            t = yr+doy/365.25
            if os.path.isfile(fname):
                a = np.loadtxt(fname,skiprows=3,comments='%')
                nr,nc=a.shape # nr is number of obs
                filler = datetime.datetime(year=yr, month=month, day=day)
                # this is for the daily average
                newl = [yr, doy, nr]
                if (t >= tstart) & (t <= tend):
                    #print(nr, year, doy)
                    tv = np.append(tv, [newl],axis=0)
                    obstimes.append(filler)
            else:
                if (t >= tstart) & (t <= tend):
                    newl = [yr, doy, 0]
                    tv = np.append(tv, [newl],axis=0)
                    filler = datetime.datetime(year=yr, month=month, day=day)
                    obstimes.append(filler)

    fs = 12
    fig,ax=plt.subplots()
    plt.plot(obstimes, tv[:,2]/1000,'b.')
    fig.autofmt_xdate()
    plt.ylabel('nobs/1000',fontsize=fs)
    plt.title('Observations for Station: ' + station,fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.xticks(fontsize=fs)
    plt.grid()
    plt.show()


if __name__ == "__main__":
    main()
