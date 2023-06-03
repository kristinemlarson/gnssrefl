#!/usr/bin/env python
# -*- coding: utf-8 -*-
import numpy as np
import os
import subprocess 
import sys

def read_snr_multiday(obsfile,obsfile2,twoDays,dec=1):
    """
    originally meant to make snr arrays longer than a day to take care
    of midnight crossing.  not currently invoked.

    Snr data have units changed to linear units I believed.

    Parameters
    ----------
    obsfile : string
        name of first SNR input file

    obsfile2 : string
        name of second SNR input file

    twoDays : boolean
        False (default) for using only the first file

    dec : int
        decimation value. 1 means do nothing

    Results
    -------
    allGood1 : numpy array

    sat : numpy array
        satellite numbers 

    ele : numpy array
        elevation angle (degrees)

    azi : numpy array
        azimuth angles (degrees)

    t : numpy array
        time, seconds of the day, GPS time

    edot : numpy array
        derivative of elevation angle with respect to time

    s1 : numpy array
        SNR on L1 frequency

    s2 : numpy array
        SNR on L2 frequency

    s5 : numpy array
        SNR on L5 frequency

    s6 : numpy array
        SNR on L6 frequency

    s7 : numpy array
        SNR on L7 frequency

    s8 : numpy array
        SNR on L8 frequency

    snrE : boolean
        whether it exists

    """
#   defaults so all returned vectors have something stored in them
    sat=[]; ele =[]; azi = []; t=[]; edot=[]; s1=[];
    s2=[]; s5=[]; s6=[]; s7=[]; s8=[];
    snrE = np.array([False, True, True,False,False,True,True,True,True],dtype = bool)
#
    allGood1 = 0; allGood2 = 0
    # set these for now.  should be passed 
    # not being used ??? why are they here
    #e1 = 5
    #e2 = 15
    try:
#       this will be 24 hours - all in one calendar day 
#        print('>>>>>>>>>>>>>>>>>>>>> try to read file 1:')
        compressedObs = obsfile + '.xz'
        if (os.path.isfile(compressedObs) == True):
            print('compressed file exists, so uncompress it')
            subprocess.call(['unxz', compressedObs])
        sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snrE = read_one_snr(obsfile,1)
        allGood1 = 1
#        g.print_file_stats(ele,sat,s1,s2,s5,s6,s7,s8,e1,e2)
    except:
        print('>>>>> Could not read the first SNR file:', obsfile)
#
    if (dec != 1) & (allGood1 == 1):
        print('Invoking the decimation flag:')
        rem_arr = np.remainder(t, [dec])
        iss = (rem_arr==0)
        sat=sat[iss] ; ele=ele[iss] ; azi=azi[iss]
        t=t[iss] ; edot=edot[iss]
        s1= s1[iss] ; s2= s2[iss] ; 
        if len(s5) > 0:
            s5= s5[iss] ;
        if len(s6) > 0:
            s6= s6[iss] ; 
        if len(s7) > 0:
            s7= s7[iss] ; 
        if len(s8) > 0:
            s8= s8[iss]
#
    if twoDays:
#   restrict day one to first 21 hours.  will then merge iwth last three hours
#   of previous day
#       in case these observables do not exist
        Qs5=[]; Qs6=[]; Qs7=[]; Qs8=[]
        tt = t 
        hours21 = 21*3600
        print('length(tt)', len(tt))
        Qt =tt[tt < hours21]
        Qsat =sat[tt < hours21]
        Qele =ele[tt < hours21]
        Qazi =azi[tt < hours21]
        Qedot = edot[tt < hours21]
        Qs1 = s1[tt < hours21]
        Qs2 = s2[tt < hours21]
        if snrE[5]:
            Qs5 = s5[tt < hours21]
        if snrE[6]:
            Qs6 = s6[tt < hours21]
        if snrE[7]:
            Qs7 = s7[tt < hours21]
        if snrE[8]:
            Qs8 = s8[tt < hours21]
#       I think this is ok??
        QsnrE = snrE
        try:
            compressedObs = obsfile2 + '.xz'
            if (os.path.isfile(compressedObs) == True):
                print('compressed file exists, so uncompress it')
                cmd = 'unxz ' + compressedObs; os.system(cmd)
            #print('>>>>>>>>>>>>>>>>>>>>> try to read last three hours of file 2:')
            Psat, Pele, Pazi, Pt, Pedot, Ps1, Ps2, Ps5, Ps6, Ps7, Ps8, PsnrE = read_one_snr(obsfile2,2)
            allGood2 = 1
        except: 
            print('failed to read second file')
    if (twoDays) & (allGood1 == 1) & (allGood2 == 1):
        print('stack the two days')
        ele = np.hstack((Pele,Qele))
        sat = np.hstack((Psat,Qsat))
        azi = np.hstack((Pazi,Qazi))
        t =   np.hstack((Pt,Qt))
        edot= np.hstack((Pedot,Qedot))
        s1 =  np.hstack((Ps1,Qs1))
        s2 =  np.hstack((Ps1,Qs2))
        s5 =  np.hstack((Ps1,Qs5))
        s6 =  np.hstack((Ps1,Qs6))
        s7 =  np.hstack((Ps1,Qs7))
        s8 =  np.hstack((Ps1,Qs8))
    return  allGood1,sat,ele,azi,t,edot,s1,s2,s5,s6,s7,s8,snrE

def read_one_snr(obsfile,ifile):
    """
    reads a SNR file, changes units (linear) and stores as variables

    Parameters
    ----------
    obsfile : str
        SNR file name
    ifile : int
        1 for primary file or 2 for the day before the primary file

    Returns
    -------
    sat: numpy array of int 
        satellite number 
    ele : numpy array of floats 
        elevation angle in degrees
    azi : numpy array of floats
        azimuth in degrees
    t:  numpy array of floats
        time in seconds of the day
    edot : numpy array of floats
        elevation angle derivative (units?)
    s1 : numpy array of floats
        L1 SNR in dB-Hz
    s2:  numpy array of floats 
        L2 SNR in dB-Hz
    s5 :  numpy array of floats 
        L5 SNR in dB-Hz
    s6 :  numpy array of floats 
        L6 SNR in dB-Hz
    s7 :  numpy array of floats 
        L7 SNR in dB-Hz
    s8 :  numpy array of floats 
        L8 SNR in dB-Hz
    snrE : bool list
        whether the SNR exists for that Frequency 

    """

    sat=[]; ele=[]; az=[]; t=[]; edot=[]; s=[];  s2=[]; s5=[];  s6=[]; s7=[];  s8=[];
#SNR existence array : s0, s1,s2,s3,s4,s5,s6,s7,s8.  fields 0,3,4 are always false
#

    snrE = np.array([False, True, True,False,False,True,True,True,True],dtype = bool)
    f = np.genfromtxt(obsfile,comments='%')
    #print('reading from this snr file ',obsfile)
    r,c = f.shape
    if (r > 0) & (c > 0):
        #print('make sure no negative elevation angle data are used')
        i= f[:,1] > 0
        f=f[i,:]
    if r == 0:
        print('no rows in this file!')
    if c == 0:
        print('no columns in this file!')

    #print('Number of rows:', r, ' Number of columns:',c)
#   store into new variable f
#   now only keep last three hours if previous day's file
    hoursKept = 21*3600
    if (ifile == 2):
        print('window last three hours')
        tt = f[:,3]
        f=f[tt > hoursKept]
#   save satellite number, elevation angle, azimuth value
    sat = f[:,0]
    ele = f[:,1]
    azi = f[:,2]
#   negative time tags for day before
    if (ifile == 1):
        #print('keep timetags as they are ')
        t =  f[:,3]
    else:
        print('make timetags negative')
        t =  f[:,3] - 86400
#   ok - the rest is the same as alwasy
#   this is sometimes all zeros
    edot =  f[:,4]
    s1 = f[:,6]
    s2 = f[:,7]
#   typically there is a zero in this row, but older files may have something
#   something that should not be used 
    s6 = f[:,5]

    s1 = np.power(10,(s1/20))  
    s2 = np.power(10,(s2/20))  
#
    s6 = s6/20
    s6 = np.power(10,s6)  
#
#   sometimes these records exist, sometimes not
#   depends on when the file was made, which version was used
#   make sure s5 has default value?
    s5 = []
    if c > 8:
        s5 = f[:,8]
        if (sum(s5) > 0):
            s5 = s5/20; s5 = np.power(10,s5)  
    if c > 9:
        s7 = f[:,9]
        if (sum(s7) > 0):
            s7 = np.power(10,(s7/20))  
        else:
            s7 = []

    if c > 10:
        s8 = f[:,10]
        if (sum(s8) > 0):
            s8 = np.power(10,(s8/20))  
        else:
            s8 = []

    if (np.sum(s5) == 0):
        snrE[5] = False
        #print('no s5 data')
    if (np.sum(s6) == 0):
        #print('no s6 data')
        snrE[6] = False
    if (np.sum(s7) == 0):
        #print('no s7 data')
        snrE[7] = False
    if (np.sum(s8) == 0):
        snrE[8] = False
        #print('no s8 data')

    return sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snrE

def compress_snr_files(wantCompression, obsfile, obsfile2,TwoDays,gzip):
    """
    compresses SNR files

    Parameters
    ----------
    wantCompression : bool
        whether the file should be compressed again
    obsfile : str
        name of first SNR file
    obsfile2 : str
        name of second SNR file
    TwoDays : bool
        whether second file is being input
    gzip : bool
        whether you want to gzip/gunzip the file

    """
    if gzip:
        if (os.path.isfile(obsfile) == True):
            subprocess.call(['gzip', obsfile])
        if (os.path.isfile(obsfile2) == True and twoDays == True):
            subprocess.call(['gzip', obsfile2])
    else:
        # this is only for xz compression
        if wantCompression:
            if (os.path.isfile(obsfile) == True):
                subprocess.call(['xz', obsfile])
            if (os.path.isfile(obsfile2) == True and twoDays == True):
                subprocess.call(['xz', obsfile2])
