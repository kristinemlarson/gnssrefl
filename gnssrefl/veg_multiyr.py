# -*- coding: utf-8 -*-
"""
kristine larson
combine multiple years of teqc multipath metrics, 
write a file, and make a plot
"""
import argparse
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys
import time
import wget

import gnssrefl.gps as g
import gnssrefl.computemp1mp2 as veg
def in_winter(d):
    """(td testing autodoc api generation)

    pretty silly winter screen tool

    Parameters
    ----------
    d : int
        day of year

    Returns
    -------
    bool
        True if doy is in winter, False if not considered "winter".
    """
    inwinter = False
    if (d < 105) or (d > 274):
        inwinter = True
    return inwinter 

def newvegplot(vegout,station):
    """
    send the file name and try to make a plot segreating for 
    changes in teqc metric and receiver type
    """
    # get the numerical data
    tv = np.loadtxt(vegout,usecols=(0,1,2,3))
    # read the receiver type separately ... because it is a string
    r = np.genfromtxt(vegout,usecols=(4),dtype='str')
    rcvs = np.unique(r)
# number of receivers
    N = len(rcvs)
    colors = 'brybrybry'
    plt.figure()
    k=0
    for i in range(0,N):
        receiver = rcvs[i]
    # find the indices with the correct receiver
        ii = (receiver == r)
        outx = tv[ii,0] + tv[ii,1]/365.25
    # now segreate by those that are not zero ... because teqc changed
    # from using MP1 to MP12
        outcol2 = tv[ii,2]
        outcol3 = tv[ii,3]
        ii = (outcol2 > 0)
        jj = (outcol3 > 0)
    # since we have a legend we don't want to plot it when it is empty
        xout = np.append(outx[ii],outx[jj])
        yout = np.append(-outcol2[ii],-outcol3[jj])
        plt.plot(xout,yout,'.', label=receiver)
        #if (len(outx[ii]) > 0):
        #    plt.plot(outx[ii], -outcol2[ii],dd,label=receiver)
        #if (len(outx[jj]) > 0):
        #    plt.plot(outx[jj], -outcol3[jj],dd,label=receiver)
        k = k + 1
    plt.legend(loc="lower left")
    plt.ylabel('-L1 rms (m)')
    plt.grid()
    plt.title('L1 Multipath Statistics for ' + station.upper() )
    plt.show()

def vegoutfile(station):
    """
    make sure directories exist for prelim veg output file
    returns name of the otuput file
    """
    vegdir = os.environ['REFL_CODE'] + '/Files'
    if not os.path.isdir(vegdir):
        subprocess.call(['mkdir',vegdir])
    vegdir = vegdir + '/veg'
    if not os.path.isdir(vegdir):
        subprocess.call(['mkdir',vegdir])
    vegout =  vegdir + '/' + station + '_veg.txt'
    print('File will be written to: ', vegout)

    return vegout 


def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year1", help="beginning year", type=int)
    parser.add_argument("year2", help="end year", type=int)
    parser.add_argument("-rcvtype", default = None, help="Receiver type", type=str)
    parser.add_argument("-winter", default = None, help="Removes winter points", type=str)

    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

#   assign to normal variables
    station = args.station
    if len(station) != 4:
        print('illegal station - must be 4 char')
        sys.exit()

    vegout = vegoutfile(station)

    y1 = args.year1
    y2 = args.year2 + 1

    if args.rcvtype == None:
        # do not restrict as the default
        rcvtype = 'NONE'
    else:
        rcvtype = args.rcvtype

    # should add a header
    vegid = open(vegout,'w+')

    if args.winter == None:
        winterMask = False
    else:
        winterMask = True
    k = 0
    if winterMask:
        for y in range(y1,y2):
            for d in range(1,367):
                if not in_winter(d):
                    sfile = veg.sfilename(station, y, d)
                    if os.path.isfile(sfile):
                        mp12, mp1,requested_rcv,rcvinfile=veg.readoutmp(sfile,rcvtype)
                        if requested_rcv:
                            k+=1
                            yy,mm,dd= g.ydoy2ymd(y,d)
                            vegid.write("{0:4.0f} {1:3.0f} {2:s} {3:s}  {4:s} {5:2.0f} {6:2.0f} \n".format(y,d,mp12[0:6],mp1[0:6], rcvinfile,mm,dd))
    else:
        for y in range(y1,y2):
            for d in range(1,367):
                sfile = veg.sfilename(station, y, d)
                if os.path.isfile(sfile):
                    mp12, mp1,requested_rcv,rcvinfile=veg.readoutmp(sfile,rcvtype)
                    if requested_rcv:
                        k+=1
                        yy,mm,dd= g.ydoy2ymd(y,d)
                        vegid.write("{0:4.0f} {1:3.0f} {2:s} {3:s}  {4:s} {5:2.0f} {6:2.0f} \n".format(y,d,mp12[0:6],mp1[0:6], rcvinfile,mm,dd))
    vegid.close()
    print(k, ' daily observations')
    if k > 0:
        newvegplot(vegout,station)
if __name__ == "__main__":
    main()
