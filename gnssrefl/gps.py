# toolbox for GPS/GNSS data analysis
import datetime
from datetime import date
from datetime import timedelta
#from datetime import datetime

import getpass
import json
import math
import os
import pickle
import re
import requests
import subprocess
import sys
import sqlite3
from urllib.parse import urlparse
import time
from ftplib import FTP #import FTP commands from python's built-in ftp library
from ftplib import FTP_TLS

# remove for now
from importlib.metadata import version

import scipy.signal as spectral
from scipy.interpolate import interp1d

import matplotlib.pyplot as plt
import numpy as np
import wget
from numpy import array

import gnssrefl.read_snr_files as snr
import gnssrefl.karnak_libraries as k
import gnssrefl.EGM96 as EGM96
import gnssrefl.rinex2snr as rnx
import gnssrefl.kelly as kelly

# for future ref
#import urllib.request


# various numbers you need in the GNSS world
# mostly frequencies and wavelengths
class constants:
    c= 299792458 # speed of light m/sec
#   GPS frequencies and wavelengths
    fL1 = 1575.42 # MegaHz 154*10.23
    fL2 = 1227.60 # 120*10.23
    fL5 = 115*10.23 # L5
#  GPS wavelengths
    wL1 = c/(fL1*1e6) # meters wavelength
    wL2 = c/(fL2*1e6)
    wL5 = c/(fL5*1e6)
#   galileo frequency values
    gal_L1 = 1575.420
    gal_L5 = 1176.450
    gal_L6 = 1278.70
    gal_L7 = 1207.140
    gal_L8 = 1191.795
#  galileo wavelengths, meters
    wgL1 = c/(gal_L1*1e6)
    wgL5 = c/(gal_L5*1e6)
    wgL6 = c/(gal_L6*1e6)
    wgL7 = c/(gal_L7*1e6)
    wgL8 = c/(gal_L8*1e6)

#   beidou frequencies and wavelengths
    bei_L2 = 1561.098
    bei_L7 = 1207.14
    bei_L6 = 1268.52
    wbL2 = c/(bei_L2*1e6)
    # these values are defined in Rinex 3 
    wbL7 = c/(bei_L7*1e6)
    wbL6 = c/(bei_L6*1e6)
    # does this even exist? I am using gps l5 for now
    bei_L5 = 1176.45
    wbL5 = c/(bei_L5*1e6)

#   Earth rotation rate used in GPS Nav message
    omegaEarth = 7.2921151467E-5 #	%rad/sec
    mu = 3.986005e14 # Earth GM value


class wgs84:
    """
    wgs84 parameters for Earth radius and flattening
    """
    a = 6378137. # meters Earth radius
    f  =  1./298.257223563 # flattening factor
    e = np.sqrt(2*f-f**2) # 

def is_it_legal(freq):
    """
    checks whether the frequency list set by the user in gnssir is legal

    Parameters
    ----------
    freq : list of integers
        frequencies you want to check

    Returns:
    --------
    legal : bool
        whether it is legal or not
    """
    # currently allowed
    legal_list = [1,2,20,5,101,102,201,205,206,207,208,302,306,307]
    # assume legal
    legal = True

    for f in freq:
        if f not in legal_list:
            print('This is not a legal gnssrefl frequency:', f)
            legal = False

    return legal

def myfavoriteobs():
    """
    returns list of SNR obs needed for gfzrnx. 

    """
    # not even sure why i have C here for beidou
    # 2023feb02 added L1C - back up to L1 C/A
    gobblygook = 'G:S1C,S1X,S2X,S2L,S2S,S2X,S5I,S5Q,S5X+R:S1P,S1C,S2P,S2C+E:S1,S5,S6,S7,S8+C:S2C,S7C,S6C,S2I,S7I,S6I,S2X,S6X,S7X'
    # testing C vs P for glonass
    #gobblygook = 'G:S1C,S1X,S2X,S2L,S2S,S2X,S5I,S5Q,S5X+R:S1C,S1P,S2C,S2P+E:S1,S5,S6,S7,S8+C:S2C,S7C,S6C,S2I,S7I,S6I,S2X,S6X,S7X'

    return gobblygook

def myfavoritegpsobs():
    """
    returns list of GPS only SNR obs needed for gfzrnx. 

    """
    # can't have non-GPS obs if you ask for only GPS signals 
    # 2023feb02 added L1C which i believe to be S1X. But c/a still the default
    gobblygook = 'G:S1C,S1X,S2X,S2L,S2S,S2X,S5I,S5Q,S5X'

    return gobblygook

def ydoych(year,doy):
    """
    Converts year and doy to various character strings
    (two char year, 4 char year, 3 char day of year)

    Parameters
    ----------
    year : int
        full year
    doy : int
        day of year

    Returns
    -------
    cyyyy : str
        4 character year
    cyy : str
        2 character year
    cdoy : str
        3 character day of year

    """
    cyyyy = str(year)
    cyy = cyyyy[2:4]
    cdoy = '{:03d}'.format(doy)

    return cyyyy,cyy,cdoy


def define_and_xz_snr(station,year,doy,snr):
    """
    finds and checks for existence of a SNR file
    uncompresses if that is needed (xz or gz)

    Parameters
    ----------
    station: str
        station name, 4 characters
    year : int
        full year
    doy : int
        day of year
    snr : int
        kind of snr file (66,77, 88 etc)

    Returns
    -------
    fname : str
        full name of the SNR file
    fname2 : str
        no longer used but kept for backwards capability
    snre : bool
        whether the file exists or not

    """
    xdir = os.environ['REFL_CODE']
    cyyyy, cyy, cdoy = ydoych(year,doy)
    f= station + cdoy + '0.' + cyy + '.snr' + str(snr)
    fmakan = station.upper() + cdoy + '0.' + cyy + '.snr' + str(snr)
    fname = xdir + '/' + cyyyy + '/snr/' + station + '/' + f
    fname2 = xdir + '/' + cyyyy  + '/snr/' + station + '/' + f  + '.xz'
    fname3 = xdir + '/' + cyyyy  + '/snr/' + station + '/' + f  + '.gz'
    # for makan
    fname4 = xdir + '/' + cyyyy  + '/snr/' + station.upper() + '/' + fmakan  
    # yet another makan option
    fname5 = xdir + '/' + cyyyy  + '/snr/' + station.upper() + '/' + fmakan   + '.gz'

    snre = False
    # add gzip
    if os.path.isfile(fname):
        snre = True
    else:
        if os.path.isfile(fname2):
            subprocess.call(['unxz', fname2])
        else:
            if os.path.isfile(fname3):
                subprocess.call(['gunzip', fname3])
                fname2 = fname3 #Switch file names for .xz to .gz, for returning proper name below
        # make sure the uncompression worked
        if os.path.isfile(fname):
            snre = True
        else:
            #print('did not find lowercase station snr file but will look for uppercase')
            if os.path.isfile(fname4):
                print('found uppercase station name in a snr file')
                fname = fname4
                fname2 = fname4 # not needed
            elif os.path.isfile(fname5):
                print('found gzipped uppercase station name')
                subprocess.call(['gunzip', fname5])
                fname = fname4
                fname2 = fname4 # not needed
                snre = True

    if not os.path.isfile(fname):
        print('I looked everywhere for that SNR file and could not find it')
        print(fname); print(fname2) ; 
        print(fname3); print(fname4); print(fname5)

#   return fname2 but only for backwards compatibility
    return fname, fname2, snre 

def azimuth_angle(RecSat, East, North):
    """
    Given cartesian Receiver-Satellite vectors, and East and North
    unit vectors, computes azimuth angle 

    Parameters
    ----------
    RecSat : 3-vector 
        meters

    East : 3-vector
        unit vector in east direction

    North : 3-vector 
        unit vector in north direction

    Returns 
    -------
    azangle : float
        azimuth angle in degrees

    """
    staSatE = East[0]*RecSat[0] + East[1]*RecSat[1] + East[2]*RecSat[2]
    staSatN = North[0]*RecSat[0] + North[1]*RecSat[1] + North[2]*RecSat[2]
#    azangle = 0
    azangle = np.arctan2(staSatE, staSatN)*180/np.pi
    if azangle < 0:
        azangle = 360 + azangle
# 
    return azangle

def rot3(vector, angle):
    """
    Parameters
    ----------
    vector : 3 vector
        float
    angle : float
        radians

    Returns
    -------
    vector2 : 3 vector
        float, original vector rotated by angle 

    """
    rotmat = np.matrix([[ np.cos(angle), np.sin(angle), 0],
                        [-np.sin(angle), np.cos(angle), 0],
                        [             0,             0, 1]])
    vector2 = np.array((rotmat*np.matrix(vector).T).T)[0]
    return vector2

def xyz2llh(xyz, tol):
    """
    Computes latitude, longitude and height from XYZ (meters)

    Parameters
    ----------
    xyz : list or np array 
        X,Y,Z in meters

    tol : float
        tolerance in meters for the calculation (1E-8 is good enough)

    Returns
    -------
    lat : float
        latitude in radians

    lon : float
        longitude in radians

    h : float
        ellipsoidal height in WGS84 in meters

    """
    x=xyz[0]
    y=xyz[1]
    z=xyz[2]
    lon = np.arctan2(y, x)
    p = np.sqrt(x**2+y**2)
    lat0 = np.arctan((z/p)/(1-wgs84.e**2))
    b = wgs84.a*(1-wgs84.f)
    error = 1
    a2=wgs84.a**2
    i=0 # make sure it doesn't go forever
    while (error > tol) and (i < 6):
        n = a2/np.sqrt(a2*np.cos(lat0)**2+b**2*np.sin(lat0)**2)
        h = p/np.cos(lat0)-n
        lat = np.arctan((z/p)/(1-wgs84.e**2*n/(n+h)))
        error = np.abs(lat-lat0)
        lat0 = lat
        i+=1
    return lat, lon, h

def xyz2llhd(xyz):
    """
    Converts cartesian coordinates to latitude,longitude,height

    Parameters
    ----------
    xyz : three vector of floats
        Cartesian position in meters

    Returns
    -------
    lat : float
        latitude in degrees

    lon : float
        longitude in degrees

    h : float
        ellipsoidal height in WGS84 in meters

    """
    x=xyz[0]
    y=xyz[1]
    z=xyz[2]
    lon = np.arctan2(y, x)
    p = np.sqrt(x**2+y**2)
    lat0 = np.arctan((z/p)/(1-wgs84.e**2))
    b = wgs84.a*(1-wgs84.f)
    error = 1
    a2=wgs84.a**2
    i=0 # make sure it doesn't go forever
    tol = 1e-10
    while error > tol and i < 6:
        n = a2/np.sqrt(a2*np.cos(lat0)**2+b**2*np.sin(lat0)**2)
        h = p/np.cos(lat0)-n
        lat = np.arctan((z/p)/(1-wgs84.e**2*n/(n+h)))
        error = np.abs(lat-lat0)
        lat0 = lat
        i+=1
    return lat*180/np.pi, lon*180/np.pi, h

def zenithdelay(h):
    """
    a very simple zenith troposphere delay in meters
    this is NOT to be used for precise geodetic applications

    Parameters
    ----------
    h: float
        ellipsoidal (height) in meters

    Returns
    -------
    zd : float
        simple zenith delay for the troposphere in meters

    """

    zd = 0.1 + 2.31*np.exp(-h/7000.0)
    return zd

def up(lat,lon):
    """
    returns the up unit vector, and local east and north unit vectors needed 
    for azimuth calc.

    Parameters
    ----------
    latitude : float
        radians

    longitude : float
        radians

    Returns
    -------
    East : three vector
        local transformation unit vector

    North : three vector
        local transformation unit vector

    """
    xo = np.cos(lat)*np.cos(lon)
    yo = np.cos(lat)*np.sin(lon)
    zo = np.sin(lat)
    u= np.array([xo,yo,zo])    
#    c ... also define local east/north for station: took these from fortran
    North = np.zeros(3)
    East = np.zeros(3)
    North[0] = -np.sin(lat)*np.cos(lon)
    North[1] = -np.sin(lat)*np.sin(lon)
    North[2] = np.cos(lat)
    East[0] = -np.sin(lon)
    East[1] = np.cos(lon)
    East[2] = 0
    return u, East, North

def norm(vect):
    """
    calculates magnitude of a vector

    Parameters
    ----------
    vect : float
        vector

    Returns
    -------
    nv : float
        norm of vect

    """  
    nv = np.sqrt(np.dot(vect,vect))
    return nv

def elev_angle(up, RecSat):
    """
    computes satellite elevation angle

    Parameters
    ----------
    up : 3 vector float 
        unit vector in the up direction

    RecSat : 3 vector numpy 
        Cartesian vector pointing from receiver to satellite in meters

    Returns
    -------
    angle : float
        elevation angle in radians

    """
    ang = np.arccos(np.dot(RecSat,up) / (norm(RecSat)))
    angle = np.pi/2.0 - ang
    return angle
 
def dec31(year):
    """
    Calculates the day of year for December 31

    Parameters 
    ----------
    input: integer
        year

    Returns 
    -------
    doy : integer
        day of year for December 31
    """
    today=datetime.datetime(year,12,31)
    doy = (today - datetime.datetime(year, 1, 1)).days + 1

    return doy

def ymd2doy(year,month,day):
    """
    Calculates day of year and other date strings
    
    Parameters
    ----------
    year : integer
        full year

    month : integer
        month

    day : integer
        day of the month

    Returns
    -------
    doy : int
         day of year
    cdoy : str
         three character day of year
    cyyyy : str 
         four character year
    cyy : str 
         two character year

    """
    today=datetime.datetime(year,month,day)
    doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
    cyyyy, cyy, cdoy = ydoych(year,doy)
    return doy, cdoy, cyyyy, cyy

def hatanaka_warning():
    """
    Returns 
    -------
    warning about missing Hatanaka executable

    """
    print('WARNING WARNING WARNING WARNING')
    print('You are trying to convert Hatanaka files without having the proper')
    print('executable, CRX2RNX. See links in the gnssrefl documentation')

def getnavfile(year, month, day):
    """
    picks up nav file and stores it in the ORBITS directory

    Parameters
    ----------
    year : int
        full year
    month: int
        if day is zero, the month value is really the day of year
    day: int
        day of the month

    Returns
    -------
    navname : string
        name of navigation file
    navdir : string
        location of where the nav file should be stored
    foundit : bool
        whether the file was found

    """
    foundit = False
    ann = make_nav_dirs(year)
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)
    navname,navdir = nav_name(year, month, day)
    nfile = navdir + '/' + navname
    if not os.path.exists(navdir):
        subprocess.call(['mkdir',navdir])

    foundit = check_navexistence(year,month,day)

    if (not foundit):
        navstatus = navfile_retrieve(navname, cyyyy,cyy,cdoy) 
        if navstatus:
            #print('\n navfile being moved to online storage area')
            subprocess.call(['mv',navname, navdir])
            foundit = True
        else:
            print('No navfile found')

    return navname,navdir,foundit

def getsp3file(year,month,day):
    """
    retrieves IGS sp3 precise orbit file from CDDIS

    Parameters
    ----------
    year : integer
        full year
    month : integer
        calendar month
    day : integer
        calendar day

    Returns
    -------
    name : str
        filename for the orbits
    fdir : str
        directory for the orbits

    """
    name, fdir = sp3_name(year,month,day,'igs') 
    cddis = 'ftp://cddis.nasa.gov'


    # try new way using secure ftp
    #dir_secure = '/pub/gnss/data/daily/' + cyyyy + '/' + cdoy + '/' + cyy + 'o/'
    #file_secure = file1

    if (os.path.isfile(fdir + '/' + name ) == True):
        okok = 1
        #print('sp3file already exists')
    else:
        gps_week = name[3:7]
        file1 = name + '.Z'
        filename1 = '/gnss/products/' + str(gps_week) + '/' + file1
        url = cddis + filename1 
        # new secure ftp way
        sec_dir = '/gnss/products/' + str(gps_week) + '/'
        sec_file = file1
        try:
            #wget.download(url,file1)
            cddis_download_2022B(sec_file, sec_dir) 
            subprocess.call(['uncompress',file1])
            store_orbitfile(name,year,'sp3') 
        except:
            print('some kind of problem -remove empty file')
            subprocess.call(['rm',file1])

    return name, fdir

def getsp3file_flex(year,month,day,pCtr):
    """
    retrieves sp3files
    returns the name of the orbit file and its directory from CDDIS
    only gets the old-style filenames

    Parameters
    ----------
    year : integer

    month : integer

    day : integer

    pCtr : string
        3 character orbit processing center

    Returns
    -------
    name : str
        filename for the orbits
    fdir : str
        directory for the orbits
    fexist : bool
        whether the orbit file was successfully found

    """
    # really should use mgex version
    # returns name and the directory
    name, fdir = sp3_name(year,month,day,pCtr) 
    #print(name, fdir)
    gps_week = name[3:7]
    file1 = pCtr + name[3:8] + '.sp3.Z'
    name = pCtr + name[3:8] + '.sp3'
    foundit = False
    ofile = fdir + '/' + name
    # new CDDIS way
    sec_dir = '/gnss/products/' + str(gps_week) + '/'
    sec_file = file1

    if (os.path.isfile(ofile ) == True):
        foundit = True
    elif (os.path.isfile(ofile + '.xz') == True):
        subprocess.call(['unxz', ofile + '.xz'])
        foundit = True
    else:
        filename1 = '/gnss/products/' + str(gps_week) + '/' + file1
        cddis = 'ftp://cddis.nasa.gov'
        url = cddis + filename1 
        try:
            cddis_download_2022B(sec_file, sec_dir) 
            subprocess.call(['uncompress',file1])
            store_orbitfile(name,year,'sp3') 
            foundit = True
        except:
            print('some kind of problem-remove empty file, if it exists')
        if os.path.isfile(sec_file):
            siz = os.path.getsize(sec_file)
            if (siz == 0):
                subprocess.call(['rm','-f',sec_file])

    return name, fdir, foundit

def getsp3file_mgex(year,month,day,pCtr):
    """
    retrieves MGEX sp3 orbit files 

    Parameters
    ----------
    year : integer

    month : integer

    day : integer

    pCtr : string
        name of the orbit center

    Returns
    -------
    name : str
        orbit filename

    fdir : str
        file directory

    foundit : bool

    """
    screenstats = False # for now
    foundit = False
    # this returns sp3 orbit product name
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    name, fdir = sp3_name(year,month,day,pCtr) 
    print('sp3 filename ',name)
    gps_week = name[3:7]
    igps_week = int(gps_week)
    # unfortunately the CDDIS archive was at one point computing the GPS week wrong
    igps_week_at_cddis = 1 + int(gps_week)
    #print('GPS week', gps_week,igps_week)
    file1 = name + '.Z'

    # get the sp3 filename for the new format - which assumes it is gzipped
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    if pCtr == 'gbm': # GFZ
        file2 = 'GFZ0MGXRAP_' + cyyyy + cdoy + '0000_01D_05M_ORB.SP3.gz'
    if pCtr == 'wum': # Wuhan, 
        # used to only use first 24 hours, but now can use whole orbit file
        #nyear, ndoy = nextdoy(year,doy)
        #cndoy = '{:03d}'.format(ndoy); cnyear = '{:03d}'.format(nyear)
        file2 = 'WUM0MGXULA_' + cyyyy + cdoy + '0000_01D_05M_ORB.SP3.gz'
        file2 = 'WUM0MGXULT_' + cyyyy + cdoy + '0000_01D_05M_ORB.SP3.gz'
        print(file2,screenstats)
    if pCtr == 'grg': # french group
        file2 = 'GRG0MGXFIN_' + cyyyy + cdoy + '0000_01D_15M_ORB.SP3.gz'
    if pCtr == 'sha': # shanghai observatory
        # change to 15 min 2020sep08
        # this blew up - do not know why. removing Shanghai for now
        file2 = 'SHA0MGXRAP_' + cyyyy + cdoy + '0000_01D_15M_ORB.SP3.gz'
    # try out JAXA - should have GPS and glonass
    if pCtr == 'jax':
        file2 = 'JAX0MGXFIN_' + cyyyy + cdoy + '0000_01D_05M_ORB.SP3.gz'
    # this is name without the gzip
    name2 = file2[:-3] 

     
    # this is the default setting - no file exists
    mgex = 0
    n1 = os.path.isfile(fdir + '/' + name)
    n1c = os.path.isfile(fdir + '/' + name + '.xz')
    if (n1 == True):
        if screenstats:
            print('first kind of MGEX sp3file already exists online')
        mgex = 1
        foundit = True
    elif (n1c  == True): 
        if screenstats:
            print('xz first kind of MGEX sp3file already exists online-unxz it')
        fx =  fdir + '/' + name + '.xz'
        subprocess.call(['unxz', fx])
        mgex = 1
        foundit = True

    n2 = os.path.isfile(fdir + '/' + name2)
    n2c = os.path.isfile(fdir + '/' + name2 + '.xz')
    if (n2 == True):
        if screenstats:
            print('MGEX sp3file already exists online')
        mgex = 2 ; foundit = True
    elif (n2c == True):
        if screenstats:
            print('MGEX sp3file already exists online')
        mgex = 2 ; foundit = True
        fx =  fdir + '/' + name2 + '.xz'
        subprocess.call(['unxz', fx])

    if (mgex == 2):
        name = name2
    if (mgex == 1):
        name = file1[:-2]

    print('Type 1 filename',file1)
    print('Type 2 filename',file2)

    if not foundit:
        if (mgex == 0):
            if not foundit:
                name = file2[:-3] 
                secure_file = file2
                secure_dir = '/gps/products/mgex/' + str(igps_week) + '/'
                foundit = orbfile_cddis(name, year, secure_file, secure_dir, file2)
            if not foundit:
                secure_dir = '/gps/products/' + str(igps_week) + '/'
                foundit = orbfile_cddis(name, year, secure_file, secure_dir, file2)
            if not foundit:
                secure_dir = '/gps/products/mgex/' + str(igps_week) + '/'
                secure_file = file1 # Z compressed
                name = file1[:-2]
                foundit = orbfile_cddis(name, year, secure_file, secure_dir, file1)
            if (not foundit):
                secure_dir = '/gps/products/' + str(igps_week) + '/'
                foundit = orbfile_cddis(name, year, secure_file, secure_dir, file2)

    return name, fdir, foundit

def orbfile_cddis(name, year, secure_file, secure_dir, file2):
    """
    tries to download a file from a directory at CDDIS which 
    it then stores it the year directory (with a given name)

    Parameters
    ----------
    name : str
        the name of the orbit file you want to download from CDDIS
    year : int
        full year
    secure_file : str
        name of the file at CDDIS
    secure_dir : str
        where the file lives at CDDIS
    file2 : str
        name without the compression???

    Returns
    -------
    foundit : bool
        whether the file was found

    now checks that file size is not zero. allows old file name downloads

    """
    # assume file was not found
    foundit = False
    #print(secure_dir, secure_file)
    # Z or gz expected ...
    if secure_file[-3:] == '.gz':
        gzip = True
    else:
        gzip = False
    try:
        cddis_download_2022B(secure_file, secure_dir)
    except:
        ok = 1
    # found a file
    if os.path.isfile(secure_file):
        siz = os.path.getsize(secure_file)
        #print('File size', siz)
        if (siz == 0):
            subprocess.call(['rm', secure_file])
        else:
            foundit = True
            if gzip:
                subprocess.call(['gunzip', secure_file])
                store_orbitfile(name,year,'sp3') ; 
            else:
                subprocess.call(['uncompress', secure_file])
                store_orbitfile(name,year,'sp3') ; 

    return foundit

def kgpsweek(year, month, day, hour, minute, second):
    """
    Calculates GPS week and GPS second of the week
    There is another version that works on character string.
    I think (kgpsweekC)
    
    Examples
    --------
    kgpsweek(2023,1,1,0,0,0)
        returns 2243  and  0

    Parameters
    ----------
    year : int 
        full year
    month : int 
        calendar month
    day : int 
        calendar day
    hour: int
        hour of the Day (gps time)
    minute : int 
        minutes 
    second : int
        seconds

    Returns
    -------
    GPS_wk : int
        GPS week
    GPS_sec_wk : int
        GPS second of the week

    """

    year = int(year)
    M = int(month)
    D = int(day)
    H = int(hour)
    minute = int(minute)
    
    UT=H+minute/60.0 + second/3600. 
    if M > 2:
        y=year
        m=M
    else:
        y=year-1
        m=M+12
        
    JD=np.floor(365.25*y) + np.floor(30.6001*(m+1)) + D + (UT/24.0) + 1720981.5
    GPS_wk=np.floor((JD-2444244.5)/7.0);
    GPS_wk = int(GPS_wk)
    GPS_sec_wk=np.rint( ( ((JD-2444244.5)/7)-GPS_wk)*7*24*3600)            
     
    return GPS_wk, GPS_sec_wk

def kgpsweekC(z):
    """
    converts RINEX timetag line into integers/float

    Parameters
    ----------
    z : str
        timetag from rinex file (YY MM DD MM SS.SSSS )

    Returns
    -------
    gpsw : integer
        GPS week

    gpss : integer
        GPS seconds

    """
    y= int(z[1:3])
    m = int(z[4:6])
    d=int(z[7:9])
    hr=int(z[10:12])
    mi=int(z[13:15])
    sec=float(z[16:26])
    gpsw,gpss = kgpsweek(y+2000,m,d,hr,mi,sec)

    return gpsw, gpss

def igsname(year,month,day):
    """
    returns the name of an IGS orbit file

    Parameters
    ----------
    year : integer
        four character year

    month : integer

    day : integer 

    Returns
    -------
    name : str
        IGS orbit name

    clockname : string
        COD clockname 

    """
    [wk,sec]=kgpsweek(year,month,day,0,0,0)
    x=int(sec/86400)
    dd = str(wk) + str(x) 
    name = 'igs' + str(wk) + str(x) + '.sp3'
    # i think at some point they changed to lower case?
   # clockname = 'COD' + dd + '.CLK_05S.txt'
    clockname = 'cod' + dd + '.clk_05s'

    return name, clockname

def read_sp3(file):
    """
    borrowed from Ryan Hardy, who got it from David Wiese ... 
    """
    try:      
        f = open(file)
        raw = f.read()
        f.close()
        lines  = raw.splitlines()
        nprn = int(lines[2].split()[1])
        lines  = raw.splitlines()[22:-1]
        epochs = lines[::(nprn+1)]
        nepoch =  len(lines[::(nprn+1)])
        week, tow, x, y, z, clock, prn = np.zeros((nepoch*nprn, 7)).T
        for i in range(nepoch):
            year, month, day, hour, minute, second = np.array(epochs[i].split()[1:], dtype=float)
            week[i*nprn:(i+1)*nprn], tow[i*nprn:(i+1)*nprn] = \
				kgpsweek(year, month, day, hour, minute, second)
            for j in range(nprn):
                prn[i*nprn+j] =  int(lines[i*(nprn+1)+j+1][2:4])
                x[i*nprn+j] = float(lines[i*(nprn+1)+j+1][4:18])
                y[i*nprn+j] = float(lines[i*(nprn+1)+j+1][18:32])
                z[i*nprn+j] = float(lines[i*(nprn+1)+j+1][32:46])
                clock[i*nprn+j] = float(lines[(i)*(nprn+1)+j+1][46:60])
    except:
        print('sorry - the sp3file does not exist')
        week,tow,x,y,z,prn,clock=[0,0,0,0,0,0,0]
		
    return week, tow, prn, x, y, z, clock

def myreadnav(file):
    """
    Parameters
    ----------
    file : str
        nav filename

    output is complicated - broadcast ephemeris blocks
    """
# input is the nav file
    try:
        f = open(file, 'r')
        nav = f.read()
        f.close()
        nephem = (len(nav.split('END OF HEADER')[1].splitlines())-1)/8
        nephem = int(nephem) #    print(nephem)         
        lines = nav.split('END OF HEADER')[1].splitlines()[1:]
        table = np.zeros((nephem, 32))
        #print('Total number of ephemeris messages',nephem)
        for i in range(nephem):
            for j in range(8):
                if j == 0:
                    prn = int(lines[i*8+j][:2])
                    year = int(lines[i*8+j].split()[1])
                    if year > 76:
                        year += 1900
                    else:
                        year += 2000
                    month = int(lines[i*8+j].split()[2])
                    day = int(lines[i*8+j].split()[3])
                    hour = int(lines[i*8+j].split()[4])
                    minute = int(lines[i*8+j].split()[5])
                    second = float(lines[i*8+j][17:22])
                    table[i, 0] = prn
#                    print('Ephem for: ', prn, year, month, day, hour, minute)
                    week, Toc = kgpsweek(year, month, day, hour, minute, second)
                    table[i, 1] =  week
                    table[i, 2] = Toc
                    Af0 = float(lines[i*8][-3*19:-2*19].replace('D', 'E'))
                    Af1 = float(lines[i*8][-2*19:-1*19].replace('D', 'E'))
                    Af2 = float(lines[i*8][-19:].replace('D', 'E'))
                    table[i,3:6] = Af0, Af1, Af2
                elif j != 7:
                    for k in range(4):
                        value = float(lines[i*8+j][19*k+3:19*(k+1)+3].replace('D', 'E'))
                        table[i,2+4*j+k] = value
                elif j== 7:
                    table[i,-2]= float(lines[i*8+j][3:19+3].replace('D', 'E'))
                    if not lines[i*8+7][22:].replace('D', 'E').isalpha():
                        table[i,-1]= 0
                    else:
                        table[i, -1] = float(lines[i*8+7][22:41].replace('D', 'E'))
# output is stored as:
#
# 0-10   prn, week, Toc, Af0, Af1, Af2, IODE, Crs, delta_n, M0, Cuc,\
# 11-22    ecc, Cus, sqrta, Toe, Cic, Loa, Cis, incl, Crc, perigee, radot, idot,\
# 23-24?                   l2c, week, l2f, sigma, health, Tgd, IODC, Tob, interval 
# week would be 24 by this scheme?
# Toe would be 14 
#	
        ephem = table
    except:
        #print('This ephemeris file does not exist',file)
        ephem = []
    return ephem

def myfindephem(week, sweek, ephem, prn):
    """
# inputs are gps week, seconds of week
# ephemerides and PRN number
# returns the closest ephemeris block after the epoch
# if one does not exist, returns the first one    
"""
    t = week*86400*7+sweek
# defines the TOE in all the ephemeris 
# he is taking the week and adding ToE (14?)
# poorly coded is all i'm gonna say

    teph = ephem[:, 24]*86400*7+ephem[:, 14]     
    prnmask = np.where(ephem[:, 0]== prn)    

    [nr,nc]=np.shape(prnmask)
#    print(nr,nc)
    if nc == 0:
        print('no ephemeris for that PRN number')
        closest_ephem = []
    else:
        try:          
            signmask = np.where(t >= teph[prnmask])
            proxmask =  np.argmin(t-teph[prnmask][signmask])
            closest_ephem = ephem[prnmask][signmask][proxmask]
        except:
#           print('using first ephemeris - but not after epoch')
            closest_ephem = ephem[prnmask][0]
        
  
    return closest_ephem

def findConstell(cc):
    """
    determine constellation integer value 

    Parameters
    -----------
    cc : string  is one character (from rinex satellite line)
        constellation definition:
            G : GPS
            R : Glonass
            E : Galileo
            C : Beidou

    Returns
    -------
    out : integer
        value added to satellite number for our system,
        0 for GPS, 100 for Glonass, 200 for Galileo, 300 for everything else
    """
    if (cc == 'G' or cc == ' '):
        out = 0
    elif (cc == 'R'): # glonass
        out = 100
    elif (cc == 'E'): # galileo
        out = 200
    else:
        out = 300
        
    return out

def myscan(rinexfile):
    """
    stripping the header code came from pyrinex.  
    data are stored into a variable called table
    columns 0,1,2 are PRN, GPS week, GPS seconds, and observables
    rows are the different observations. these should be stored 
    properly - this is a kluge
    """
    f=open(rinexfile,'r')
    lines = f.read().splitlines(True)
    lines.append('')
    # setting up a set or directionary
    # sets must be unique - so that is hwy he checks to see if it already exists
    header={}        
    eoh=0
# looks like it reads all the header lines, so you can extract them as you like
    for i,line in enumerate(lines):
        if "END OF HEADER" in line:
            eoh=i
            break
#        print(line[60:].strip())
        if line[60:].strip() not in header:
            header[line[60:].strip()] = line[:60].strip()
        else:
            header[line[60:].strip()] += " "+line[:60].strip()
    
    header['APPROX POSITION XYZ'] = [float(i) for i in header['APPROX POSITION XYZ'].split()]
    w = header['APPROX POSITION XYZ']
#    print(w)
#    approxpos = [float(i) for i in header['APPROX POSITION XYZ'].split()]
    header['# / TYPES OF OBSERV'] = header['# / TYPES OF OBSERV'].split()
#    typesObs = header['# / TYPES OF OBSERV'].split()
    aa=header['# / TYPES OF OBSERV']
    types = aa[1:] # this means from element 1 to the end
    # these are from the pyrinex verison of hte code
    header['# / TYPES OF OBSERV'][0] = int(header['# / TYPES OF OBSERV'][0])
    header['INTERVAL'] = float(header['INTERVAL'])
    # need to get approx position of the receiver
    x,y,z = header['APPROX POSITION XYZ']
    numobs = int(np.ceil(header['# / TYPES OF OBSERV'][0]))

# initial three columns in the newheader variable
    newheader = 'PRN\tWEEK\tTOW'
# add in the observation types from this file
    for j in range(numobs):
        newheader += '\t'+types[j]
# header using the Ryan Hardy style
#    print(newheader)

#    # set the line reader to after the end of the header
    # this tells it where to start
    i=eoh+1
    # so try to implement ryan hardy's storing procedure, where 0 is prn,
    # 1 is week, 2 is seconds of week, 3-N are the observables
    table = np.zeros((0, numobs+3))
    print('number of observables ', numobs)
    if numobs > 10:
        print('Tooooo many observables. I cannot deal with this')
        return
    print('line number ' , eoh)
    l = 0 # start counter for blocks
    while True:
        if not lines[i]: break
        if not int(lines[i][28]):
#            print(lines[i])
#            z=lines
            [gw,gs]=kgpsweekC(lines[i])
#            print('week and sec', gw,gs)    
            numsvs = int(lines[i][30:32])  # Number of visible satellites at epoch
#            print('number of satellites',numsvs)
            # strictly speaking i don't understand this line.
            table = np.append(table, np.zeros((numsvs, numobs+3)), axis=0)
            table[l:l+numsvs, 1] = gw
            table[l:l+numsvs, 2] = gs
            #headlength.append(1 + numsvs//12)
            sp = []
                
            if(numsvs>12):
                for s in range(numsvs):
                    xv = findConstell(lines[i][32+(s%12)*3:33+(s%12)*3]) 
                    sp.append(xv + int(lines[i][33+(s%12)*3:35+(s%12)*3]))
                    if s>0 and s%12 == 0:
                        i+= 1  # For every 12th satellite there will be a new row with satellite names                sats.append(sp) # attach satellites here
            else:
                for s in range(numsvs):
                    xv = findConstell(lines[i][32+(s%12)*3:33+(s%12)*3])
                    sp.append(xv + int(lines[i][33+(s%12)*3:35+(s%12)*3]))

#            print(len(sp), 'satellites in this block', sp)
            for k in range(numsvs): 
                table[l+k,0]=sp[k]
                if (numobs > 5):
                    for d in range(5):
                        gg = d*16
                        f=lines[i+1+2*k][gg:gg+14]
                        if not(f == '' or f.isspace()):
                            val = float(lines[i+1+2*k][gg:gg+14])
                            table[l+k, 3+d] = val
                    for d in range(numobs-5):
                        gg = d*16
                        f=lines[i+2+2*k][gg:gg+14]
                        if not (f == '' or f.isspace()):
                            val = float(lines[i+2+2*k][gg:gg+14])
                            table[l+k, 3+5+d] = val
                else:
                    for d in range(numobs):
                        gg = d*16
                        f = lines[i+1+2*k][gg:gg+14]
                        if (f == '' or f.isspace()):
                            val = float(lines[i+2+2*k][gg:gg+14])
                            table[l+k, 3+d] = val

            i+=numsvs*int(np.ceil(header['# / TYPES OF OBSERV'][0]/5))+1
            l+=numsvs
        else:
            print('there was a comment or some header info in the rinex')
            flag=int(lines[i][28])
            if(flag!=4):
                print('this is a flag that is not 4', flag)
            skip=int(lines[i][30:32])
            print('skip this many lines',skip)
            i+=skip+1
            print('You are now on line number',i)
    [nr,nc]=np.shape(table)
    print('size of the table variable is ',nr, ' by ', nc)    
    # code provided by ryan hardy - but not needed???
#    format = tuple(np.concatenate((('%02i', '%4i', '%11.7f'), 
#							((0, numobs+3)[-1]-3)*['%14.3f'])))
# I think this takes the newheader and combines it with the information in
# the table variable
    obs =  dict(zip(tuple(newheader.split('\t')), table.T))
    return obs,x,y,z

def read_files(year,month,day,station):
    """
    """   

    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    # i have a function for this ....
    rinexfile = station + cdoy + '0.' + cyy + 'o'
    navfilename = 'auto'  + cdoy + '0.' + cyy +  'n'
    if os.path.isfile(rinexfile):
        print('rinexfile exists')
    else:
        print(rinexfile)
        print('get the rinex file')
        rinex_unavco(station, year, month, day)
    # organize the file names
    print('get the sp3 and clock file names')
    sp3file, cname = igsname(year,month,day)

    # define some names of files
    if os.path.isfile(navfilename):
        print('nav exists')
    else:
        print('get nav')
        navname,navdir,foundit = getnavfile(year,month,day)
    print('read in the broadcast ephemeris')
    ephemdata = myreadnav(navfilename)
    if os.path.isfile(cname):
        print('file exists')
    else:        
        print('get the CODE clock file')
        codclock(year,month,day)
    pname = cname[0:9] + 'pckl'
    print('pickle', pname)
    # if file exists already     
    if os.path.isfile(pname):
        print('read existing pickle file')
        f = open(pname, 'rb')
        [prns,ts,clks] = pickle.load(f)
        f.close()
    else:
        print('read and save as pickle')
        prns, ts, clks = readPreciseClock(cname)
        # and then save them
        f = open(pname, 'wb')
        pickle.dump([prns,ts,clks], f)
        f.close()
    if os.path.isfile(sp3file):
        print('sp3 exsts')
    else:
        print('get sp3')
        getsp3file(year,month,day)
    print('read in the sp3 file', sp3file)
    
    sweek, ssec, sprn, sx, sy, sz, sclock = read_sp3(sp3file)
    
#20    print('len returned data', len(ephemdata), navfilename
    rinexpickle = rinexfile[0:11] + 'pclk'
    if os.path.isfile(rinexpickle):
        print('rinex pickle exists')
        f=open(rinexpickle,'rb')
        [obs,x,y,z]=pickle.load(f)
        f.close()
    else:     
        print('read the RINEX file ', rinexfile)
        obs,x,y,z = myscan(rinexfile)
        print('save as pickle file')
        f=open(rinexpickle,'wb')
        pickle.dump([obs,x,y,z], f)
        f.close()
        
    return ephemdata, prns, ts, clks, sweek, ssec, sprn, sx, sy,sz,sclock,obs,x,y,z

def propagate(week, sec_of_week, ephem):
    """
    inputs are GPS week, seconds of the week, and the appropriate 
    ephemeris block from the navigation message
    returns the x,y,z, coordinates of the satellite 
    and relativity correction (also in meters), so you add,
    not subtract

    """

# redefine the ephem variable
    prn, week, Toc, Af0, Af1, Af2, IODE, Crs, delta_n, M0, Cuc,\
    ecc, Cus, sqrta, Toe, Cic, Loa, Cis, incl, Crc, perigee, radot, idot,\
    l2c, week, l2f, sigma, health, Tgd, IODC, Tob, interval = ephem
    sweek = sec_of_week
    # semi-major axis
    a = sqrta**2
    t = week*7*86400+sweek
    tk = t-Toe
    # no idea if Ryan Hardy is doing this correctly - it should be in a function
    tk  =  (tk - 302400) % (302400*2) - 302400
    n0 = np.sqrt(constants.mu/a**3)
    n = n0+ delta_n
    Mk = M0 + n*tk
    i = 0
    Ek = Mk
    E0 = Mk + ecc*np.sin(Mk)
    # solve kepler's equation
    while(i < 15 or np.abs(Ek-E0) > 1e-12):
        i +=1
        Ek = Mk + ecc*np.sin(E0) 
        E0 = Mk + ecc*np.sin(Ek)
    nuk = np.arctan2(np.sqrt(1-ecc**2)*np.sin(Ek),np.cos(Ek)-ecc)
    Phik = nuk + perigee
    duk = Cus*np.sin(2*Phik)+Cuc*np.cos(2*Phik)
    drk = Crs*np.sin(2*Phik)+Crc*np.cos(2*Phik)
    dik = Cis*np.sin(2*Phik)+Cic*np.cos(2*Phik)
    uk = Phik + duk
    rk = a*(1-ecc*np.cos(Ek))+drk
       
    ik = incl+dik+idot*tk
    xkp = rk*np.cos(uk)
    ykp = rk*np.sin(uk)
    Omegak = Loa + (radot-constants.omegaEarth)*tk -constants.omegaEarth*Toe
    xk = xkp*np.cos(Omegak)-ykp*np.cos(ik)*np.sin(Omegak)
    yk = xkp*np.sin(Omegak)+ykp*np.cos(ik)*np.cos(Omegak)
    zk = ykp*np.sin(ik) 
    # using class
    F = -2*np.sqrt(constants.mu)/constants.c
    relcorr = F*ecc*sqrta*np.sin(Ek)
#    return [xk, yk, zk], relcorr
    return [xk[0], yk[0], zk[0]], relcorr


def get_ofac_hifac(elevAngles, cf, maxH, desiredPrec):
    """
    Computes two factors - ofac and hifac - that are inputs to the
    Lomb-Scargle Periodogram code.
    We follow the terminology and discussion from Press et al. (1992)
    in their LSP algorithm description.

    Parameters
    ------------
    elevAngles:  numpy of floats
        vector of satellite elevation angles in degrees 

    cf: float
        (L-band wavelength/2 ) in meters    

    maxH: int
        maximum LSP grid frequency in meters

    desiredPrec:  float
        the LSP frequency grid spacing in meters 
        i.e. how precise you want he LSP reflector height to be estimated

    Returns
    -------
    ofac: float
        oversampling factor

    hifac: float
        high-frequency factor

    """
# in units of inverse meters
    X= np.sin(elevAngles*np.pi/180)/cf     

# number of observations
    N = len(X) 
# observing Window length (or span)
# units of inverse meters
    W = np.max(X) - np.min(X)         
    if W == 0:
        print('bad window length - which will lead to illegal ofac/hifac calc')
        return 0,0

# characteristic peak width, meters
    cpw= 1/W

# oversampling factor
    ofac = cpw/desiredPrec 

# Nyquist frequency if the N observed data samples were evenly spaced
# over the observing window span W, in meters
    fc = N/(2*W)

# Finally, the high-frequency factor is defined relative to fc
    hifac = maxH/fc  

    return ofac, hifac

def strip_compute(x,y,cf,maxH,desiredP,pfitV,minH):
    """
    strips snr data

    Parameters
    -----------
    x : numpy array 
        elevation angles in degrees
    y : numpy array
        SNR data 
    cf : float
        scale factor for given frequency
    maxH : float
        maximum reflector height in meters
    desiredP : float
        precision of Lomb Scargle in meters
    pfitV : integer
        polynomial order for DC model
    minH : float
        minimum reflector height in meters

    Returns 
    -------
    maxF : float
        maximum Reflector height (meters)
    maxAmp : float
        amplitude of periodogram
    eminObs : float
        minimum observed elevation angle in degrees
    emaxObs : float
        maximum observed elevation angle in degrees
    riseSet : integer
        1 for rise and -1 for set
    px : numpy array
        periodogram, x-axis, RH, meters
    pz : numpy array
        periodogram, y-axis, volts/volts 
    """
    ofac,hifac = get_ofac_hifac(x,cf,maxH,desiredP)
    if np.isnan(ofac):
        print("WARNING - bad ofac")
        return 0, 0, 0, 0,0,0,0 
    if ofac == 0:
        print("WARNING - bad ofac")
        return 0, 0, 0, 0,0, 0,0

#   min and max observed elevation angles
    eminObs = min(x); emaxObs = max(x)
    if x[0] > x[1]:
        riseSet = -1
    else:
        riseSet = 1

#   change so everything is rising, i.e. elevation angle is increasing
    ij = np.argsort(x)
    x = x[ij]
    y = y[ij]

    x = np.sin(x*np.pi/180)
#   polynomial fit done before

#   scale by wavelength
    x=x/cf
#    y=newy
#   get frequency spacing
    px = freq_out(x,ofac,hifac) 
#   compute spectrum using scipy
    scipy_LSP = spectral.lombscargle(x, y, 2*np.pi*px)

#   find biggest peak
#   scaling required to get amplitude spectrum
    pz = 2*np.sqrt(scipy_LSP/len(x))
#   now window
#    ij = np.argmax(px > minH)
#    new_px = px[ij]
    new_pz = pz[(px > minH)]
    new_px = px[(px > minH)]
    px = new_px
    pz = new_pz
#   find the max
#   was causing it to crash.  check that pz has anything in it
    if len(pz) == 0:
        print('invalid LSP, no data returned. If this is pervasive, check your inputs')
        maxF = 0; maxAmp = 0
    else:
        ij = np.argmax(pz)
        maxF = px[ij]
        maxAmp = np.max(pz)

    return maxF, maxAmp, eminObs, emaxObs,riseSet, px,pz

def window_data(s1,s2,s5,s6,s7,s8, sat,ele,azi,seconds,edot,f,az1,az2,e1,e2,satNu,pfitV,pele,screenstats):
    """

    window the SNR data for a given satellite azimuth and elevation angle range

    also calculates the scale factor for various GNSS frequencies.  currently
    returns meanTime in UTC hours and mean azimuth in degrees
    cf, which is the wavelength/2
    currently works for GPS, GLONASS, GALILEO, and Beidou
    new: pele are the elevation angle limits for the polynomial fit. these are appplied
    before you start windowing the data

    Parameters
    ----------
    s1 : numpy array 
        SNR L1 data, floats
    s2 : numpy array 
        SNR L2 data, floats 
    s5 : numpy array
        SNR L5 data
    s6 : numpy array floats
        SNR L6 data
    s7 : numpy array floats
        SNR L7 data
    s8 : numpy array floats
        SNR L8 data
    sat : numpy array
        satellite number
    ele : numpy array
        elevation angle (Degrees)
    azi : numpy array
        azimuth angle (Degrees)
    seconds : numpy array
        seconds of the day (GPS time)
    edot : numpy array
        elev angle time rate of change (units?)
    f : int
        requested frequency
    az1 : float
        minimum azimuth limit, degrees
    az2 : float
        maximum azimuth limit, degrees
    e1 : float
        minimum elevation angle limit, degrees
    e2 : float
        maximum elevation angle limit, degrees
    satNu : int
        requested satellite number
    pfitV : int
        polynomial order for DC fit
    screenstats : bool
        Whether statistics come to the screen

    Returns
    -------
    x : numpy array of floats 
        elevation angle, deg
    y : numpy array of floats
        SNR, db-Hz
    Nvv : int
        number of points in x
    cf : float
        refl scale factor (lambda/2)
    meanTime : float
        UTC hour of the arc
    avgAzim : float
        average azimuth of the track (degrees)
    outFact1 : float
        tan(elev)/elevdot, hours, from SNR file
    outFact2 : float
        tan(elev)/elevdot, hours, from linear fit
    delT : float
        track length in minutes

    """
    cunit = 1
    dat = []; x=[]; y=[]
#   get scale factor
#   added glonass, 101 and 102
    if False:
        print('frequency and satellite', f,sat)
    if (f == 1) or (f==101) or (f==201) or (f==301):
        dat = s1
    if (f == 2) or (f == 20) or (f == 102) or (f==302):
        dat = s2
    if (f == 5) or (f==205):
        dat = s5
#   these are galileo frequencies (via RINEX definition)
    if (f == 206) or (f == 306):
        dat = s6
    if (f == 207) or (f == 307):
        dat = s7
    if (f == 208):
        dat = s8
#   get the scaling factor for this frequency and satellite number
    cf = arc_scaleF(f,satNu)

#   if not, frequency does not exist, will be tripped by Nv
#   this does remove the direct signal component - but gets you ready to do that
    #print('cf before removeDC', cf,' freq and sat ', f, satNu)
    if (satNu > 100):
        # check that there are even any data because this is crashing on files w/o SNR beidou data in them
        if (f == 307):
            if len(s7) > 0:
                x,y,sat,azi,seconds,edot  = removeDC(dat, satNu, sat,ele, pele, azi,az1,az2,edot,seconds) 
            else:
                x=[]; y=[]; sat=[];azi=[];seconds=[];edot =[]
        elif (f == 207):
            if len(s7) > 0:
                x,y,sat,azi,seconds,edot  = removeDC(dat, satNu, sat,ele, pele, azi,az1,az2,edot,seconds)
            else:
                x=[]; y=[]; sat=[];azi=[];seconds=[];edot =[]
        elif (f == 208):
            if len(s8) > 0:
                x,y,sat,azi,seconds,edot  = removeDC(dat, satNu, sat,ele, pele, azi,az1,az2,edot,seconds)
            else:
                x=[]; y=[]; sat=[];azi=[];seconds=[];edot =[]
        else:
            x,y,sat,azi,seconds,edot  = removeDC(dat, satNu, sat,ele, pele, azi,az1,az2,edot,seconds) 
    else:
        if (cf > 0):
            x,y,sat,azi,seconds,edot  = removeDC(dat, satNu, sat,ele, pele, azi,az1,az2,edot,seconds) 

#
    Nv = len(y); Nvv = 0 ; 
#   some defaults in case there are no data in this region
    meanTime = 0.0; avgAzim = 0.0; avgEdot = 1; Nvv = 0
    avgEdot_fit =1; delT = 0.0
#   no longer have to look for specific satellites. some minimum number of points required 
    #if screenstats:
    #    print('Starting Npts', Nv)
    if Nv > 30:
        model = np.polyfit(x,y,pfitV)
        fit = np.polyval(model,x)
#       redefine x and y as old variables
        ele = x
        dat = y - fit
#       ok - now figure out what is within the more restricted elevation angles
        x =   ele[(ele > e1) & (ele < e2) & (azi > az1) & (azi < az2)]
        y =   dat[(ele > e1) & (ele < e2) & (azi > az1) & (azi < az2)]
        ed = edot[(ele > e1) & (ele < e2) & (azi > az1) & (azi < az2)]
        a =   azi[(ele > e1) & (ele < e2) & (azi > az1) & (azi < az2)]
        t = seconds[(ele > e1) & (ele < e2) & (azi > az1) & (azi < az2)]
        ifound = 0
        #if screenstats:
        #    print('Starting/Windowed Npts', Nv, len(x))
        if len(x) > 0:
            ijkl = np.argmax(x)
            if (ijkl == 0):
            #print('ok, at the beginning ')
                ifound = 1;
            elif (ijkl == len(x)-1):
            #print('ok, at the end')
                ifound = 2;
            else:
                ifound = 3;
                if screenstats:
                    iamok = True
                    print('Rising Setting Arc, length, and index ', len(x),ijkl )
                    print("Rising/Setting Arc, length: %5.0f eangles begin %6.2f end %6.2f peak %6.2f"% (len(x), x[0],x[-1], x[ijkl] ) )
                edif1 = x[ijkl] - x[0]
                edif2 = x[ijkl] - x[-1]
                if edif1 > edif2:
                    x = x[0:ijkl]; y = y[0:ijkl]; ed = ed[0:ijkl]
                    a = a[0:ijkl]; t = t[0:ijkl]
                else:
                    x = x[ijkl:-1]; y = y[ijkl:-1]; ed = ed[ijkl:-1]
                    a = a[ijkl:-1]; t = t[ijkl:-1]
                #if screenstats:
                     #print('length of the arc is now', len(x))
        sumval = np.sum(y)
        kristine = True
        if sumval == 0:
            x = []; y=[] ; Nv = 0 ; Nvv = 0
#   since units were changed to volts/volts, the zeros got changed to 1 values
        if sumval == Nv:
            x = []; y=[] ; Nv = 0 ; Nvv = 0
        Nvv = len(y)
#       calculate average time in UTC (actually it is GPS time) in hours and average azimuth
#       this is fairly arbitrary, but can't be so small you can't fit a polymial to it
        if (Nvv > 10):
            dd = np.diff(t)
#           edot, in radians/sec
            model = np.polyfit(t,x*np.pi/180,1)
#  edot in radians/second
            avgEdot_fit = model[0]
            avgAzim = np.mean(a)
            meanTime = np.mean(t)/3600
            # this is degrees/second? - but if the values are not in the file
            # this will be zero
            avgEdot = np.mean(ed) 
#  delta Time in minutes
            delT = (np.max(t) - np.min(t))/60 
# average tan(elev)
            cunit =np.mean(np.tan(np.pi*x/180))
#           return tan(e)/edot, in units of one over (radians/hour) now. used for RHdot correction
#           so when multiplyed by RHdot - which would be meters/hours ===>>> you will get a meter correction
    if avgEdot == 0:
        outFact1 = 0
    else:
        # this was never implemented
        #outFact1 = cunit/(avgEdot*3600) 
        # rad/hour
        outFact1 = cunit/((avgEdot*np.pi/180)*3600) 
    # now change it to per hour ... 
    outFact2 = cunit/(avgEdot_fit*3600) 

    return x,y,Nvv,cf,meanTime,avgAzim,outFact1, outFact2, delT

def arc_scaleF(f,satNu):
    """
    calculates LSP scale factor cf , the wavelength divided by 2

    Parameters
    --------
    f : integer
        satellite frequency
    satNu : integer
        satellite number (1-400)

    Returns
    -------
    cf : float
        GNSS wavelength/2 (meters)

    """ 
#   default value for w so that if someone inputs an illegal frequency, it does not crash
    w = 0
    if f == 1:
        w = constants.wL1
    if (f == 2) or (f == 20):
        w = constants.wL2
    if f == 5:
        w = constants.wL5
#   galileo satellites
#   must be a smarter way to do this
    if (f > 200) and (f < 210):
        if (f == 201):
            w = constants.wgL1
        if (f == 205):
            w = constants.wgL5
        if (f == 206):
            w = constants.wgL6
        if (f == 207):
            w = constants.wgL7
        if (f == 208):
            w = constants.wgL8
#
#   add beidou 18oct15
#  i am confused about this ...
    if (f > 300) and (f < 310):
        if (f == 301):
            w = constants.wbL1
        if (f == 302):
            w = constants.wbL2
        if (f == 306):
            w = constants.wbL6
        if (f == 307):
            w = constants.wbL7

#   glonass satellite frequencies
    if (f == 101) or (f == 102):
        w = glonass_channels(f,satNu) 
    cf = w/2
    return cf 

def freq_out(x,ofac,hifac):
    """

    Parameters
    ------------
    x : numpy array
        sine(elevation angle)
    ofac: float
        oversamping factor
    hifac : float
        how far to calculate RH frequencies  (in meters)

    Returns
    ------------
    pd: float numpy arrays
        frequencies 

    """
#
# number of points in input array
    n=len(x)
#
# number of frequencies that will be used
    xmax = np.max(x) 
    xmin = np.min(x) 

    #print('ofac hifac,n,xmin,xmax', ofac,hifac,n,xmin,xmax)

    nout=int(0.5*ofac*hifac*n)
	 
    xdif=xmax-xmin 

    if xdif == 0:
        return []
    if nout == 0:
        return []
    if np.isnan(ofac ):
        return []

# starting frequency 
    pnow=1.0/(xdif*ofac) 
    pstart = pnow
    pstop = hifac*n/(2*xdif)
# 
# output arrays
#    px = np.zeros(nout)
#    for i in range(0,nout):
#        px[i]=pnow
#        pnow=pnow+1.0/(ofac*xdif)
# simpler way
    pd = np.linspace(pstart, pstop, nout)
    return pd

def find_satlist_wdate(f,snrExist,year,doy):
    """
    find satellite list for a given frequency and date

    Parameters
    ----------
    f : integer
        frequency
    snrExist : numpy array, bool
        tells you if a signal is (potentially) legal
    year : int
        full year
    doy : int
        day of year

    Returns
    -------
    satlist: numpy list of integers
        satellites to use

    june 24, 2021: updated for SVN78

    """
    # get list of relevant satellites
    l2c_sat, l5_sat = l2c_l5_list(year,doy)

    l1_sat = np.arange(1,33,1)
    satlist = []
    if f == 1:
        satlist = l1_sat
    if f == 20:
        satlist = l2c_sat
    if f == 2:
        satlist = l1_sat
    if f == 5:
        satlist = l5_sat
#   i do not think they have 26 - but ....
#   glonass L1
    if (f == 101) or (f==102):
# only have 24 frequencies defined
        satlist = np.arange(101,125,1)
#   galileo - 40 max?
#   use this to check for existence, mostly driven by whether there are
#   extra columns (or if they are non-zero)
    gfs = int(f-200)

    if (f >  200) and (f < 210) and (snrExist[gfs]):
        satlist = np.arange(201,241,1)
#   galileo has no L2 frequency, so set that always to zero
    if f == 202:
        satlist = []
#   pretend there are 32 Beidou satellites for now
    if (f > 300):
        satlist = np.arange(301,333,1)

    # minimize screen output
    #if len(satlist) == 0:
    #    print('     illegal frequency: no sat list being returned')
    return satlist



def glonass_channels(f,prn):
    """
    Retrieves appropriate wavelength for a given Glonass satellite

    Parameters
    ----------
    f : int
        frequency( 101 or 102)
    prn : int
        satellite number

    Returns
    -------
    l : float
        wavelength for glonass satellite in meters

    logic from Simon Williams 
    """
#   we define glonass by adding 100.  remove this for definition of the wavelength
    if (prn > 100):
        prn = prn - 100
    lightSpeed = 299792458
    slot = [14,15,10,20,19,13,12,1,6,5,22,23,24,16,4,8,3,7,2,18,21,9,17,11]
    channel = [-7,0,-7,2,3,-2,-1,1,-4,1,-3,3,2,-1,6,6,5,5,-4,-3,4,-2,4,0]
    slot = np.matrix(slot)
    channel = np.matrix(channel)
#   main frequencies
    L1 = 1602e6
    L2 = 1246e6
#   deltas
    dL1 = 0.5625e6
    dL2 = 0.4375e6

    ch = channel[(slot == prn)]
    ch = int(ch)
#   wavelengths in meters
#    print(prn,ch,f)
    l = 0.0
    if (f == 101):
        l = lightSpeed/(L1 + ch*dL1)
    if (f == 102):
        l = lightSpeed/(L2 + ch*dL2)
    return l

def open_outputfile(station,year,doy,extension):
    """
    opens an output file in 
    $REFL_CODE/year/results/station/extension directory
    for lomb scargle periodogram results

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    doy : int
        day of year
    extension : str
        analysis extension name (for storage of results)

    Returns
    -------
    fileID : ?
        I don't know the proper name of this - but what comes out
        when you open a file so you can keep writing to it

    """
    if os.path.isdir('logs'):
        skippingxist = True
    else:
        subprocess.call(['mkdir', 'logs'])
    fout = 0
#   primary reflector height output goes to this directory
    xdir = os.environ['REFL_CODE']
    cdoy = '{:03d}'.format(doy)
#   extra file with rejected arcs
    w = 'logs/reject.' + str(year) + '_' + cdoy  + station + '.txt'

    filedir = xdir + '/' + str(year)  + '/results/' + station 
#   changed to a function
    filepath1,fexit = LSPresult_name(station,year,doy,extension)
    #print('Output will go to:', filepath1)
    versionNumber = 'v' + str(version('gnssrefl'))
    #versionNumber = 'working-on-it'
    tem = '% station ' + station + ' https://github.com/kristinemlarson/gnssrefl ' + versionNumber  + '\n'
    try:
        fout=open(filepath1,'w+')
#       put a header in the output file
        fout.write(tem)
        fout.write("% Phase Center corrections have NOT been applied \n")
        fout.write("% year, doy, RH, sat,UTCtime, Azim, Amp,  eminO, emaxO,NumbOf,freq,rise,EdotF, PkNoise  DelT     MJD   refr-appl\n")
        fout.write("% (1)  (2)   (3) (4)  (5)     (6)   (7)    (8)    (9)   (10)  (11) (12) (13)    (14)     (15)    (16)   (17)\n")
        fout.write("%             m        hrs    deg   v/v    deg    deg  values            hrs               min         1 is yes  \n")
    except:
        print('problem on first attempt - so try making results directory')
        f1 = xdir + '/' + str(year) + '/results/'
        subprocess.call(['mkdir',f1])
        # os.system(cm)
        f2 = xdir + '/' + str(year) + '/results/' + station
        subprocess.call(['mkdir',f2])
        # os.system(cm)
        try:
            fout=open(filepath1,'w+')
            print('successful open')
        except:
            print('problems opening the file')
            sys.exit()
    frej = 100

    return fout, frej

def removeDC(dat,satNu, sat,ele, pele, azi,az1,az2,edot,seconds):
    """
    remove direct signal using given elevation angle (pele) and azimuth 
    (az1,az2) constraints, return x,y as primary used data and windowed
    azimuth, time, and edot
    removed zero points, which 10^0 have value 1.  used 5 to be sure?

    Parameters
    ----------
    dat : numpy array of floats 
        SNR data
    satNu : float
        requested satellite number
    sat : numpy array of floats
        satellite numbers
    ele : numpy array of floats
        elevation angles, deg
    pele : list of floats
        min and max elevation angles (deg)
    azi : numpy array of floats 
        azimuth angle, deg
    az1 : float
        minimum azimuth angle (deg)
    az2 : float
        maximum azimuth angle (deg)
    edot : numpy array of floats  
        derivative elevation angle (deg/sec)
    seconds : numpy array of floatas
        seconds of the day

    Returns
    -------
    x : numpy array of floats
        sine of elevation angle ( i believed)
    y : numpy array of floats
        SNR data in lineer units with DC component removed
    sat : ??
        not sure why  this is sent and returned
    azi : numpy array of flaots
        azimuth angles
    seconds : numpy array of flaots
        seconds of the day
    edot : numpy array of floats
        derivative of elevation angle

    """
    p1 = pele[0]; p2 = pele[1]
#   look for data within these azimuth and elevation angle constraints
    #ytest = dat[(sat == satNu)]
    #print(len(ytest))

    x = ele[(sat == satNu) & (ele > p1) & (ele < p2) & (azi > az1) & (azi < az2) & (dat > 5)]
    y = dat[(sat == satNu) & (ele > p1) & (ele < p2) & (azi > az1) & (azi < az2) & (dat > 5)]
    edot = edot[(sat == satNu) & (ele > p1) & (ele < p2) & (azi > az1) & (azi < az2) & (dat > 5)]
    seconds = seconds[(sat == satNu) & (ele > p1) & (ele < p2) & (azi > az1) & (azi < az2) & (dat > 5)]
    azi = azi[(sat == satNu) & (ele > p1) & (ele < p2) & (azi > az1) & (azi < az2) & (dat > 5)]

    return x,y,sat,azi,seconds,edot

def quick_plot(plt_screen, gj,station,pltname,f):
    """
    inputs plt_screen variable (1 means go ahead) and integer variable gj
    which if > 0 there is something to plot
    also station name for the title
    pltname is png filename, if requested
    """
    if (plt_screen == 1  and gj > 0):
        plt.subplot(212)
        plt.xlabel('Reflector height(m)')
        plt.ylabel('SNR Spectral Amplitude')
        plt.subplot(211)
        plt.title('Station:' + station + '/freq:' + str(f))
        plt.ylabel('SNR (volts/volts)')
        plt.xlabel('elevation angle(degrees)')
        if pltname != 'None':
            plt.savefig(pltname)
        else:
            print('plot file not saved ')
        plt.show()

def print_file_stats(ele,sat,s1,s2,s5,s6,s7,s8,e1,e2):
    """
    inputs 

    ele

    sat

    s1 

    s2 

    """
    gps = ele[(sat > 0) & (sat < 33) & (ele < e2) ]
    glonass = ele[(sat > 100) & (sat < 125) & (ele < e2) ]
    beidou = ele[(sat > 300) & (sat < 340) & (ele < e2) ]
    galileo = ele[(sat > 200) & (sat < 240) & (ele < e2) ]
    print('GPS     obs ', len(gps) )
    print('Glonass obs ', len(glonass))
    print('Galileo obs ', len(galileo))
    print('Beidou  obs ', len(beidou))

    return



def diffraction_correction(el_deg, temp=20.0, press=1013.25):
    """ 
    Computes and return the elevation correction for refraction in the atmosphere such that the elevation of the
    satellite plus the correction is the observed angle of incidence.

    Based on an empirical model by G.G. Bennet.
    This code was provided by Chalmers Group, Joakim Strandberg and Thomas Hobiger
    Bennett, G. G. The calculation of astronomical refraction in marine navigation.
    Journal of Navigation 35.02 (1982): 255-259.

    Parameters
    ----------
    el_deg : array_like
        A vector of true satellite elevations in degrees for which the correction is calculated.

    temp : float, optional
        Air temperature at ground level in degrees celsius, default 20 C.

    press : float, optional
        Air pressure at ground level in hPa, default 1013.25 hPa.

    Returns
    -------
    corr_el_deg : 1d-array
        The elevation correction in degrees.

    """
    el_deg = np.array(el_deg)

    corr_el_arc_min = 510/(9/5*temp + 492) * press/1010.16 * 1/np.tan(np.deg2rad(el_deg + 7.31/(el_deg + 4.4)))

    corr_el_deg = corr_el_arc_min/60

    return corr_el_deg


def fdoy2mjd(year,fdoy):
    """
    calculates modified julian day from year and fractional day of year

    Parameters
    ----------
    year : int
        full year

    fdoy : float
        fractional day of year

    Returns
    -------
    mjd : float
        modified julian day
    """
    doy = math.floor(fdoy)
    yy,mm,dd, cyyyy, cdoy, YMD = ydoy2useful(year,doy)
    fract_hour = 24*(fdoy - doy)

    mjd = getMJD(year,mm,dd,fract_hour)

    return mjd

def mjd(y,m,d,hour,minute,second):
    """
    calculate the integer part of MJD and the fractional part.

    Parameters
    ----------
    year : int
        full year
    month : int
        calendar month
    day : int
        calendar day
    hour : int
        hour of day
    minute : int
        minute of the day
    second : int
        second of the day

    Returns
    -------
    mjd : float
        modified julian day of y-m-d

    fracDay : float
        fractional day 

    using information from http://infohost.nmt.edu/~shipman/soft/sidereal/ims/web/MJD-fromDatetime.html
    """
    if  (m <= 2):
        y, m = y-1, m+12
    if ((y, m, d) >= (1582, 10, 15)):
        A = int(y / 100)
        B = 2 - A + int(A / 4)
    else:
        B = 0
    C = int(365.25 * y)
    D = int(30.6001 *(m + 1))
    mjd = B + C + D + d - 679006
#   calculate seconds
    s = hour*3600 + minute*60 + second
    fracDay = s/86400
    return mjd, fracDay

def mjd_to_datetime(mjd):
    """
    Parameters
    ----------
    mjd : float
        modified julian date

    Returns
    -------
    dt : datetime object

    """
    base_date=datetime.datetime(1858,11,17)
    delta=datetime.timedelta(days=mjd)
    dt = base_date+delta

    return dt


def doy2ymd(year, doy):
    """
    Parameters
    ----------
    year : int

    doy : int
        day of year

    Returns
    -------
    d : datetime object

    """

    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    #print('ymd',d)
    return d 

def getMJD(year,month,day,fract_hour):
    """
    Parameters
    ----------
    year : int

    month : int

    day : int

    fract_hour : float
        hour (fractional)

    Returns 
    -------
    mjd : float
        modified julian day

    """
#   convert fract_hour to HH MM SS
#   ignore fractional seconds for now
    hours = math.floor(fract_hour) 
    leftover = fract_hour - hours
    minutes = math.floor(leftover*60)
    seconds = math.floor(leftover*3600 - minutes*60)
#    print(fract_hour, hours, minutes, seconds)
    MJD, fracS = mjd(year,month,day,hours,minutes,seconds)
    MJD = MJD + fracS
    return MJD

def update_plot(plt_screen,x,y,px,pz):
    """
    is this used?

    plt_screen : int 
        1 means update the plot
    x : numpy array of floats 
        elevation angles (deg)
    y :  numpy array of floats
        SNR data, volts/volts
    px : numpy array of floats
        periodogram, x-axis (meters)
    pz : numpy array of floats 
        periodogram, y-axis

    """
    if (plt_screen == 1):
        plt.subplot(211)  
        plt.plot(x,y)
        #plt.title(station)
        plt.subplot(212)  
        plt.plot(px,pz)

def open_plot(plt_screen):
    """
    is this used?

    simple code to open a figure, called by gnssIR_lomb
    """
    if (plt_screen == 1):
        plt.figure()


def store_orbitfile(filename,year,orbtype):
    """
    Stores orbit files locally

    Parameters
    ----------
    filename : str
        orbit filename
    year : int 
        full year
    orbtype : str
        kind of orbit (nav or sp3)

    Returns
    -------
    xdir : str
        local directory where the orbit belongs

    """
    # parent directory of the orbits for that year
    xdir = os.environ['ORBITS'] + '/' + str(year)
    # check that directories exist
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    xdir = os.environ['ORBITS'] + '/' + str(year) + '/' + orbtype
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    if (os.path.isfile(filename) == True):
        #print('moving ', filename, ' to ', xdir)
        status = subprocess.call(['mv','-f', filename, xdir])
    else:
        print('The orbit file did not exist, so it was not stored')

    return xdir

def make_snrdir(year,station):
    """
    makes various directories needed for SNR file/analysis outputs

    Parameters
    ----------
    year : int
        full year
    station : str
        4 ch station name

    """
    xdir = os.environ['REFL_CODE'] + '/' + str(year)
    # check that directories exist
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    xdir = xdir + '/snr'
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    xdir = xdir + '/' + station 
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)

def store_snrfile(filename,year,station):
    """
    move an snr file to the right place 

    Parameters
    ----------
    filename  : str
        name of SNR file
    year : int
        full year
    station : str
        4 ch station name

    """
    xdir = os.environ['REFL_CODE'] + '/' + str(year)
    # check that directories exist
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    xdir = xdir + '/snr'
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    xdir = xdir + '/' + station 
    if not os.path.isdir(xdir): #if year folder doesn't exist, make it
        os.makedirs(xdir)
    if (os.path.isfile(filename) == True):
        status = subprocess.call(['mv','-f', filename, xdir])
    else:
        print('the SNR file does not exist, so nothing was moved')

def rinex_name(station, year, month, day):
    """
    Defines rinex 2.11 file name

    Parameters
    ---------
    station : str
        4 character station ID
    year : int
        full year
    month : int

    day : int 

    Returns
    -------
    fnameo : str
         RINEX 2.11 name

    fnamed : 
         RINEX 2.11 name, Hatanaka compressed

    """
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    fnameo = station + cdoy + '0.' + cyy + 'o'
    fnamed = station + cdoy + '0.' + cyy + 'd'

    return fnameo, fnamed

def snr_name(station, year, month, day,option):
    """
    Defines SNR filename

    Parameters
    --------
    station : str
        4 ch station name

    year : int

    month : int

    day : int

    option : int
        snr filename delimiter, i.e. 66

    Returns
    -------
    fname : string
        snr filename 
    """
    doy,cdoy,cyyy,cyy = ymd2doy(year,month,day)

    fname = station + cdoy + '0.' + cyy + '.snr' + str(option)

    return fname

def nav_name(year, month, day):
    """
    returns the name and location of the navigation file

    Parameters
    ----------
    year : integer

    month : integer

    day : integer

    Returns
    -------
    navfilename : str
        name of the navigation file

    navfiledir : str
        local directory where navigation file will be stored
    """
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    navfilename = 'auto'  + cdoy + '0.' + cyy  +  'n'
    navfiledir = os.environ['ORBITS'] + '/' + cyyyy + '/nav'

    return navfilename,navfiledir

def sp3_name(year,month,day,pCtr):
    """
    defines old-style sp3 name

    Parameters
    -------------
    year : int

    month : int

    day : int

    pCtr : str
        Orbit processing center

    Returns
    -------
    sp3name : str
        old-style (lowercase) IGS name for sp3 file
    sp3dir : str
        where file is stored locally

    """
    name,clkn=igsname(year,month,day)
    gps_week = name[3:7]
    sp3name = pCtr + name[3:8] + '.sp3'
    sp3dir = os.environ['ORBITS'] + '/' + str(year) + '/sp3'
    return sp3name, sp3dir


def rinex_unavco_highrate(station, year, month, day):
    """
    picks up a 1-Hz RINEX 2.11 file from unavco.  

    Parameters
    -------------
    station : str
        4 ch station name
    year : int

    month : intr

    day : int

    """
    #print('in rinex_unavco_highrate')
    crnxpath = hatanaka_version()
    # added this for people that submit doy instead of month and day
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    rinexfile,rinexfiled = rinex_name(station, year, month, day)

    #print('Using new unavco protocols')
    #unavco = 'https://data-idm.unavco.org/archive/gnss/highrate/1-Hz/rinex/' 
    unavco = 'https://data.unavco.org/archive/gnss/highrate/1-Hz/rinex/'


    filename1 = rinexfile + '.Z'
    filename2 = rinexfiled + '.Z'
    url1 = unavco+  cyyyy + '/' + cdoy + '/' + station + '/' + filename1
    url2 = unavco+  cyyyy + '/' + cdoy + '/' + station + '/' + filename2
    #print(url1)
    #print(url2)

    # hatanaka executable has to exist
    s1 = time.time()
    if os.path.isfile(crnxpath): 
        #print('try', url2, filename2)

        try:
            #wget.download(url2,filename2) old way
            foundit,file_name = kelly.the_kelly_simple_way(url2,filename2)
            if foundit:
                subprocess.call(['uncompress',filename2])
                subprocess.call([crnxpath, rinexfiled])
                subprocess.call(['rm','-f',rinexfiled])
        except:
            okok = 1
    if not os.path.isfile(rinexfile):
        #print('Did not find Hatanaka. Try for obs file')
        #print('try', url1, filename1)
        try:
            #wget.download(url1,filename1) old way
            foundit,file_name = kelly.the_kelly_simple_way(url1,filename1)
            if foundit:
                subprocess.call(['uncompress',filename1])
        except:
            okok = 1
    s2 = time.time()
    print('That download experience took ', int(s2-s1), ' seconds.')


def ydoy2ymd(year, doy):
    """
    inputs: year and day of year (doy)
    returns: year, month, day
    """

    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    month = int(d.month)
    day = int(d.day)
    return year, month, day

def rewrite_UNR_highrate(fname,station,year,doy):
    """
    takes a filename from was already retrieved? from 
    UNReno, reads it, rewrites as all numbers for other uses.
    no header, but year, month, day, day of year, seconds vertical, east, north
    the latter three are in meters
    stores in $REFL_CODE/yyyy/pos/station
    """
# make sure the various output directories  are there
    xdir = os.environ['REFL_CODE'] 
    dir1 = xdir + '/' + str(year)
    if not os.path.isdir(dir1):
        status = subprocess.call(['mkdir', dir1])

    dir1 = xdir + '/' + str(year) + '/' + 'pos'
    if not os.path.isdir(dir1):
        status = subprocess.call(['mkdir', dir1])

    dir1 = xdir + '/' + str(year) + '/' + 'pos' + '/' + station
#   make filename for the output
    yy,mm,dd, cyyyy, cdoy, YMD = ydoy2useful(year,doy)
    outputfile = dir1 + '/' + cdoy + '_hr.txt'
    print('file will go to: ' , outputfile)
    if not os.path.isdir(dir1):
        print('use subprocess to make directory')
        status = subprocess.call(['mkdir', dir1])
    try:
        x=np.genfromtxt(fname, skip_header=1, usecols = (3, 4, 5, 6, 7, 8, 9, 10))
        N = len(x)
        print('open outputfile',outputfile)
        f=open(outputfile,'w+')
        for i in range(0,N):
            f.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:3.0f} {4:7.0f} {5:9.4f} {6:9.4f} {7:9.4f} \n".format(x[i,0], x[i,1],x[i,2],x[i,3], x[i,4],x[i,5],x[i,6],x[i,7]))
        print('delete the original Blewitt file')
        subprocess.call(['rm','-f', fname])
        f.close()
    except:
        print('problem with accessing the file')

def month_converter(month):
    """
    brendan gave this to me - give it a 3 char month, returns integer
    """
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    return months.index(month) + 1

def char_month_converter(month):
    """
    integer month to 3 character month

    Parameters 
    ----------
    month : int
        integer month (1-12)

    Returns 
    ----------
    month : str
        three char month, uppercase

    """
    months = ['JAN', 'FEB', 'MAR', 'APR', 'MAY', 'JUN', 'JUL', 'AUG', 'SEP', 'OCT', 'NOV', 'DEC']
    return months[(month-1)]

def UNR_highrate(station,year,doy):
    """
    picks up the 5 minute time series from UNR website for a given station

    Parameters
    ----------
    station : str
        4 character station name
    year : int
        full year
    doy : int
        day of year

    Returns
    -------
    filename : str
        output filename
    goodDownload : bool
        whether your download was successful

    """
    yy,mm,dd, cyyyy, cdoy, YMD = ydoy2useful(year,doy)
    stationUP = station.upper()
    dirdir = 'ftp://gneiss.nbmg.unr.edu/rapids_5min/kenv/' + cyyyy + '/' + cdoy + '/'
    filename = YMD + station.upper() + '_fix.kenv'
    url = dirdir + filename
    if (os.path.isfile(filename) == True):
        print('file already exists')
        goodDownload = True
    else:
        try:
            wget.download(url,filename)
            goodDownload = True
        except:
            print(url)
            print('could not get the highrate file from UNR')
            goodDownload = False
    return filename, goodDownload

def mjd_to_date(jd):
    """
    https://gist.github.com/jiffyclub/1294443

    Converts Modified Julian Day to y,m,d
    
    Algorithm from Practical Astronomy with your Calculator or Spreadsheet 
        4th ed., Duffet-Smith and Zwart, 2011.
    
    Parameters
    ----------
    jd : float
        Julian Day
        
    Returns
    -------
    year : int
        Year as integer. Years preceding 1 A.D. should be 0 or negative.
        The year before 1 A.D. is 0, 10 B.C. is year -9.
        
    month : int
        Month as integer, Jan = 1, Feb. = 2, etc.
    
    day : float
        Day, may contain fractional part.
        
    
    """
   # first step is to change MJD to jd, since original code expected it 
    jd = jd + 2400000.5
    # start of the original code
    jd = jd + 0.5
    
    F, I = math.modf(jd)
    I = int(I)
    
    A = math.trunc((I - 1867216.25)/36524.25)
    
    if I > 2299160:
        B = I + 1 + A - math.trunc(A / 4.)
    else:
        B = I
        
    C = B + 1524
    
    D = math.trunc((C - 122.1) / 365.25)
    
    E = math.trunc(365.25 * D)
    
    G = math.trunc((C - E) / 30.6001)
    
    day = C - E + F - math.trunc(30.6001 * G)
    
    if G < 13.5:
        month = G - 1
    else:
        month = G - 13
        
    if month > 2.5:
        year = D - 4716
    else:
        year = D - 4715
        
    day = int(day)
    return year, month, day

def getseries(site):
    """
    originally from brendan crowell.
    picks up two UNR time series - stores in subdirectory called tseries 
    input is station name (four character, lower case)
    """
    # i changed this to download ENV instead of XYZ (or both?)
    #if tseries folder doesn't exist, make it
    if not os.path.exists('tseries'): 
        os.makedirs('tseries')
    # change station to uppercase
    siteid = site.upper()
    # why still ITRF 2008?
    fname = 'tseries/' + siteid + '.IGS08.tenv3'
    # NA12 env time series
    fname2 = 'tseries/' + siteid + '.NA12.tenv3'
    # NA12 env rapid time series
    fname3 = 'tseries/' + siteid + '.NA12.rapid.tenv3'

    if (os.path.isfile(fname) ):
        print ('Timeseries file ' + fname + ' already exists')
    else:
        url = 'http://geodesy.unr.edu/gps_timeseries/tenv3/IGS08/' + siteid + '.IGS08.tenv3'
        wget.download(url, out='tseries/')
#
    if (os.path.isfile(fname2)):
        print ('Timeseries file ' + fname2 + ' already exists')
    else:
        url = 'http://geodesy.unr.edu/gps_timeseries/tenv3/NA12/' + siteid + '.NA12.tenv3'
        wget.download(url, out='tseries/')

    if (os.path.isfile(fname3)):
        print ('Timeseries file ' + fname3 + ' already exists')
    else:
        url = 'http://geodesy.unr.edu/gps_timeseries/rapids/tenv3/NA12/' + siteid + '.NA12.tenv3'
        wget.download(url, out=fname3)

def rewrite_tseries(station):
    """
    given a station name, look at a daily blewitt position (ENV) 
    file and write a new file that is more human friendly

    Parameters
    ----------
    station : str
        4 character station name
    """
    siteid = station.upper()
    # NA12 env time series
    fname = 'tseries/' + siteid + '.NA12.tenv3'
    fname_rapid = 'tseries/' + siteid + '.NA12.rapid.tenv3'
    outputfile = 'tseries/' + station+ '_na12.env'
    print(fname,outputfile)
    try:
        x=np.genfromtxt(fname, skip_header=1, usecols = (3, 7, 8, 9, 10, 11, 12,13))
        N = len(x)
        print(N,'open outputfile',outputfile)
        f=open(outputfile,'w+')
        for i in range(0,N):
            mjd = x[i,0]
            yy,mm,dd = mjd_to_date(mjd) 
            doy, cdoy, cyyyy, cyy = ymd2doy(yy,mm,dd)
            east = x[i,1] + x[i,2]
            north= x[i,3] + x[i,4]
            # adding in the antenna
            vert = x[i,5] + x[i,6] +  x[i,7]
            f.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:3.0f} {4:13.4f} {5:13.4f} {6:13.4f} \n".format(yy,mm,dd,doy,east,north,vert))
        f.close()
    except:
        print('some problem writing the new output file')

def rewrite_tseries_igs(station):
    """
    given a station name, look at a daily blewitt position (ENV)
    file and write a new file that is less insane to understand
    """
    siteid = station.upper()
    # NA12 env time series
    fname = 'tseries/' + siteid + '.IGS08.tenv3'
    outputfile = 'tseries/' + station + '_igs08.env'
    print(fname,outputfile)
    try:
        x=np.genfromtxt(fname, skip_header=1, usecols = (3, 7, 8, 9, 10, 11, 12,13))
        N = len(x)
        print(N)
        print(N,'open outputfile',outputfile)
        f=open(outputfile,'w+')
        for i in range(0,N):
            mjd = x[i,0]
            yy,mm,dd = mjd_to_date(mjd)
            doy, cdoy, cyyyy, cyy = ymd2doy(yy,mm,dd)
            east = x[i,1] + x[i,2]
            north= x[i,3] + x[i,4]
            # adding in the antenna
            vert = x[i,5] + x[i,6] +  x[i,7]
            f.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:3.0f} {4:13.4f} {5:13.4f} {6:13.4f} \n".format(yy,mm,dd,doy,east,north,vert))
        f.close()
    except:
        print('some problem writing the output')


def llh2xyz(lat,lon,height):
    """
    converts llh to Cartesian values

    Parameters
    -----------
    lat : float
        latitude in degrees

    lon : float
        longitude in degrees

    height : float
        ellipsoidal height in meters

    Returns
    -------
    x : float
        X coordinate (m)

    y : float
        Y coordinate (m)

    z : float
        Z coordinate (m)

    Ref: Decker, B. L., World Geodetic System 1984,
    Defense Mapping Agency Aerospace Center.
    modified from matlab version kindly provided by CCAR
    """
    A_EARTH = 6378137;
    f= 1/298.257223563;
    NAV_E2 = (2-f)*f; # also e^2
    deg2rad = math.pi/180.0
    if ((lat+lon+height) == 0):
        print('You have entered all zero values')
        x=0; y=0; z=0
    else:
        slat = math.sin(lat*deg2rad);
        clat = math.cos(lat*deg2rad);
        r_n = A_EARTH/(math.sqrt(1 - NAV_E2*slat*slat))
        x= (r_n + height)*clat*math.cos(lon*deg2rad)
        y= (r_n + height)*clat*math.sin(lon*deg2rad)
        z= (r_n*(1 - NAV_E2) + height)*slat

    return x, y, z

def LSPresult_name(station,year,doy,extension):
    """
    makes name for the Lomb Scargle output

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    doy : int
        day of year
    extension : str
        name of subdirectory for results

    Returns
    -------
    filepath1 : str
        where Lomb Scargle output goes
    fileexists : bool
        whether output already exists

    """
    # for testing
    xdir = os.environ['REFL_CODE']
    cyear = str(year)
    cdoy = '{:03d}'.format(doy)
    # this is default location where the results will go
    filedir = xdir + '/' + cyear  + '/results/' + station
    # this is now also done in the result_directories function,
    # but I guess no harm is done
    if not os.path.isdir(filedir):
        #print('making new results bdirectory ')
        subprocess.call(['mkdir', filedir])
    filedirx = filedir + '/' + extension
    # this is what you do if there is an extension
    if not os.path.isdir(filedirx):
        #print('making new results subdirectory ')
        subprocess.call(['mkdir', filedirx])

    filepath1 =  filedirx + '/' + cdoy  + '.txt'

    if os.path.isfile(filepath1):
        fileexists = True
    else:
        fileexists = False

    return filepath1, fileexists

def result_directories(station,year,extension):
    """
    Creates directories for results

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    extension : str
        subdirectory for results (used for analysis strategy)

    """
    xdir = os.environ['REFL_CODE']
    cyear = str(year)

    f1 = xdir + '/' + cyear
    if not os.path.isdir(f1):
        subprocess.call(['mkdir',f1])

    f1 = f1 + '/results'
    if not os.path.isdir(f1):
        subprocess.call(['mkdir',f1])


    f1 = f1 + '/' + station
    if not os.path.isdir(f1):
        subprocess.call(['mkdir',f1])

    if (extension != ''):
        f1 = f1 + '/' + extension
        if not os.path.isdir(f1):
            subprocess.call(['mkdir',f1])

    f1 = xdir + '/' + cyear + '/phase'
    if not os.path.isdir(f1):
        subprocess.call(['mkdir',f1])

    f1 = f1 + '/' + station
    if not os.path.isdir(f1):
        subprocess.call(['mkdir',f1])

def write_QC_fails(delT,delTmax,eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,reqamp,tooclose2edge):
    """
    prints out various QC fails to the screen

    Parameters
    ----------
    delT : float
        how long the satellite arc is (minutes)
    delTmax : float
        max satellite arc allowed (minutes)
    eminObs: float
        minimum observed elev angle (Deg)
    emaxObs : float
        maximum observed elev angle (Deg)
    e1 : float
        minimum allowed elev angle (deg)
    e2 : float
        maximum allowed elev angle (deg)
    ediff : float
        allowed min/max elevation diff from obs min/max elev angle (deg) 
    maxAmp : float
        measured peak LSP 
    Noise : float
        measured noise value for the periodogram
    PkNoise : float
        required peak to noise
    reqamp : float
        require peak LSP
    tooclose2edge : bool
        wehther peak value is too close to begining or ending of the RH constraints

    """
    print('delT,delTmax,eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,reqamp,tooclose2edge')
    print(delT,delTmax,eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,reqamp,tooclose2edge)
    if tooclose2edge:
        print('     Retrieved reflector height too close to the edge of the RH space')

    if delT >= delTmax:
        print('     Obs delT {0:.3f} minutes vs {1:.1f} requested limit '.format(delT,delTmax ))
    if eminObs  > (e1 + ediff):
        print('     Obs emin {0:.1f} is higher than {1:.1f} +- {2:.1f} degrees '.format(eminObs, e1, ediff ))
    if emaxObs  < (e2 - ediff):
        print('     Obs emax {0:.1f} is lower than {1:.1f} +- {2:.1f} degrees'.format(emaxObs, e2, ediff ))
    if maxAmp < reqamp:
        print('     Obs Ampl {0:.1f} vs {1:.1f} required '.format(maxAmp,reqamp  ))
    if maxAmp/Noise < PkNoise:
        print('     Obs PkN  {0:.1f} vs {1:.1f} required'.format(maxAmp/Noise, PkNoise ))
        
def define_quick_filename(station,year,doy,snr):
    """
    defines SNR File name

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    doy : int
        day of year
    snr : int
        snr file type (66,88, etc)

    Returns 
    -------
    f : str
        SNR filename

    """
    cyyyy, cyy, cdoy = ydoych(year,doy)
    f= station + str(cdoy) + '0.' + cyy + '.snr' + str(snr)
    return f

def update_quick_plot(station, f):
    """
    updates plot in quickLook

    Parameters
    ----------
    station : str
        4 ch name
    f : int
        frequency
    """
    plt.subplot(212)
    plt.xlabel('reflector height (m)'); plt.title('SNR periodogram')
    plt.subplot(211)
    plt.xlabel('elev Angles (deg)')
    plt.title(station + ' SNR Data/' + ftitle(f) + ' Frequency') 

    return True

def navfile_retrieve(navfile,cyyyy,cyy,cdoy):
    """
    retrieves navfile from either SOPAC or CDDIS

    Parameters 
    ----------
    navfile : str
        name of the broadcast orbit file
    cyyyy :  str
        4 character yaer
    cyy : string
        2 character year
    cdoy : str
        3 character day of year

    Returns
    -------
    FileExists : bool
        whether the file was found

    """
    navname = navfile
    FileExists = False
    xx=get_sopac_navfile(navfile,cyyyy,cyy,cdoy) 
    
    cddis_is_failing = False
    if not os.path.isfile(navfile) :
        if not cddis_is_failing:
            print('SOPAC download did not work, so will try CDDIS')
            get_cddis_navfile(navfile,cyyyy,cyy,cdoy) 
        else:
            print('CDDIS is unreliable and is being blocked by us')
    else:
        print('found nav file at SOPAC')

    if os.path.isfile(navfile):
        FileExists = True
    else:
        FileExists = False

    return FileExists

def make_nav_dirs(yyyy):
    """
    input year and it makes sure output directories are created for orbits

    Parameters
    ----------
    yyyy : int
        year
    """
    n = os.environ['ORBITS']
    # if parent nav dir does not exist, exit
    if not os.path.isdir(n):
        print('You have not defined ORBITS environment variable properly. Exiting')
        print(n)
        sys.exit()
    cyyyy = '{:04d}'.format(yyyy)
    navfiledir = os.environ['ORBITS'] + '/' + cyyyy 
    if not os.path.exists(navfiledir):
        subprocess.call(['mkdir',navfiledir])
        #print('making year directory')
    navfiledir1 = os.environ['ORBITS'] + '/' + cyyyy + '/nav' 
    if not os.path.exists(navfiledir1):
        subprocess.call(['mkdir',navfiledir1])
        #print('making nav specific directory')
    navfiledir2 = os.environ['ORBITS'] + '/' + cyyyy + '/sp3'
    if not os.path.exists(navfiledir2):
        #print('making sp3 specific directory')
        subprocess.call(['mkdir',navfiledir2])

    return True


def check_inputs(station,year,doy,snr_type):
    """
    inputs to Lomb Scargle and Rinex translation codes
    are checked for sensibility. Returns true or false to 
    code can exit. 

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    doy : int
        day of year
    snr_type : int
        snr file type (e.g. 66)

    Returns
    -------
    exitSys : bool
        whether fatal error is trigger by a bad choice 

    """
    exitSys = False
    if len(station) != 4:
        print('Station name must be four characters. Exiting')
        exitSys = True

    if len(str(year)) != 4:
        print('Year must be four characters. Exiting')
        exitSys = True

    if (doy < 1) or (doy > 366):
        print('Day of year must be bewteen 1 and 366. Exiting')
        exitSys = True

    s = snr_type
    if (s == 99) or (s == 50) or (s==66) or (s==88) or (s==77):
        okokok = 1
        #print('You have picked a proper SNR file format ending.' )
    else:
        print('You have picked an improper SNR file format ending: ' + str(s))
        print('Allowed values are 99, 66, 88, 77, or 50. Exiting')
        exitSys = True

    return exitSys


def rewrite_tseries_wrapids(station):
    """
    given a station name, look at a daily blewitt position (ENV)
    file and write a new file that is less insane to understand
    """
    siteid = station.upper()
    # NA12 env time series
    fname = 'tseries/' + siteid + '.NA12.tenv3'
    fname_rapid = 'tseries/' + siteid + '.NA12.rapid.tenv3'
    outputfile = 'tseries/' + station+ '_na12.env'
    print(fname,outputfile)
    try:
        x=np.genfromtxt(fname, skip_header=1, usecols = (3, 7, 8, 9, 10, 11, 12,13))
        y=np.genfromtxt(fname_rapid, skip_header=1, usecols = (3, 7, 8, 9, 10, 11, 12,13))
        N = len(x)
        N2 = len(y)
        print(N,'open outputfile',outputfile)
        f=open(outputfile,'w+')
        for i in range(0,N):
            mjd = x[i,0]
            yy,mm,dd = mjd_to_date(mjd)
            doy, cdoy, cyyyy, cyy = ymd2doy(yy,mm,dd)
            east = x[i,1] + x[i,2]
            north= x[i,3] + x[i,4]
            # adding in the antenna
            vert = x[i,5] + x[i,6] +  x[i,7]
            f.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:3.0f} {4:13.4f} {5:13.4f} {6:13.4f} \n".format(yy,mm,dd,doy,east,north,vert))
# write out the rapid numbers
        for i in range(0,N2):
            mjd = y[i,0]
            yy,mm,dd = mjd_to_date(mjd)
            doy, cdoy, cyyyy, cyy = ymd2doy(yy,mm,dd)
            east = y[i,1] + y[i,2]
            north= y[i,3] + y[i,4]
            # adding in the antenna
            vert = y[i,5] + y[i,6] +  y[i,7]
            f.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:3.0f} {4:13.4f} {5:13.4f} {6:13.4f} \n".format(yy,mm,dd,doy,east,north,vert))
#  then close it
        f.close()
    except:
        print('some problem writing the output')

def back2thefuture(iyear, idoy):
    """
    code checks that this is not a day in the future
    also rejects data before the year 2000

    Parameters
    ----------
    iyear : int
        full year
    idoy : int
        day of year

    Returns
    -------
    badDay : bool
        whether your day exists (yet)

    """
    # find out today's date
    year = int(date.today().strftime("%Y"));
    month = int(date.today().strftime("%m"));
    day = int(date.today().strftime("%d"));

    today=datetime.datetime(year,month,day)
    doy = (today - datetime.datetime(today.year, 1, 1)).days + 1

    badDay = False
    if (iyear > year):
        badDay = True
    elif (iyear == year) & (idoy >= doy):
        badDay = True
    elif (iyear < 2000):
        badDay = True

    return badDay


def rinex_ga_highrate(station, year, month, day):
    """
    no longer supported - 

    Parameters
    ----------
    station : str
        4 character station ID, lowercase
    year : int
        full year
    month : int
        calendar month
    day : integer
        day of the month

    """
    crnxpath = hatanaka_version()
    teqcpath = teqc_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)

    GAstopday = 2020 + 196/365.25 # date i got the email saing they weren't going to have v2.11 anymore 
    if (year + doy/365.25) > GAstopday:
        print('GA no longer provides high-rate v 2.11 RINEX files')
        print('If there is significant interest, I will try to port this function over to RINEX 3')
        return
    # old directory
    #gns = 'ftp://ftp.ga.gov.au/geodesy-outgoing/gnss/data/highrate/' + cyyyy + '/' + cyy + cdoy 
    if not os.path.isfile(teqcpath):
        print('You need to install teqc to use high-rate RINEX data from GA.')
        return

    gns = 'ftp://ftp.data.gnss.ga.gov.au/highrate/' + cyyyy + '/' + cdoy + '/'
    print('WARNING: Downloading high-rate GPS data takes a long time.')
    fileF = 0
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            dname = station + cdoy + alpha[h] + e + '.' + cyy + 'd.gz'
            dname1 = station + cdoy + alpha[h] + e + '.' + cyy + 'd'
            dname2 = station + cdoy + alpha[h] + e + '.' + cyy + 'o'
            url = gns + '/' + ch + '/' + dname
            #print(url)
            try:
                wget.download(url,dname)
                subprocess.call(['gunzip',dname])
                subprocess.call([crnxpath, dname1])
                # delete the d file
                subprocess.call(['rm',dname1])
                fileF = fileF + 1
            except:
                okok = 1
                #print('download failed for some reason')

    # you cannot merge things that do not exist
    if (fileF > 0):
        foutname = 'tmp.' + station + cdoy
        rinexname = station + cdoy + '0.' + cyy + 'o'
        print('merge the 15 minute files and move to ', rinexname)
        mergecommand = [teqcpath + ' +quiet ' + station + cdoy + '*o']
        fout = open(foutname,'w')
        subprocess.call(mergecommand,stdout=fout,shell=True)
        fout.close()
        cm = 'rm ' + station + cdoy + '*o'
        print(cm)
        # if the output is made (though I guess this does not check to see if it is empty)
        if os.path.isfile(foutname):
            # try to remove the 15 minute files
            subprocess.call(cm,shell=True)
            subprocess.call(['mv',foutname,rinexname])
    else:
        print('No files were available for you from GA.')


def highrate_nz(station, year, month, day):
    """
    NO LONGER SUPPORTED 
    picks up a high-rate RINEX 2.11 file from GNS New zealand
    requires teqc to convert/merge the files

    Parameters
    ----------
    station : str
        station name
    year : int
        full year
    month :  int
        month or day of year
    day : int
        day or zero

    """
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    #gns = 'ftp://ftp.geonet.org.nz/gnss/event.highrate/1hz/raw/' + cyyyy +'/' + cdoy + '/'
    gns = 'https://data.geonet.org.nz/gnss/event.highrate/1hz/raw/' + cyyyy +'/' + cdoy + '/'
    print(gns)
    stationU=station.upper()
    # will not work for all days but life is short
    cmm  = '{:02d}'.format(month)
    cdd  = '{:02d}'.format(day)
    exedir = os.environ['EXE']
    trimbleexe = exedir + '/runpkr00' 
    #teqc = exedir + '/teqc' 
    teqc = teqc_version()
    if not os.path.exists(teqc):
        print('teqc executable does not exist. Exiting')
        print('This could be replaced with gfzrnx. Please submitting a pull request.')
        sys.exit()
         
    for h in range(0,24):
        # subdirectory
        chh = '{:02d}'.format(h)
        file1= stationU + cyyyy + cmm + cdd  + chh + '00b.T02'
        file1out= stationU + cyyyy + cmm + cdd  + chh + '00b.tgd'
        file2= stationU + cyyyy + cmm + cdd  + chh + '00b.rnx'
        url = gns + file1
        try:
            wget.download(url,file1)
            subprocess.call([trimbleexe, '-g','-d',file1])
            print(file1out, file2)
            f = open(file2, 'w')
            subprocess.call([teqc, '-week', '2083', '-O.obs', 'S1+S2+C2+L2', file1out], stdout=f)
            f.close()
            print('successful download from GeoNet New Zealand')
        except:
            print('some kind of problem with download',file1)


def get_orbits_setexe(year,month,day,orbtype,fortran):
    """
    picks up and stores orbits as needed.
    It also sets executable location for translation (gpsonly vs multignss)

    Parameters
    ----------
    year : int
        full year
    month : int
        calendar month
    day : int
        calendar day
    orbtype : str
        orbit source, e.g. nav, gps...
    fortran : bool
        whether you are using fortran code for translation

    Returns
    -------
    foundit : bool
        whether orbit file was found
    f : str
        name of the orbit file
    orbdir : str
        location of the orbit file
    snrexe : str 
        location of SNR executable. only relevant for fortran users

    """
    #default values
    # if they ask for gnss or gnss3, always use rapid.
    # at least for years 2022 and after
    #if year >= 2022:
    #    if (orbtype == 'gnss') or (orbtype == 'gnss3'):
    #        orbtype = 'rapid'
        #if orbtype == 'gbm':
        #    orbtype = 'rapid'

    foundit = False
    f=''; orbdir=''
    # define directory for the conversion executables
    exedir = os.environ['EXE']
    if (orbtype == 'grg'):
        # French multi gnss, but there are no Beidou results
        f,orbdir,foundit=getsp3file_mgex(year,month,day,'grg')
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'gfr'):
        f,orbdir,foundit=rapid_gfz_orbits(year,month,day)
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'rapid'):
        f,orbdir,foundit=rapid_gfz_orbits(year,month,day)
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'gnss3') or (orbtype == 'gnss-gfz'):
        f,orbdir,foundit=gbm_orbits_direct(year,month,day)
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'sp3'):
        #print('uses default IGS orbits, so only GPS ?')
        f,orbdir,foundit=getsp3file_flex(year,month,day,'igs')
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'gfz'):
        print('using Final gfz sp3 file, GPS and GLONASS') # though I advocate gbm
        f,orbdir,foundit=getsp3file_flex(year,month,day,'gfz')
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'igr'):
        print('using rapid IGS orbits, so only GPS')
        f,orbdir,foundit=getsp3file_flex(year,month,day,'igr') # use default
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'igs'):
        print('using IGS final orbits, so only GPS')
        f,orbdir,foundit=getsp3file_flex(year,month,day,'igs') # use default
        snrexe = gnssSNR_version(); warn_and_exit(snrexe,fortran)
    elif (orbtype == 'gbm'):
        # this uses GFZ multi-GNSS and is rapid, but not super rapid - but from CDDIS ... 
        # having it look first at GFZ for this file, which has a different name
        f,orbdir,foundit=getsp3file_mgex(year,month,day,'gbm')
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'wum'):
        # this uses WUHAN multi-GNSS which is ultra, but is not rapid ??
        # but only hour 00:00
        f,orbdir,foundit=getsp3file_mgex(year,month,day,'wum')
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif (orbtype == 'wum2'):
        # Wuhan ultra-rapid orbit from the Wuhan FTP
        # but only hour 00:00
        f,orbdir,foundit=get_wuhan_orbits(year,month,day)
        snrexe = gnssSNR_version() ; warn_and_exit(snrexe,fortran)
    elif orbtype == 'jax':
        # this uses JAXA, has GPS and GLONASS and appears to be quick and reliable
        f,orbdir,foundit=getsp3file_mgex(year,month,day,'jax')
        snrexe = gnssSNR_version(); warn_and_exit(snrexe,fortran)
    # added iwth help of Makan Karegar 
    elif orbtype == 'esa':
        # this uses ESA, GPS+GLONASS available from Aug 6, 2006 (added by Makan)
        f,orbdir,foundit=getsp3file_flex(year,month,day,'esa')
        snrexe = gnssSNR_version(); 
        warn_and_exit(snrexe,fortran)
    elif orbtype == 'test':
        # i can't even remember this ... 
        print('getting gFZ orbits from CDDIS using test protocol')
        f,orbdir,foundit=getnavfile(year, month, day) # use default version, which is gps only
        snrexe = gnssSNR_version(); warn_and_exit(snrexe,fortran)
    elif orbtype == 'ultra':
        print('getting ultra rapid orbits from GFZ local machine')
        f, orbdir, foundit = ultra_gfz_orbits(year,month,day,0)
        snrexe = gnssSNR_version(); warn_and_exit(snrexe,fortran)
    else:
        if ('nav' in orbtype):
            print('Requested a GPS only nav file')
            if orbtype == 'nav':
                f,orbdir,foundit=getnavfile(year, month, day) # use default version, which is gps only
                snrexe = gpsSNR_version() ; warn_and_exit(snrexe,fortran)
            if orbtype == 'nav-sopac':
                f,orbdir,foundit=getnavfile_archive(year, month, day,'sopac') # use default version, which is gps only
                snrexe = gpsSNR_version() ; warn_and_exit(snrexe,fortran)
            if orbtype == 'nav-cddis':
                f,orbdir,foundit=getnavfile_archive(year, month, day,'cddis') # use default version, which is gps only
                snrexe = gpsSNR_version() ; warn_and_exit(snrexe,fortran)
            if orbtype == 'nav-esa':
                f,orbdir,foundit=getnavfile_archive(year, month, day,'esa') # use default version, which is gps only
                snrexe = gpsSNR_version() ; warn_and_exit(snrexe,fortran)
        else:
            print('I do not recognize the orbit type you tried to use: ', orbtype)

    return foundit, f, orbdir, snrexe

def warn_and_exit(snrexe,fortran):
    """
    if the GNSS/GPS to SNR executable does not exist, exit

    Parameters
    ----------
    snrexe : str
        name of the executable
    fortran : bool
        whether fortran is being used for translation
    """
    if not fortran:
        ok = 1
        #print('not using fortran, so it does not matter if translation exe exists')
    else:
        #print('you are using fortran, so good to check now if translation exe exists')
        if (os.path.isfile(snrexe) == False):
            print('This RINEX translation executable does not exist:' + snrexe )
            print('Install it or use -fortran False. Exiting')
            sys.exit()

def new_rinex3_rinex2(r3_filename,r2_filename,dec=1,gpsonly=False):
    """
    This code translates a RINEX 3 file into a RINEX 2.11 file.
    It is assumed that the gfzrnx exists and that the RINEX 3 file is 
    Hatanaka uncompressed or compressed.

    Parameters
    ----------
    r3_filename : str
         RINEX 3 format filename. Either Hatanaka 
         compressed or uncompressed allowed
    r2_filename : str
         RINEX 2.11 file
    dec : integer
        decimation factor. If 0 or 1, no decimation is done.
    gpsonly : bool
        whether you want only GPS signals. Default is false

    Returns
    -------
    fexists : bool
        whether the RINEX 2.11 file was created and exists

    """
    fexists = False
    gexe = gfz_version()
    crnxpath = hatanaka_version()
    #lastbit =  r3_filename[-6:]
    if r3_filename[-3:] == 'crx':
        if not os.path.exists(crnxpath):
            print('You need to install Hatanaka translator. Exiting.')
            sys.exit()
        r3_filename_new = r3_filename[0:35] + 'rnx'
        s1=time.time()
        print('Converting to Hatanaka compressed to uncompressed')
        subprocess.call([crnxpath, r3_filename])
        s2=time.time()
        print(round(s2-s1,2), ' seconds')
        # removing the compressed version - will keep new version
        subprocess.call(['rm', '-f', r3_filename ])
        # now swap name
        r3_filename = r3_filename_new
    gobblygook = myfavoriteobs()
    gobblygook_gps = myfavoritegpsobs()
    #print('decimate value: ', dec)
    if not os.path.exists(gexe):
        print('gfzrnx executable does not exist and this file cannot be translated')
    else:
        s1=time.time()
        if os.path.isfile(r3_filename):
            try:
                if (dec == 1) or (dec == 0):
                    if (gpsonly):
                        subprocess.call([gexe,'-finp', r3_filename, '-fout', r2_filename, '-vo','2','-ot', gobblygook_gps, '-f','-q'])
                    else:
                        subprocess.call([gexe,'-finp', r3_filename, '-fout', r2_filename, '-vo','2','-ot', gobblygook, '-f','-q'])
                    #'-sei','out','-smp',crate
                else:
                    crate = str(dec)
                   #subprocess.call([gfzpath,'-finp', searchpath, '-fout', tmpname, '-vo',str(version),'-sei','out','-smp',crate,'-f','-q'])

                    if (gpsonly):
                        subprocess.call([gexe,'-finp', r3_filename, '-fout', r2_filename, '-vo','2','-ot', gobblygook_gps, '-sei','out','-smp', crate, '-f','-q'])
                    else:
                        subprocess.call([gexe,'-finp', r3_filename, '-fout', r2_filename, '-vo','2','-ot', gobblygook, '-sei','out','-smp', crate, '-f','-q'])
                if os.path.exists(r2_filename):
                    #print('Look for the rinex 2.11 file here: ', r2_filename)
                    fexists = True
                else:
                    sigh = 0
            except:
                print('some kind of problem in translation from RINEX 3 to RINEX 2.11')
        else:
            print('RINEX 3 file does not exist', r3_filename)
        s2=time.time()
        #print('gfzrnx rinex3 to rinex 2:', round(s2-s1,2), ' seconds')


    return fexists


def ign_orbits(filename, directory,year):
    """
    Downloads sp3 files from the IGN archive

    Parameters
    ----------
    filename : str
        name of the sp3 file
    directory : str
        location of orbits at the IGN
    year : int
        full year

    Returns
    -------
    foundit : bool
        whether sp3 file was found

    """
    # without gz
    stripped_name = filename[0:-3]
    url = directory + filename

    try:
        wget.download(url,filename)
        if os.path.exists(filename):
            subprocess.call(['gunzip',filename])
            store_orbitfile(stripped_name,year,'sp3') ; 
            foundit = True
    except:
        #print('some kind of issue at ign_orbits')
        foundit = False

    return foundit 


def ign_rinex3(station9ch, year, doy,srate):
    """
    Downloads a RINEX 3 file from IGN

    Parameters
    ----------
    station9ch : str
        9 character station name
    year : int
        full year
    doy : int
        day of year 
    srate : int
        sample rate

    Returns
    -------
    fexist : bool
        whether file was downloaded
    """
    fexist = False
    crnxpath = hatanaka_version()
    cyyyy, cyy, cdoy = ydoych(year,doy)

    csrate = '{:02d}'.format(srate)

    url = 'ftp://igs.ensg.ign.fr/pub/igs/data/' + cyyyy + '/' + cdoy + '/'
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx.gz'
    ff1 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx'
    ff2 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.rnx'
    url = url + ff
    #print(url)
    try:
        wget.download(url,ff)
        subprocess.call(['gunzip',ff])
        subprocess.call([crnxpath,ff1])
        # get rid of compressed file
        subprocess.call(['rm','-f',ff1])
    except:
        print('problem with IGN download')

    if os.path.exists(ff2):
        fexist = True

    return fexist


def hatanaka_version():
    """
    Finds the Hatanaka decompression executable

    Returns
    -------
    hatanakav : str 
        name/location of hatanaka executable

    """
    exedir = os.environ['EXE']
    hatanakav = exedir + '/CRX2RNX'
    # heroku version should be in the main area
    if not os.path.exists(hatanakav):
        hatanakav = './CRX2RNX'
    return hatanakav

def gfz_version():
    """
    Finds location of the gfzrnx executable

    Returns
    -------
    gfzv : str
        name/location of gfzrnx executable

    """
    exedir = os.environ['EXE']
    gfzv = exedir + '/gfzrnx'
    # heroku version should be in the main area
    if not os.path.exists(gfzv):
        gfzv = './gfzrnx'
    return gfzv

def gpsSNR_version():
    """
    Finds location of the gps to SNR executable

    Returns
    -------
    gpse : str
        location of gpsSNR executable
    """
    exedir = os.environ['EXE']
    gpse = exedir + '/gpsSNR.e'
    # heroku version should be in the main area
    if not os.path.exists(gpse):
        gpse = './gpsSNR.e'
    return gpse

def gnssSNR_version():
    """
    Finds location of the GNSS to SNR executable

    Returns
    -------
    gpse : str 
        location of gnssSNR executable

    """
    exedir = os.environ['EXE']
    gpse = exedir + '/gnssSNR.e'
    # heroku version should be in the main area
    if not os.path.exists(gpse):
        gpse = './gnssSNR.e'
    return gpse

def teqc_version():
    """
    Finds location of the teqc executable

    Returns
    -------
    gpse : str
        location of teqc executable

    """
    exedir = os.environ['EXE']
    gpse = exedir + '/teqc'
    # heroku version should be in the main area
    if not os.path.exists(gpse):
        gpse = './teqc'
    return gpse

def snr_exist(station,year,doy,snrEnd):
    """
    check to see if the SNR file already exists
    uncompresses if necessary (gz or xz)

    Parameters
    ----------
    station : str
        four character station name
    year : int
        full year
    doy : int
        day of year
    snrEnd : str
        2 character snr type, i.e. 66, 99

    Returns
    -------
    snre : boolean
        whether SNR file exists. 

    """
    xdir = os.environ['REFL_CODE']
    cyyyy, cyy, cdoy = ydoych(year,doy)

    f= station + cdoy + '0.' + cyy + '.snr' + snrEnd
    fname = xdir + '/' + cyyyy + '/snr/' + station + '/' + f
    fname2 = xdir + '/' + cyyyy + '/snr/' + station + '/' + f  + '.xz'
    fname3 = xdir + '/' + cyyyy + '/snr/' + station + '/' + f  + '.gz'
    snre = False
    # check for both
    if os.path.isfile(fname):
        snre = True
    if os.path.isfile(fname2) and (not snre):
        snre = True # but needs to be uncompressed
        subprocess.call(['unxz', fname2])
    if os.path.isfile(fname3) and (not snre):
        snre = True # but needs to be ungzipped 
        #subprocess.call(['gunzip', fname3])
        #TS - Removed this line Aug 2023 to stop unecessary decompression in nmea2snr

    return snre 

def get_sopac_navfile_cron(yyyy,doy):
    """
    downloads navigation file from SOPAC to be used in a cron job

    Parameters
    ----------
    yyyy : int
        full year
    doy : int
        day of year

    Returns
    -------
    filefound : bool
        whether file is found

    """
    filefound = False
    cyyyy = str(yyyy)
    cyy = cyyyy[2:4]
    cdoy = '{:03d}'.format(doy)

    sopac = 'ftp://garner.ucsd.edu'
    # regular unix compressed file
    navfile =  'auto' + cdoy + '0.' + cyy + 'n'
    navfile_sopac1 =  navfile + '.Z' 

    url_sopac1 = sopac + '/pub/rinex/' + cyyyy + '/' + cdoy + '/' + navfile_sopac1

    try:
        wget.download(url_sopac1,navfile_sopac1)
        subprocess.call(['uncompress',navfile_sopac1])
    except:
        okokok = 1

    if os.path.exists(navfile):
        filefound = True
    else:
        print('Corrupted file/download failures at SOPAC')
        subprocess.call(['rm','-f',navfile_sopac1])
        subprocess.call(['rm','-f',navfile])

    return filefound 


def get_sopac_navfile(navfile,cyyyy,cyy,cdoy):
    """
    downloads navigation file from SOPAC 

    Parameters
    ----------
    navfile : string
        name of GPS broadcast orbit file
    cyyyy : string
        4 char year
    cyy : string
        2 char year
    cdoy : string
        3 char day of year

    Returns 
    -------
    navfile : string 
        should be the same name as input. not logical!
        I have no idea why i did it this way.

    """
    foundfile = False
    sopac = 'ftp://garner.ucsd.edu'
    navfile_sopac1 =  navfile   + '.Z' # regular nav file
    navfile_compressed = navfile_sopac1
    url_sopac1 = sopac + '/pub/rinex/' + cyyyy + '/' + cdoy + '/' + navfile_sopac1


    try:
        wget.download(url_sopac1,navfile_compressed)
        subprocess.call(['uncompress',navfile_compressed])
    except:
        okokok = 1

    if os.path.exists(navfile):
        foundfile = True
    else:
        print('Corrupted file/download failures at SOPAC')
        subprocess.call(['rm','-f',navfile_compressed])
        subprocess.call(['rm','-f',navfile])

    return navfile

def get_esa_navfile(cyyyy,cdoy):
    """

    downloads GPS broadcast navigation file from ESA
    tries both Z and gz compressed

    Parameters
    ----------
    cyyyy : str
        4 char year
    cdoy : str
        3 char day of year

    Returns
    -------
    fstatus : bool
        whether file was found or not

    """
    fstatus = False
    cyy = cyyyy[2:4]
    year = int(cyyyy)
    navfile_out = 'auto' + cdoy + '0.' + cyy + 'n' 

    esa = 'ftp://gssc.esa.int/gnss/data/daily/' + cyyyy + '/brdc/'
    # what we want to find
    navfile = 'brdc' + cdoy + '0.' + cyy + 'n' 
    # have to check both Z and gz because ...
    navfilegz = 'brdc' + cdoy + '0.' + cyy + 'n.gz' 
    #print(esa+navfilegz)
    navfileZ = 'brdc' + cdoy + '0.' + cyy + 'n.Z' 

    # this is when they switched to gzip... 
    # brdc3350.20n.gz
    tday = year + int(cdoy)/365.25
    dday = 2020 + 335/365.25

    navfile_url =  esa + navfilegz

    # try gzip
    if (tday >= dday):
        try:
            wget.download(navfile_url,navfilegz)
            subprocess.call(['gunzip',navfilegz])
        except:
            print('Did not find gzip version')

    # try Z version
    if not os.path.exists(navfile):
        navfile_url =  esa + navfileZ
        try:
            wget.download(navfile_url,navfileZ)
            subprocess.call(['uncompress',navfileZ])
        except:
            okokok = 1

    # rename it.
    if os.path.exists(navfile):
        subprocess.call(['mv',navfile, navfile_out])
        fstatus = True
    else:
        print('No file was found at ESA')

    return fstatus

def get_cddis_navfile(navfile,cyyyy,cyy,cdoy):
    """
    Tries to download navigation file from CDDIS
    Renames it to my convention (auto0010.22n)

    Parameters
    ----------
    navfile : str
        name of GPS broadcast orbit file
    cyyyy : str
        4 char year
    cyy : str
        2 char year
    cdoy : str
        3 char day of year

    Returns
    -------
    navfile : str
        full path of the stored navigation file

    """

    cddisfile = 'brdc' + cdoy + '0.' +cyy  +'n'
    cddisfile_compressed = cddisfile + '.Z'
    cddisfile_gzip = cddisfile + '.gz'
    # where the file should be at CDDIS ....
    mdir = '/gps/data/daily/' + cyyyy + '/' + cdoy + '/' +cyy + 'n/'

    foundit = False
    # they used to use Z compression
    if (int(cyyyy) < 2021):
        print('Try the unix compressed version')
        try:
            cddis_download_2022B(cddisfile_compressed,mdir)
        except:
            okokok = 1

        if os.path.isfile(cddisfile_compressed):
            size = os.path.getsize(cddisfile_compressed)
            if (size == 0):
                subprocess.call(['rm',cddisfile_compressed])
            else:
                subprocess.call(['uncompress',cddisfile_compressed])
            foundit = True

    print('Try the gzipped version')
    if (not foundit):
        try:
            cddis_download_2022B(cddisfile_gzip,mdir)
        except:
            okokok = 1
        if os.path.isfile(cddisfile_gzip):
            size = os.path.getsize(cddisfile_gzip)
            if (size == 0):
                subprocess.call(['rm',cddisfile_gzip])
            else:
                subprocess.call(['gunzip',cddisfile_gzip])
                foundit = True
    
    if os.path.isfile(cddisfile):
        print('Change the filename to what we use ', navfile)
        subprocess.call(['mv',cddisfile,navfile])

    return navfile

def ydoy2useful(year, doy):
    """
    Calculates various dates

    Parameters
    ----------
    year : int
        full year
    doy : int
        day of year

    Returns
    -------
    year : int
        full year
    month : int
        calendar month
    day : integer
        calendar day
    cyyyy : str
        four character year
    cdoy : str
        three character day of year
    YMD : str
         date as in '19-12-01' for December 1, 2019

    """

    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
#   not sure you need to do this int step
    month = int(d.month)
    day = int(d.day)
    cyyyy, cyy, cdoy = ydoych(year,doy)

    cdd = '{:02d}'.format(day)
    cmonth = char_month_converter(month)
    YMD = cyy + cmonth + cdd
    return year, month, day, cyyyy,cdoy, YMD

def prevdoy(year,doy):
    """
    Given year and doy, return previous year and doy

    Parameters
    ----------
    year : int
        full year
    doy : int
        day of year

    Returns
    -------
    pyear : int
        previous year
    pdoy : int
        previous day of year 
    """
    if (doy == 1):
        pyear = year -1
        doyx,cdoyx,cyyyy,cyy = ymd2doy(pyear,12,31)
        pdoy = doyx
    else:
#       doy is decremented by one and year stays the same
        pdoy = doy - 1
        pyear = year

    return pyear, pdoy

def nextdoy(year,doy):
    """
    given a year/doy returns the subsequent year/doy

    Parameters
    ----------
    year : int
        day of year
    doy : int
        day of year

    Returns
    -------
    nyear : int
        next year
    ndoy : int
        next day of year

    """
    dec31,cdoy,ctmp,ctmp2 = ymd2doy(year,12,31)
    if (doy == dec31):
        nyear = year + 1
        ndoy = 1
    else:
        nyear = year
        ndoy = doy + 1

    return nyear, ndoy

def read_sp3file(file_path):
    """ 
    input: file_path is the sp3file name
    this code is from Joakim Strandberg I believe.
    It is for the python only version of the translator, which 
    should be deprecated

    Returns
    -------
    sp3 : ndarray
    colums are satnum, gpsweek, gps_sow, x,y,z
    x,y,z are in meters
    satnum has 0, 100, 200, 300 added for gps, glonass, galileo,beidou,
    respectively.  all other satellites are ignored

    """
    ignorePoint = False
    max_sat = 150 # not used
    # store as satNu, week, sec of week , x, y, and z?
    sp3 = np.empty(shape=[0, 6])
    count = -1
    firstEpochFound = False

    f = open(file_path, 'r')
    for line in f.readlines():
        #all time tags have a * in first column
        if line[0] == '*':
            year,month,day,hour,minute,second = line.split()[1:]
            wk,swk = kgpsweek(int(year), int(month), int(day), int(hour), int(minute), float(second))
            wk = int(wk) ; swk = float(swk)
            if (not firstEpochFound):
                firstWeek = wk 
                firstEpochFound = True
                #print('first GPS Week and Seconds in the file', firstWeek, swk)
            count += 1
            if (wk != firstWeek):
                #print('this is a problem - this code should not be used with files that crossover GPS weeks ')
                #print('JAXA orbits have this extra point, which is going to be thrown out')
                ignorePoint = True
        if (line[0] == 'P') and (not ignorePoint):
            co = line[1]
            out = findConstell(co)
            satNu = int(line[2:4]) + out
            xs = line.split()
            # do not allow SBAS etc
            if satNu < 400:
                x = float(xs[1])*1000.0
                y = float(xs[2])*1000.0
                z = float(xs[3])*1000.0
                lis = [satNu, wk,swk, x,y,z]
                sp3 = np.vstack((sp3,lis))
    f.close()
    nr,nc = sp3.shape
    #print('number of rows and columns being returned from the sp3 file', nr,nc)
    return sp3

def nicerTime(UTCtime):
    """
    Converts fractional time (hours) to HH:MM

    Parameters
    ----------
    UTCtime : float
        fractional hours of the day 

    Returns 
    -------
    T : str
        output as HH:MM 

    """
    hour = int(np.floor(UTCtime))
    minute = int ( np.floor(60* ( UTCtime - hour )))
    second = int ( 3600*UTCtime - 3600*hour  - 60*minute)
    #print(hour,minute,second)
    if (second > 30):
        # up the minutes ...
        minute = minute + 1
        # sure hope this works - beyond annoying
        if minute == 60:
            minute = 0
            hour = hour + 1

    chour = '{:02d}'.format(hour)
    cminute = '{:02d}'.format(minute)
    T = chour + ':' + cminute  

    return T


def big_Disk_work_hard(station,year,month,day):
    """
    Attempts to pick up subdaily RINEX 2.11 files from the NGS archive
    creates a single RINEX file

    If day is 0, then month is presumed to be the day of year

    Requires teqc

    Parameters
    ----------
    station: str
        4 char station name
    year: int
        year
    month: int
        month
    day: integer
        day

    """
    if (day == 0):
        doy = month
        year, month, day, cyyyy,cdoy, YMD = ydoy2useful(year,doy)
        cyy = cyyyy[2:4]
    else:
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)

    # want to merge the hourly files into this filename
    rinexfile =  station + cdoy + '0.' + cyy + 'o'
    exc = teqc_version()
    if not os.path.exists(exc):
        print('teqc is used for this subroutine - it does not exist, so exiting.')
        print('Please help us by submitting a pull request.')
        sys.exit()

    let = 'abcdefghijklmnopqrstuvwxyz';
    alist = [exc]
    blist = ['rm']
    for i in range(0,24):
        idtag = let[i:i+1]
        fname= station + cdoy + idtag + '.' + cyy + 'o'
        # if it does not exist, try to get it
        if not os.path.isfile(fname):
            big_Disk_in_DC_hourly(station, year, month, day,idtag) 
        else:
            print(fname, ' exists')
        if os.path.isfile(fname):
            alist.append(fname)
            blist.append(fname)

    print(alist)
    fout = open(rinexfile,'w')
    subprocess.call(alist,stdout=fout)
    fout.close()
    print('file created: ', rinexfile)
    # should delete the hourly files
    subprocess.call(blist)


def big_Disk_in_DC_hourly(station, year, month, day,idtag):
    """
    Picks up a one hour RINEX file from CORS. and gunzips it

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    month : int
        calendar month
    day : integer
        day of the month. if zero, it means month is really day of year
    idtag : str
        small case letter from a to x; tells the code which hour it is

    """
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    # define names
    crinexfile = station + cdoy + idtag + '.' + cyy + 'o.gz'
    rinexfile =  station + cdoy + idtag + '.' + cyy + 'o'
    # do not know if this works - but what the hey
    mainadd = 'https://geodesy.noaa.gov/corsdata/rinex/'
    #mainadd = 'ftp://www.ngs.noaa.gov/cors/rinex/'
    url = mainadd + cyyyy + '/' + cdoy+ '/' + station + '/' + crinexfile
    print(url)
    try:
        wget.download(url, out=crinexfile)
        status = subprocess.call(['gunzip', crinexfile])
    except:
        print('some problem in download - maybe the site does not exist on this archive')


def check_environ_variables():
    """
    Checks to see if you have set the expected environment variables
    used in gnssrefl
    """
    variables= ['EXE','ORBITS','REFL_CODE']
    for env_var in variables:
        if env_var not in os.environ:
            print(env_var, ' not found, so set to current directory')
            os.environ[env_var] = '.'


def ftitle(freq):
    """
    makes a frequency title for plots 

    Parameters
    ----------
    freq : int
        GNSS frequency

    Returns
    -------
    returnf : str
        nice string for the constellation/frequency for the title of a plot
    """
    f=str(freq)
    out = {}
    out['1'] = 'GPS L1'
    out['2'] = 'GPS L2'
    out['20'] = 'GPS L2C'
    out['5'] = 'GPS L5'
    out['101'] = 'Glonass L1'
    out['102'] = 'Glonass L2'
    out['201'] = 'Galileo L1'
    out['205'] = 'Galileo L5'
    out['206'] = 'Galileo L6'
    out['207'] = 'Galileo L7'
    out['208'] = 'Galileo L8'
    # still need to work on these because it is confusing!...
    out['301'] = 'Beidou L1'
    out['302'] = 'Beidou L2'
    out['305'] = 'Beidou L5'
    out['306'] = 'Beidou L6'
    out['307'] = 'Beidou L7'
    if freq not in [1,2, 20,5,101,102,201,205,206,207,208,301,302,305,306,307]:
        returnf = ''
    else:
        returnf = out[f]

    return returnf 

def cdate2nums(col1):
    """
    returns fractional year from ch date, e.g. 2012-02-15
    if time is blank, return 3000

    Parameters
    ----------
    col1 : str
        date in yyyyy-mm-dd, 2012-02-15

    Returns
    -------
    t : float
        fractional date, year + doy/365.25
    """
    year = int(col1[0:4])
    if year == 0:
        t=3000 # made up very big time!
    else:
        month = int(col1[5:7])
        day = int(col1[8:10])
        #print(col1, year, month, day)
        doy,cdoy,cyyyy,cyy = ymd2doy(year, month, day )
        t = year + doy/365.25

    return t

def cdate2ydoy(col1):
    """
    returns year and day of year from character date, e.g. '2012-02-15'

    Parameters
    ----------
    col1 : str
        date in yyyyy-mm-dd, 2012-02-15

    Returns
    -------
    year : int 
        full year
    doy : int 
        day of year
    """
    year = int(col1[0:4])
    if year == 0:
        t = 3000 # made up very big time!
    else:
        month = int(col1[5:7])
        day = int(col1[8:10])
        #print(col1, year, month, day)
        doy,cdoy,cyyyy,cyy = ymd2doy(year, month, day )
        #t = year + doy/365.25

    return year, doy


def l2c_l5_list(year,doy):
    """
    Creates a satellite list of L2C and L5 transmitting satellites
    for a given year/doy

    Parameters
    ----------
    year: int
        full year
    doy: integer
        day of year

    Returns
    -------
    l2csatlist : numpy array (int)
        satellites possibly transmittingL2C 

    l5satlist : numpy array (int)
        satellites possibly transmitting L5 

    """

    # this numpy array has the satellite number, year, and doy of each launch of a L2C satellite
    # updated 2023 feb 1 to include prn 28 - was set operational on jan 31
    l2c=np.array([[1 ,2011 ,290], [3 ,2014 ,347], [4 ,2018 ,357], [5 ,2008 ,240],
        [6 ,2014 ,163], [7 ,2008 ,85], [8 ,2015 ,224], [9 ,2014 ,258], [10 ,2015 ,343],
        [11, 2021, 168],
        [12 ,2006 ,300], [14 ,2020 ,310], [15 ,2007 ,285], [17 ,2005 ,270],
        [18 ,2019 ,234], [23 ,2020 ,182], [24 ,2012 ,319], [25 ,2010 ,240],
        [26 ,2015 ,111], [27 ,2013 ,173], [28,2023,17], [29 ,2007 ,355], 
        [30 ,2014 ,151], [31 ,2006 ,270], [32 ,2016 ,36]])
    # indices that meet your criteria
    ij=(l2c[:,1] + l2c[:,2]/365.25) < (year + doy/365.25)
    l2csatlist = l2c[ij,0]

    # The L5 list is defined by all L2C satellites after 2010, doy 148
    firstL5 = 2010 + 148/365.25 # launch may 28, 2010  - some delay before becoming healthy

    newlist = l2c[ij,:]
    ik= (newlist[:,1] + newlist[:,2]/365.25) > firstL5
    l5satlist = newlist[ik,0]

    return l2csatlist, l5satlist


def binary(string):
    """
    changes python string to bytes for use in
    fortran code using f2py via numpy
    input is a string, output is bytes with null at the end
    """
    j=bytes(string,'ascii') + b'\0\0'

    return array(j)

def ymd_hhmmss(year,doy,utc,dtime):
    """
    translates year, day of year and UTC hours 
    into various other time parameters

    Parameters
    ----------
    year : int
        full year
    doy : int
        full year
    UTC : float
        fractional hours
    dtime : bool
        whether you want datetime object

    Returns 
    -------
    bigT : datetime object

    year : int
        full year
    month : int
        calendar month
    day : int
        calendar day
    hour : int
        hour of the day
    minute: int
        minutes of the day
    second : int
        seconds

    """
    year = int(year) # just in case
    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    month = int(d.month)
    day = int(d.day)
    hour = int(np.floor(utc))
    minute = int ( np.floor(60* ( utc- hour )))
    #second = int(utc*3600 - (hour*3600 + minute*60))
    second = round(utc*3600 - (hour*3600 + minute*60))
    #print(second, utc*3600 - (hour*3600 + minute*60))
    if second == 60:
        second = 0
        minute = minute + 1
    if minute == 60:
        minute = 0
        hour = hour + 1
    # i dunno what you do if hour > 24! well, i do, but it is annoying
    bigT = 0
    if dtime:
        bigT = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
    return bigT, year, month, day, hour, minute, second


def get_obstimes(tvd):
    """
    Calculates datetime objects for times associated with 
    LSP results file contents, i.e. the variable created when you read 
    in the results file.  

    Parameters
    ----------
    tvd : numpy array
        results of LSP results

    Returns
    ------
    obstimes : numpy array
        datetime objects
    """
    nr,nc = tvd.shape
    obstimes = []

    if nr > 0:
        for ijk in range(0,nr):
            dtime, iyear,imon,iday,ihour,imin,isec = ymd_hhmmss(tvd[ijk,0],tvd[ijk,1],tvd[ijk,4],True)
            obstimes.append(dtime)
    else:
        print('empty file')

    return obstimes

def get_obstimes_plus(tvd):
    """
    send a LSP results file, so the variable created when you read
    in the results file.  return obstimes for matplotlib plotting purposes
    2022jun10 - added MJD output

    See get_obstimes 


    """
    nr,nc = tvd.shape
    obstimes = []
    modjulian = np.empty(shape=[0,1])

    if nr > 0:
        for ijk in range(0,nr):
            dtime, iyear,imon,iday,ihour,imin,isec = ymd_hhmmss(tvd[ijk,0],tvd[ijk,1],tvd[ijk,4],True)
            obstimes.append(dtime)
            m,f = mjd(iyear,imon,iday,ihour,imin,isec)
            x=[m+f]
            modjulian = np.append(modjulian, [x],axis=0 )
    else:
        print('empty file')

    return obstimes, modjulian


def confused_obstimes(tvd):
    """

    Parameters
    ----------
    tvd : numpy array
        results of LSP results

    Returns
    -------
    modifiedjulian : numpy array of floats
        modified julian date values
    """
    nr,nc = tvd.shape
    modifiedjulian = []
    if nr > 0:
        for ijk in range(0,nr):
            dtime, iyear,imon,iday,ihour,imin,isec = ymd_hhmmss(tvd[ijk,0],tvd[ijk,1],tvd[ijk,4],True)
            m,f = mjd(iyear,imon,iday,ihour,imin,isec)
            modifiedjulian = np.append(modifiedjulian, m+f)
    else:
        print('empty file')

    return modifiedjulian

def more_confused_obstimes(tvd):
    """

    Parameters
    ----------
    tvd : numpy array of floats
        lsp results from a loadtxt command

    Returns
    -------
    modifiedjulian : numpy array of floats 
         mjd values
        
    """
    nr,nc = tvd.shape
    modifiedjulian = []
    if nr > 0:
        for ijk in range(0,nr):
            #MM DD HH Min Sec
            (18,19,20,21,22)
            #dtime, iyear,imon,iday,ihour,imin,isec = ymd_hhmmss(tvd[ijk,0],tvd[ijk,1],tvd[ijk,4],True)
            iyear = tvd[ijk,0]; imon = tvd[ijk,17]; iday = tvd[ijk,18]
            ihour = tvd[ijk,19]; imin = tvd[ijk,20]
            isec =  tvd[ijk,21]
            m,f = mjd(iyear,imon,iday,ihour,imin,isec)
            modifiedjulian = np.append(modifiedjulian, m+f)
    else:
        print('empty file')

    return modifiedjulian



def read_simon_williams(filename,outfilename):
    """
    Reads a PSMSL file and creates a new file in the 
    standard format I use for tide gauge data in gnssrefl
    
    Parameters
    ----------
    filename : str
        datafile of GNSS based water level measurements from 
        the archive at PSMSL created by Simon Williams 

    outfilename : str
        where the rewritten data will go

    Returns
    -------
    outobstimes : datetime array
        time of observations

    outmjd : numpy array of floats
        modified julian day

    outsealevel : numpy array of floats 
        sea level, meters

    prn : numpy array of integers
        satellite numbers

    fr : numpy array of integers
        frequency

    az : numpy array of floats
        azimuth (degrees)

    """

    fout = open(outfilename,'w+')
    print('Writing PSMSL GNSS-IR data to ', outfilename)
    csv = False
    if outfilename[-3:] == 'csv':
        csv = True

    if csv:
        fout.write("# YYYY,MM,DD,HH,MM, Water(m),DOY, MJD, Seconds,Freq, Azim,PRN \n")
    else:
        fout.write("%YYYY  MM  DD  HH  MM  Water(m) DOY    MJD    Sec   Freq  Azim    PRN  raw  fit-tide mod-raw \n")
        fout.write("% (1) (2) (3) (4)  (5)   (6)    (7)     (8)   (9)   (10)   (11)  (12)  (13)  (14)     (15)\n")

    # read the file three times because i am loadtxt impaired
    # string
    tv = np.loadtxt(filename,usecols=(0,1,2,3),skiprows=10,dtype='str',delimiter=',')
    # integers
    ivals = np.loadtxt(filename,usecols=(4,5),skiprows=10, dtype='int',delimiter=',')
    # floats
    fvals = np.loadtxt(filename,usecols=(6),skiprows=10, dtype='float',delimiter=',')
    # store the latter columns directly
    prn = ivals[:,0]
    fr = ivals[:,1]
    az = fvals

    nr = len(tv)
    # these are converted to numpy at the bottom
    obstimes = []
    modjulian = []
    sealevel = []
    s1=time.time()

    for i in range(0,nr):
        year = int(tv[i,0][0:4])
        mm = int(tv[i,0][5:7])
        dd = int(tv[i,0][8:10])
        doy,cdoy,cyyyy,cyy = ymd2doy(year,mm,dd)
        hh = int(tv[i,0][11:13])
        minutes = int(tv[i,0][14:16])
        sec = int(tv[i,0][17:19])
        raw = float(tv[i,1])
        modraw = float(tv[i,2])
        tidefit = float(tv[i,3])
        dtime = datetime.datetime(year=year, month=mm, day=dd, hour=hh, minute=minutes, second=sec)
        imjd, frac = mjd(year,mm,dd,hh,minutes,sec)
        x = [imjd+frac]
        # go ahead and write to a file ... 
        if csv:
            fout.write(" {0:4.0f},{1:2.0f},{2:2.0f},{3:2.0f},{4:2.0f},{5:7.3f},{6:3.0f},{7:15.6f},{8:2.0f},{9:1.0f},{10:8.3f},{11:2.0f},{12:6.3f},{13:6.3f} \n".format(year, mm, dd, hh, minutes, modraw, doy, imjd+frac, sec, fr[i], az[i],prn[i],raw,tidefit))
        else:
            fout.write(" {0:4.0f} {1:3.0f} {2:3.0f} {3:3.0f} {4:3.0f} {5:7.3f} {6:3.0f} {7:15.6f} {8:2.0f} {9:1.0f} {10:8.3f} {11:2.0f} {12:6.3f} {13:6.3f}  \n".format(year, mm, dd, hh, minutes, modraw, doy, imjd+frac, sec, fr[i], az[i], prn[i], raw,tidefit))

        obstimes.append(dtime)
        modjulian.append(x)
        sealevel.append(modraw)

    fout.close()

    s2=time.time()
    print('that took ', round(s2-s1,2), ' seconds')

    outobstimes= np.asarray(obstimes)
    outsealevel = np.asarray(sealevel)
    outmjd = np.asarray(modjulian)

    return outobstimes, outmjd, outsealevel, prn, fr, az


def get_noaa_obstimes(t):
    """
    Needs to be be fixed for new file structure

    Parameters
    ----------
    t : list of integers
        year, month, day, hour, minute, second 

    Returns
    -------
    obstimes : datetime 

    """
    nr,nc = t.shape
    obstimes = []

    # if i read in the file better, would not have to change from float
    # year mon day hour min sealevel doy mjd seconds
    if nr > 0:
        for i in range(0,nr):
            dtime = datetime.datetime(year=int(t[i,0]), month=int(t[i,1]), day=int(t[i,2]), hour=int(t[i,3]), minute=int(t[i,4]), second=int(t[i,5]) )
            obstimes.append(dtime)
    else:
        print('you sent me an empty variable')

    return obstimes

def get_noaa_obstimes_plus(t,**kwargs):
    """
    given a list of time tags (y,m,d,h,m,s), it calculates datetime
    objects and modified julian days

    Parameters
    ----------
    t : numpy array
        our water level format
        where year, month, day, hour, minute, second are in the first columns

    Returns
    -------
    obstimes : datetime obj
        timetags 

    modjulian : numpy array of floats
        modified julian date array 

    """
    time_format = kwargs.get('time_format','new')
    if time_format == 'new':
        tt = True
    else:
        tt = False

    nr,nc = t.shape
    obstimes = []
    modjulian = np.empty(shape=[0,1])
    #modjulian=[]

    # if i read in the file better, would not have to change from float
    if nr > 0:
        for i in range(0,nr):
            # new fileformat
            if tt:
                year = int(t[i,0]); month=int(t[i,1]); day=int(t[i,2]); hour=int(t[i,3]); minute=int(t[i,4]); second = int(t[i,5])
            else:
                year = int(t[i,0]); month=int(t[i,1]); day=int(t[i,2]); hour=int(t[i,3]); minute=int(t[i,4]); second = int(t[i,8])

            dtime = datetime.datetime(year=year, month=month, day=day, hour=hour, minute=minute, second=second)
            obstimes.append(dtime)
            imjd, fr = mjd(year,month,day,hour,minute,second)
            x = [imjd+fr]
            modjulian = np.append(modjulian, x)
    else:
        print('you sent me an empty variable')

    return obstimes, modjulian


def final_gfz_orbits(year,month,day):
    """
    downloads gfz final orbit and stores in $ORBITS

    Parameters
    ----------
    year : int
        full year
    month : int
        month or day of year if day is set to zero
    day : int
        day of month

    Returns
    -------
    littlename : str
        orbit filename, fdir, foundit
    fdir: str
        directory where the orbit file is stored locally
    foundit : bool
        whether the file was found
    """
    foundit = False
    dday = 2021 + 137/365.25
    wk,sec=kgpsweek(year,month,day,0,0,0)

    gns = 'ftp://ftp.gfz-potsdam.de/pub/GNSS/products/final/'
    if day == 0:
       doy=month
       d = doy2ymd(year,doy);
       month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    fdir = os.environ['ORBITS'] + '/' + cyyyy + '/sp3'
    littlename = 'gbm' + str(wk) + str(int(sec/86400)) + '.sp3'
    #GFZ0MGXRAP_20222740000_01D_05M_ORB.SP3
    #GFZ0OPSFIN
    # GFZ0MGXRAP_20222440000_01D_05M_ORB.SP3
    littlename = 'GFZ0MGXRAP_' + str(year) + cdoy + '0000_01D_05M_ORB.SP3'

    url = gns + 'w' + str(wk) + '/' + littlename + '.gz'
    #print(url)

    fullname = fdir + '/' + littlename + '.xz'
    if os.path.isfile(fullname):
        subprocess.call(['unxz', fullname])

    fullname = fdir + '/' + littlename + '.gz'
    if os.path.isfile(fullname):
        subprocess.call(['gunzip', fullname])

    if os.path.isfile(fdir + '/' + littlename):
        #print(littlename, ' already exists on disk')
        return littlename, fdir, True 

    try:
        wget.download(url,littlename + '.gz')
        subprocess.call(['gunzip', littlename + '.gz'])
    except:
        print('Problems downloading final multi-GNSS GFZ orbit from GFZ')
        print(url)

    if os.path.isfile(littlename):
       store_orbitfile(littlename,year,'sp3') ; foundit = True

    return littlename, fdir, foundit

def rapid_gfz_orbits(year,month,day):
    """
    downloads gfz rapid orbit and stores in $ORBITS locally

    Parameters
    ----------
    year : int
        full year
    month : int
        month or day of year if day is set to zero
    day : int
        day of month

    Returns
    -------
    littlename : str
        name of the orbit file
    fdir: str
        name of the file directory where orbit is stored
    foundit : bool
        whether file was found

    """
    foundit = False
    dday = 2021 + 137/365.25
    wk,sec=kgpsweek(year,month,day,0,0,0)

    gns = 'ftp://ftp.gfz-potsdam.de/pub/GNSS/products/rapid/'
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    fdir = os.environ['ORBITS'] + '/' + cyyyy + '/sp3'
    littlename = 'gfz' + str(wk) + str(int(sec/86400)) + '.sp3'
    url = gns + 'w' + str(wk) + '/' + littlename + '.gz'
    #print(url)
    if (year + doy/365.25) < dday:
        print('No rapid GFZ orbits until 2021/doy137')
        return '', '', foundit
    fullname = fdir + '/' + littlename + '.xz'
    # look for compressed file
    if os.path.isfile(fullname):
        subprocess.call(['unxz', fullname])

    if os.path.isfile(fdir + '/' + littlename):
        #print(littlename, ' already exists on disk')
        return littlename, fdir, True 
    try:
        wget.download(url,littlename + '.gz')
        subprocess.call(['gunzip', littlename + '.gz'])
    except:
        print('Problems downloading Rapid GFZ orbit')
        print(url)

    if os.path.isfile(littlename):
       store_orbitfile(littlename,year,'sp3') ; foundit = True

    return littlename, fdir, foundit


def ultra_gfz_orbits(year,month,day,hour):
    """
    downloads rapid GFZ sp3 file and stores them in $ORBITS

    Parameters
    ----------
    year : int
        full year
    month : int
        month or day of year
    day : int
        day or if set to 0, then month is really day of year
    hour : int
        hour of the day

    Returns
    -------
    littlename : str
        name of the orbit file
    fdir: str
        name of the file directory where orbit is stored
    foundit : bool
        whether file was found
    """
    foundit = False
    # when they changed over?
    dday = 2021 + 137/365.25
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    # figure out the GPS week number
    wk,sec=kgpsweek(year,month,day,0,0,0)

    gns = 'ftp://ftp.gfz-potsdam.de/pub/GNSS/products/ultra/'
    fdir = os.environ['ORBITS'] + '/' + cyyyy + '/sp3'
    # change the hour into two character string
    chr = '{:02d}'.format(hour)
    littlename = 'gfu' + str(wk) + str(int(sec/86400)) + '_' + chr + '.sp3'  

    url = gns + 'w' + str(wk) + '/' + littlename + '.gz'
    #print(url)
    if (year + doy/365.25) < dday:
        print('No rapid GFZ orbits until 2021/doy137')
        return '', '', foundit

    # check to see if the file is there already
    fullname = fdir + '/' + littlename + '.xz'
    if os.path.isfile(fullname):
        subprocess.call(['unxz', fullname])

    # check to see if the file is there already
    fullname = fdir + '/' + littlename + '.gz'
    if os.path.isfile(fullname):
        subprocess.call(['gunzip', fullname])

    if os.path.isfile(fdir + '/' + littlename):
        #print(littlename, ' already exists on disk')
        return littlename, fdir, True

    try:
        wget.download(url,littlename + '.gz')
        subprocess.call(['gunzip', littlename + '.gz'])
    except:
        print('Problems downloading ultrarapid GFZ orbit')

    if os.path.isfile(littlename):
        store_orbitfile(littlename,year,'sp3') ; foundit = True

    return littlename, fdir, foundit


def get_wuhan_orbits(year: int, month: int, day: int) -> [str, str, bool]:
    """
    Downloads ultra-rapid Wuhan sp3 file and stores them in $ORBITS

    Parameters
    ----------
    year : int
        full year
    month : int
        month or day of year
    day : int
        day or if set to 0, then month is really day of year

    Returns
    -------
    unzipped_filename : str
        name of the sp3 orbit file
    orbit_dir: str
        name of the file directory where orbit is stored
    foundit : bool
        whether file was found
    """
    foundit = False
    gps_week, _ = kgpsweek(year, month, day, 0, 0, 0)
    _, _, doy, _, _, _ = ymd2ch(year, month, day)

    url_base = f'ftp://igs.gnsswhu.cn/pub/gnss/products/mgex/{gps_week}/'
    filename = f'WUM0MGXULT_{year}{doy:03}0000_01D_05M_ORB.SP3.gz'
    unzipped_filename = filename[:-3]
    orbit_dir = f'{os.environ["ORBITS"]}/{year}/sp3'
    if not os.path.isfile(f'{orbit_dir}/{unzipped_filename}'):
        try:
            wget.download(f'{url_base}{filename}', filename)
            subprocess.call(['gunzip', filename])
        except:
            print('Problems downloading ultra-rapid Wuhan orbit')
            print(f'{url_base}{filename}')
        if os.path.isfile(unzipped_filename):
            store_orbitfile(unzipped_filename, year, 'sp3')
            foundit = True
    else:
        #print('Wuhan orbit wum2 is stored locally')
        foundit = True

    return unzipped_filename, orbit_dir, foundit


def rinex_unavco(station, year, month, day):
    """
    This is being used by the vegetation code
    picks up a RINEX 2.11 file from unavco low-rate area
    requires Hatanaka code

    Parameters
    ----------
    station: str
        4 ch station name

    year : integer
        full year

    month : integer
        month or day of year

    day: integer
        day of month or zero

    """
    exedir = os.environ['EXE']
    crnxpath = hatanaka_version()  # where hatanaka will be
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    rinexfile,rinexfiled = rinex_name(station, year, month, day)
    unavco= 'https://data.unavco.org/archive/gnss/rinex/obs/'
    filename1 = rinexfile + '.Z'
    filename2 = rinexfiled + '.Z'
    # URL path for the o file and the d file
    url1 = unavco+ cyyyy + '/' + cdoy + '/' + filename1
    url2 = unavco+ cyyyy + '/' + cdoy + '/' + filename2

    try:
        wget.download(url1,filename1)
        status = subprocess.call(['uncompress', filename1])
    except:
        okokok =1

    if not os.path.exists(rinexfile):
        if os.path.exists(crnxpath):
            try:
                wget.download(url2,filename2)
                status = subprocess.call(['uncompress', filename2])
                status = subprocess.call([crnxpath, rinexfiled])
                status = subprocess.call(['rm', '-f', rinexfiled])
            except:
                okokok =1
            #except Exception as err:
            #    print(err)
        else:
            hatanaka_warning()


def avoid_cddis(year,month,day):
    """
    work around for people that can't use CDDIS ftps
    this will get multi-GNSS files for GFZ from the IGN
    hopefully

    Parameters
    ----------
    year : int 
        full year
    month : int
        month of the year
    day : int
        calendar day

    Returns
    -------
    filename : str
        name of the orbit file
    fdir : str
        where the orbit file is stored
    foundit : bool
        whether it was found or not

    """
    fdir = os.environ['ORBITS'] + '/' + str(year) + '/sp3/'
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    foundit = False; 
    wk,swk = kgpsweek(year, month, day, 0,0,0)
    cwk = '{:04d}'.format(wk); cday = str(int(swk/86400))
    # old file name for precise files
    filenameZ = 'gbm' + cwk + cday + '.sp3.Z'
    filename = 'gbm' + cwk + cday + '.sp3'
    if os.path.isfile(fdir + filename):
        #print(filename,' orbit file already exists on disk'); 
        foundit = True
        return filename, fdir, foundit
    if os.path.isfile(fdir + filename + '.xz'):
        subprocess.call(['unxz',fdir + filename + '.xz'])
        #print(filename, ' orbit file already exists on disk'); 
        foundit = True
        return filename, fdir, foundit

    # only use this for weeks < 2050
    if (wk < 2050):
        url = 'ftp://igs.ensg.ign.fr/pub/igs/products/mgex/' + cwk +  '/' + filenameZ
        try:
            wget.download(url,filenameZ)
            subprocess.call(['uncompress',filenameZ])
            subprocess.call(['mv',filename, fdir])
            foundit = True
        except:
            print('could not find ', filename)
    if (not foundit):
        filename = 'GFZ0MGXRAP_' + cyyyy  + cdoy + '0000_01D_05M_ORB.SP3'
        filenamegz = 'GFZ0MGXRAP_' + cyyyy  + cdoy + '0000_01D_05M_ORB.SP3.gz'

        if os.path.isfile(fdir + filename):
            #print(filename, ' orbit file already exists on disk'); 
            foundit = True
            return filename, fdir, foundit
        if os.path.isfile(fdir + filename + '.xz'):
            subprocess.call(['unxz',fdir + filename + '.xz'])
            #print(filename, ' orbit file already exists on disk'); 
            foundit = True
            return filename, fdir, foundit

        url = 'ftp://igs.ensg.ign.fr/pub/igs/products/mgex/' + cwk +  '/' + filenamegz
        try:
            wget.download(url, filenamegz)
            if os.path.exists(filenamegz):
                subprocess.call(['gunzip',filenamegz])
                subprocess.call(['mv',filename, fdir])
                foundit=True
        except:
            print('could not find',filename)

    return filename, fdir, foundit

def rinex_jp(station, year, month, day):
    """
    Picks up RINEX file from Japanese GSI GeoNet archive
    URL : https://www.gsi.go.jp/ENGLISH/index.html

    Parameters
    ----------
    station : str
        station name

    year : int
        full year

    month: int
        month or day of year

    day : int
        day of month or zero
    """
    # allow it to be called with day of year
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)

    fdir = os.environ['REFL_CODE']
    if not os.path.isdir(fdir):
        print('You need to define the REFL_CODE environment variable')
        return 

    # make sure the directory exists to store passwords
    if not os.path.isdir(fdir + '/Files'):
        subprocess.call(['mkdir',fdir + '/Files'])
    if not os.path.isdir(fdir + '/Files/passwords'):
        subprocess.call(['mkdir',fdir + '/Files/passwords'])

    userinfo_file = fdir + '/Files/passwords/' + 'userinfo.pickle'
    #userinfo.pickle stores your login info
    try:
        with open(userinfo_file, 'rb') as client_info:
            login_info = pickle.load(client_info)
            user_id = login_info[0]
            password = login_info[1]
    except:
        print('User registration is required to use the database')
        print('Access https://www.gsi.go.jp/ENGLISH/geonet_english.html (English)')
        print('or https://terras.gsi.go.jp/ftp_user_regist.php (Japanese) to create an acount')
        print('Please enter your FTP user id (if you do not have an account type none')
        user_id = input()
        if user_id == 'none':
            print('You have no account at Geonet so returning to the main code')
            return
        password= getpass.getpass(prompt='Password: ', stream=None)
        #password = input()
    # if doy is input, convert to month and day
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)

    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    gns = 'terras.gsi.go.jp/data/GR_2.11/'
    file1 =station[-4:].upper() + cdoy + '0.' + cyy + 'o' + '.gz'
    url = 'ftp://' + user_id + ':' + password + '@' + gns +  cyyyy + '/' + cdoy +  '/' + file1
    print('attempt to download RINEX file from Jp GeoNet')
    try:
        wget.download(url,file1)
        subprocess.call(['gunzip', file1])
        print('successful download from JP GeoNet')
        if not os.path.isfile(userinfo_file):
            with open(userinfo_file, 'wb') as client_info:
                pickle.dump((user_id,password) , client_info)
                print('user id and password saved to', userinfo_file)
    except:
        print('some kind of problem with Japanese GSI GeoNet download',file1)
        subprocess.call(['rm', '-f',file1])


def queryUNR_modern(station):
    """
    Queries the UNR database for station coordinates that has been stored in sql. downloads 
    the sql file and stores it locally if necessary

    Parameters
    -----------
    station : str
        4 character station name
    
    Returns
    -------
    lat : float
        latitude in degrees (zero if not found)
    lon : float
        longitude in degrees (zero if not found)
    ht : float
        ellipsoidal ht in meters (zzero if not found)

    """
    lat = 0; lon = 0; ht = 0
    if len(station) != 4:
        print('The station name must be four characters long')
        return lat, lon, ht

    not_in_database = False
    xdir = os.environ['REFL_CODE']
    fdir = xdir + '/Files'
    if not os.path.isdir(fdir):
        subprocess.call(['mkdir', fdir])

    # new database locations 
    nfile00 = 'gnssrefl/station_pos_2024.db'
    nfile0 = xdir + '/Files/station_pos_2024.db'

    # old database locations
    nfile1 = 'gnssrefl/station_pos.db'
    nfile2 = xdir + '/Files/station_pos.db'


    haveit,usedatabase = unr_database(nfile0, nfile00, 'station_pos_2024.db')
    if (not haveit):
        haveit,usedatabase = unr_database(nfile2, nfile1, 'station_pos.db')

    if not haveit:
        print('No station database was found.')
        return 0, 0, 0
    else:
        print('Using database ', usedatabase)
        conn = sqlite3.connect(usedatabase)

    c=conn.cursor()
    c.execute("SELECT * FROM  stations WHERE station=:station",{'station': station})
    w = c.fetchall()
    if len(w) > 0:
        [(name,lat,lon,ht)] = w
        # if longitude is ridiculous, as it often is in the Nevada Reno database make it less so
        if (lon < -180):
            lon = lon + 360
    else:
        not_in_database = True

    # close the database
    conn.close()

    # some of the Nevada Reno stations have the same names as stations used in GNSS-IR.
    # here we override them

    if (station == 'moss'):
        lat= -16.434464800 ;lon = 145.403622520 ; ht = 71.418
    elif (station == 'mnis'):
        lat = -16.667810553; lon  = 139.170597267; ht = 60.367;  
    elif (station == 'boig'):
        lat =  -9.24365375 ; lon  = 142.253961217; ht = 82.5;  
    elif (station == 'glbx'):
        lat = 58.455146633; lon  = -135.888483766 ; ht = 12.559;  
    elif (station == 'ugar'):
        lat = -9.50477824; lon = 143.54686680 ; ht =  81.2
    elif (station == 'whla'):
        lat = -33.01640186 ; lon = 137.59157111 ; ht = 7.856
    elif (station == 'kubn'):
        lat =-10.23608303 ; lon =142.21446068; ht = 78.2
    elif (station == 'smm4'):
        lat =72.57369139 ; lon =-38.470709199 ; ht = 3262

    if (not_in_database) and (lat == 0):
        print('Did not find station coordinates :', station)

    return lat,lon,ht

def rinex3_nav(year,month,day):
    """
    not sure what this does!

    """
    foundit = False
    fdir = ''
    name = ''
    # https://cddis.nasa.gov/archive/gnss/data/daily/2021/brdc/
    if (day == 0):
        doy = month
        year, month, day, cyyyy,cdoy, YMD = ydoy2useful(year,doy)
        cyy = cyyyy[2:4]
    else:
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    dir_secure = '/pub/gnss/data/daily/' + cyyyy + '/brdc/'
    bname = 'BRDC00IGS_R_' + str(year) + cdoy + '0000_01D_MN.rnx'
    filename = bname + '.gz'
    print(dir_secure, filename)
    cddis_download_2022B(filename,dir_secure)
    status = subprocess.call(['gunzip', filename])
    if os.path.exists(bname):
        foundit = True
        name = bname
    return name, fdir, foundit



def rinex_nrcan_highrate(station, year, month, day):
    """
    picks up 1-Hz RINEX 2.11 files from NRCAN
    requires gfzrnx or teqc to merge the 15 minute files

    Parameters
    ----------
    station: string
        4 character station name
    year: integer
        year
    month: integer
        month or day of year if day is set to zero
    day: integer
        day


    """
    crnxpath = hatanaka_version()
    teqcpath = teqc_version()
    gfzrnxpath = gfz_version()
    alpha='abcdefghijklmnopqrstuvwxyz'
    # if doy is input
    if day == 0:
        doy=month
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    # NRCAN moving to new server names,
    gns = 'ftp://cacsa.nrcan.gc.ca/gps/data/hrdata/' +cyy + cdoy + '/' + cyy + 'd/'


    foundFile = 0
    print('WARNING: downloading highrate RINEX data is a slow process')
    s1 = time.time()
    for h in range(0,24):
        # subdirectory
        ch = '{:02d}'.format(h)
        print('\n Hour: ', ch)
        for e in ['00', '15', '30', '45']:
            dname = station + cdoy + alpha[h] + e + '.' + cyy + 'd.Z'
            dname1 = station + cdoy + alpha[h] + e + '.' + cyy + 'd'
            dname2 = station + cdoy + alpha[h] + e + '.' + cyy + 'o'
            url = gns +  ch + '/' + dname
            if os.path.isfile(dname2):
                print('file exists:',dname2)
                foundFile = foundFile + 1
            else:
                print(url)
                try:
                    wget.download(url,dname)
                    subprocess.call(['uncompress',dname])
                    subprocess.call([crnxpath, dname1])
                    subprocess.call(['rm',dname1])
                    foundFile = foundFile + 1
                except:
                    okok = 1

    print('Found ', foundFile ,' individual files')
    if (foundFile == 0):
        print('Nothing to merge. Exiting.')
        return
    if (not os.path.isfile(gfzrnxpath)) and (not os.path.isfile(teqcpath)):
        print('teqc and gfzrnx are missing. I have nothing to merge these files with. Exiting')
        sys.exit()

    searchpath = station + cdoy + '*.' + cyy + 'o'
    print(searchpath)
    if os.path.isfile(gfzrnxpath) and (foundFile > 0):
        rinexname = station + cdoy + '0.' + cyy + 'o'
        print('Attempt to merge the 15 minute files using gfzrnx and move to ', rinexname)
        tmpname = station + cdoy + '0.' + cyy + 'o.tmp'
        subprocess.call([gfzrnxpath,'-finp', searchpath, '-fout', tmpname, '-vo','2','-f','-q'])
        cm = 'rm ' + station + cdoy + '*o'
        if os.path.isfile(tmpname):
            # try to remove the 15 minute files
            subprocess.call(cm,shell=True)
            subprocess.call(['mv',tmpname,rinexname])
            s2 = time.time(); print('That took ', int(s2-s1), ' seconds.')
        return

    if (os.path.isfile(teqcpath)) and (foundFile > 0):
        foutname = 'tmp.' + station + cdoy
        rinexname = station + cdoy + '0.' + cyy + 'o'
        print('Attempt to merge the 15 minute files with teqc and move to ', rinexname)

        mergecommand = [teqcpath + ' +quiet ' + station + cdoy + '*o']
        fout = open(foutname,'w')
        subprocess.call(mergecommand,stdout=fout,shell=True)
        fout.close()
        cm = 'rm ' + station + cdoy + '*o'
        if os.path.isfile(foutname):
            # try to remove the 15 minute files
            subprocess.call(cm,shell=True)
            subprocess.call(['mv',foutname,rinexname])
            s2 = time.time(); print('That took ', int(s2-s1), ' seconds.')
        return


def translate_dates(year,month,day):
    """
    i do not think this is used

    """
    if (day == 0):
        doy=month
        d = doy2ymd(year,doy);
        month = d.month; 
        day = d.day
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day); 
    else:
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day); 

    return doy, cdoy, cyyyy, cyy


def bfg_password():
    """
    Picks up BFG userid and password that is stored in a pickle file
    in your REFL_CODE/Files/passwords area
    If it does not exist, it asks you to input the values and stores them for you.

    Returns  
    -------
    userid : str
        BFG username
    password : str 
        BFG password
    """

    fdir = os.environ['REFL_CODE']
    if not os.path.isdir(fdir):
        print('You need to define the REFL_CODE environment variable')
        return

    # make sure the directory exists to store passwords
    if not os.path.isdir(fdir + '/Files'):
        subprocess.call(['mkdir',fdir + '/Files'])
    if not os.path.isdir(fdir + '/Files/passwords'):
        subprocess.call(['mkdir',fdir + '/Files/passwords'])

    userinfo_file = fdir + '/Files/passwords/' + 'bfg.pickle'
    #print('user information file', userinfo_file)

    #print('Will try to pick up BFG account information',userinfo_file)
    if os.path.exists(userinfo_file):
        with open(userinfo_file, 'rb') as client_info:
            login_info = pickle.load(client_info)
            user_id = login_info[0]
            passport = login_info[1]
    else:
        user_id = getpass.getpass(prompt='Userid: ', stream=None)
        passport= getpass.getpass(prompt='Password: ', stream=None)
        # save to a file
        with open(userinfo_file, 'wb') as client_info:
            pickle.dump((user_id,passport) , client_info)
        print('User id and password saved to', userinfo_file)

    return user_id, passport

def bfg_data(fstation, year, doy, samplerate=30,debug=False):
    """
    Picks up a RINEX3 file from BFG network

    Parameters 
    -----------
    fstation: string
        4 char station ID
    year: integer
        year
    doy: integer
        day of year
    samplerate: integer
        sample rate of the receiver (default is 30)
    debug: boolean
        directory file listing provided if true
        default is false

    """
    cdoy = '{:03d}'.format(doy)
    cyyyy = str(year)

    #### these are for RINEX 3 data from the BFG network
    country_code = 'DEU'#'NLD'#country code for rinex 3 file name
    rinex_rate = '{:02d}'.format(samplerate)  + 'S'
    data_server='ftp.bafg.de' # ftp server
    rinex_dirc='/obs/' #directory on the ftp server

    user_id, passport = bfg_password()

    ftp=FTP(data_server) #log in to server
    ftp.login(user=user_id, passwd = passport)
    ftp.cwd(rinex_dirc) #change to the directory

    command=cyyyy + '/'+ cdoy +'/' #issue command to go to the folder
    #print('Looking at ', year, command, fstation,rinex_rate)
    #print(data_server+rinex_dirc + command)
    #fileid = open('bfg_listing.txt','w+')
    try:
        ftp.cwd(command) #change to that directory
        files=ftp.nlst() #list files in the directory
        for f in files:
            station = f[0:4]
            if (station == fstation.upper()) and ('crx' in f):
                if (rinex_rate in f):
                    print('downloading', f, ' and ', rinex_rate)
                    ftp.retrbinary('RETR '+f, open(f,'wb').write)
    except:
        files = []
        print('Exiting - most likely because that directory -and thus the data - does not exist.')

    if debug:
        for f in files:
            print(f)

    ftp.quit()
    return

def inout(c3gz):
    """
    Takes a Hatanaka rinex3 file that has been gzipped
    gunzips it and decompresses it 

    Parameters
    ----------
    c3gz : string
        name of a gzipped hatanaka compressed RINEX 3 filename

    Returns
    -------
    translated : boolean
        whether file was successfully translated or not 

    rnx : string
        filename of the uncompressed and de-Hatanaka'ed RINEX file

    """

    translated = False # assume failure
    c3 = c3gz[:-3] # crx filename
    rnx = c3.replace('crx','rnx') # rnx filename
    # gunzip
    if os.path.exists(c3gz):
        subprocess.call(['gunzip', c3gz])

    # executable
    crnxpath = hatanaka_version()
    if not os.path.exists(crnxpath):
        hatanaka_warning()
    else:
        if os.path.exists(c3): # file exists
            subprocess.call([crnxpath,c3])
    if os.path.exists(rnx): # file exists
        translated = True
        subprocess.call(['rm','-f',c3])

    return translated, rnx



def ga_highrate(station9,year,doy,dec,deleteOld=True):
    """
    Attempts to download highrate RINEX from GA

    Parameters
    ----------
    station9 : str
        nine character station name appropriate for rinex 3
    year : int
        full year
    doy : int
        day of year
    dec : int
        decimation value.  1 or 0 means no decimation
    deleteOld : bool
        whether to delete old rinex 3 files

    Returns 
    -------
    rinex2 : string
        rinex2 filename created by merging 96 files!
    fexist : boolean
        whether a rinex2 file was successfully created

    """
    station = station9[0:4].lower()
    cyyyy = str(year)
    cyy  = cyyyy[2:4]
    cdoy = '{:03d}'.format(doy)
    crnxpath = hatanaka_version()
    gexe = gfz_version()
    if not os.path.exists(gexe):
        print('no gfzrnx executable. exiting.')
        return

    if not os.path.exists(crnxpath):
        hatanaka_warning()
        return
    print('WARNING 1: Have some coffee, downloading 96 files of high-rate GPS data takes a long time.')
    print('WARNING 2: Downloading 96 files of high-rate GPS data from Australia takes an even longer time.')
    QUERY_PARAMS, headers = k.ga_stuff_highrate(station9, year, doy)
    API_URL = 'https://data.gnss.ga.gov.au/api/rinexFiles/'
    request = requests.get(API_URL, QUERY_PARAMS, headers=headers)

    gobblygook = myfavoriteobs()
    v=0
    crate = str(dec)
    rinex2 =  station + cdoy + '0.' + cyy + 'o'
    if len(json.loads(request.content)) >= 1:
        for query_response_item in json.loads(request.content):
            file_url = query_response_item['fileLocation']
            file_name = urlparse(file_url).path.rsplit('/', 1)[1]
            newname = file_name[:-3]
            rinexname = newname[:-3] + 'rnx'
            v = v + 1
            cv = '{:02d}'.format(v)
            tmpname=  'tmp' + cv + '.' + station + cdoy + '0.'  + cyy + 'o'
            # if you ran the program previously and have the files online
            if os.path.exists(rinexname):
                print(cv, file_name, tmpname)
                if (dec > 1):
                    subprocess.call([gexe,'-finp', rinexname, '-fout', rinex2, '-vo','2','-ot', gobblygook, '-sei','out','-smp', crate, '-f','-q'])
                else:
                    subprocess.call([gexe,'-finp', rinexname, '-fout', rinex2, '-vo','2','-ot', gobblygook, '-sei','out','-f','-q'])
                subprocess.call(['mv', rinex2,tmpname])
            else:
                if os.path.exists(file_name): # file exists
                    print('file exists so gunzip it')
                    subprocess.call(['gunzip', file_name])
                else:
                    # download and gunzip it
                    print(cv, file_name)
                    wget.download(file_url,file_name)
                    subprocess.call(['gunzip', file_name])

                # hatanaka uncompress it
                if os.path.exists(newname):
                    subprocess.call([crnxpath, newname])

                if os.path.exists(rinexname):
                    if (dec > 1):
                        subprocess.call([gexe,'-finp', rinexname, '-fout', rinex2, '-vo','2','-ot', gobblygook, '-sei','out','-smp', crate, '-f','-q'])
                    else:
                        subprocess.call([gexe,'-finp', rinexname, '-fout', rinex2, '-vo','2','-ot', gobblygook, '-sei','out','-f','-q'])
                    subprocess.call(['mv', rinex2,tmpname])

# now merge them
    searchpath = 'tmp' + '*' + station + cdoy + '0.' + cyy + 'o'
    subprocess.call([gexe,'-finp', searchpath, '-fout', rinex2, '-vo','2','-f'])
    fexist = False
    if os.path.exists(rinex2):
        fexist = True

# remove detritus
    searchpath = 'tmp*' + station + cdoy + '0.' + cyy + 'o'
    cm ='rm -f ' + searchpath
    subprocess.call(cm,shell=True)
    if deleteOld:
        searchpath = station9.upper()  + '*' + cyyyy + cdoy + '*rnx'
        cm ='rm -f ' + searchpath
        subprocess.call(cm,shell=True)
        searchpath = station9.upper()  + '*' + cyyyy + cdoy + '*crx'
        cm ='rm -f ' + searchpath
        subprocess.call(cm,shell=True)
    return rinex2, fexist


def cddis_download_2022B_new(filename,directory):
    """
    download code for CDDIS using https and password

    Parameters
    ----------
    filename : str
        name of the rinex file or orbit file

    directory : str
        where the file lives at CDDIS

    """
    print('New way of CDDIS downloads')
    basename = 'https://cddis.nasa.gov/archive'
    url = basename + directory + filename
    print(url)
    # Makes request of URL, stores response in variable r
    user,passw = cddis_password()

# requests.get('https://httpbin.org/basic-auth/user/pass', auth=('user', 'pass'))
    r = requests.get(url,auth=('user','passw'))

    if (r.status_code == 200):
# Opens a local file of same name as remote file for writing to
        with open(filename, 'wb') as fd:
            for chunk in r.iter_content(chunk_size=1000):
                fd.write(chunk)

# Closes local file
        fd.close()
    else:
        print('File does not exist')

def cddis_download_2022B(filename,directory):
    """
    Nth iteration of download code for CDDIS

    Parameters
    ----------
    filename : str
        name of the rinex file or orbit file

    directory : str
        where the file lives at CDDIS

    """
    #print('Original way of accessing CDDIS ')

    ftps = FTP_TLS(host = 'gdc.cddis.eosdis.nasa.gov')
    email = 'kristine.larson@colorado.edu'
    ftps.login(user='anonymous', passwd=email)
    ftps.prot_p()
    ftps.cwd(directory)
    ftps.retrbinary("RETR " + filename, open(filename, 'wb').write)
    siz = os.path.getsize(filename)
    if siz == 0:
        print('No file found')
        subprocess.call(['rm',filename])

def getnavfile_archive(year, month, day, archive):
    """
    picks up nav file from a specific archive and stores it in the ORBITS directory

    Parameters
    ----------
    year: integer
        full year
    month: int
        calendar month, or day of year
    day: int
        day of the month, or zero
    archive : str
        name of the GNSS archive. currently allow sopac and esa

    Returns
    -------
    navname : str
        name of navigation file (should always be auto???0.yyn, so unclear to me 
        why it is sent)
    navdir : str
        location of where the file has been stored
    foundit : bool
        whether the file was found

    """
    # make sure directories exist for orbits
    ann = make_nav_dirs(year)
    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)
    navname,navdir = nav_name(year, month, day)

    foundit = check_navexistence(year,month,day)

    if (not foundit):
        if (archive == 'esa'):
            foundit =get_esa_navfile(cyyyy,cdoy)
        if (archive == 'sopac'):
            xx = get_sopac_navfile(navname,cyyyy,cyy,cdoy)
        # found it at one of the preferred archives
        if (archive == 'cddis'):
            get_cddis_navfile(navname,cyyyy,cyy,cdoy)
        if os.path.exists(navname):
            subprocess.call(['mv',navname, navdir])
            foundit = True
        else:
            foundit = False

    if (not foundit):
        print('No navfile found at ', archive)

    return navname,navdir,foundit

def check_navexistence(year,month,day):
    """
    Check to see if you already have the nav file. Uncompresses it 
    if necessary

    Parameters
    ----------
    year : int
        full year
    month : int
        month or doy if day is zero
    day : int
        day of month or 0 

    Returns 
    -------
    foundit : boolean
        whether nav file has been found
    """
    foundit = False
    navname,navdir = nav_name(year, month, day)
    nfile = navdir + '/' + navname
    if not os.path.exists(navdir):
        subprocess.call(['mkdir',navdir])
    #print('Looking for ', navname, navdir)

    if os.path.exists(nfile):
        foundit = True
    if (not foundit) and (os.path.exists(nfile + '.xz' )):
        subprocess.call(['unxz',nfile + '.xz'])
        foundit = True
    if (not foundit) and (os.path.exists(nfile + '.gz' )):
        subprocess.call(['gunzip',nfile + '.gz'])
        foundit = True

    if foundit:
        print('Nav file exists online')

    return foundit

def ymd2ch(year,month,day):
    """
    returns doy and character versions of year,month,day
    if day is zero, it assumes doy is in the month input

    Parameters
    ----------
    year : int
        full year

    month : int
        if day is zero this is day of yaer

    day : int
        day of month or zero 

    Returns
    -------
    month : int
        numerical month of the year
    day : int
        day of the month
    doy : int
        day of year
    cyyyy : str
        4 ch year
    cyy : str
        2 ch year
    cdoy : str
        4 ch year

    """
    if (day == 0):
       doy=month
       d = doy2ymd(year,doy);
       month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)

    return month, day, doy, cyyyy, cyy, cdoy

def geoidCorrection(lat,lon):
    """
    Calculates the EGM96 geoid correction

    Parameters
    ----------
    lat : float
        latitude, degrees
    lon : float
        longitude, degrees

    Returns
    -------
    geoidC : float
        geoid correction in meters

    """
    # check that file exists
    foundfile = checkEGM()
    egm = EGM96.EGM96geoid()
    geoidC = egm.height(lat=lat,lon=lon)

    return geoidC

def checkEGM():
    """
    Downloads and stores EGM96 file in REFL_CODE/Files for use in refl_zones

    Returns
    -------
    foundfile : bool
        whether EGM96 file was found (or installed) on your local machine

    """
    foundfile = False
    xdir = os.environ['REFL_CODE']
    matfile = 'EGM96geoidDATA.mat'
    localdir = xdir + '/Files/'
    if not os.path.isdir(localdir):
        print('Making ', localdir)
        subprocess.call('mkdir',localdir)

    egm = localdir + matfile
    if 'REFL_CODE' in os.environ:
        egm = localdir + matfile
        interiorfile = 'gnssrefl/' + matfile
        if os.path.isfile(egm):
            #print('EGM96 file exists')
            foundfile = True
        elif os.path.isfile(interiorfile):
            print('cp EGM96 file to where it belongs')
            subprocess.call(['cp',interiorfile, localdir])
            foundfile = True
        else:
            print('EGM96 file does not exist. We will try to download and store it in ',localdir)
            githubdir = 'https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/docs/'   
            wget.download(githubdir+matfile, localdir + matfile)
            if os.path.isfile(egm):
                print('successful download, EGM file exists')
                foundfile = True
            else:
                print('unsuccessful download')
    else:
        print('The REFL_CODE environment variable has not been set.')

    return foundfile 

def save_plot(plotname):
    """
    save plot and send location info to the screen

    Parameters
    ----------
    plotname : str
        name of output figure file
    """
    plt.savefig(plotname,dpi=300)
    print('Plot file saved as: ', plotname)


def make_azim_choices(alist):
    """
    not used yet

    Parameters
    ----------
    alist : list of floats
        azimuth pairs - must be even number of values, i.e.
        [amin1, amax1, amin2, amax2]

    azval : list of floats
        azimuth regions for lomb scargle periodograms

    """
# want to make a list for make_json_input
# lsp['azval'] = [0, 90, 90, 180, 180, 270, 270, 360]
    if alist[0] < 0 | alist[-1] < 0 :
        print('We do not currently allow negative azimuths ')
        sys.exit()

    if len(alist) == 2:
        deltaA = np.diff(alist)
        if (deltaA < 100):
            azval = alist
        elif (deltaA >=100) & (deltaA <= 180):
            # divide by two
            d = int(deltaA/2)
            azval = [alist[0], alist[0] + d, alist[0] + d,  alist[-1]]
        elif (deltaA >=180) & (deltaA <= 270):
            # divide by three
            d = int(deltaA/3)
            azval = [alist[0], alist[0] + d, alist[0] + d,  
                    alist[0] + 2*d, alist[0]+2*d, alist[-1]]
        else:
            # divide by three
            d = int(deltaA/4)
            azval = [alist[0], alist[0] + d, alist[0] + d,  alist[0] + 2*d, 
                    alist[0]+2*d, alist[0] + 3*d, alist[0]+3*d, alist[-1]]
    else:
        print('We only allow one set of azimuth ranges at the current time') ; sys.exit()

    print('Input Azlist: ', alist, ' Output list ', azval)

    return azval

def set_subdir(subdir):
    """
    make sure that subdirectory exists for output files 
    should return the directory name ... 

    Parameters
    ----------
    subdir : str
        subdirectory in $REFL_CODE/Files

    """
    xdir = os.environ['REFL_CODE']
    if not os.path.exists(xdir):
        print('The REFL_CODE environment variable must be set')
        print('This will tell the code where to put the output.')
        sys.exit()

    outdir = xdir  + '/Files/'
    if not os.path.exists(outdir) :
        subprocess.call(['mkdir', outdir])

    if subdir == '':
        okokk = 1
        #print('Using this output directory: ', outdir)
    else:
        outdir = xdir  + '/Files/' + subdir + '/'
        #print('Using this output directory: ', outdir)
        if not os.path.exists(outdir) :
            subprocess.call(['mkdir', outdir])

    return


def mjd_more(mmjd):
    """
    This is not working yet.  

    Parameters
    ----------
    mmjd : float
        mod julian date

    Returns
    -------
    year : int
        full year
    mm : int
        month
    dd : int
        day
    doy : int
        day of year
    """
    year,mm,dd = mjd_to_date(mmjd)
    doy, cdoy, cyyyy, cyy = ymd2doy(year,mm,dd)

    return year, mm, dd, doy 


def quickazel(gweek,gpss,sat, recv,ephemdata,localup,East,North):
    """
    assumes you have read in the broadcast ephemeris,
    know where your receiver is and the time (gps week, second of week)
    """
    closest = myfindephem(gweek, gpss, ephemdata, sat)
    eleA = 0; azimA = 0
    if len(closest) > 0:
        #print(gweek,gpss,sat)
        satv = rnx.satorb_prop(gweek, gpss, sat, recv, closest)
        r=np.subtract(satv,recv) # satellite minus receiver vector
        eleA = elev_angle(localup, r)*180/np.pi
        azimA = azimuth_angle(r, East, North)
        #print('el/az',eleA, azimA)
    return eleA, azimA

def quickp(station,t,sealevel):
    """
    makes a quick plot of sea level 
    prints the plot to the screen - it does not save it.

    Parameters
    ----------
    station : str
        station name
    t : numpy array in datetime format
        time of the sea level observations UTC
    sealevel : list of floats
        meters (unknown datum)

    """
    fs = 10
    if (len(t) > 0):
        fig,ax=plt.subplots(figsize=(10,5))
        ax.plot(t, sealevel, 'b-')
        plt.title('Water Levels: ' + station.upper())
        plt.xticks(rotation =45,fontsize=fs);
        plt.ylabel('meters')
        plt.grid()
        fig.autofmt_xdate()
        plt.show()
    else:
        print('no data found - so no plot')
    return


def cddis_restriction(iyear, idoy,archive):
    """
    CDDIS has announced a restructuring of their archive.
    After 6 months files are tarred. It would be ok for the code
    to accommodate this change, but it will have to come from the community.
    If six months has passed since you ran the code, a warning will come to the 
    screen and the code will exit.

    updated now that i realize BKG does the same thing

    Parameters
    ----------
    iyear : int
        year you want to download from CDDIS
    idoy : int
        day of year you want to download from CDDIS

    archive : str
        name of archive

    Returns
    -------
    bad_day : bool
        if bad_day is true, you cannot access high-rate data from CDDIS or BKG

    """
# find out today's date
    year = int(date.today().strftime("%Y"));
    month = int(date.today().strftime("%m"));
    day = int(date.today().strftime("%d"));

    today=datetime.datetime(year,month,day)
    doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
    tdate = year + doy/365.25

    # input date
    idate = iyear + idoy/365.25

    if (tdate - idate) > 0.5:
        # i.e. half a year is six months
        bad_day =  True
        print(archive.upper() + ' does not allow direct access to their high-rate data for this day and year. ')
        print('They now tar files six months after the data archived. If you are willing to ')
        print('submit a pull request to fix this issue, we would be very willing to host it.')

    else:
        bad_day = False


    return bad_day


def cddis_password():
    """
    Picks up cddis userid and password that is stored in a pickle file
    in your REFL_CODE/Files/passwords area
    If it does not exist, it asks you to input the values and stores them for you.

    Returns
    -------
    userid : str
        cddis username

    password : str
        cddis password

    """

    fdir = os.environ['REFL_CODE']
    if not os.path.isdir(fdir):
        print('You need to define the REFL_CODE environment variable')
        return

    # make sure the directory exists to store passwords
    if not os.path.isdir(fdir + '/Files'):
        subprocess.call(['mkdir',fdir + '/Files'])
    if not os.path.isdir(fdir + '/Files/passwords'):
        subprocess.call(['mkdir',fdir + '/Files/passwords'])

    userinfo_file = fdir + '/Files/passwords/' + 'cddis.pickle'
    #print('user information file', userinfo_file)

    #print('Will try to pick up BFG account information',userinfo_file)
    if os.path.exists(userinfo_file):
        with open(userinfo_file, 'rb') as client_info:
            login_info = pickle.load(client_info)
            user_id = login_info[0]
            passport = login_info[1]
    else:
        print('You need a earthdata account to access NASA data.')
        print('https://urs.earthdata.nasa.gov/')
        user_id = getpass.getpass(prompt='Userid: ', stream=None)
        passport= getpass.getpass(prompt='Password: ', stream=None)
        # save to a file
        with open(userinfo_file, 'wb') as client_info:
            pickle.dump((user_id,passport) , client_info)
        print('User id and password saved to', userinfo_file)

    return user_id, passport



def gbm_orbits_direct(year,month,day):
    """
    downloads gfz multi-gnss orbits, aka gbm orbits, directly from GFZ.
    thus avoids CDDIS.  it first checks to see if you have the files online.
    both version of the long name.

    Parameters
    ----------
    year : int
        full year
    month : int
        month number or day of year if day is set to zero
    day : int
        calendar day of month

    """
    foundit = False
    return_name = ''

    month, day, doy, cyyyy, cyy, cdoy = ymd2ch(year,month,day)
    gpsweek,sec=kgpsweek(year,month,day,0,0,0)
    cgpsweek = str(gpsweek)

    # they changed during 2245 ... 
    if (gpsweek < 2245):
        gns = 'ftp://ftp.gfz-potsdam.de/pub/GNSS/products/mgex/' + cgpsweek + '/'
    else:
        gns = 'ftp://ftp.gfz-potsdam.de/pub/GNSS/products/mgex/' + cgpsweek + '_IGS20/'

    fdir = os.environ['ORBITS'] + '/' + cyyyy + '/sp3'
    littlename = 'gbm' + str(gpsweek) + str(int(sec/86400)) + '.sp3'
    bigname = 'GFZ0MGXRAP_' + cyyyy + cdoy + '0000_01D_05M_ORB.SP3'

    bigname2 = 'GBM0MGXRAP_' + cyyyy + cdoy + '0000_01D_05M_ORB.SP3'
    print(bigname, bigname2)

    # first, do you have it locally?  
    # look for compressed file
    fullname = fdir + '/' + littlename 
    if os.path.isfile(fullname):
        foundit = True
        return_name = littlename
    elif os.path.isfile(fullname + '.gz'):
        subprocess.call(['gunzip', fullname + '.gz'])
        foundit = True; 
        return_name = littlename

    if not foundit:
        fullname = fdir + '/' + bigname 
        if os.path.isfile(fullname):
            foundit = True
            return_name = bigname
        elif os.path.isfile(fullname + '.gz'):
            subprocess.call(['gunzip', fullname + '.gz'])
            foundit = True; 
            return_name = littlename

    # checked for the first kind of name because that is how it was stored on CDDIS.
    # now use the name as how it is stored at GFZ.  I think
    bigname = bigname2 
    if not foundit:
        url = gns + littlename + '.Z'
        print(url)
        try:
            wget.download(url,littlename + '.Z')
            subprocess.call(['uncompress', littlename + '.Z'])
        except:
            okok = 1

        if os.path.isfile(littlename):
            foundit = True ; return_name = littlename
        else:
            url = gns + bigname + '.gz'
            print(url)
            try:
                wget.download(url,bigname + '.gz')
                subprocess.call(['gunzip', bigname + '.gz'])
                foundit = True ; return_name = bigname
            except:
                okok = 1


    # store the file
    if os.path.isfile(littlename):
        store_orbitfile(littlename,year,'sp3') ; 
    elif os.path.isfile(bigname):
        store_orbitfile(bigname,year,'sp3') ; 

    if not foundit:
        print('Orbit was not found at GFZ or in a local directory')
    #else:
    #    print('Orbit found')

    return return_name, fdir, foundit


def checkFiles(station, extension):
    """
    apparently no one consistently checks for the Files directory existence.
    this is an attempt to fix that.

    Parameters
    ----------
    station : str
        4 ch station ID

    extension : str
        subdirectory for results in $REFL_CODE/Files/station

    """
    xdir = os.environ['REFL_CODE']
    if not os.path.isdir(xdir):
        print('REFL_CODE environment variable has not been set. Exiting')
        sys.exit()

    txtdir = xdir + '/Files/' 
    if not os.path.exists(txtdir) :
        subprocess.call(['mkdir', txtdir])
        print(txtdir , ' has been created.')
    txtdir = xdir + '/Files/'  + station
    if not os.path.exists(txtdir) :
        subprocess.call(['mkdir', txtdir])
        print(txtdir , ' has been created.')

    if (len(extension) > 0):
        txtdir = xdir + '/Files/'  + station + '/' + extension
        if not os.path.exists(txtdir) :
            subprocess.call(['mkdir', txtdir])
            print(txtdir , ' has been created')


def read_leapsecond_file(mjd):
    """
    reads leap second file and tries to figure out the UTC-GPS time offset
    needed for NMEA file users for the given MJD value

    It will download and store the leap second file in REFL_CODE/Files if 
    you don't already have it.

    Parameters
    ----------
    mjd : float
        Modified Julian Day for when you want to know the leap seconds since
        GPS began

    Returns
    -------
    offset : int
        UTC-GPS time offset in seconds. This should be added to UTC to get GPS

    """
    offset = 0
    xdir = os.environ['REFL_CODE']
    if not os.path.isdir(xdir):
        print('REFL_CODE environment variable has not been set. Exiting')
        sys.exit()
    # Fire currently loaded here
    xdir = os.environ['REFL_CODE'] + '/input'
    if not os.path.isdir(xdir):
         subprocess.call(['mkdir', xdir])

    # in case you decide to put it here
    xdir = os.environ['REFL_CODE'] + '/Files'
    if not os.path.isdir(xdir):
         subprocess.call(['mkdir', xdir])

    # I changed it to look for leap second file in Files
    xdir = os.environ['REFL_CODE'] + '/Files/leapseconds.txt' 
    # if file is not on your system, download it
    if not os.path.isfile(xdir):
        print('Trying to download leapsecond file from github')
        url= 'https://github.com/kristinemlarson/gnssrefl/raw/master/gnssrefl/leapseconds.txt'
        print(url)
        wget.download(url,xdir)
    if not os.path.isfile(xdir):
        print('Trying to download leapsecond file from morefunwithgps')
        url = 'https://morefunwithgps.com/public_html/leapseconds.txt'
        print(url)
        wget.download(url,xdir)
    if not os.path.isfile(xdir):
        print('Could not find the leap second file. Exiting.')
        sys.exit()

    tv = np.loadtxt(xdir,usecols=(1),comments='%')
    N = len(tv)
    # these leap seconds are set to dec 31 or june 30 but are applied at midnight
    # so add one day ...
    tv = tv + 1
    # add a value to an end point
    for i in range(0,N):
        #print(i,tv[i], mjd)
        if (i == (N-1)):
            #print('found the correct leap second ',i+1)
            offset = i+1
        elif (mjd > tv[i] ) & (mjd < tv[i+1]):
            #print('found the correct leap second ',i+1)
            offset = i+1
            break

    return offset

def ydoy2datetime(y,doy):
    """
    translates year/day of year numpy array into datetimes for plotting

    this was running slow for large datasets.  changing to use lists
    and then asarray to numpy

    Parameters
    ----------
    y : numpy array of floats
        full year
    doy : numpy array of floats
        day of year

    Returns
    -------
    bigT : numpy array
        datetime objects

    """
    obstimes = []
    obstimes_list = []
    N = len(y)
    for i in range (0,N):
        yy = int( y[i] );
        ddoy = int(doy[i])
        d = datetime.datetime(yy, 1, 1) + datetime.timedelta(days=(ddoy-1))
        #print(yy,ddoy,d.month,d.day)
        bigT = datetime.datetime(year=yy, month=d.month, day=d.day)
        #obstimes = np.append(obstimes,bigT)
        obstimes_list.append(bigT)

    obstimes = np.asarray(obstimes_list)

    return obstimes

def unr_database(file1, file2, database_file):
    """
    Checks to see if the database lives in either file1 or file2
    locations. Stem of the filename is third input, database_file

    Parameters
    ----------
    file1 : str
        full name of database in $REFL_CODE/Files
    file2 : str
        full name of database in local gnssrefl directory
    database_file : str
        database file name

    Returns
    -------
    exists_now : bool
        whether you were successful in finding the database 
    database_location : str
        full name of the database you found and want to use going on

    """
    # get the new database
    exists_now = True
    exist1 = os.path.isfile(file1)
    exist2 = os.path.isfile(file2)

    if (not exist1) & (not exist2):
        url1= 'https://github.com/kristinemlarson/gnssrefl/raw/master/gnssrefl/' + database_file
        print('Try to download the station database from github for you:', url1)
        print('If you are not online, it will fail.')
        print('If you are able to manually download the file')
        print('it should be stored in the $REFL_CODE/Files directory')
        try:
            wget.download(url1,file1)
            exists_now = True
        except:
            print('Could not download the new UNR database for you')
            exists_now = False

    exist1 = os.path.isfile(file1)
    exist2 = os.path.isfile(file2)

    if (not exist1) & exist2:
        print('cp from local directory to Files directory because that is where it goes')
        subprocess.call(['cp', file2, file1])

    # just to be sure
    if (not exist1) & (not exist2):
        exists_now = False

    return exists_now , file1


