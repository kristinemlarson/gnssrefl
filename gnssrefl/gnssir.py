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

    Computes lomb scargle periodograms for a given station, year, day of year etc.

    Parameters
    ----------
    station : string
        4 character station name

    year : integer
        full year

    doy : integer
        day of year

    snr_type : integer
        snr file type

    extension : string
        optional subdirectory to save results

    lsp : dictionary
        REQUIRES DESCRIPTION
        
    """

    #   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    # this is also checked in the command line - but for people calling the code ...
    if ((lsp['maxH'] - lsp['minH']) < 5):
        print('Requested reflector heights (', lsp['minH'], ',', lsp['maxH'], ') are too close together. Exiting.')
        print('They must be at least 5 meters apart - and preferably further than that.')
        return

    e1=lsp['e1']; e2=lsp['e2']; minH = lsp['minH']; maxH = lsp['maxH']
    ediff = lsp['ediff']; NReg = lsp['NReg']  
    PkNoise = lsp['PkNoise']; azval = lsp['azval']; naz = int(len(azval)/2)
    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp'] 

    ok = g.is_it_legal(freqs)
    if not ok:
        print('Fix your json list of frequencies. Exiting')
        sys.exit()

    plot_screen = lsp['plt_screen'] 
    onesat = lsp['onesat']; screenstats = lsp['screenstats']
    gzip = lsp['gzip']
    if 'dec' in lsp.keys():
        dec = lsp['dec']
    else:
        dec = 1 # so Jupyter notebooks do not need to be rewritten
    #print('Decimate:', dec)
    #print('Number of azimuths', len(azval))
    for i in range(0,len(azval),2):
        #print(i, azval[i], azval[i+1])
        if (azval[i+1] - azval[i]) > 100:
            print('FATAL WARNING: You are prohibited from having an azimuth range that is larger than 100 degrees.')
            print('Azimuth values:', azval[i], azval[i+1])
            print('Change the json input file. Exiting.')
            sys.exit()

    d = g.doy2ymd(year,doy); month = d.month; day = d.day
    dmjd, fracS = g.mjd(year,month,day,0,0,0)
    xdir = os.environ['REFL_CODE']
    ann = g.make_nav_dirs(year) # make sure directories are there for orbits
    g.result_directories(station,year,extension) # make directories for the LSP results

   # this defines the minimum number of points in an arc.  This depends entirely on the sampling
   # rate for the receiver, so you should not assume this value is relevant to your case.
    minNumPts = 20
    p,T,irefr = set_refraction_params(station, dmjd, lsp)
    #print(p,T)

# only doing one day at a time for now - but have started defining the needed inputs for using it
    twoDays = False
    obsfile2= '' # dummy value for name of file for the day before, when we get to that
    fname, resultExist = g.LSPresult_name(station,year,doy,extension) 
    #print('Results are written to:', fname)

    #if (resultExist):
    #    print('Results already exist on disk')
    #if (lsp['overwriteResults'] == False) & (resultExist == True):
    if (lsp['nooverwrite'] == True) & (resultExist == True):
        allGood = 0
        print('>>>>> The result file already exists for this day and you have selected the do not overwrite option')
        #sys.exit()
    else:
        # uncompress here so you should not have to do it in read_snr_multiday ...
        obsfile, obsfileCmp, snre = g.define_and_xz_snr(station,year,doy,snr_type) 
        print('Using: ', obsfile)

        allGood,sat,ele,azi,t,edot,s1,s2,s5,s6,s7,s8,snrE = snr.read_snr_multiday(obsfile,obsfile2,twoDays,dec)
        # added gzip option.  first input is xz compression
        snr.compress_snr_files(lsp['wantCompression'], obsfile, obsfile2,twoDays,gzip) 
    if (allGood == 1):
        print('Results will be written to:', fname)

        ele=apply_refraction_corr(lsp,ele,p,T)
        fout,frej = g.open_outputfile(station,year,doy,extension) 
#  main loop a given list of frequencies
        total_arcs = 0
        ct = 0
        for f in freqs:
            found_results = False
            if plot_screen: 
                # no idea if this will work
                fig, (ax1, ax2) = plt.subplots(2, 1,figsize=(10,7))
            rj = 0
            gj = 0
            if screenstats: 
                print('**** looking at frequency ', f, ' ReqAmp', reqAmp[ct], ' doy ', doy, 'ymd', year, month, day )
#   get the list of satellites for this frequency
            if onesat == None:
                # added time dependent L2c and L5 satellite lists
                satlist = g.find_satlist_wdate(f,snrE,year,doy)
            else:
                # check that your requested satellite is the right frequency
                satlist = onesat_freq_check(onesat,f )

            for satNu in satlist:
                if screenstats: 
                    print('Satellite', satNu)
                for a in range(naz):
                    az1 = azval[(a*2)] ; az2 = azval[(a*2 + 1)]
                    x,y,Nv,cf,UTCtime,avgAzim,avgEdot,Edot2,delT= g.window_data(s1,s2,s5,s6,
                            s7,s8,sat,ele,azi,t,edot,f,az1,az2,e1,e2,satNu,lsp['polyV'],lsp['pele'],screenstats) 
                    MJD = g.getMJD(year,month,day, UTCtime)
                    if Nv > minNumPts:
                        found_results = True
                        #print('length of x', len(x))
                        maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,lsp['desiredP'],lsp['polyV'],minH) 
                        if (maxF ==0) & (maxAmp == 0):
                            #print('you have tripped a warning')
                            tooclose == True; Noise = 1; iAzim = 0;
                        else:
                            nij =   pz[(px > NReg[0]) & (px < NReg[1])]
                            Noise = 1
                            if (len(nij) > 0):
                                Noise = np.mean(nij)
                            iAzim = int(avgAzim)
                            tooclose = False
                            if abs(maxF - minH) < 0.10: #  peak too close to min value
                                tooclose = True
                        # KL added 2022 march 26
                            if abs(maxF - maxH) < 0.10: #  peak too close to max value
                                tooclose = True
                        if (not tooclose) & (delT < lsp['delTmax']) & (eminObs < (e1 + ediff)) & (emaxObs > (e2 - ediff)) & (maxAmp > reqAmp[ct]) & (maxAmp/Noise > PkNoise):
                            # request from a tide gauge person for Month, Day, Hour, Minute
                            if lsp['mmdd']:
                                ctime = g.nicerTime(UTCtime); ctime2 = ctime[0:2] + ' ' + ctime[3:5]
                                fout.write(" {0:4.0f} {1:3.0f} {2:6.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:5s} \n".format(year,doy,maxF,satNu, UTCtime, avgAzim,maxAmp,eminObs,emaxObs,Nv, f,riseSet, Edot2, maxAmp/Noise, delT, MJD,irefr,month,day,ctime2)) 
                            else:
                                fout.write(" {0:4.0f} {1:3.0f} {2:6.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} \n".format(year,doy,maxF,satNu, UTCtime, avgAzim,maxAmp,eminObs,emaxObs,Nv, f,riseSet, Edot2, maxAmp/Noise, delT, MJD,irefr)) 
                            gj +=1
                            if screenstats:
                                print('Writing out ', np.round(Edot2,3), np.round(avgEdot,3))
                                T = g.nicerTime(UTCtime)
                                print('SUCCESS Azimuth {0:3.0f} Sat {1:3.0f} RH {2:7.3f} m PkNoise {3:4.1f} Amp {4:4.1f} Fr{5:3.0f} UTC {6:5s} DT {7:3.0f} '.format(iAzim,satNu,maxF,maxAmp/Noise,maxAmp, f,T,round(delT)))
                            if plot_screen:
                                failed = False
                                local_update_plot(x,y,px,pz,ax1,ax2,failed)
                        else:
                            rj +=1
                            if screenstats:
                                print('FAILED QC for Azimuth {0:.1f} Satellite {1:2.0f} UTC {2:5.2f}'.format( iAzim,satNu,UTCtime))
                                g.write_QC_fails(delT,lsp['delTmax'],eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,reqAmp[ct],tooclose)
                            if plot_screen:
                                failed = True
                                local_update_plot(x,y,px,pz,ax1,ax2,failed)

            if screenstats:
                print('=================================================================================')
                print('     Frequency ', f, ' good arcs:', gj, ' rejected arcs:', rj )
                print('=================================================================================')
            total_arcs = gj + total_arcs
# close the output files
            ct += 1
            #'Yes' if fruit == 'Apple' else 'No'
            # used to send the plot to the screen and user had to clear it before it would go to the next
            #if found_results and plot_screen:
            if found_results and plot_screen:
                print('data found for this frequency: ',f)
                ax1.set_xlabel('Elevation Angles (deg)')
                ax1.grid(True, linestyle='-'); ax2.grid(True, linestyle='-')
                ax1.set_title(station + ' Raw Data/Periodogram for ' + g.ftitle(f) + ' Frequency')
                ax2.set_xlabel('Reflector Height (m)');
                ax2.set_ylabel('volts/volts') ; ax1.set_ylabel('volts/volts')
                plt.show()
                #plot2screen(station, f, ax1, ax2,lsp['pltname']) 
            else:
                if plot_screen: 
                    print('no data found for this frequency: ',f)
                    #plt.close()

        fout.close() ; # these are the LSP results written to text file 
        # try moving this
        if found_results and plot_screen:
            plot2screen(station, f, ax1, ax2,lsp['pltname']) 


def set_refraction_params(station, dmjd,lsp):
    """
    set values used in refraction correction

    Parameters
    ----------
    station : string
        4 character station name

    dmjd : float
        modified julian date

    lsp : dictionary

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

    Parameters
    ----------
    lsp : dictionary
        info from make_json_input
    ele : numpy array of floats
        elevation angles  (deg)
    p : float
        pressure
    T : float
        temperature (C)

    Returns
    -------
    ele : numpy array of floats
         elevation angle (deg)
    """
    if lsp['refraction']:
        #print('<<<<<< apply refraction correction >>>>>>')
        corrE = refr.corr_el_angles(ele, p,T)
        ele = corrE

    return ele

def local_update_plot(x,y,px,pz,ax1, ax2,failure):
    """
    updates result plot

    Parameters
    ----------
    x : numpy array
        elevation angle (deg)
    y : numpy array
        SNR (volt/volt)
    px : numpy array
        reflector height (m)
    pz : numpy array
        spectral amplitude (volt/volt)
    ax1 : matplotlib figure control
        top plot
    ax2 : matplotlib figure control
        bottom plot
    failure : boolean
        whether periodogram fails QC 

    """
    if failure:
        ax1.plot(x,y,color='gray',linewidth=0.5)
        ax2.plot(px,pz,color='gray',linewidth=0.5)
    else:
        ax1.plot(x,y)
        ax2.plot(px,pz)


def plot2screen(station, f,ax1,ax2,pltname):
    """
    Add axis information and Send the plot to the screen.
    https://www.semicolonworld.com/question/57658/matplotlib-adding-an-axes-using-the-same-arguments-as-a-previous-axes

    Parameters
    ----------
    station : string
        4 character station ID

    """
    ax2.set_xlabel('Reflector Height (m)'); 
    #ax2.set_title('SNR periodogram')
    ax2.set_ylabel('volts/volts')
    ax1.set_ylabel('volts/volts')
    ax1.set_xlabel('Elevation Angles (deg)')
    ax1.grid(True, linestyle='-')
    ax2.grid(True, linestyle='-')
    ax1.set_title(station + ' SNR Data/' + g.ftitle(f) + ' Frequency')
    plt.show()

    return True


def read_json_file(station, extension):
    """
    picks up json instructions for calculation of lomb scargle periodogram

    Parameters
    ----------
    station : str
        4 character station name

    extension : str
        experimental subdirectory - default is ''

    Returns
    -------
    lsp : dictionary

    """
    lsp = {} # 
    # leftover from when i was using None
    if len(extension) == 0:
        useextension = False
        instructions_ext = ''
    else:
        useextension = True 
        instructions_ext = str(os.environ['REFL_CODE']) + '/input/' + station + '.' + extension + '.json'

    instructions = str(os.environ['REFL_CODE']) + '/input/' + station + '.json'

    if useextension and os.path.isfile(instructions_ext):
        usefile = instructions_ext
        #print('using specific instructions for this extension')
        with open(instructions_ext) as f:
            lsp = json.load(f)
    else:
        #print('will use the default instruction file')
        usefile = instructions
        if os.path.isfile(instructions):
            with open(instructions) as f:
                lsp = json.load(f)
        else:
            print('The json instruction file does not exist: ', instructions)
            print('Please make with make_json_input and run this code again.')
            sys.exit()

    if len(lsp['reqAmp']) < len(lsp['freqs']) :
        print('Number of frequencies found in json: ', len(lsp['freqs']))
        print('Number of required amplitudes found in json: ', len(lsp['reqAmp']))
        print('You need to have a required Amplitude for each frequency.')
        print('Please fix your json file: ', usefile)
        sys.exit()

    return lsp


def onesat_freq_check(satlist,f ):
    """
    for a given satellite name - tries to determine
    if you have a compatible frequency

    Parameters
    ----------
    satlist : list 
        integer
    f : integer
        frequency

    Returns
    -------
    satlist : list
        integer 
    """
    isat = int(satlist[0])
    if (isat < 100):
        if (f > 100):
            print('wrong satellite name for this frequency:', f)
            satlist = [] # ???
    elif (isat >= 101) & (isat < 200):
        if (f < 101) | (f > 102):
            print('wrong satellite name for this frequency:', f)
            satlist = [] # ???
    elif (isat > 201) & (isat < 300):
        if (f < 201) | (f > 208):
            print('wrong satellite name for this frequency:', f)
            satlist = [] # ???
    elif (isat > 300) & (isat < 400):
        if (f < 302) | (f > 307):
            print('wrong satellite name for this frequency:', f)
            satlist = [] # ???
    else:
        satlist= []

    return satlist
