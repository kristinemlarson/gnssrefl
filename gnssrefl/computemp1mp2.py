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
    and winter flag for wehther to throw out ~jan-apr
    and ~oct-dec
    """
    if (winter == 'True'):
        cc = ((tv[:,1] > 105) & (tv[:,1] < 274))
        tv = tv[cc,:]
    plt.figure()
    t = tv[:,0]+tv[:,1]/365.25
    d = tv[:,2]
    plt.plot(t,-d,'b.')
    plt.ylabel('-MP1rms(m)')
    plt.title(station + ' preliminary Vegetation statistic')
    plt.grid()
    plt.show()


def sfilename(station, year, doy):
    """
    input station name, year and day of year
    and it returns the full filename on your local system
    """
    cdoy = '{:03d}'.format(doy)
    cyyyy = str(year)
    cyy = cyyyy[2:4]
    ddir = os.environ['REFL_CODE'] + '/' + cyyyy + '/mp/' + station + '/'

    xfile = ddir+ station + cdoy + '0.' + cyy + 'S'

    return xfile



def ReadRecAnt(teqclog):
    """
    input is the name of a teqc log 
    prints out Receiver and Antenna name
    """
    mp1 = 0
    mp2 = 0
    foundRec = False
    rinexfile = teqclog
    if os.path.isfile(teqclog):
        f=open(rinexfile,'r')
        lines = f.read().splitlines(True)
        lines.append('')

        for i,line in enumerate(lines):
            if "Receiver type" in line:
                print(line[0:60])
            if "Antenna type" in line:
                print(line[0:60])
            # this assumes Antenna is after Receiver
                break
        f.close()
    else:
        print('File does not exist:', teqclog)

def readoutmp(teqcfile,rcvtype):
    """
    teqcfile input is the full name of a teqc log 
    rcvtype is a string that includes the name of the receiver you are searching
    for. it does not have to be exact (so NETR would work for NETRS)
    returns MP1, MP2 (both in meters), and a boolean as to whether the values were found
    if rcvtype is set to NONE, it will return data without restriction 
    """
    # change variable be ause i am reusing old code
    rinexfile = teqcfile

    f=open(rinexfile,'r')
    lines = f.read().splitlines(True)
    lines.append('')

    mp1 = 0
    mp2 = 0
    # set this to always be true if you don't want to restrict to one receiver
    if rcvtype == 'NONE':
        foundRec = True
    else:
        foundRec = False
    for i,line in enumerate(lines):
        if "Moving average MP1" in line:
            mp1 = line[26:34].strip()
        if "Moving average MP2" in line:
            mp2 = line[26:34].strip()
        if  rcvtype in line:
            foundRec = True
    f.close()
    return mp1, mp2, foundRec


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
    checks that directories exist for teqc logs
    author: kristine larson
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
    parser.add_argument("-rcvant", default = None, help="True to output receiver/antenna type", type=str)

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

    # check the receiver and antenna in the teqc file
    if args.rcvant != None: 
        s = sfilename(station, year, doy)
        ReadRecAnt(s)
        sys.exit()


    # get the name/location of the teqc executable
    teqc = g.teqc_version()

    if not os.path.isfile(teqc):
        print('teqc has to be installed in EXE. Exiting. ')
        sys.exit()
    else:
           # run multiple days for a station within a given year
        for d in range(doy,doy_end):
            navfile, rinexfile,foutname,mpdir = get_files(station,year,d)
            run_teqc(teqc,navfile,rinexfile,foutname,mpdir)

if __name__ == "__main__":
    main()


