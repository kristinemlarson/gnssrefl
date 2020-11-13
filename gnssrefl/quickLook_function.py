"""
quickLook functions - consolidated snr reader (previously in a separate file)
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure

import scipy.interpolate
import scipy.signal

import gnssrefl.gps as g
import gnssrefl.rinex2snr as rinex


def read_snr_simple(obsfile):
    """
    author: Kristine Larson
    input: SNR observation filenames and a boolean for 
    whether you want just the first day (twoDays)
    output: contents of the SNR file, withe various other metrics
    """
#   defaults so all returned vectors have something stored in them
    sat=[]; ele =[]; azi = []; t=[]; edot=[]; s1=[];
    s2=[]; s5=[]; s6=[]; s7=[]; s8=[];
    snrE = np.array([False, True, True,False,False,True,True,True,True],dtype = bool)
#   
    allGood = 1
    try:
        f = np.genfromtxt(obsfile,comments='%')
        r,c = f.shape
        #print('read_snr_simple, Number of rows:', r, ' Number of columns:',c)
        sat = f[:,0]; ele = f[:,1]; azi = f[:,2]; t =  f[:,3]
        edot =  f[:,4]; s1 = f[:,6]; s2 = f[:,7]; s6 = f[:,5]
        s1 = np.power(10,(s1/20))  
        s2 = np.power(10,(s2/20))  
        s6 = s6/20; s6 = np.power(10,s6)  
#   make sure s5 has default value?
        s5 = []
        if c > 8:
            s5 = f[:,8]
            if (sum(s5) > 0):
                s5 = s5/20; s5 = np.power(10,s5)  
            print(len(s5))
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
            snrE[5] = False; #print('no s5 data')
        if (np.sum(s6) == 0):
            #print('no s6 data'); 
            snrE[6] = False
        if (np.sum(s7) == 0):
           # print('no s7 data'); 
            snrE[7] = False
        if (np.sum(s8) == 0):
            snrE[8] = False; # print('no s8 data')
    except:
        print('problem reading the SNR file')
        allGood = 0
    return allGood, sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snrE


def quickLook_function(station, year, doy, snr_type,f,e1,e2,minH,maxH,reqAmp,pele,satsel,PkNoise,fortran):
    """
    inputs:
    station name (4 char), year, day of year
    snr_type is the file extension (i.e. 99, 66 etc)
    f is frequency (1, 2, 5), etc
    e1 and e2 are the elevation angle limits in degrees for the LSP
    minH and maxH are the allowed LSP limits in meters
    reqAmp is LSP amplitude significance criterion
    pele is the elevation angle limits for the polynomial removal.  units: degrees
    KL 20may10 pk2noise value is now sent from main function, which can be set online
    KL 20aug07 added fortran boolean
    """
    # make sure environment variables exist
    g.check_environ_variables()

    webapp = False 
    # orbit directories
    ann = g.make_nav_dirs(year)
    # titles in 4 quadrants - for webApp
    titles = ['Northwest', 'Southwest','Northeast', 'Southeast']
    # define where the axes are located
    bx = [0,1,0,1]; by = [0,0,1,1]; bz = [1,3,2,4]

    # various defaults - ones the user doesn't change in this quick Look code
    delTmax = 70
    polyV = 4 # polynomial order for the direct signal
    desiredP = 0.01 # 1 cm precision
    ediff = 2 # this is a QC value, eliminates small arcs
    #four_in_one = True # put the plots together
    minNumPts = 20 
    #noise region for LSP QC. these are meters
    NReg = [minH, maxH]
    print('Refl. Ht. Noise Region used: ', NReg)
    # for quickLook, we use the four geographic quadrants - these are azimuth angles in degrees
    azval = [270, 360, 180, 270, 0, 90, 90, 180]
    naz = int(len(azval)/2) # number of azimuth pairs
    pltname = 'temp.png' # default plot
    requireAmp = reqAmp[0]
    screenstats = True

# to avoid having to do all the indenting over again
# this allows snr file to live in main directory
# not sure that that is all that useful as I never let that happen
    obsfile = g.define_quick_filename(station,year,doy,snr_type)
    if os.path.isfile(obsfile):
        print('>>>> The snr file exists ',obsfile)
    else:
        if True:
            print('looking for the SNR file on disk')
            obsfile, obsfileCmp, snre =  g.define_and_xz_snr(station,year,doy,snr_type)
            if snre:
                dkfjaklj = True
                #print('file exists on disk')
            else:
                print('>>>> The SNR the file does not exist ',obsfile)
                print('I will try to pick up a RINEX file ')
                print('and translate it for you. This will be GPS only.')
                print('For now I will check all the official archives for you.')
                rate = 'low'; dec_rate = 0; archive = 'all'; 
                rinex.conv2snr(year, doy, station, int(snr_type), 'nav',rate,dec_rate,archive,fortran)
                if os.path.isfile(obsfile):
                    print('the SNR file now exists')  
                else:
                    print('the RINEX file did not exist, had no SNR data, or failed to convert, so exiting.')
    allGood,sat,ele,azi,t,edot,s1,s2,s5,s6,s7,s8,snrE = read_snr_simple(obsfile)
    if allGood == 1:
        # make output file for the quickLook RRH values, just so you can give them a quick look see
        rhout = open('rh.txt','w+')
        amax = 0
        minEdataset = np.min(ele)
        print('minimum elevation angle (degrees) for this dataset: ', minEdataset)
        if minEdataset > (e1+0.5):
            print('It looks like the receiver had an elevation mask')
            e1 = minEdataset
        if webapp:
            fig = Figure(figsize=(10,6), dpi=120)
            axes = fig.subplots(2, 2)
        else:
            #plt.figure()
            # trying to help Kelly
            plt.figure(figsize=(10,6))
        for a in range(naz):
            if not webapp:
                plt.subplot(2,2,bz[a])
                plt.title(titles[a])
            az1 = azval[(a*2)] ; az2 = azval[(a*2 + 1)]
            # this means no satellite list was given, so get them all
            if satsel == None:
                satlist = g.find_satlist(f,snrE)
            else:
                satlist = [satsel]

            for satNu in satlist:
                x,y,Nv,cf,UTCtime,avgAzim,avgEdot,Edot2,delT= g.window_data(s1,s2,s5,s6,s7,s8,sat,ele,azi,t,edot,f,az1,az2,e1,e2,satNu,polyV,pele,screenstats) 
                if Nv > minNumPts:
                    maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,desiredP,polyV,minH) 
                    nij =   pz[(px > NReg[0]) & (px < NReg[1])]
                    Noise = 0
                    iAzim = int(avgAzim)
                    if (len(nij) > 0):
                        Noise = np.mean(nij)
                    else:
                        Noise = 1; iAzim = 0 # made up numbers
                    if (delT < delTmax) & (eminObs < (e1 + ediff)) & (emaxObs > (e2 - ediff)) & (maxAmp > requireAmp) & (maxAmp/Noise > PkNoise):
                        T = g.nicerTime(UTCtime)
                        rhout.write('SUCCESS Azimuth {0:3.0f} RH {1:6.3f} m, Sat {2:3.0f} Freq {3:3.0f} Amp {4:4.1f} PkNoise {5:3.1f} UTC {6:5s} \n '.format( 
                            avgAzim,maxF,satNu,f,maxAmp,maxAmp/Noise,T))
                        if not webapp:
                            plt.plot(px,pz,linewidth=1.5)
                        else:
                            axes[bx[a],by[a]].plot(px,pz,linewidth=2)
                            axes[bx[a],by[a]].set_title(titles[a])
                    else:
                        if not webapp:
                            plt.plot(px,pz,'gray',linewidth=0.5)

            # i do not know how to add a grid using these version of matplotlib
            tt = 'GNSS-IR results: ' + station.upper() + ' Freq:' + str(f) + ' ' + str(year) + '/' + str(doy)
            aaa, bbb = plt.ylim()
            amax = max(amax,  bbb) # do not know how to implement this ...
            if (a == 3) or (a==1):
                plt.xlabel('reflector height (m)')
        plt.suptitle(tt, fontsize=12)

        rhout.close()
        print('Reflector Height results are stored in a file called rh.txt')
        if webapp:
            fig.savefig('temp.png', format="png")
        else:
            plt.show()
    else: 
        print('some kind of problem with SNR file, so I am exiting the code politely.')
