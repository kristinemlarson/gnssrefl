# -*- coding: utf-8 -*-
"""
kristine larson
combine multiple years of teqc multipath metrics, 
write a file, and make a plot

updated to include gz versions of teqc log
should be updated to gzip them back....
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
def writeout_one_year(station, year,rcvtype):
    """
    if file exists, return values. otherwise write out a file
    """
    fileout = vegoutfile(station, year)
    if os.path.isfile(fileout):
        data = np.loadtxt(fileout,usecols=(0,1,2,3),comments='%')
        vegreceiver = np.genfromtxt(fileout, usecols=4,dtype='str')
        k=len(data)
        return k, data, vegreceiver
    else:
        vegid = open(fileout, 'w+')

    endv = g.dec31(year) + 1
    k=0
    for d in range(1,endv):
        yy,mm,dd= g.ydoy2ymd(year,d)
        mp1rms = 0
        foundit = False
        sfile, sexist = veg.sfilename(station, year, d)
        if sexist:
            mp1rms, mp1,requested_rcv,rcvinfile=veg.readoutmp(sfile,rcvtype)
            mp1rms = float(mp1rms)
            k=k+1
            vegid.write("{0:4.0f} {1:3.0f} {2:8.4f} {3:8.4f}  {4:s} {5:2.0f} {6:2.0f} \n".format(year,d, mp1rms, float(mp1), rcvinfile,mm,dd))

    vegid.close()
    data = np.loadtxt(fileout,usecols=(0,1,2,3),comments='%')
    vegreceiver = np.genfromtxt(fileout, usecols=4,dtype='str')

    return k , data, vegreceiver


def in_winter(day, winter1, winter2):
    """(td testing autodoc api generation)

    pretty silly winter screen tool

    Parameters
    ----------
    day : int
        day of year

    Returns
    -------
    bool
        True if doy is in winter, False if not considered "winter".
    """
    inwinter = False
    if (day < winter1) or (day > winter2):
        inwinter = True
    return inwinter 


def vegoutfile(station,year):
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
    vegdir = vegdir  + '/' + station
    if not os.path.isdir(vegdir):
        subprocess.call(['mkdir',vegdir])

    vegout =  vegdir + '/' + station + '_' + str(year) + '_veg.txt'
    print(vegout)

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
    parser.add_argument("-winter", default = 'F', help="Whether snow masking is done (T)", type=str)
    parser.add_argument("-winter_vals",  nargs="*", default = [], type=int, help="doy: end of winter, start of winter")
    parser.add_argument("-ylimits",  nargs="*", default = [], type=float, help="ylimits")

    args = parser.parse_args()

    print('First time thru this can be slow because it is reading/writing/gzipping a gazillion')
    print('teqc logs. But once that is done, it will be faster and you can')
    print('investigate various choices. But until you recreate the analysis stream')
    print('used by PBO H2O you will not have a true vegetation stat. Read Larson and Small 2014.')
    print('Plus, you will need to do something about the receiver changes.')

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    station = args.station
    if len(station) != 4:
        print('illegal station name - must be 4 char')
        sys.exit()

    # default is no
    winterMask = False
    if args.winter == 'T':
          winterMask = True
          if len(args.winter_vals) ==2 : 
              winter1 = args.winter_vals[0]
              winter2 = args.winter_vals[1]
          else:
              winter1 = 105; winter2 = 274; 

    ylimits = args.ylimits

    y1 = args.year1 ; y2 = args.year2 

    if args.rcvtype == None:
        # do not restrict as the default
        rcvtype = 'NONE'
    else:
        rcvtype = args.rcvtype

    # should add a header
    k=0
    dataout = np.empty(shape=[0, 4])
    rout = np.empty(shape=[0, 1])
    for year in range(y1,y2+1):
        nobs,data,rcvout = writeout_one_year(station, year,rcvtype)
        dataout = np.vstack((dataout,data))
        v = np.reshape(rcvout, (len(rcvout), 1))
        rout = np.vstack((rout, v))

        k = k + nobs

    if winterMask:
        doy = dataout[:,1]
        r1 = np.where(np.logical_and(doy > winter1 , doy < winter2))[0]
#r1 = np.where(np.logical_and(vegdumb[:,1] > 90, vegdumb[:,1] < 290))[0]
        rout = rout[r1]
        dataout = dataout[r1,:]

    receiver_types = np.unique(rout)
    # number of receivers
    N = len(receiver_types)
    print(len(dataout), ' daily observations and ', N, ' receiver types')

    if k > 0:
        plt.figure()
        for i in range(0,N):
            rname = receiver_types[i]
            r1 = dataout[np.where(rout==rname)[0]]
            outx = r1[:,0] + r1[:,1]/365.25
            jj = (r1[:,2] > 0)
            kk = (r1[:,3] > 0)
            xout = np.append(outx[jj],outx[kk])
            yout = np.append( -r1[jj,2], -r1[kk,3])
            plt.plot(xout, yout, '.',label=rname)

    # since we have a legend we don't want to plot it when it is empty

        plt.title('L1 Multipath Statistics for ' + station.upper() )
        plt.grid()
        plt.legend(loc="upper left")
        plt.ylabel('-L1 rms (m)')
        if len(ylimits) == 2:
            plt.ylim((ylimits))
        plt.show()




if __name__ == "__main__":
    main()
