from scipy.interpolate import interp1d
import math
import numpy as np
import os
import subprocess
import sys
import time
import wget

import gnssrefl.gps as g

import simplekml


# https://developers.google.com/kml/documentation/kml_tut#ground-overlays


def makeFresnelEllipse(A,B,center,azim):
    """
    make an Fresnel zone given size, center, and orientation

    Parameters
    ----------
    A : float
        semi-major axis of ellipse in meters
    B : float
        semi-minor axis of ellipse in meters
    center : float 
        center of the ellipse, provided as distance along the satellite azimuth direction
    azimuth : float
        azimuth angle of ellipse in degrees. 
        this will be clockwise positive as defined from north

    Returns
    --------
    x : numpy array of floats 
        x value of cartesian coordinates of ellipse
    y : numpy array of floats
        y value of cartesian coordinates of ellipse
    xcenter : float
        x value for center of ellipse in 2-d cartesian
    ycenter : float
        y value for center of ellipse in 2-d cartesian

    """

    # this is backwards but it works and i have stopped caring
    width =  A
    height = B
    # fro my matlab code
    angle = 360-azim  + 90

    allAngles = np.deg2rad(np.arange(0.0, 375.0, 15.0))
    # get the x and y coordinates for an ellipse centered at 0,0
    x =  width * np.cos(allAngles)
    y =  height * np.sin(allAngles)

    # rotation angle for the ellipse
    rtheta = np.radians(angle)
    # rotation array
    R = np.array([
        [np.cos(rtheta), -np.sin(rtheta)],
        [np.sin(rtheta),  np.cos(rtheta)], ])
    

#   rotate x and y into this new system
    x, y = np.dot(R, np.array([x, y]))
#   figure out center of the ellipse
    xcenter = center*np.cos(rtheta)
    ycenter = center*np.sin(rtheta)
    # print('center of the ellipse', xcenter, ycenter)
# finally, new coordinates for x and y
    x += xcenter
    y += ycenter
    return x, y, xcenter, ycenter


def FresnelZone(f,e,h):
    """
    based on GPS Tool Box Roesler and Larson (2018).
    Original source is Felipe Nievinski as published in the appendix of 
    Larson and Nievinski 2013
    this code assumes a horizontal, untilted reflecting surface    

    Parameters
    ----------
    f : int
        frequency (1,2, or 5)
    e : float
        elevation angle (deg)
    h : float
        reflector height (m)

    Returns
    -------
    firstF: list of floats 
        [a, b, R ] in meters where:
        a : is the semi-major axis, aligned with the satellite azimuth 
        b : is the semi-minor axis
        R : locates the center of the ellispe on the satellite azimuth direction (theta)

    """

# SOME GPSCONSTANTS	
    CLIGHT = 299792458;  # speed of light, m/sec
    FREQ = [0, 1575.42e6, 1227.6e6, 0, 0, 1176.45e6];   # GPS frequencies, Hz
    CYCLE = CLIGHT/FREQ[f]; #  wavelength per cycle (m/cycle)
    RAD2M = 0.5*CYCLE/np.pi; # % (m)
    erad = e*np.pi/180;

# check for legal frequency later

# delta = locus of points corresponding to a fixed delay;
# typically the first Fresnel zone is is the 
# "zone for which the differential phase change across
# the surface is constrained to lambda/2" (i.e. 1/2 the wavelength)
    delta = CYCLE/2; # 	% [meters]


# semi-major and semi-minor dimension
# from the appendix of Larson and Nievinski, 2013
    sin_elev = math.sin(erad);
    d = delta; 
    B = math.sqrt( (2*d*h / sin_elev) + (d/sin_elev)*(d/sin_elev) ) ; # % [meters]
    A = B / sin_elev ; #% [meters]


# determine distance to ellipse center 
    center = (h + delta/sin_elev)/ math.tan(erad)  #  	% [meters]
#    print('center distance is', center)

    return A, B, center

def makeEllipse_latlon(freq,el,h,azim,latd,lngd):
    """
    for given fresnel zone, produces coordinates of an ellipse

    Parameters
    ----------
    freq : int
        frequency
    el : float
        elevation angle in degrees
    h : float
        reflector height in meters
    azim : float
        azimuth in degrees
    latd : float
        latitude in degrees
    lngd : float
        longitude in degrees

    Returns
    -------
    lngdnew : float
        new longitudes in degrees

    latdnew : float
        new latitudes in degrees

    """
    A,B,center = FresnelZone(freq,el,h) 
    # print(A,B,center)
    x,y,xc,yc = makeFresnelEllipse(A,B,center,azim)
    d=np.sqrt(x*x+y*y); # this is in meters  
    d=d/1000; # convert d from meters to km
    # average Radius of Earth, in km
    R=6378.14; 
    theta=np.arctan2(x,y)
# map coordinates need a reference, so use the station coordinates, in degrees and radians
    lat = latd*np.pi/180
    lng = lngd*np.pi/180
    sinlat = math.sin(lat)
    coslat = math.cos(lat)

# this will be in radians
    latnew= np.arcsin(sinlat*np.cos(d/R) + coslat*np.sin(d/R)*np.cos(theta) );

    arg1 =  np.sin(theta)*np.sin(d/R)*coslat
    arg2 =  np.cos(d/R) - sinlat*np.sin(latnew)
# new lngnew will be degrees
    lngnew = lngd + 180.0/np.pi  * np.arctan2(arg1, arg2)
# put latitude back into degrees
    latnew=latnew*180./np.pi 

    return lngnew, latnew

def set_final_azlist(a1ang,a2ang,azlist):
    """
    edits initial azlist to restrict to given azimuths

    Parameters
    ----------
    a1ang : float
        minimum azimuth (degrees)
    a2ang : float
        maximum azimuth (degrees)
    azlist : list of floats 
        list of tracks, [azimuth angle, satNumber, elevation angle ]

    Returns
    -------
    azlist : list of floats

    """
# we convert the azimuth tracks to -180 to 180, sort of
    if (a1ang < 0):
        kk = (azlist[:,0] > 0) & (azlist[:,0] < a2ang)
        kk2 = (azlist[:,0] > (360+a1ang)) & (azlist[:,0] < 360)
        azlist1 = azlist[kk,:]
        azlist2 = azlist[kk2,:]
        azlist = np.vstack((azlist1, azlist2))
    # these might overlap if you put in silly numbers but i don't think it will crash
    else:
        kk = (azlist[:,0] > a1ang) & (azlist[:,0] < a2ang)
        azlist = azlist[kk,:]

    return azlist


def set_azlist_multi_regions(sectors,azlist):
    """
    edits initial azlist to restrict to given azimuth sectors.
    assumes that illegal list of sectors have been checked (i.e.
    no negative azimuths, they should be pairs, and increasing)

    Parameters
    ----------
    sectors: list of floats
        min and max azimuth (degrees). Must be in pairs, no negative numbers
    azlist : list of floats
        list of tracks, [azimuth angle, satNumber, elevation angle ]

    Returns
    -------
    azlist2 : list of floats
         same format as before, but with azimuths removed outside the restricted zones

    """
    npairs = int(len(sectors)/2)
    azlist2 = np.empty(shape=[0, 3])
    for n in range(0,npairs):
        a1 = sectors[n*2] # min azim of sector
        a2 = sectors[n*2+1] # max zzim of sector
        kk = (azlist[:,0] > a1) & (azlist[:,0] < a2)
        azlistsec = azlist[kk,:]
        azlist2 = np.vstack((azlist2, azlistsec))

    return azlist2

def calcAzEl_new(prn, newf,recv,u,East,North):
    """
    function to gather azel for all low elevation angle data
    this is used in the reflection zone mapping tool

    Parameters
    ----------
    prn : int
        satellite number
    newf : 3 vector of floats
        cartesian coordinates of the satellite (meters)
    recv : 3 vector of floats
        receiver coordinates (meters)
    u : 3 vector
        cartesian unit vector for up
    East : 3 vector
        cartesian unit vector for east direction
    North : 3 vector
        cartesian unit vector for north direction

    Returns
    -------
    tv : numpy array of floats
        list of satellite tracks
        [prn number, elevation angle, azimuth angle]
    """
    tv = np.empty(shape=[0, 3])
    # number of values
    NV = len(newf)
    #for t in range(0,480):
    for t in range(0,NV):
        satv= [newf[t,2], newf[t,3],newf[t,4]]
        etime = newf[t,1]
        r=np.subtract(satv,recv) # satellite minus receiver vector
        eleA = g.elev_angle(u, r)*180/np.pi
        #Check if the elevation angle is within the allowed range
        if ( (eleA >= 0) & (eleA <= 61)):
            azimA = g.azimuth_angle(r, East, North)
#            print(etime, eleA, azimA)
            newl = [prn, eleA, azimA]
            tv = np.append(tv, [newl],axis=0)
    nr,nc=tv.shape
    return tv


def rising_setting_new(recv,el_range,obsfile):
    """
    Calculates potential rising and setting arcs

    Parameters
    ----------
    recv : list of floats
         Cartesian coordinates of station in meters
    el_range : list of floats
         elevation angles in degrees
    obsfile : str
         orbit filename

    Returns
    -------
    azlist : list of floats
        azimuth angle (deg), PRN, elevation angle (Deg)

    """
    # will put azimuth and satellite number
    azlist = np.empty(shape=[0, 3])
    # these are in degrees and meters
    lat, lon, nelev = g.xyz2llhd(recv)
    # calculate unit vectors
    u, East,North = g.up(np.pi*lat/180,np.pi*lon/180)
    # load the cartesian satellite positions
    f = np.genfromtxt(obsfile,comments='%')
    r,c = f.shape
    # print('Number of rows:', r, ' Number of columns:',c)
#   reassign the columns to make it less confusing
    sat = f[:,0]; t = f[:,1]; x = f[:,2]; y = f[:,3]; z =  f[:,4]
#   examine all 32 satellites
#   should this be more for Beidou?
    for prn in range(1,33):
        newf = f[ (f[:,0] == prn) ]
        tvsave=calcAzEl_new(prn, newf,recv,u,East,North)
        nr,nc=tvsave.shape
        for e in el_range:
            #print('elevation angle: ', e)
            el = tvsave[:,1] - e
            for j in range(0,nr-1):
                az = round(tvsave[j,2],2)
                newl = [az, prn, e]
                if ( (el[j] > 0) & (el[j+1] < 0) ) :
                    azlist = np.append(azlist, [newl], axis=0)
                if ( (el[j] < 0) & (el[j+1] > 0) ) :
                    azlist = np.append(azlist, [newl], axis=0)

    return azlist

def write_coords(lng, lat):
    """
    Parameters
    ----------
    lng : list of floats
        longitudes in degrees
    lat : list of floats 
        latitudes in degrees

    Returns
    -------
    points : list of pairs  of long/lat
        for google maps

    """
    points = []
    data = [lng, lat]
    for i in range(len(lng)):
        coord = (data[0][i], data[1][i])
        points.append(coord)
        i+=1

    return points

# Function makes the fresnel zones to KML file
def make_FZ_kml(station, filename,freq, el_list, h, lat,lng,azlist):
    """
    makes fresnel zones for given azimuth and elevation angle 
    lists.  

    Parameters
    ----------
    station: str
        four character station name
    filename : str
        output filename (the kml extension should already be there)
    freq : int
        frequency (1,2, or 5)
    el_list : list of floatss
        elevation angles
    h : float
        reflector height in meters
    lat : float
        latitude in deg
    lng : float 
        longitude in degrees
    azlist : list of floats
        azimuths

    """
    # starting azimuth
    nr,nc=azlist.shape
    n=0
    kml = simplekml.Kml()
    # this loop goes through all the Fresnel zone azimuths in azlist
    while (n < nr):
        azim = azlist[n,0]; el = azlist[n,2]
        prn = int(azlist[n,1])
        k = el_list.index(el) ; # color index
        lng_el, lat_el = makeEllipse_latlon(freq,el,h,azim, lat,lng)
        points = write_coords(lng_el, lat_el)
        #pname = 'prn {0} elev'.format(prn)
        pname = 'PRN:' + str(prn) + ' elev:' + str(int(el))
        #pname = 'ElevAngle {0}'.format(int(el), prn)
        ls = kml.newpolygon(name=pname, altitudemode='relativeToGround') # creating new polygon for each azimuth zone in azlist
        ls.outerboundaryis = points
        # wont work ...
        # print(points)
        #ls.labelstyle.scale = 5
        if el ==el_list[0]:
            ls.style.linestyle.color = simplekml.Color.yellow
            ls.style.linestyle.width = 3
            ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.yellow)
        elif el==el_list[1]:
            ls.style.linestyle.color = simplekml.Color.blue
            ls.style.linestyle.width = 3
            ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.blue)
        elif el==el_list[2]:
            ls.style.linestyle.color = simplekml.Color.red
            ls.style.linestyle.width = 3
            ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.red)
        elif el==el_list[3]:
            ls.style.linestyle.color = simplekml.Color.green
            ls.style.linestyle.width = 3
            ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.green)
        elif el==el_list[4]:
            ls.style.linestyle.color = simplekml.Color.cyan
            ls.style.linestyle.width = 3
            ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.cyan)
        else:
            ls.style.polystyle.color = simplekml.Color.white
            ls.style.linestyle.width = 5
        n+=1

    #print('put end of file on the geoJSON')
    azim = azlist[nr-1,0]
    # try this instead of hardwiring 5!
    el=el_list[0]
    #print('elevation angle for last one')
    #print(el_list[0])
    lng_el, lat_el = makeEllipse_latlon(freq,el,h,azim, lat,lng)
    # i do not think this is needed so removed it

    if False:
        points = write_coords(lng_el, lat_el)

    #print(points)
    if False:
        ls = kml.newpolygon(name='A Polygon {0}'.format(n+1))
        ls.outerboundaryis = points
        ls.style.linestyle.color = simplekml.Color.yellow
        ls.style.linestyle.width = 3
        ls.style.polystyle.color = simplekml.Color.changealphaint(50, simplekml.Color.yellow)

    # try adding a point at the station
    pnt = kml.newpoint(name=station)
    #pnt.labelstyle.scale = 3
    pnt.coords = [(lng, lat)]
    pnt.style.iconstyle.icon.href = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle.png'

    # save to a file
    kml.save(filename)
    return True

def set_system(system):
    """
    finds the file needed to compute orbits for reflection zones

    Parameters
    ----------
    system : str
        gps,glonass,beidou, or galileo
    it : int
        simple pointer from former code. 1 is GPS, 2 is Glonass etc

    Returns
    -------
    orbfile : str
        orbit filename with Cartesian coordinates for one day 

    """
    it = 1
    xdir = os.environ['REFL_CODE'] 
    if not os.path.exists(xdir):
        print('REFL_CODE environment variable must be set. Exiting.')
        sys.exit()
    xdir = os.environ['REFL_CODE'] + '/Files/'
    if not os.path.exists(xdir):
        subprocess.call(['mkdir', xdir])

    if (system is None) or (system == 'gps'):
        system = 'gps'
        orbfile = xdir + 'GPSorbits_21sep17.txt'
        it = 1
    elif (system == 'galileo'):
        orbfile = xdir + 'GALILEOorbits_21sep17.txt'
        it = 3
    elif (system == 'glonass'):
        orbfile = xdir + 'GLONASSorbits_21sep17.txt'
        it = 2
    elif (system == 'beidou'):
        orbfile = xdir + 'BEIDOUorbits_21sep17.txt'
        it = 4
    else:
       print('Using GPS')
       system = 'gps'
       it = 1
       orbfile = xdir + 'GPSorbits_21sep17.txt'

    return orbfile, it 

def save_reflzone_orbits():
    """
    check that orbit files exist for reflection zone code.
    downloads to $REFL_CODE$/Files directory if needed

    Returns
    -------
    foundfiles : bool
        whether needed files were found
    """
    xdir = os.environ['REFL_CODE'] 

    if not os.path.exists(xdir):
        print('The REFL_CODE environment variable must be set. Exiting.')
        sys.exit()

    xdir = os.environ['REFL_CODE'] + '/Files/'

    if not os.path.exists(xdir):
        subprocess.call(['mkdir', xdir])

    githubdir = 'https://raw.githubusercontent.com/kristinemlarson/gnssrefl/master/docs/_static/'

    for otypes in ['GPS','GLONASS','GALILEO','BEIDOU']:
        orbfile = otypes + 'orbits_21sep17.txt'
        #print( githubdir+orbfile)
        if not os.path.exists(xdir + orbfile):
            print('download from github and put in local Files directory: ', otypes)
            wget.download(githubdir+orbfile, xdir + orbfile)
        #else:
        #    print('file already exists', otypes)

    found = 0 
    for otypes in ['GPS','GLONASS','GALILEO','BEIDOU']:
        orbfile = otypes + 'orbits_21sep17.txt'
        if os.path.exists(xdir + orbfile):
            found = found + 1

    foundfiles = False
    if found == 4:
        foundfiles = True

    return foundfiles 

def nyquist_simple(t,elev,azims, emin,emax,azriseset,reqsamplerate):
    """
    given numpy array of elevation angles (elev)
    and limtis (emin,emax) and azriseset, reqsamplerate

    Parameters
    ----------
    t : ??
        cannot remember
    elev : numpy array of floats
        elevation angle of rising/setting arcs
    azims : numpy array of floats
        azimuths of rising/setting arcs
    emin : float
        minimum elevation angle, degrees
    emax : float
        maximum elevation angle, degrees
    azriseset : ??
        cannot remember
    reqsamplerate : float
        requested receiver sampling rate

    """
    # sample rate used for primary orbit calculation.  will scale by requested sample rate
    samplerate = 30
    # t is every five minutes
    ie= interp1d(t, elev, kind='quadratic',bounds_error=False,fill_value='extrapolate')
    ia= interp1d(t, azims, kind='quadratic',bounds_error=False,fill_value='extrapolate')
    tnew = np.arange(t[0], t[-1], samplerate)
    # interporlate el and az
    enew = ie(tnew)
    anew = ia(tnew)
    # window it
    i = (np.abs(anew-azriseset) < 20); enew = enew[i]
    i = (enew >= emin) & (enew <= emax); enew = enew[i]
    # scale factor for L1
    cf = 0.1902936/2
    N = len(enew)
    if (N > 2):
        maxe = max(enew); mine = min(enew)
    # highest observation has to be within 0.5 degrees of requested
        if ( maxe < (emax-0.5)):
        #print(azriseset, 'max ele ', round(maxe,2), ' Not a significant arc')
            nyq = np.nan
        else:
            diffT = (np.sin( maxe*np.pi/180) - np.sin(mine*np.pi/180) ) /cf
    # we do 30 sec and then multiple by ratio of requested sample rate
            nyq = round(N/(2*diffT),2)*(samplerate/reqsamplerate)
    else:
        nyq = np.nan

    return nyq


def calcAzEl_newish(prn, newf,recv,u,East,North):
    """
    should be consolidated with the other function.but who has the time!

    Parameters
    ----------
    prn : int
        satellite number ?

    newf : 

    u : numpy array
        up unit vector
    East: 

    North : 

    Returns
    -------
    tv : numpy array

    """
    tv = np.empty(shape=[0, 4])
    # number of values
    NV = len(newf)
    for t in range(0,NV):
        satv= [newf[t,2], newf[t,3],newf[t,4]]
        etime = newf[t,1]
        r=np.subtract(satv,recv) # satellite minus receiver vector
        eleA = g.elev_angle(u, r)*180/np.pi
        if ( (eleA >= 0) & (eleA <= 20)):
            azimA = g.azimuth_angle(r, East, North)
#            print(etime, eleA, azimA)
            newl = [prn, eleA, azimA, etime]
            tv = np.append(tv, [newl],axis=0)
    nr,nc=tv.shape
    return tv

