# -*- coding: utf-8 -*-
import datetime
import json
import matplotlib.pyplot as plt
import numpy as np
import os
import scipy.interpolate
import scipy.signal
import subprocess
import sys
import warnings

import gnssrefl.gps as g
import gnssrefl.read_snr_files as snr
import gnssrefl.refraction as refr

def gnssir_guts(station,year,doy, snr_type, extension,lsp):
    """
    my attempt to separate the inputs to the code and the guts of the code
    inputs are station name, year, day of year (integers)
    snr_type is an integer (99, 66, etc). lsp is a json
    """

    #   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    e1=lsp['e1']; e2=lsp['e2']; minH = lsp['minH']; maxH = lsp['maxH']
    ediff = lsp['ediff']; NReg = lsp['NReg']  
    PkNoise = lsp['PkNoise']; azval = lsp['azval']; naz = int(len(azval)/2)
    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp'] 
    plot_screen = lsp['plt_screen'] 
    onesat = lsp['onesat']; screenstats = lsp['screenstats']
    #print('value of screenstats ', screenstats, lsp['screenstats'])
    azval = lsp['azval']

    d = g.doy2ymd(year,doy); month = d.month; day = d.day
    dmjd, fracS = g.mjd(year,month,day,0,0,0)
    xdir = os.environ['REFL_CODE']
    ann = g.make_nav_dirs(year) # make sure directories are there for orbits
    g.result_directories(station,year,extension) # make directories for the LSP results

   # this defines the minimum number of points in an arc.  This depends entirely on the sampling
   # rate for the receiver, so you should not assume this value is relevant to your case.
    minNumPts = 20
    p,T,irefr = set_refraction_params(station, dmjd, lsp)

# only doing one day at a time for now - but have started defining the needed inputs for using it
    twoDays = False
    obsfile2= '' # dummy value for name of file for the day before, when we get to that
    fname, resultExist = g.LSPresult_name(station,year,doy,extension) 
    print('Results are written to:', fname)

    #if (resultExist):
    #    print('Results already exist on disk')
    if (lsp['overwriteResults'] == False) & (resultExist == True):
        allGood = 0
        print('>>>>> The result file already exists for this day and you have selected the do not overwrite option')
        #sys.exit()
    #print('go ahead and access SNR data - first define SNR filename')
    else:
        obsfile, obsfileCmp, snre = g.define_and_xz_snr(station,year,doy,snr_type) 
    #print(obsfile, 'snrexistence',snre,' and ', snr_type)
    # removing this option
    #if (not snre) and (not lsp['seekRinex']):
    #    print('The SNR file does not exist and you have set the seekRinex variable to False')
    #    print('Use rinex2snr.py to make SNR files')
    #    #sys.exit()
    #    allGood = 0
    #if (not snre) and lsp['seekRinex']:
    #    print('The SNR file does not exist. I will try to make a GPS only file using the Fortran option.')
    #    rate = 'low'; dec_rate = 0; orbtype = 'nav'
    #    g.quick_rinex_snrC(year, doy, station, snr_type, orbtype,rate, dec_rate)

        allGood,sat,ele,azi,t,edot,s1,s2,s5,s6,s7,s8,snrE = snr.read_snr_multiday(obsfile,obsfile2,twoDays)
        snr.compress_snr_files(lsp['wantCompression'], obsfile, obsfile2,twoDays) 
    if (allGood == 1):
        ele=apply_refraction_corr(lsp,ele,p,T)
        fout,frej = g.open_outputfile(station,year,doy,extension) 
#  main loop a given list of frequencies
        total_arcs = 0
        ct = 0
        for f in freqs:
            if plot_screen: 
                # no idea if this will work
                fig, (ax1, ax2) = plt.subplots(2, 1,figsize=(10,7))
                #axes = fig.subplots(2, 2)
                #fig = Figure(figsize=(10,6))
            rj = 0
            gj = 0
            print('**** looking at frequency ', f, ' ReqAmp', reqAmp[ct], ' doy ', doy, 'ymd', year, month, day )
#   get the list of satellites for this frequency
            if onesat == None:
                satlist = g.find_satlist(f,snrE)
            else:
                satlist = onesat
                if (int(satlist[0]) < 100) and (f > 100):
                    print('wrong satellite name for this frequency')
                
            for satNu in satlist:
                #if screenstats: print('Satellite', satNu)
                for a in range(naz):
                    az1 = azval[(a*2)] ; az2 = azval[(a*2 + 1)]
                    x,y,Nv,cf,UTCtime,avgAzim,avgEdot,Edot2,delT= g.window_data(s1,s2,s5,s6,s7,s8,sat,ele,azi,t,edot,f,az1,az2,e1,e2,satNu,lsp['polyV'],lsp['pele'],screenstats) 
                    MJD = g.getMJD(year,month,day, UTCtime)
                    if Nv > minNumPts:
                        maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,lsp['desiredP'],lsp['polyV'],minH) 
                        nij =   pz[(px > NReg[0]) & (px < NReg[1])]
                        Noise = 0
                        if (len(nij) > 0):
                            Noise = np.mean(nij)
                        iAzim = int(avgAzim)
                        okPk = True
                        if abs(maxF - minH) < 0.10: #  peak too close to min value
                            okPk = False
                            #print('found a peak too close to the edge of the restricted RH region')
                        if okPk & (delT < lsp['delTmax']) & (eminObs < (e1 + ediff)) & (emaxObs > (e2 - ediff)) & (maxAmp > reqAmp[ct]) & (maxAmp/Noise > PkNoise):
                            fout.write(" {0:4.0f} {1:3.0f} {2:6.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} \n".format(year,doy,maxF,satNu, UTCtime, avgAzim,maxAmp,eminObs,emaxObs,Nv, f,riseSet, Edot2, maxAmp/Noise, delT, MJD,irefr)) 
                            gj +=1
                            if screenstats:
                                T = g.nicerTime(UTCtime)
                                print('SUCCESS Azimuth {0:3.0f} Sat {1:3.0f} RH {2:7.3f} m PkNoise {3:4.1f} Amp {4:4.1f} Fr{5:3.0f} UTC {6:5s} DT {7:3.0f} '.format(iAzim,satNu,maxF,maxAmp/Noise,maxAmp, f,T,round(delT)))
                            if plot_screen:
                                local_update_plot(x,y,px,pz,ax1,ax2)
                        else:
                            rj +=1
                            if screenstats:
                                print('FAILED QC for Azimuth {0:.1f} Satellite {1:2.0f} UTC {2:5.2f}'.format( iAzim,satNu,UTCtime))
                                g.write_QC_fails(delT,lsp['delTmax'],eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,reqAmp[ct])
            print('=================================================================================')
            print('     Frequency ', f, ' good arcs:', gj, ' rejected arcs:', rj )
            print('=================================================================================')
            total_arcs = gj + total_arcs
# close the output files
            ct += 1
            #'Yes' if fruit == 'Apple' else 'No'
            if plot_screen: plot2screen(station, f, ax1, ax2,lsp['pltname']) 
        fout.close() ; # these are the LSP results written to text file 


def set_refraction_params(station, dmjd,lsp):
    """
    called from guts.  pick up refr info
    inputs are station name, modified julian day, and the 
    lsp dictionary
    """
    xdir = os.environ['REFL_CODE']
    p = 0; T = 0; irefr = 0
    if lsp['refraction']:
        irefr = 1
        refr.readWrite_gpt2_1w(xdir, station, lsp['lat'], lsp['lon'])
# time varying is set to no for now (it = 1)
        it = 1
        dlat = lsp['lat']*np.pi/180; dlong = lsp['lon']*np.pi/180; ht = lsp['ht']
        p,T,dT,Tm,e,ah,aw,la,undu = refr.gpt2_1w(station, dmjd,dlat,dlong,ht,it)
        #print("Pressure {0:8.2f} Temperature {1:6.1f} \n".format(p,T))

    return p,T,irefr

def apply_refraction_corr(lsp,ele,p,T):
    """
    """
    if lsp['refraction']:
        #print('<<<<<< apply refraction correction >>>>>>')
        corrE = refr.corr_el_angles(ele, p,T)
        ele = corrE

    return ele

def local_update_plot(x,y,px,pz,ax1, ax2):
    """
    input plt_screen integer value from gnssIR_lomb.
    (value of one means update the SNR and LSP plot)
    and values of the SNR data (x,y) and LSP (px,pz)
    """
    ax1.plot(x,y)
    ax2.plot(px,pz)


def plot2screen(station, f,ax1,ax2,pltname):
    """
    painful painful
    https://www.semicolonworld.com/question/57658/matplotlib-adding-an-axes-using-the-same-arguments-as-a-previous-axes
    """
    #print(pltname)
    ax2.set_xlabel('Reflector Height (m)'); 
    #ax2.set_title('SNR periodogram')
    ax2.set_ylabel('SNR periodogram')
    ax1.set_ylabel('volts/volts')
    ax1.set_xlabel('Elevation Angles (deg)')
    ax1.set_title(station + ' SNR Data and Frequency L' + str(f))
    plt.show()

    return True


def read_json_file(station, extension):
    """
    picks up json instructions for periodogram
    inputs are the station name and an extension (which can just be '')
    """
    lsp = {} # ???
    instructions_ext = str(os.environ['REFL_CODE']) + '/input/' + station + '.' + extension + '.json'
    instructions = str(os.environ['REFL_CODE']) + '/input/' + station + '.json'
    if os.path.isfile(instructions_ext):
        print('using specific instructions for this extension')
        with open(instructions_ext) as f:
            lsp = json.load(f)
    else:
        print('will use the default instruction file')
        if os.path.isfile(instructions):
            with open(instructions) as f:
                lsp = json.load(f)
        else:
            print('json instruction file does not exist: ', instructions)
            print('Please make with make_json_input and run this code again.')
            sys.exit()

    return lsp
