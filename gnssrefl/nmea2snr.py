# -*- coding: utf-8 -*-
"""
convert nmea files to snr files 
"""
from __future__ import division
import numpy as np 
import os
import subprocess
from scipy.interpolate import interp1d

import gnssrefl.gps as g

def NMEA2SNR(locdir, fname, snrfile, csnr):
    """

    Parameters
    -----------
    locdir : str
        directory where your SNR files are kept
    fname : string
        NMEA filename 

    snrfile : str
        name of output file for SNR data

    csnr : str
        snr option, i.e. '66' or '99'

    """
    
    missing = True

#check whether the input file is a uncompressed or compressed     
    if os.path.exists(locdir + fname):
        subprocess.call(['cp', '-f',locdir + fname ,'.'])
        t, prn, az, elv, snr = read_nmea(fname)#read nmea files
        subprocess.call(['rm',fname])
        missing = False

    if os.path.exists(locdir + fname + '.gz') and missing:
        subprocess.call(['cp', '-f',locdir + fname + '.gz' ,'.'])
        subprocess.call(['gunzip', fname + '.gz'])
        t, prn, az, elv, snr = read_nmea(fname)#read nmea files
        subprocess.call(['rm',fname])
        missing = False
        
    if os.path.exists(locdir + fname + '.Z') and missing:
        subprocess.call(['cp', '-f',locdir + fname + '.Z','.'])
        subprocess.call(['uncompress', fname + '.Z'])
        t, prn, az, elv, snr = read_nmea(fname)#read nmea files
        subprocess.call(['rm',fname])
        missing = False
        
    t = np.array(t);az = np.array(az);elv = np.array(elv);snr = np.array(snr);prn = np.array(prn)

# remove empty records
    t = t[az !=''];snr = snr[az !=''];prn = prn[az !=''];elv = elv[az !=''];az = az[az !='']
    t = t[elv !=''];az = az[elv !=''];snr = snr[elv !=''];prn = prn[elv !=''];elv = elv[elv !='']
    t = t[snr !=''];az = az[snr !=''];prn = prn[snr !=''];elv = elv[snr !=''];snr = snr[snr !='']
    t = t[prn !=''];az = az[prn !=''];elv = elv[prn !=''];snr = snr[prn !=''];prn = prn[prn !='']
    
    az = az.astype(float);elv = elv.astype(float);snr = snr.astype(float);prn = prn.astype(int)

    prn_unique = np.unique(prn) 

    T = []; PRN = []; AZ = []; ELV = []; SNR = []
        
    for i_prn in prn_unique:
        # the original code added 100 - but did not take into account the 
        # satellite numbers have been shifted for glonass.
        # also there is an illegal signal at satellite "48" 
        # i do not know what that is, but i am ignoring it.
        #if (i_prn > 32):
        #    print(i_prn, 'looks like an illegal satellite number')
 #       print(i_prn)
        time = t[prn == i_prn];angle = elv[prn == i_prn];azimuth = az[prn == i_prn]
        Snr = snr[prn == i_prn];Prn = prn[prn == i_prn]
        
        angle_fixed, azim_fixed = fix_angle_azimuth(time, angle, azimuth)#fix the angles 
        if (len(angle_fixed)== 0 and len(azim_fixed) ==0):
            continue
            
        T.extend(time);AZ.extend(azim_fixed);ELV.extend(angle_fixed);SNR.extend(Snr);        PRN.extend(Prn)
        
        del  time, angle, azimuth, Snr, Prn, angle_fixed, azim_fixed
        
    inx = np.argsort(T) 
    
    T = np.array(T);PRN = np.array(PRN);ELV = np.array(ELV);SNR = np.array(SNR);AZ = np.array(AZ)
    
    T = T[inx];PRN = PRN[inx];ELV = ELV[inx];SNR = SNR[inx];AZ = AZ[inx]
                               
    emin,emax = elev_limits(int(csnr))#select snr option 50, 66, 88, 99
#write to an output file 
    fout = open(snrfile, 'w')
    for i in range(len(T)):
        if (float(ELV[i]) >= emin) and (float(ELV[i]) <= emax):
            if (PRN[i] > 100):
                # names were translated incorrectly for Glonass records - so removing 65 from them all ;-)
                p = float(PRN[i]) -65 + 1
            else:
                p = float(PRN[i])
            # only allow glonass and correct GPS
            if (p > 100) | (p < 33):
                fout.write("%3g %10.4f %10.4f %10g %4s %4s %7.2f %4s %4s\n" % (p, float(ELV[i]), float(AZ[i]), float(T[i]),'0', '0', float(SNR[i]),'0', '0')) 
    fout.close()
    
def read_nmea(fname):
    """
    read GPGGA sentence (includes snr data) in NMEA files    

    Parameters
    ----------
    fname : string
        NMEA filename

    Returns
    -------
    t : list of integers
        timetags in GPS seconds 

    prn : list of integers
        GPS satellite numbers

    az : list of floats ??
        azimuth values (degrees)

    elv : list of floats ??
        elevation angles (degrees)

    snr : list of floats
        snr values

    """
    
    f=open(fname, 'rb')
    lines = f.read().splitlines()
    f.close()

    t = []; prn = []; az = []; elv = []; snr = []
    for i, line in enumerate(lines):
    
        if b"GGA" in line: #read GPGGA sentence: Global Positioning System Fix Data 
            hr = int(line.decode("utf-8").split(",")[1][0:2])
            mn = int(line.decode("utf-8").split(",")[1][2:4])
            sc = float(line.decode("utf-8").split(",")[1][4:8])
            t_sec = hr*3600 + mn*60 + sc
            if (i > 100 and t_sec == 0):                   #set t to 86400 for the midnight data
                t_sec = 86400

        elif b"GSV" in line:                             #read GPGSV sentence: GPS Satellites in view in this cycle   
        
            if b"GPGSV" in line:
                prn_offset = 0
            elif b"GLGSV" in line:
                prn_offset = 100
            elif b"GAGSV" in line:
                prn_offset = 200
            elif b"BDGSV" in line:
                prn_offset = 300
            sent = line.decode("utf-8").split(",")         #GPGSV sentence 
            ttl_ms = int(sent[1])                          #Total number of messages in the GPGSV sentence 
            ms = int(sent[2])                              #Message number 
        
            if (len(sent) == 20):                          #Case 1: 4 sat in view in this sentence 
                cnt = 0
                for j in range(0,4):
                    prn.append(str(prn_offset + int(sent[4+cnt]))) #field 4,8,12,16 :  SV PRN number
                    elv.append(sent[5+cnt]) #field 5,9,13,17 :  Elevation in degrees, 90 maximum
                    az.append(sent[6+cnt]) #field 6,10,14,18:  Azimuth in degrees
                    snr.append(sent[7+cnt].split("*")[0])  #field 7,11,15,19:  SNR, 00-99 dB (null when not tracking)
                    if ms <= ttl_ms:
                        t.append(t_sec)
                    
                    cnt = cnt + 4
#            ###    
            elif (len(sent) == 16):     #Case 2: 3 sat in view in this sentence    
                cnt = 0
                for j in range(0,3):
                    prn.append(str(prn_offset + int(sent[4+cnt])))               
                    elv.append(sent[5+cnt])             
                    az.append(sent[6+cnt])                
                    snr.append(sent[7+cnt].split("*")[0]) 
                    if ms <= ttl_ms:
                        t.append(t_sec)
                
                    cnt = cnt + 4
#            ###    
            elif (len(sent) == 12):   #Case 3: 2 sat in view in this sentence    
                cnt = 0
                for j in range(0,2):
                    prn.append(str(prn_offset + int(sent[4+cnt])))              
                    elv.append(sent[5+cnt])                
                    az.append(sent[6+cnt])                 
                    snr.append(sent[7+cnt].split("*")[0]) 
                    if ms <= ttl_ms:
                        t.append(t_sec)
                
                    cnt = cnt + 4
#            ###                   
            elif (len(sent) == 8):  #Case 4: 1 sat in view in this sentence    
                cnt = 0
                for j in range(0,1):
                    prn.append(str(prn_offset + int(sent[4+cnt])))               
                    elv.append(sent[5+cnt])                
                    az.append(sent[6+cnt])                
                    snr.append(sent[7].split("*")[0])  
                    if ms <= ttl_ms:
                        t.append(t_sec)
                
                    cnt = cnt + 4
#            ###    
            ttl_ms = 0
            ms = 0
    return t, prn, az, elv, snr

def fix_angle_azimuth(time, angle, azimuth):
    """
    interpolate elevation angles and azimuth to retrieve decimal values thru time     
    this is for NMEA files.

    Parameters
    ----------
    time : list of floats
        GPS seconds of the week
    angle : list of floats
        elevation angles  (degrees)

    azimuth : list of floats
        azimuth angles (degrees)

    Returns
    -------
    angle_fixed : list of floats
        interpolated elevation angles

    azim_fixed : list of floats
        interpolated azimuth angles

    """
    
#delet nans
    time = time[~np.isnan(angle)];azimuth =  azimuth[~np.isnan(angle)];angle = angle[~np.isnan(angle)]
#delet nans
    time = time[~np.isnan(azimuth)];angle = angle[~np.isnan(azimuth)];azimuth =  azimuth[~np.isnan(azimuth)]
#delet nans
    angle = angle[~np.isnan(time)];azimuth =  azimuth[~np.isnan(time)];time = time[~np.isnan(time)]

    dangle = np.diff(angle)#diff angle
    ind1 = np.array(np.where(dangle!=0))
    
    dazim = azimuth_diff1(azimuth)#diff azimuth
    ind3 = np.array(np.where(dazim!=0))
    
    if ind1.size > 1 and ind3.size > 1:
        ind2 = ind1 +1
        time_angle0 = ( (time[ind1]+time[ind2])/2.0 )[0]
        angle0 = ( (angle[ind1]+angle[ind2])/2.0 )[0]

        ind4 = ind3 +1
        time_azim0 = ( (time[ind3]+time[ind4])/2.0 )[0]
        azim0 = azimuth_mean(azimuth[ind3], azimuth[ind4])

#interpolate at mean values
        f_ang = interp1d(time_angle0, angle0, kind = 'linear', fill_value="extrapolate")
        f_azim = interp1d(time_azim0, azim0, kind = 'linear', fill_value="extrapolate")
        angle_fixed = f_ang(time)#interpolated elev angle
        azim_fixed = f_azim(time)#interpolated azimuth angle

    else:#return emty outputs for tracks with not changing elv and/or azm values. This often happnes for a chunk of nmea data when the daily record is not complete  
        angle_fixed = []; azim_fixed = []
    
    return angle_fixed, azim_fixed  
        

def azimuth_diff2(azim1, azim2):
    diff = azim1 - azim2
    idx = (diff > +180)  
    diff[idx] = diff[idx] - 360
    idx = (diff < -180)  
    diff[idx] = diff[idx] + 360
    return diff

def azimuth_diff1 (azim):
    """
    Parameters
    ----------
    azim: ??

    """
    azim_a = azim[0:-1]
    azim_b = azim[1:]
    diff = azimuth_diff2 (azim_b, azim_a);
    #diff = azimuth_diff2 (azima, azimb);  % WRONG!   
    return diff

def azimuth_diff(azim1, azim2):
    """
    Parameters
    ----------
    azim1 : ??

    azim2 : ??

    """
    if not(azim2.size):
        diff = azimuth_diff1 (azim1)
    else:
        diff = azimuth_diff2 (azim1, azim2)
#    diff = np.abs(diff)
    return diff
     
def angle_range_positive(ang):
    """

    Parameters
    ----------
    ang : ??

    """
#    idx1 = np.isfinite(ang)
    ang = np.angle(np.exp(1j*ang*np.pi/180))*180/np.pi  
    idx2 = (ang < 0)
    ang[idx2] = 360 + ang[idx2]
    return ang

def azimuth_mean(azim1, azim2):
    """
    Parameters
    ----------
    azim1 : list of floats ? 
         azimuth degrees

    azim2 : list of floats
         azimuth degrees

    Returns
    -------
    azim : list of floats ?
        azimuths in degrees
    """
    azim = np.concatenate([azim1, azim2])
    if np.all(azim1 >= 0) and np.all(azim2 >= 0):
        azim1 = angle_range_positive(azim1)
        azim2 = angle_range_positive(azim2)
        azim = ( (azim1 + azim2)/2.0 )[0] 
    else:
        x1 = np.sin(azim1*np.pi/180);x2 = np.sin(azim2*np.pi/180)
        y1 = np.cos(azim1*np.pi/180);y2 = np.cos(azim2*np.pi/180) 
        x = ( (x1 + x2)/2.0 )[0];y = ( (y1 + y2)/2.0 )[0]
        azim = 180/np.pi * np.arctan2(x, y)

    return azim

def quickname(station,year,cyy, cdoy, csnr):
    """
    full name of the snr file name (incl path) 

    Parameters
    ----------
    station : str
        4 ch station name

    year : int
        full year

    cyy : str 
        two character year

    cdoy : str
        three character day of year

    csnr : str
        snr type, e.g. '66' 

    Returns
    -------
    fname : str
        output filename

    """
    
    xdir  = os.environ['REFL_CODE'] + '/'
    fname =  xdir + str(year) + '/snr/' + station + '/' + station + cdoy + '0.' + cyy + '.snr' + csnr
    if not (os.path.exists(xdir + str(year) + '/snr/' + station+'/')):
        os.system('mkdir -p '+xdir + str(year) + '/snr/' + station+'/')

    return fname

def elev_limits(snroption):
    """

    given snr option return the elevation angle limits

    Parameters
    ----------
    snroption : int
        snrfile number

    Returns
    -------
    emin : float
        min elevation angle (degrees)
    emax : float
        max elevation angle (degrees)

    """

    if (snroption == 99):
        emin = 5; emax = 30
    elif (snroption == 50):
        emin = 0; emax = 10
    elif (snroption == 66):
        emin = 0; emax = 30
    elif (snroption == 88):
        emin = 5; emax = 90
    else:
        emin = 5; emax = 30

    return emin, emax
  
def run_nmea2snr(station, year_list, doy_list, isnr, overwrite):
    """
    runs the nmea2snr conversion code

    Parameters
    ----------
    station : str
        name of station 

    year_list : list of integers
        years 

    doy_list : list of days of year
        days of years

    isnr : int
        snr file type

    overwrite : bool
        whether make a new SNR file even if one already exists

    """
    # loop over years and day of years
    for yr in year_list:
        
        locdir= os.environ['REFL_CODE'] + '/nmea/' + station + '/' + str(yr) + '/'
        for dy in doy_list:
            csnr = str(isnr)
            cdoy = '{:03d}'.format(dy)
            cyy = '{:02d}'.format(yr-2000)
            snrfile =  quickname(station,yr,cyy,cdoy,csnr)#snr filename
            snre = g.snr_exist(station,yr,dy,csnr)#check if snrfile already sxists
            if snre:
                print('SNR file exists', snrfile)
            if overwrite:
                subprocess.call(['rm', snrfile])
                snre = False
        
            illegal_day = False
            if (float(dy) > g.dec31(yr)):
                illegal_day = True
        
            if (not illegal_day) and (not snre):
                r =  station + cdoy + '0.' + cyy + '.A'# nmea file name example:  WESL2120.21.A 
                
                if os.path.exists(locdir+r) or os.path.exists(locdir+r+'.gz') or os.path.exists(locdir+r+'.Z'):
                    print('Creating '+snrfile)
                    NMEA2SNR(locdir, r, snrfile, csnr)
                    
                else:
                    print('NMEA file '+r+' does not exist')
