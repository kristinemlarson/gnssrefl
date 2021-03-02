# -*- coding: utf-8 -*-
"""
computes mp1mp2 using teqc
kristine larson
2020sep03 - modified environment variable requirement
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


def vegplt(station, tv,winter):
    """
    input station name 
    tv: np array (year, doy, mp1, mp2) 
    and winter flag for wehther to throw out jan-apr
    and oct-dec
    """
    if (winter == 'True'):
        cc = ((tv[:,1] > 105) & (tv[:,1] < 244))
        tv = tv[cc,:]
    plt.figure()
    t = tv[:,0]+tv[:,1]/365.25
    d = tv[:,2]
    plt.plot(t,-d,'bo',marker='o',markersize=5)
    plt.ylabel('-MP1rms(m)')
    plt.title(station + ' prelim veg stat')
    plt.grid()
    plt.show()


def sfilename(station, year, doy):
    """
    """
    cdoy = '{:03d}'.format(doy)
    cyyyy = str(year)
    cyy = cyyyy[2:4]
    ddir = os.environ['REFL_CODE'] + '/' + cyyyy + '/mp/' + station + '/'

    xfile = ddir+ station + cdoy + '0.' + cyy + 'S'

    return xfile



def readoutmp(rinexfile,rcvtype):
    """
    """
    f=open(rinexfile,'r')
    lines = f.read().splitlines(True)
    lines.append('')

    mp1 = 0
    mp2 = 0
    netrs = False
    for i,line in enumerate(lines):
        if "Moving average MP1" in line:
            mp1 = line[26:34].strip()
        if "Moving average MP2" in line:
            mp2 = line[26:34].strip()
        if  rcvtype in line:
            netrs = True
#        if  "NETRS" in line:
    f.close()
#    print(mp1,mp2,netrs)
    return mp1, mp2, netrs

def mpfile_unavco(station,year,doy):
    """
    picks up teqc log from unavco if it exists
    """
    cdoy = '{:03d}'.format(doy)
    cyyyy = str(year)
    cyy = cyyyy[2:4]

    # info for unavco
    fdir = 'ftp://data-out.unavco.org/pub/rinex/qc/'
    fdir = fdir + cyyyy + '/' + cdoy + '/'
    fname = station + cdoy + '0.' + cyy + 'S'
    url = fdir + fname
    print(url)
    print(fname)

    # local directory info
    ddir = os.environ['REFL_CODE'] + '/' + cyyyy + '/mp/' + station + '/'
    if os.path.isfile(ddir + fname):
        print('file already exists')
    else:
        try:
            wget.download(url,out=fname)
        except:
            print('download failed for ', station)
        if os.path.isfile(fname):
           subprocess.call(['mv', fname, ddir])
           print('\n SUCCESS', fname)


def run_teqc(teqc,navfile,rinexfile,foutname,mpdir):
    """
    inputs: nav file, rinexfile, and output file name 
    run teqc and store in the file called foutname
    """
    fout = open(foutname,'w')
    subprocess.call([teqc, '-nav', navfile, '+qc', rinexfile], stdout=fout)
    fout.close()
    details = rinexfile[0:11] + 'S'
    print('SUCCESS: ',mpdir + '/' + details)
    subprocess.call(['mv','-f',details,mpdir] )

def check_directories(station,year):
    """
    inputs: station name and year
    """
    navfiledir = os.environ['ORBITS']  + '/' + str(year)
    if not os.path.isdir(navfiledir):
        subprocess.call(['mkdir',navfiledir] )

    navfiledir = os.environ['ORBITS']  + '/' + str(year) + '/nav'
    if not os.path.isdir(navfiledir):
        subprocess.call(['mkdir',navfiledir] )



    foutdir =  os.environ['REFL_CODE'] + '/' + str(year) 
    if not os.path.isdir(foutdir):
        subprocess.call(['mkdir',foutdir] )

    foutdir =  os.environ['REFL_CODE'] + '/' + str(year) + '/mp'
    if not os.path.isdir(foutdir):
        subprocess.call(['mkdir',foutdir] )

    foutdir =  os.environ['REFL_CODE'] + '/' + str(year) + '/mp/' + station
    if not os.path.isdir(foutdir):
        subprocess.call(['mkdir',foutdir] )

    return navfiledir, foutdir


def get_files(station,year,doy):
    """
    inputs station name, year, and day of year
    makes sure the files exist etc.
    """

    # should check that REFL_CODE and ORBITS exist

    if len(str(year)) != 4:
        print('Year must have four characters: ', year)
        sys.exit()

    if len(station) != 4:
        print('station must have four characters: ', station)
        sys.exit()


    # check that directories exist. Make them if they do not
    navfiledir, foutdir = check_directories(station,year)
    mpdir = foutdir

    cdoy = '{:03d}'.format(doy) ; cyy = '{:02d}'.format(year-2000)

    navfile = navfiledir + '/' + 'auto' + cdoy + '0.' + cyy + 'n'
    nd = navfile + '.xz'

    if not os.path.isfile(navfile):
        # it is either zipped
        if os.path.isfile(nd):
            subprocess.call(['unxz',nd] )
        # or you should go get it
        else:
            n1,n2,foundit = g.getnavfile(year, doy, 0)

    rinexfile = station + cdoy + '0.' + cyy + 'o'
    rexist = os.path.isfile(rinexfile)
    nexist = os.path.isfile(navfile)

    if not rexist:
        print('No input RINEX file',rinexfile)
        sys.exit()
    if not nexist:
        print('No nav file',navfile)
        sys.exit()

    foutname = foutdir + '/' + station + cdoy + '0.' + cyy + '.mp'
    return navfile, rinexfile,foutname,mpdir

def main():
    """
    command line interface for download_rinex
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)
    parser.add_argument("-doy_end", default = None, help="day of year - to analyze multiple days", type=int)
    parser.add_argument("-year_end", default = None,  type=int)
    parser.add_argument("-unavco", default = None, help="True picks up UNAVCO log", type=str)
    parser.add_argument("-combine", default = None, help="True combines multiple years", type=str)
    parser.add_argument("-winter", default = None, help="Removes winter points", type=str)
    parser.add_argument("-rcvtype", default = None, help="Receiver type", type=str)

    args = parser.parse_args()

#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

#   assign to normal variables
    station = args.station
    if len(station) != 4:
        print('illegal station - must be 4 char')
        sys.exit()

    year = args.year
    doy = args.doy
    if args.doy_end == None:
        doy_end = doy + 1
    else:
        doy_end = args.doy_end + 1
    teqc = g.teqc_version()
    if args.combine != None:
        tv = np.empty(shape=[0, 4])
        y1 = year; y2 = year + 1
        if args.rcvtype == None:
            rcvtype = 'NETRS'
        else:
            rcvtype = args.rcvtype
        if args.year_end != None:
            y2 = args.year_end + 1

        vegdir = os.environ['REFL_CODE'] + '/Files'
        if not os.path.isdir(vegdir):
            subprocess.call(['mkdir',vegdir])
        vegdir = vegdir + '/veg'
        if not os.path.isdir(vegdir):
            subprocess.call(['mkdir',vegdir])

        vegout =  vegdir + '/' + station + '_veg.txt'
        if 
        print('File will be written to: ', vegout)

        vegid = open(vegout,'w+')
        # should add a header

        a = []; b=[]; m1=[]; m2=[]
        for y in range(y1,y2):
            for d in range(doy,doy_end):
                sfile = sfilename(station, y, d)
                if os.path.isfile(sfile):
                    mp1, mp2,reqested_receiver=readoutmp(sfile,rcvtype)
                    if requested_receiver:
                        vegid.write("{0:4.0f} {1:3.0f} {2:s} {3:s} \n".format(y,d,mp1[0:6],mp2[0:6]))
        vegid.close()
        tv = np.loadtxt(vegout)
        vegplt(station, tv,args.winter)
        sys.exit()
    if args.unavco == None: 
        if not os.path.isfile(teqc):
            print('teqc has to be installed in EXE. Exiting. ')
            sys.exit()
        else:
           # run multiple days for a station within a given year
            for d in range(doy,doy_end):
                navfile, rinexfile,foutname,mpdir = get_files(station,year,d)
                run_teqc(teqc,navfile,rinexfile,foutname,mpdir)
    else:
        # picking up teqc logs from unavco for multiple years
        y1 = year; y2 = year + 1
        if args.year_end != None:
            y2 = args.year_end + 1
        for y in range(y1,y2):
            check_directories(station,y)
            for d in range(doy,doy_end):
                mpfile_unavco(station, y, d)

if __name__ == "__main__":
    main()



#        for y in range(y1,y2):
#            for d in range(doy,doy_end):
#                sfile = sfilename(station, y, d)
#                if os.path.isfile(sfile):
#                    mp1, mp2 = readoutmp(sfile)
#                    newl = [y, d, float(mp1[0:6]), float(mp2[0:6])]
#                    tv = np.append(tv, [newl], axis=0)
                    #print("{0:4.0f} {1:3.0f} {2:s} {3:s} ".format(y,d,mp1[0:6],mp2[0:6]))
                    #vegid.write("{0:4.0f} {1:3.0f} {2:s} {3:s} \n".format(y,d,mp1[0:6],mp2[0:6]))
                    #newl = [y, d, float(mp1[0:6]), float(mp2[0:6])]
                        #m1.append(float(mp1))
                        #m2.append(float(mp2))
                    #tv = np.append(tv, [newl], axis=0)
                    #print("{0:4.0f} {1:3.0f} {2:s} {3:s} ".format(y,d,mp1[0:6],mp2[0:6]))
