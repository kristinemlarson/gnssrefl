"""
written in python from 
from original TU Vienna codes for GMF
"""
import datetime
import math
import os
import pickle
import subprocess
import sys
import wget

import numpy as np
from scipy.interpolate import interp1d

import gnssrefl.gps as g


def read_4by5(station, dlat,dlon,hell):
    """
    reads existing grid points for a given location

    Parameters
    ----------
    station : string
        name of station
    dlat : float
        latitude in degrees
    dlon : float
        longitude in degrees
    hell : float
        ellipsoidal height in meters

    Returns
    -------
    pgrid : 4 by 5 numpy array
        pressure in hPa

    Tgrid : 4 by 5 numpy array 
        temperature in C

    Qgrid : 4 by 5 numpy array 

    dTgrid : 4 by 5 numpy array  
       temperature lapse rate in degrees per km 

    u : 4 by 1 numpy array
        geoid undulation in meters

    Hs : 4 by 1 numpy array  

    ahgrid : 4 by 5 numpy array
        hydrostatic mapping function coefficient at zero height (VMF1) 

    awgrid : 4 by 5 numpy array
        wet mapping function coefficient (VMF1) 

    lagrid : 4 by 5 numpy array

    Tmgrid : 4 by 5 numpy array
        mean temperature of the water vapor in degrees Kelvin 

    requires that an environment variable exists for REFL_CODE
    """
#
    xdir = str(os.environ['REFL_CODE'])
    inputpath = xdir + '/input/'
#    if not os.path.isdir(inputpath): #if year folder doesn't exist, make it
#        os.makedirs(inputpath)

    # input file should be written here
    obsfile = inputpath + station + '_refr.txt'
    #print('reading from station refraction file: ', obsfile)
    x = np.genfromtxt(obsfile,comments='%')
    max_ind = 4
    pgrid = np.zeros((4,5))
    Tgrid = np.zeros((4,5))
    Qgrid = np.zeros((4,5))
    dTgrid = np.zeros((4,5))
    u = np.zeros((4,1))
    Hs = np.zeros((4,1)) 
    ahgrid = np.zeros((4,5))
    awgrid = np.zeros((4,5))
    lagrid = np.zeros((4,5))
    Tmgrid = np.zeros((4,5))

    for n in [0,1,2,3]:
        ij = 0
        u[n]= x[n*5,6]
        Hs[n]= x[n*5,7]
        for m in range(n*5, n*5+5):
            pgrid[n,ij] = x[m,2] 
            Tgrid[n,ij] = x[m,3] 
            Qgrid[n,ij] = x[m,4]/1000
            dTgrid[n,ij] = x[m,5]/1000
            ahgrid[n,ij] = x[m,8]/1000
            awgrid[n,ij] = x[m,9]/1000
            lagrid[n,ij] = x[m,10] 
            Tmgrid[n,ij] = x[m,11] 
            ij +=1

    return pgrid, Tgrid, Qgrid, dTgrid, u, Hs, ahgrid, awgrid, lagrid, Tmgrid
#
def gpt2_1w (station, dmjd,dlat,dlon,hell,it):
    """
    Parameters
    ----------
    station : str
        station name
    dmjd:  float 
        modified Julian date (scalar, only one epoch per call is possible)
    dlat : float 
        ellipsoidal latitude in radians [-pi/2:+pi/2] 
    dlon : float
        longitude in radians [-pi:pi] or [0:2pi] 
    hell : float 
        ellipsoidal height in m 
    it: integer
        case 1: no time variation but static quantities

        case 0: with time variation (annual and semiannual terms)

    Returns
    -------
    p : float
        pressure in hPa
    T:  float
        temperature in degrees Celsius 
    dT : float
       temperature lapse rate in degrees per km 
    Tm : float
        mean temperature of the water vapor in degrees Kelvin 
    e : float
        water vapor pressure in hPa 
    ah: float
        hydrostatic mapping function coefficient at zero height (VMF1) 
    aw: float
        wet mapping function coefficient (VMF1) 
    la: float
        water vapor decrease factor 
    undu: float
        geoid undulation in m 

    """

#  need to find diffpod and difflon
    if (dlon < 0):
        plon = (dlon + 2*np.pi)*180/np.pi;
    else:
        plon = dlon*180/np.pi;
# transform to polar distance in degrees
    ppod = (-dlat + np.pi/2)*180/np.pi; 

#       % find the index (line in the grid file) of the nearest point
#  	  % changed for the 1 degree grid (GP)
    ipod = np.floor(ppod+1); 
    ilon = np.floor(plon+1);
    
#   normalized (to one) differences, can be positive or negative
#	% changed for the 1 degree grid (GP)
    diffpod = (ppod - (ipod - 0.5));
    difflon = (plon - (ilon - 0.5));


# change the reference epoch to January 1 2000
    #print('Modified Julian Day', dmjd)
    dmjd1 = dmjd-51544.5 

    pi2 = 2*np.pi
    pi4 = 4*np.pi

# mean gravity in m/s**2
    gm = 9.80665;
# molar mass of dry air in kg/mol
    dMtr = 28.965E-3 
#    dMtr = 28.965*10^-3 
# universal gas constant in J/K/mol
    Rg = 8.3143 

# factors for amplitudes, i.e. whether you want time varying
    if (it==1):
        #print('>>>> no refraction time variation ')
        cosfy = 0; coshy = 0; sinfy = 0; sinhy = 0;
    else: 
        cosfy = np.cos(pi2*dmjd1/365.25)
        coshy = np.cos(pi4*dmjd1/365.25) 
        sinfy = np.sin(pi2*dmjd1/365.25) 
        sinhy = np.sin(pi4*dmjd1/365.25) 
    cossin = np.matrix([1, cosfy, sinfy, coshy, sinhy])
# initialization of new vectors
    p =  0; T =  0; dT = 0; Tm = 0; e =  0; ah = 0; aw = 0; la = 0; undu = 0;
    undul = np.zeros(4)
    Ql = np.zeros(4)
    dTl = np.zeros(4)
    Tl = np.zeros(4)
    pl = np.zeros(4)
    ahl = np.zeros(4)
    awl = np.zeros(4)
    lal = np.zeros(4)
    Tml = np.zeros(4)
    el = np.zeros(4)
#
    pgrid, Tgrid, Qgrid, dTgrid, u, Hs, ahgrid, awgrid, lagrid, Tmgrid = read_4by5(station,dlat,dlon,hell)
#
    for l in [0,1,2,3]:
        KL = l   #silly to have this as a variable like this 
#  transforming ellipsoidal height to orthometric height:
#  Hortho = -N + Hell
        undul[l] = u[KL] 
        hgt = hell-undul[l] 
#  pressure, temperature at the height of the grid
        T0 = Tgrid[KL,0] + Tgrid[KL,1]*cosfy + Tgrid[KL,2]*sinfy + Tgrid[KL,3]*coshy + Tgrid[KL,4]*sinhy;
        tg = float(Tgrid[KL,:] *cossin.T)
#     print(T0,tg)

        p0 = pgrid[KL,0] + pgrid[KL,1]*cosfy + pgrid[KL,2]*sinfy + pgrid[KL,3]*coshy + pgrid[KL,4]*sinhy;
 
#       humidity 
        Ql[l] = Qgrid[KL,0] + Qgrid[KL,1]*cosfy + Qgrid[KL,2]*sinfy + Qgrid[KL,3]*coshy + Qgrid[KL,4]*sinhy;
 
# reduction = stationheight - gridheight
        Hs1 = Hs[KL]
        redh = hgt - Hs1;

# lapse rate of the temperature in degree / m
        dTl[l] = dTgrid[KL,0] + dTgrid[KL,1]*cosfy + dTgrid[KL,2]*sinfy + dTgrid[KL,3]*coshy + dTgrid[KL,4]*sinhy;
   
# temperature reduction to station height
        Tl[l] = T0 + dTl[l]*redh - 273.15;

#  virtual temperature
        Tv = T0*(1+0.6077*Ql[l])   
        c = gm*dMtr/(Rg*Tv) 
        
# pressure in hPa
        pl[l] = (p0*np.exp(-c*redh))/100 
            
#  hydrostatic coefficient ah
        ahl[l] = ahgrid[KL,0] + ahgrid[KL,1]*cosfy + ahgrid[KL,2]*sinfy + ahgrid[KL,3]*coshy + ahgrid[KL,4]*sinhy;
            
# wet coefficient aw
        awl[l] = awgrid[KL,0] + awgrid[KL,1]*cosfy + awgrid[KL,2]*sinfy + awgrid[KL,3]*coshy + awgrid[KL,4]*sinhy;
					 
# water vapor decrease factor la - added by GP
        lal[l] = lagrid[KL,0] + lagrid[KL,1]*cosfy + lagrid[KL,2]*sinfy + lagrid[KL,3]*coshy + lagrid[KL,4]*sinhy;
					 
# mean temperature of the water vapor Tm - added by GP
        Tml[l] = Tmgrid[KL,0] +  Tmgrid[KL,1]*cosfy + Tmgrid[KL,2]*sinfy + Tmgrid[KL,3]*coshy + Tmgrid[KL,4]*sinhy;
					 		 
# water vapor pressure in hPa - changed by GP
        e0 = Ql[l]*p0/(0.622+0.378*Ql[l])/100; # % on the grid
        aa = (100*pl[l]/p0)
        bb = lal[l]+1
        el[l] = e0*np.power(aa,bb)  # % on the station height - (14) Askne and Nordius, 1987
           
    dnpod1 = np.abs(diffpod); # % distance nearer point
    dnpod2 = 1 - dnpod1;   # % distance to distant point
    dnlon1 = np.abs(difflon);
    dnlon2 = 1 - dnlon1;
        
#   pressure
    R1 = dnpod2*pl[0]+dnpod1*pl[1];
    R2 = dnpod2*pl[2]+dnpod1*pl[3];
    p = dnlon2*R1+dnlon1*R2;
            
#   temperature
    R1 = dnpod2*Tl[0]+dnpod1*Tl[1];
    R2 = dnpod2*Tl[2]+dnpod1*Tl[3];
    T = dnlon2*R1+dnlon1*R2;
        
#   temperature in degree per km
    R1 = dnpod2*dTl[0]+dnpod1*dTl[1];
    R2 = dnpod2*dTl[2]+dnpod1*dTl[3];
    dT = (dnlon2*R1+dnlon1*R2)*1000;
            
#   water vapor pressure in hPa - changed by GP
    R1 = dnpod2*el[0]+dnpod1*el[1];
    R2 = dnpod2*el[2]+dnpod1*el[3];
    e = dnlon2*R1+dnlon1*R2;
            
#   hydrostatic
    R1 = dnpod2*ahl[0]+dnpod1*ahl[1];
    R2 = dnpod2*ahl[2]+dnpod1*ahl[3];
    ah = dnlon2*R1+dnlon1*R2;
           
#   wet
    R1 = dnpod2*awl[0]+dnpod1*awl[1];
    R2 = dnpod2*awl[2]+dnpod1*awl[3];
    aw = dnlon2*R1+dnlon1*R2;
        
#  undulation
    R1 = dnpod2*undul[0]+dnpod1*undul[1];
    R2 = dnpod2*undul[2]+dnpod1*undul[3];
    undu = dnlon2*R1+dnlon1*R2;

#   water vapor decrease factor la - added by GP
    R1 = dnpod2*lal[0]+dnpod1*lal[1];
    R2 = dnpod2*lal[2]+dnpod1*lal[3];
    la = dnlon2*R1+dnlon1*R2;
		
#   mean temperature of the water vapor Tm - added by GP
    R1 = dnpod2*Tml[0]+dnpod1*Tml[1];
    R2 = dnpod2*Tml[2]+dnpod1*Tml[3];
    Tm = dnlon2*R1+dnlon1*R2; 

    return p, T, dT,Tm,e,ah,aw,la,undu

def readWrite_gpt2_1w(xdir, station, site_lat, site_lon):
    """
    makes a grid for refraction correction

    Parameters
    ----------
    xdir : str
        directory for output
    station : str
        station name, 4 ch
    lat : float
        latitude in degrees
    lon : float 
        longitude in degrees 

    """
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(PROJECT_ROOT)
    try3 = PROJECT_ROOT + '/' + 'gpt_1wA.pickle'

    # check that output path exists.  
    outpath = xdir + '/input/'
    if not os.path.isdir(outpath): 
        os.makedirs(outpath)

    outfile = outpath + station + '_refr.txt'
    if os.path.isfile(outfile):
        okokok = 1
        #print('refraction file for this station already exists')
    else:
        print('A station specific refraction output file will be written to ', outfile)

#   change to radians
        dlat = site_lat*np.pi/180 
        dlon = site_lon*np.pi/180 

#   read VMF gridfile in pickle format 
        pname = xdir + '/input/' + 'gpt_1wA.pickle'
        foundit, pname = look_for_pickle_file() 
        if foundit:
            f = open(pname, 'rb')
            [All_pgrid, All_Tgrid, All_Qgrid, All_dTgrid, All_U, All_Hs, All_ahgrid, All_awgrid, All_lagrid, All_Tmgrid] = pickle.load(f)
            f.close()
        else:
            print('You will need to download gpt_1wA.pickle MANUALLY from github and store it in REFL_CODE/input')
            sys.exit()

# really should e zero to four, but whatever
        indx = np.zeros(4,dtype=int)
        indx_lat = np.zeros(4,dtype=int)
        indx_lon = np.zeros(4,dtype=int)


#figure out grid index
# % only positive longitude in degrees
        if (dlon < 0):
            plon = (dlon + 2*np.pi)*180/np.pi;
        else:
            plon = dlon*180/np.pi 
#
#  transform to polar distance in degrees
        ppod = (-dlat + np.pi/2)*180/np.pi  

#% find the index (line in the grid file) of the nearest point
# % changed for the 1 degree grid (GP)
        ipod = np.floor(ppod+1)  
        ilon = np.floor(plon+1) 
    
#    % normalized (to one) differences, can be positive or negative
# % changed for the 1 degree grid (GP)
        diffpod = (ppod - (ipod - 0.5)) 
        difflon = (plon - (ilon - 0.5)) 
#    % added by HCY
# % changed for the 1 degree grid (GP)
        if (ipod == 181):
            ipod = 180 
        if (ilon == 361):
            ilon = 1 
        if (ilon == 0):
            ilon = 360

#     get the number of the corresponding line
#	 changed for the 1 degree grid (GP)
        indx[0] = (ipod - 1)*360 + ilon 
#  save the lat lon of the grid points
        indx_lat[0] = 90-ipod+1  
        indx_lon[0] = ilon-1   
# % near the poles: nearest neighbour interpolation, otherwise: bilinear
# % with the 1 degree grid the limits are lower and upper (GP)

        bilinear = 0 
        max_ind = 1 
        if (ppod > 0.5) and (ppod < 179.5):
            bilinear = 1           
        if (bilinear == 1):
            max_ind =4 

#    % bilinear interpolation
#    % get the other indexes 
 
        ipod1 = ipod + np.sign(diffpod) 
        ilon1 = ilon + np.sign(difflon) 
# % changed for the 1 degree grid (GP)
        if (ilon1 == 361):
            ilon1 = 1 
        if (ilon1 == 0):
            ilon1 = 360 
#         get the number of the line
# changed for the 1 degree grid (GP)
# four indices ???
        indx[1] = (ipod1 - 1)*360 + ilon; # % along same longitude
        indx[2] = (ipod  - 1)*360 + ilon1;# % along same polar distance
        indx[3] = (ipod1 - 1)*360 + ilon1;# % diagonal
#
# save the lat lon of the grid points  lat between [-90 ;90]  lon [0 360] 
        indx_lat[1] =   90 - ipod1+np.sign(diffpod)     
        indx_lon[1] = ilon-1 
        indx_lat[2] =   90-ipod +1
        indx_lon[2] =  ilon1 - np.sign(difflon) 
        indx_lat[3] =   90 -ipod1+np.sign(diffpod)     
        indx_lon[3] = ilon1- np.sign(difflon);

# extract the new grid
# will need to do 0-4 instead of 1-5 because stored that way in python
# which values to use in the bigger array
# assign the correct values
        indx = indx - 1
        indx_list = indx.tolist()
#    print(indx_list)
#    print(indx)
#print(np.shape(indx_lat))
#print(np.shape(indx_lon))
        w = 0
# need to write values for a given station to a plain text file
#
        fout = open(outfile, 'w+')
        for a in indx_list:
            for k in [0,1,2,3,4]:
                fout.write(" {0:4.0f} {1:5.0f} {2:13.4f} {3:10.4f} {4:10.6f} {5:10.4f} {6:12.5f} {7:12.5f} {8:10.6f} {9:10.6f} {10:10.6f} {11:10.4f} \n".format( indx_lat[w], indx_lon[w],All_pgrid[a,k],All_Tgrid[a,k],All_Qgrid[a,k]*1000,All_dTgrid[a,k]*1000,All_U[a,0],All_Hs[a,0], All_ahgrid[a,k]*1000, All_awgrid[a,k]*1000, All_lagrid[a,k], All_Tmgrid[a,k] ))

            w+=1
        fout.close()
        print('station specific refraction file written')


def corr_el_angles(el_deg, press, temp):
    """
    Corrects elevation angles for refraction using simple angle bending model

    Parameters
    ----------
    el_deg : numpy array of floats
        elevation angles in degrees
    press : float
        pressure in hPa
    temp : float
        temperature in degrees C

    Returns
    -------
    corr_el_deg : numpy array of floats
        corrected elevation angles (in degrees)

    """

#  Formula in python from Strandberg, originally from Astronomy journal
    corr_el_arc_min = 510/(9/5*temp + 492) * press/1010.16 * 1/np.tan(np.deg2rad(el_deg + 7.31/(el_deg + 4.4)))
    correction = corr_el_arc_min/60 
     
    corr_el_deg = el_deg + correction   
    return corr_el_deg


def look_for_pickle_file():
    """
    latest attempt to solve the dilemma of the pickle file needed for
    the refraction correction

    Returns
    -------
    foundit : bool
        whether pickle file found
    fullpname : str
        full path to the pickle file
    """
#   read VMF gridfile in pickle format

    pfile = 'gpt_1wA.pickle'

    # at one point i thought this was useful
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
    BASE_DIR = os.path.dirname(PROJECT_ROOT)
    try3 = PROJECT_ROOT + '/' + pfile
    # do i need str??
    xdir = str(os.environ['REFL_CODE'])
    inputdir = xdir + '/input/'
    if os.path.isdir(inputdir):
        print('found ', inputdir)
    else:
        print('make directory: ', inputdir)
        subprocess.call(['mkdir',inputdir])

    fdir = xdir + '/Files'
    if not os.path.isdir(fdir):
        print('make Files directory: ', fdir)
        subprocess.call(['mkdir', fdir])

    # where the file should be stored
    fullpname = inputdir + pfile

    print('The large refraction file should be stored here:', fullpname)
    foundit = False

    if os.path.isfile(fullpname):
        print('1st attempt: found in ', fullpname)
        foundit = True
    else:
        print('1st attempt: not found in ', fullpname)

    if not foundit:
        pname =  'gnssrefl/gpt_1wA.pickle'
        print('2nd attempt: look in subdirectory of current working directory:', pname)
        if os.path.isfile(pname):
            subprocess.call(['cp','-f',pname, fullpname  ])
            foundit = True

    if not foundit:
        pname = try3
        print('3rd attempt try looking here: ',pname)
        if os.path.isfile(pname):
            foundit = True
            print('cp it to ', fullpname)
            subprocess.call(['cp','-f',pname, fullpname])
        else:
            print('that did not work')

    url= 'https://github.com/kristinemlarson/gnssrefl/raw/master/gnssrefl/' + pfile
    if not foundit:
        print('4th attempt - download from github', url)
        try:
            wget.download(url,fullpname)
        except:
            print('download or cp failed')
        if os.path.isfile(fullpname):
            foundit = True

    if not foundit:
        url= 'https://morefunwithgps.com/public_html/' + pfile
        print('5th attempt - ',url)
        try:
            wget.download(url,fullpname)
        except:
            print('Failed again.')

        if os.path.isfile(fullpname):
            foundit = True
        else:
            print('File should be stored in ', inputdir, ' but is not')

    return foundit , fullpname


def Ulich_Bending_Angle(ele, N0,lsp,p,T,ttime,sat):   #UBA
    """
    Ulich, B. L. "Millimeter wave radio telescopes: Gain and pointing characteristics." (1981)

    Author: 20220629, fengpeng
    modified to use numpy so I can do arrays

    currently writes out corrections to a file for testing

    Parameters
    ----------
    ele : numpy array of floats
        true elevation angle, degrees

    N0 : float
        antenna refractivity in ppm

    Returns
    -------
    De : numpy array of floats
        corrected elevation angle, deg
        
    """
    e_simple_corr = corr_el_angles(ele, p,T)
    deg2rad = np.pi/180

    # change to radians
    ele_rad = deg2rad*(ele)
    r = N0/1000000.
    f = np.cos(ele_rad) / (np.sin(ele_rad) + 0.00175 * np.tan(deg2rad*(87.5) - ele_rad))
    dE = (r * f)/deg2rad
    fout = open('ulich.txt', 'w+')
    for i in range(0,len(ele)):
        fout.write(" {0:8.5f} {1:8.5f} {2:8.5f} {3:10.0f} {4:5.0f} \n ".format( 
            ele[i], ele[i]+dE[i], e_simple_corr[i], ttime[i], sat[i]))

    fout.close()

    return dE + ele

def refrc_Rueger(drypress,vpress,temp):
    """
    Obtains refractivity index suitable for GNSS-IR

    Rüeger, Jean M. "Refractive index formulae for radio waves." Proceedings of the 
    FIG XXII International Congress, Washington, DC, USA. Vol. 113. 2002.

    Parameters
    ----------
    drypress : float
        dry pressure hPa
    vpress : float
        vapor pressure in hPa
    temp : float
        temperature in Kelvin

    Returns 
    -------
    ref : list of floats
         [Ntotal, Nhydro, Nwet], which are total, hydrostatic and wet refractivity in ppm

    """

    # Rüeger's "best average", for 375 ppm CO2, 77.690 for 392 ppm CO2
    [K1r,K2r,K3r]=[77.689 ,71.2952 ,375463.]     

    # Rueger,IAG recommend, in ppm
    Nrueger = K1r * drypress / temp + K2r * vpress / temp + K3r * vpress / (temp ** 2)  

    # gas constant (SI exact), molar masses of dry air and water, kg/mol
    [Rgas,Md,Mw] = [8.31446261815324,0.0289644,0.01801528]   

    #density in kg/m^3
    drydensity=(drypress*100.)*Md/(Rgas*temp)    
    #in PV=nRT, P in Pa, V in m^3, n in g/mol, T in K, R=8.314 Pa*m^3/(k*mol)
    vdensity=(vpress*100.)*Mw/(Rgas*temp)   
    totaldensity=drydensity+vdensity

    #divide 100 because hPa in Rueger formula, result in ppm
    Nhydro=(K1r*Rgas*totaldensity/Md)/100.   
    K2rr=K2r-K1r*(Mw/Md)
    Nwet=K2rr * vpress / temp + K3r * vpress / (temp ** 2)
    # in ppm
    ref=[round(Nrueger,4),round(Nhydro,4),round(Nwet,4)]    
    return ref


def Equvilent_Angle_Corr_NITE(Hr_apr, e_T, N_ant, ztd_ant, mpf_tot, dmpf_de_tot):
    """
    NITE formula equvilent angle correction and forward model
    From Peng et al. 2023

    Parameters
    ----------
    Hr_apr : float
        a priori reflector height, meters

    e_T : float
        elevation angle - units!!!!!

    N_ant : float
        antenna refractivity

    ztd_ant : float
        total zenith tropo delay, meters

    mpf_tot : float

    dmpf_de_tot : float


    Returns
    -------
    new_elev : float
        new elevation angle, units?

    """
    e_A = e_T+Ulich_Bending_Angle_original(e_T, N_ant)
    sita_E = sita_Earth(Hr_apr, e_A)
    sita_S = sita_Satellite(Hr_apr, e_A)
    e_A_r = e_A+sita_E +sita_S
    Hv_ratio = Hv_Hr_ratio(Hr_apr, 6378137., e_A)
    sin_eqv_geo = 0.5 * Hv_ratio / np.sin(np.radians(e_A_r + sita_E)) * (1. - np.cos(np.radians(e_T + e_A_r + sita_E)))
    Nl = N_layer(N_ant, Hr_apr)
    dsin_up = Hv_ratio*(Nl / 1000000.)/np.sin(np.radians(e_A_r + sita_E))
    ddele_T_dh = np.tan(np.radians(e_A))
    dsin_down = Nl / 1000000.*mpf_tot-ztd_ant*(dmpf_de_tot*(1. / (6378137. *ddele_T_dh ))+dmpf_dh(e_T, dhgt=1.))
    dsin = 0.5*(dsin_up + dsin_down)
    ele_eqv = np.degrees(np.arcsin(sin_eqv_geo + dsin))
    new_elev = ele_eqv - e_T
    return new_elev


def gmf_deriv(dmjd,dlat,dlon,dhgt,zd):
    """
    This subroutine determines the Global Mapping Functions GMF  and derivative.
    Translated from https://vmf.geo.tuwien.ac.at/codes/gmf_deriv.f by Peng Feng in March, 2023.

    Johannes Boehm, 2005 August 30
    
    ref 2006 Aug. 14: derivatives (U. Hugentobler)
    ref 2006 Aug. 14: recursions for Legendre polynomials (O. Montenbruck)
    ref 2011 Jul. 21: latitude -> ellipsoidal latitude

    Parameters
    ----------
    dmjd: float
        modified julian date
    dlat: float
        ellipsoidal latitude in radians
    dlon: float
        longitude in radians
    dhgt: float
        height in m
    zd: float
        zenith distance in radians ??? ( is this really what you mean??

    Returns
    -------
    gmfh(2): floats
        hydrostatic mapping function and derivative wrt z

    gmfw(2): floats
        wet mapping function and derivative wrt z
    
    """

    ah_mean=[+1.2517e+02, +8.503e-01, +6.936e-02, -6.760e+00, +1.771e-01,
             +1.130e-02, +5.963e-01, +1.808e-02, +2.801e-03, -1.414e-03,
             -1.212e+00, +9.300e-02, +3.683e-03, +1.095e-03, +4.671e-05,
             +3.959e-01, -3.867e-02, +5.413e-03, -5.289e-04, +3.229e-04,
             +2.067e-05, +3.000e-01, +2.031e-02, +5.900e-03, +4.573e-04,
             -7.619e-05, +2.327e-06, +3.845e-06, +1.182e-01, +1.158e-02,
             +5.445e-03, +6.219e-05, +4.204e-06, -2.093e-06, +1.540e-07,
             -4.280e-08, -4.751e-01, -3.490e-02, +1.758e-03, +4.019e-04,
             -2.799e-06, -1.287e-06, +5.468e-07, +7.580e-08, -6.300e-09,
             -1.160e-01, +8.301e-03, +8.771e-04, +9.955e-05, -1.718e-06,
             -2.012e-06, +1.170e-08, +1.790e-08, -1.300e-09, +1.000e-10]

    bh_mean=[+0.000e+00, +0.000e+00, +3.249e-02, +0.000e+00, +3.324e-02,
             +1.850e-02, +0.000e+00, -1.115e-01, +2.519e-02, +4.923e-03,
             +0.000e+00, +2.737e-02, +1.595e-02, -7.332e-04, +1.933e-04,
             +0.000e+00, -4.796e-02, +6.381e-03, -1.599e-04, -3.685e-04,
             +1.815e-05, +0.000e+00, +7.033e-02, +2.426e-03, -1.111e-03,
             -1.357e-04, -7.828e-06, +2.547e-06, +0.000e+00, +5.779e-03,
             +3.133e-03, -5.312e-04, -2.028e-05, +2.323e-07, -9.100e-08,
             -1.650e-08, +0.000e+00, +3.688e-02, -8.638e-04, -8.514e-05,
             -2.828e-05, +5.403e-07, +4.390e-07, +1.350e-08, +1.800e-09,
             +0.000e+00, -2.736e-02, -2.977e-04, +8.113e-05, +2.329e-07,
             +8.451e-07, +4.490e-08, -8.100e-09, -1.500e-09, +2.000e-10]

    ah_amp=[ -2.738e-01, -2.837e+00, +1.298e-02, -3.588e-01, +2.413e-02,
            +3.427e-02, -7.624e-01, +7.272e-02, +2.160e-02, -3.385e-03,
            +4.424e-01, +3.722e-02, +2.195e-02, -1.503e-03, +2.426e-04,
            +3.013e-01, +5.762e-02, +1.019e-02, -4.476e-04, +6.790e-05,
            +3.227e-05, +3.123e-01, -3.535e-02, +4.840e-03, +3.025e-06,
            -4.363e-05, +2.854e-07, -1.286e-06, -6.725e-01, -3.730e-02,
            +8.964e-04, +1.399e-04, -3.990e-06, +7.431e-06, -2.796e-07,
            -1.601e-07, +4.068e-02, -1.352e-02, +7.282e-04, +9.594e-05,
            +2.070e-06, -9.620e-08, -2.742e-07, -6.370e-08, -6.300e-09,
            +8.625e-02, -5.971e-03, +4.705e-04, +2.335e-05, +4.226e-06,
            +2.475e-07, -8.850e-08, -3.600e-08, -2.900e-09, +0.000e+00]

    bh_amp=[+0.000e+00, +0.000e+00, -1.136e-01, +0.000e+00, -1.868e-01,
            -1.399e-02, +0.000e+00, -1.043e-01, +1.175e-02, -2.240e-03,
            +0.000e+00, -3.222e-02, +1.333e-02, -2.647e-03, -2.316e-05,
            +0.000e+00, +5.339e-02, +1.107e-02, -3.116e-03, -1.079e-04,
            -1.299e-05, +0.000e+00, +4.861e-03, +8.891e-03, -6.448e-04,
            -1.279e-05, +6.358e-06, -1.417e-07, +0.000e+00, +3.041e-02,
            +1.150e-03, -8.743e-04, -2.781e-05, +6.367e-07, -1.140e-08,
            -4.200e-08, +0.000e+00, -2.982e-02, -3.000e-03, +1.394e-05,
            -3.290e-05, -1.705e-07, +7.440e-08, +2.720e-08, -6.600e-09,
            +0.000e+00, +1.236e-02, -9.981e-04, -3.792e-05, -1.355e-05,
            +1.162e-06, -1.789e-07, +1.470e-08, -2.400e-09, -4.000e-10]

    aw_mean=[+5.640e+01, +1.555e+00, -1.011e+00, -3.975e+00, +3.171e-02,
             +1.065e-01, +6.175e-01, +1.376e-01, +4.229e-02, +3.028e-03,
             +1.688e+00, -1.692e-01, +5.478e-02, +2.473e-02, +6.059e-04,
             +2.278e+00, +6.614e-03, -3.505e-04, -6.697e-03, +8.402e-04,
             +7.033e-04, -3.236e+00, +2.184e-01, -4.611e-02, -1.613e-02,
             -1.604e-03, +5.420e-05, +7.922e-05, -2.711e-01, -4.406e-01,
             -3.376e-02, -2.801e-03, -4.090e-04, -2.056e-05, +6.894e-06,
             +2.317e-06, +1.941e+00, -2.562e-01, +1.598e-02, +5.449e-03,
             +3.544e-04, +1.148e-05, +7.503e-06, -5.667e-07, -3.660e-08,
             +8.683e-01, -5.931e-02, -1.864e-03, -1.277e-04, +2.029e-04,
             +1.269e-05, +1.629e-06, +9.660e-08, -1.015e-07, -5.000e-10]

    bw_mean=[+0.000e+00, +0.000e+00, +2.592e-01, +0.000e+00, +2.974e-02,
             -5.471e-01, +0.000e+00, -5.926e-01, -1.030e-01, -1.567e-02,
             +0.000e+00, +1.710e-01, +9.025e-02, +2.689e-02, +2.243e-03,
             +0.000e+00, +3.439e-01, +2.402e-02, +5.410e-03, +1.601e-03,
             +9.669e-05, +0.000e+00, +9.502e-02, -3.063e-02, -1.055e-03,
             -1.067e-04, -1.130e-04, +2.124e-05, +0.000e+00, -3.129e-01,
             +8.463e-03, +2.253e-04, +7.413e-05, -9.376e-05, -1.606e-06,
             +2.060e-06, +0.000e+00, +2.739e-01, +1.167e-03, -2.246e-05,
             -1.287e-04, -2.438e-05, -7.561e-07, +1.158e-06, +4.950e-08,
             +0.000e+00, -1.344e-01, +5.342e-03, +3.775e-04, -6.756e-05,
             -1.686e-06, -1.184e-06, +2.768e-07, +2.730e-08, +5.700e-09]

    aw_amp=[+1.023e-01, -2.695e+00, +3.417e-01, -1.405e-01, +3.175e-01,
            +2.116e-01, +3.536e+00, -1.505e-01, -1.660e-02, +2.967e-02,
            +3.819e-01, -1.695e-01, -7.444e-02, +7.409e-03, -6.262e-03,
            -1.836e+00, -1.759e-02, -6.256e-02, -2.371e-03, +7.947e-04,
            +1.501e-04, -8.603e-01, -1.360e-01, -3.629e-02, -3.706e-03,
            -2.976e-04, +1.857e-05, +3.021e-05, +2.248e+00, -1.178e-01,
            +1.255e-02, +1.134e-03, -2.161e-04, -5.817e-06, +8.836e-07,
            -1.769e-07, +7.313e-01, -1.188e-01, +1.145e-02, +1.011e-03,
            +1.083e-04, +2.570e-06, -2.140e-06, -5.710e-08, +2.000e-08,
            -1.632e+00, -6.948e-03, -3.893e-03, +8.592e-04, +7.577e-05,
            +4.539e-06, -3.852e-07, -2.213e-07, -1.370e-08, +5.800e-09]

    bw_amp=[+0.000e+00, +0.000e+00, -8.865e-02, +0.000e+00, -4.309e-01,
            +6.340e-02, +0.000e+00, +1.162e-01, +6.176e-02, -4.234e-03,
            +0.000e+00, +2.530e-01, +4.017e-02, -6.204e-03, +4.977e-03,
            +0.000e+00, -1.737e-01, -5.638e-03, +1.488e-04, +4.857e-04,
            -1.809e-04, +0.000e+00, -1.514e-01, -1.685e-02, +5.333e-03,
            -7.611e-05, +2.394e-05, +8.195e-06, +0.000e+00, +9.326e-02,
            -1.275e-02, -3.071e-04, +5.374e-05, -3.391e-05, -7.436e-06,
            +6.747e-07, +0.000e+00, -8.637e-02, -3.807e-03, -6.833e-04,
            -3.861e-05, -2.268e-05, +1.454e-06, +3.860e-07, -1.068e-07,
            +0.000e+00, -2.658e-02, -1.947e-03, +7.131e-04, -3.506e-05,
            +1.885e-07, +5.792e-07, +3.990e-08, +2.000e-08, -5.700e-09]


    pi = 3.141592653590000

#   reference day is 28 January
#   this is taken from Niell (1996) to be consistent
    doy = dmjd  - 44239.0 + 1 - 28

#   degree n and order m
    nmax = 9
    mmax = 9

#   unit vector
    x = math.cos(dlat)*math.cos(dlon)
    y = math.cos(dlat)*math.sin(dlon)
    z = math.sin(dlat)
  
# Legendre polynomials (Cunningham)

    V=[[0. for j in range(nmax+1) ] for i in range(nmax+1)]
    W = [[0. for j in range(mmax + 1)] for i in range(mmax + 1)]

    V[0][0]=1.0
    W[0][0]=0.0
    V[1][0]=z*V[0][0]
    W[1][0]=0.0
    # print(z)


    for n in range(2,nmax+1):
        V[n][0]=((2*n-1) * z * V[n-1][0] - (n-1) * V[n-2][0])  / n
        W[n][0]=0.0


    for m in range(1,nmax+1):
        V[m][m] = (2 * m - 1) * (x * V[m - 1][m - 1] - y * W[m - 1][m - 1])
        W[m][m] = (2 * m - 1) * (x * W[m - 1][m - 1] + y * V[m - 1][m - 1])

        if m<nmax:
            V[m + 1][m] = (2 * m + 1) * z * V[m][m]
            W[m + 1][m] = (2 * m + 1) * z * W[m][m]
        for n in range(m+2,nmax+1):
            V[n][m] = ((2 * n - 1) * z * V[n-1][m] - (n + m - 1) * V[n-2][m]) / (n - m)
            W[n][m] = ((2 * n - 1) * z * W[n-1][m] - (n + m - 1) * W[n-2][m]) / (n - m)
    # print(V)
    # print(W)


    #hydrostatic
    bh = 0.0029
    c0h = 0.062
    if dlat <0.: # southern hemisphere
        phh = pi
        c11h = 0.007
        c10h = 0.002
    else: # northern hemisphere
        phh = 0
        c11h = 0.005
        c10h = 0.001
    ch = c0h + ((math.cos(doy / 365.25 * 2. * pi + phh) + 1) * c11h / 2. + c10h) *(1. - math.cos(dlat))

    ahm = 0.
    aha = 0.
    i = 0
    for n in range(0,nmax+1):
        for m in range(0,n+1):
            ahm = ahm + (ah_mean[i] * V[n][m] + bh_mean[i] * W[n][m])
            # print('ahm',i,n,m,ahm,ah_mean[i] , V[n][m] , bh_mean[i],W[n][m])
            aha = aha + (ah_amp[i] * V[n][m]+ bh_amp[i] * W[n][m])
            # print('aha', i, n, m, aha, ah_amp[i], V[n][m], bh_amp[i], W[n][m])
            i=i+1
    ah=(ahm + aha*math.cos(doy/365.250*2.0*pi))*1.e-5
    # print('ah',ah,ahm,aha,i)
    # print(V)
    # print(W)
    # print(ah_mean)


    sine = math.sin(pi / 2 - zd)
    cose = math.cos(pi / 2 - zd)
    beta = bh / (sine + ch)
    gamma = ah / (sine + beta)
    topcon = (1.0 + ah / (1.0 + bh / (1.0 + ch)))
    gmfh=[0.,0.]
    gmfh[0] = topcon / (sine + gamma)
#   derivative
    gmfh[1] = gmfh[0] ** 2 / topcon * cose * (1 - gamma ** 2 / ah * (1 - beta ** 2 / bh))

#    height correction for hydrostatic mapping function from Niell (1996)
    a_ht = 2.53e-5
    b_ht = 5.49e-3
    c_ht = 1.14e-3
    hs_km = dhgt / 1000.0

    beta = b_ht / (sine + c_ht)
    gamma = a_ht / (sine + beta)
    topcon = (1.0 + a_ht / (1.0 + b_ht / (1.0 + c_ht)))
    ht_corr_coef = 1 / sine - topcon / (sine + gamma)
    ht_corr = ht_corr_coef * hs_km
    gmfh[0] = gmfh[0] + ht_corr

#   derivative
    gmfh[1]= gmfh[1] + (cose/sine**2 - topcon*cose/(sine+gamma)**2*(1-gamma**2/a_ht*(1-beta**2/b_ht))) * hs_km


#   wet
    bw = 0.00146
    cw = 0.04391
    awm = 0.0
    awa = 0.0
    i=0
    for n in range(0,nmax+1):
        for m in range(0,n+1):
            awm = awm + (aw_mean[i] * V[n][m] + bw_mean[i] * W[n][m])
            awa = awa + (aw_amp[i] * V[n][m] + bw_amp[i] * W[n][m])
            i=i+1

    aw = (awm + awa * math.cos(doy / 365.250 * 2 * pi))*1e-5
    beta = bw / (sine + cw)
    gamma = aw / (sine + beta)
    topcon = (1.0 + aw / (1.0 + bw / (1.0 + cw)))

    gmfw = [0., 0.]
    gmfw[0] = topcon / (sine + gamma)

#   derivative
    gmfw[1] = gmfw[0] ** 2 / topcon * cose * (1 - gamma ** 2 / aw * (1 - beta ** 2 / bw))
    return [gmfh[0],gmfh[1],gmfw[0],gmfw[1]]


def sita_Earth(Hr, e_A):                                   
    """
    no documentation
    # in meter, in degree


    """

    # earth center angle between the reflection point and the GNSS antenna
    sita_E = Hr / (6378137. * np.tan(np.radians(e_A)))
    return round(np.degrees(sita_E), 6)                              # in degree

def sita_Satellite(Hr, e_A):                               
    """
    no documentation 
    # in meter, in degree
    # satellite angle between the reflection point and the GNSS antenna

    """

    ant2satell = 4.*6378137.    # assume satellite distance 4 times earth radius
    sita_S = 2 * Hr * np.cos(np.radians(e_A)) / ant2satell
    return round(np.degrees(sita_S), 6)    # in degree, small for MEO satellites

def dH_curve(Hr, Re, e_A):                       
    """
    no documentation provided
    # in meter, in meter, in degree
    #vertial displacement of the reflection point vs. a "plane reflection"
    """
    dH = Re * (1. - np.cos(Hr / np.tan(np.radians(e_A)) / Re))
    return round(dH, 6)    # in meters

def Hv_Hr_ratio(Hr, Re, e_A):
    """
    no documentation provided
    # in meter, in meter, in degree
    """
    dH = Re * (1. - np.cos(Hr / np.tan(np.radians(e_A)) / Re))
    return (Hr+dH) /Hr    #ratio, allways bigger than 1

def N_layer(N_antenna, Hr):
    """
    no documentation 

    #in ppm, in meter
    # average refractivity in the layer between GNSS antenna and sea surface
    """
    Nl = N_antenna *(1+np.exp(Hr/8000.)) /2
    return round(Nl, 4)     #in ppm

def saastam2(press, lat, height):
    """
    no documentation
    in hPa,  in degree, in meter
    Saastamion model with updated refractivity equation from Rüeger (2002)

    as best i understand this it is the dry delay
    """
    phi = lat / 180 * 3.14159265359
    height = height / 1000.
    f = 1. - 0.0026 * np.cos(2. * phi) - 0.00028 * height
    # ZHD in meter
    return round(2.2794 * press / f / 1000., 6)                   

def mpf_tot(gmf_h, gmf_w, zhd, zwd):  
    """
    no documentation
    #convert seperate wet&dry MPF to total MPF

    guessing

    gmf_h : float
        ?
    gmf_w : float
        ?
    zhd : float
        zenith hydrostatic delay
    zwd : float
        zenith wet delay
    """
    mpf_tot1=(gmf_h*zhd+gmf_w*zwd)/(zhd+zwd)

    return mpf_tot1

def dmpf_dh(ele, dhgt):    
    """
    no documentation
    # mapping function height correction by (Niell, 1996)
    """
    sine = np.sin(np.radians(ele))
    [a_ht, b_ht, c_ht] = [0.0000253, 0.00549, 0.00114]
    hs_km = dhgt / 1000.
    beta = b_ht / (sine + c_ht)
    topcon = (1. + a_ht / (1. + b_ht / (1. + c_ht)))
    ht_corr_coef = 1 / sine - topcon / (sine + a_ht / (sine + beta))
    return ht_corr_coef * hs_km


def Ulich_Bending_Angle_original(ele, N0):   
    """
    no documentation
    # input degree, ppm
    """
    ele = np.radians(ele)
    r = N0/1000000.
    f = np.cos(ele) / (np.sin(ele) + 0.00175 * np.tan(np.radians(87.5) - ele))
    return np.degrees(r * f)

