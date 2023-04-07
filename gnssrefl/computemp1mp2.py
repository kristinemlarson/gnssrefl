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
    makes a plot of MP1 multipath metric. Sends to the screen

    Parameters
    ----------
    station : str
        4 ch station name

    tv: np array 
        (year, doy, mp1, mp2) 

    winter : bool
        whether to throw out ~jan-apr and ~oct-dec

    """
    if (winter == 'True'):
        cc = ((tv[:,1] > 105) & (tv[:,1] < 274))
        tv = tv[cc,:]
    plt.figure()
    t = tv[:,0]+tv[:,1]/365.25
    ii = (tv[:,2] > 0) # MP12
    jj = (tv[:,3] > 0) # MP1
    plt.plot(t[ii],-tv[ii,2],'b.',label='MP12')
    plt.plot(t[jj],-tv[jj,3],'r.',label='MP1')
    plt.ylabel('-L1 Multipath rms(m)')
    plt.title(station + ' preliminary Vegetation statistic')
    plt.grid()
    plt.show()


def sfilename(station, year, doy):
    """
    Finds mp1 filename on your system

    Parameters
    ----------
    station : string
        4 character station name 
    year : integer

    doy : integer
        day of year

    Returns
    -------
    xfile : string
        the full SNR filename on your local system
    """
    cdoy = '{:03d}'.format(doy)
    cyyyy = str(year)
    cyy = cyyyy[2:4]
    ddir = os.environ['REFL_CODE'] + '/' + cyyyy + '/mp/' + station + '/'

    xfile = ddir+ station + cdoy + '0.' + cyy + 'S'

    return xfile

def ReadRecAnt(teqclog):
    """
    prints out Receiver and Antenna name from a teqc log

    Parameters
    ----------
    teqclog : str
        the name of a teqc log 

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

    # defaults  so there is something to return
    mp12 = '0'
    mp1 = '0'
    rcvtypeinfile = 'xxxx'
    # set this to always be true if you don't want to restrict to one receiver
    if rcvtype == 'NONE':
        foundRec = True
    else:
        foundRec = False

    for i,line in enumerate(lines):
        if "Receiver type" in line:
            # remove white space
            rcvtypeinfile=line[26:40].replace(" ","")
        # new style teqc
        if "Moving average MP12" in line:
            mp12 = line[26:34].strip()
        # old style teqc
        if "Moving average MP1 " in line:
            mp1 = line[26:34].strip()
        if  rcvtype in line:
            foundRec = True
    f.close()
    return mp12, mp1, foundRec, rcvtypeinfile


def run_teqc(teqc,navfile,rinexfile,foutname,mpdir):
    """
    run teqcs and stores the output 

    Parameters
    ----------
    teqc : str
        location of the teqc executable
    navfile : str
        name of the RINEX nav file
    rinexfile : string
        name of the RINEX observation file
    foutname : str
        name of the output file
    mpdir : str
        location of the multipath directory on your system

    """
    line = [teqc, '-nav', navfile, '+qc', rinexfile]
    subprocess.call(line)
    details = rinexfile[0:11] + 'S'
    print('SUCCESS: ',mpdir + '/' + details)
    subprocess.call(['mv','-f',details,mpdir] )
    # clean up - remove rinex file
    subprocess.call(['rm','-f',rinexfile] )

def check_directories(station,year):
    """
    checks that directories exist for teqc logs

    Parameters
    ----------
    station : str
        4 character station name

    year : int
        full year

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


def get_files(station,year,doy,look):
    """
    Parameters
    ----------
    station : str
        4 character station name
    year : int
        full year
    doy : int
        day of year
    look : bool
        whether you should try to get the file from unavco 
        if it does not exist locally

    Returns
    -------
    navfile : str
        navigation/orbit file
    rinexfile : str
        name of the obs file
    foutname : str
        full name of the teqc log output 
    mpdir :  str
        directory for MP results
    goahead : boolean
        whether you should go ahead and run teqc

    """
    goahead = False # means you found everything and can run teqc

    # check that directories exist. Make them if they do not
    navfiledir, foutdir = check_directories(station,year)
    mpdir = foutdir

    cdoy = '{:03d}'.format(doy) ; 
    cyy = '{:02d}'.format(year-2000)
    cyyyy = '{:04d}'.format(year-2000)

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
        print('No RINEX file',rinexfile)
        if look == None:
            goahead = False
        else:
            g.rinex_unavco(station, year, doy,0)
            if os.path.isfile(rinexfile):
                goahead = True
                print('retrieved from UNAVCO: ',rinexfile)
    else:
        goahead = True

    if not nexist:
        goahead = False
        print('No nav file',navfile)

    foutname = foutdir + '/' + station + cdoy + '0.' + cyy + '.mp'
    print(navfile, rinexfile,foutname,mpdir)
    return navfile, rinexfile,foutname,mpdir, goahead

def main():
    """
    computes MP1 MP2 stats using teqc or reads existing log

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)
    parser.add_argument("-doy_end", default = None, help="day of year - to analyze multiple days", type=int)
    parser.add_argument("-year_end", default = None,  type=int)
    parser.add_argument("-rcvant", default = None, help="True to output receiver/antenna type", type=str)
    parser.add_argument("-look", default = None, help="True to try and download from unavco", type=str)

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
            navfile, rinexfile,foutname,mpdir,goahead = get_files(station,year,d,args.look)
            if goahead:
                run_teqc(teqc,navfile,rinexfile,foutname,mpdir)

if __name__ == "__main__":
    main()


