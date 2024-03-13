import sys
import os
import numpy as np
import math
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import subprocess
import warnings

import scipy.interpolate
import scipy.signal

import gnssrefl.gps as g
import gnssrefl.refraction as refr
import gnssrefl.rinex2snr as rinex
import gnssrefl.gnssir_v2 as gnssir_v2


def quickLook_function(station, year, doy, snr_type,f,e1,e2,minH,maxH,reqAmp,pele,satsel,PkNoise,fortran,
        pltscreen,azim1,azim2,ediff, delTmax,hires_figs,**kwargs):
    """
    This is the main function to compute spectral characteristics of a SNR file.
    It takes in all user inputs and calculates reflector heights. It makes two png files to summarize
    the data.


    This is a new version that tries to picks all rising and setting arcs, not just those constrained to 90 degree
    quadrants.

    Parameters
    ----------
    station : str
        station name (4 char) 
    year : int
        full year
    doy : int
        day of year  
    snr_type : int
        snr file extension (i.e. 99, 66 etc)
    f : int
        frequency (1, 2, 5), etc
    e1 : float
        minimum elevation angle in degrees
    e2 : float
        maximum elevation angle in degrees
    minH : float
        minimum allowed reflector height in meters
    maxH : float
        maximum allowed reflector height in meters
    reqAmp : float
        is LSP amplitude significance criterion
    pele : list of floats
        is the elevation angle limits for the polynomial removal.  units: degrees
    satsel : int
        satellite number
    PkNoise : float
        peak to noise ratio for QC
    fortran : bool
         whether external fortran translator is being explicitly called. 
    pltscreen : bool
        whether you want plots sent to the terminal
    azim1 : float
         minimum azimuth in degrees
    azim2 : float
         maximum azimuth in degrees
    ediff : float
         QC parameter - restricts length of arcs (degrees)
    delTmax : float
         maximum arc length in minutes
    hires_figs: bool
         whether to use eps instead of png

    """
    if f not in [1, 2, 20, 5, 101, 102, 201, 205, 206, 207, 208, 302,306]:
        print('As far as I know, this is an illegal frequency for this software. Exiting. ', f)
        sys.exit()
    # it really should only mean whether you want to run plt.show()
    if ((maxH - minH) < 5.5):
        print('Requested reflector heights (', minH, ',', maxH, ') are too close together. ')
        print('They must be at least 5.5 meters apart - and preferably further than that. Exiting')
        return

    testing = kwargs.get('test',False)
    if testing: 
        print('working on new strategy')

    screenstats = kwargs.get('screenstats',False)
    if screenstats:
        print('Some screen statistics will print to the screen')

    if (minH > maxH):
        print('Minimum RH',minH, ' cannot be greater than maximum RH.', maxH, ' Exiting.')
        return [],[]

    # dictionary for output
    data = {'NW':{},'SW':{},'NE':{},'SE':{},'fNW':{},'fSW':{},'fNE':{},'fSE': {} }

    # dictionary for key
    datakey = {'NW':{},'SW':{},'NE':{},'SE':{},'fNW':{},'fSW':{},'fNE':{},'fSE': {} }

    # make sure environment variables exist
    g.check_environ_variables()

    # make sure logs directory exists
    if not os.path.isdir('logs'):
        subprocess.call(['mkdir', 'logs'])

    # if it finds the station coordinates, it will return irefr as 1
    quick_p,quick_T,irefr, quick_e = quick_refraction(station)

    webapp = False 
    # orbit directories
    ann = g.make_nav_dirs(year)
    # titles in 4 quadrants - for webApp
    titles = ['Northwest', 'Southwest','Northeast', 'Southeast']
    stitles = ['NW', 'SW','NE', 'SE']
    # define where the axes are located
    bx = [0,1,0,1]; by = [0,0,1,1]; bz = [1,3,2,4]

    #  fontsizes
    fs = 10
    FS = 12
    # various defaults - ones the user doesn't change in this quick Look code
    polyV = 4 # polynomial order for the direct signal
    desiredP = 0.01 # 1 cm precision for a "quick Look"

    #four_in_one = True # put the plots together
    minNumPts = 20 
    #noise region for LSP QC. these are meters
    NReg = [minH, maxH]
    # for quickLook, we use the four geographic quadrants - these are azimuth angles in degrees
    azval = [270, 360, 180, 270, 0, 90, 90, 180]
    # try adding 5 degrees at the quadrant edges, except for north
    naz = int(len(azval)/2) # number of azimuth pairs
    pltname = 'temp.png' # default plot
    requireAmp = reqAmp[0]

    obsfile, obsfileCmp, snre =  g.define_and_xz_snr(station,year,doy,snr_type)
    allGood, snrD, nrows, ncols = gnssir_v2.read_snr(obsfile)

    if allGood == 0:
        print('file does not exist'); sys.exit()
    else:
        # make output file for the quickLook RRH values, just so you can give them a quick look see
        # also used in the azimuth QC plot
        quicklog = 'logs/rh_' + station + '.txt'
        rhout = open(quicklog,'w+')
        amax = 0
        minEdataset = min(snrD[:,1])
        print('minimum elevation angle (degrees) for this dataset: ', minEdataset)
        if minEdataset > (e1+0.5):
            print('It looks like the receiver had an elevation mask. Overriding e1 to this value.')
            e1 = minEdataset

        # apply elevation angle correction for simple refraction here
        if irefr == 1:
            print('found simple refraction parameters')
            lsp={}; lsp['refraction'] = True
            snrD[:,1] = gnssir_v2.apply_refraction_corr(lsp,snrD[:,1],quick_p,quick_T)
        # restrict to DC limits 
        ele = snrD[:,1]


        i= (ele >= pele[0]) & (ele < pele[1])
        ele = ele[i]
        snrD = snrD[i,:]
        sats = snrD[:,0]

        # very rare that no GPS data exist, so will not check it.  I will probably regret this
        #if (f < 6):
        #    b = sats[(sats<100)]; print('gps',len(b))
        if (f > 100) and (f < 200): # glonass
            b = sats[(sats>100) & (sats<200)]; # print('glonass',len(b))
            if len(b) == 0:
                print('NO Glonass DATA in the file') ; 
                return data, datakey
        elif (f > 200) & (f < 300): # galileo
            b = sats[(sats>200) & (sats<300)]; # print('galileo',len(b))
            if len(b) == 0:
                print('NO Galileo data in the file'); 
                return data, datakey
        elif (f > 300): # beidou
            b = sats[(sats>300) & (sats<400)]; # print('beidou',len(b))
            if len(b) == 0:
                print('NO Beidou data in the file'); 
                return data, datakey

        fig = plt.figure(figsize=(10,6))
        ax1=plt.subplot(2,2,bz[0]); ax2=plt.subplot(2,2,bz[1]) ; ax3=plt.subplot(2,2,bz[2]) ; ax4=plt.subplot(2,2,bz[3])
        # save the handles in a dictionary
        saxis = {} ; saxis['0'] = ax1 ; saxis['1'] = ax2; saxis['2'] = ax3 ; saxis['3'] = ax4

        allpoints = 0

        # keep track of the maximum amplitude for each track in each quadrant so you can have them be hte same
        axisSize =np.empty(shape=[0, 2])

        if (satsel == None):
            satlist = gnssir_v2.find_mgnss_satlist(f,year,doy)
        else:
            satlist = [satsel]

        azvalues = [0,360] # for the start

        for satNu in satlist:
            iii = (sats == satNu)
            thissat = snrD[iii,:]
            goahead = False

            if len(thissat) > 0:
                # if there are data for this satellite, find all the arcs
                arclist = gnssir_v2.new_rise_set(thissat[:,1],thissat[:,2],thissat[:,3],e1, e2,ediff,satNu,screenstats)
                nr,nc = arclist.shape
                if nr > 0:
                    goahead = True
                else:
                    goahead = False

                if goahead:
                    for arc in range(0,nr):
                        sind = int(arclist[arc,0]) ; eind = int(arclist[arc,1])
                        d2 = np.array(thissat[sind:eind, :], dtype=float)
                    # window the data - which also removes DC
                        x,y, Nvv, cf, meanTime,avgAzim,outFact1, Edot2, delT= gnssir_v2.window_new(d2, f,
                                satNu,ncols,pele, polyV,e1,e2,azvalues,screenstats)
                        Nv = Nvv # number of points
                        UTCtime = meanTime
                    # for this arc, which a value is it?
                        a = whichquad(avgAzim)
                        #print('Looking at arc ', arc, ' quad ', a, avgAzim)
                        tooclose = False
                        if (delT != 0) & (Nv > 20):
                            T = g.nicerTime(UTCtime)
                            maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,desiredP,polyV,minH)
                            if (maxF ==0) & (maxAmp == 0):
                                tooclose == True; Noise = 1; iAzim = 0;
                            else:
                                nij =  pz[(px > NReg[0]) & (px < NReg[1])]

                            Noise = 1
                            if (len(nij) > 0):
                                Noise = np.mean(nij)

                            iAzim = int(avgAzim)

                            if abs(maxF - minH) < 0.10: #  peak too close to min value
                                tooclose = True

                            if abs(maxF - maxH) < 0.10: #  peak too close to max value
                                tooclose = True

                            if (not tooclose) & (delT < delTmax) & (maxAmp > requireAmp) & (maxAmp/Noise > PkNoise) & (iAzim >= azim1) & (iAzim <= azim2):
                                rhout.write('{0:3.0f} {1:6.3f} {2:3.0f} {3:4.1f} {4:3.1f} {5:6.2f} {6:2.0f} \n '.format(iAzim,maxF,satNu,
                                    maxAmp,maxAmp/Noise,UTCtime,1))
                                lw=1.5 ; colorful(a,px,pz,lw,True,saxis)
                                idc = stitles[a]
                                data[idc][satNu] = [px,pz]
                                datakey[idc][satNu] = [avgAzim, maxF, satNu,f,maxAmp,maxAmp/Noise, UTCtime]
                                if screenstats:
                                    print('SUCCESS for Azimu {0:5.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:7.3f} PkNoise {4:6.2f}'.format( avgAzim,satNu,UTCtime,maxF,maxAmp/Noise))
                                # try to track the maximum amplitude in each quadrant this way
                                newl=[a,maxAmp]; axisSize =np.append(axisSize,[newl], axis=0)

                            else:
                                if (iAzim > azim1) & (iAzim < azim2):
                                    lw = 0.5 ; colorful(a,px,pz,lw,False,saxis) # add to the plot
                                    if screenstats:
                                        print('FAILED QC for Azimuth {0:5.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:7.3f} '.format( avgAzim,satNu,UTCtime,maxF))
                                        g.write_QC_fails(delT,delTmax,eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,requireAmp,tooclose)

                                    idc = 'f' + stitles[a]
                                    data[idc][satNu] = [px,pz]
                                    datakey[idc][satNu] = [avgAzim, maxF, satNu,f,maxAmp,maxAmp/Noise, UTCtime]
                                    rhout.write('{0:3.0f} {1:6.3f} {2:3.0f} {3:4.1f} {4:3.1f} {5:6.2f} {6:2.0f} \n '.format(iAzim,maxF,
                                        satNu,maxAmp,maxAmp/Noise,UTCtime,-1))

        rhout.close()

        # put on all the labels ... hopefully
        set_labels(saxis,axisSize,fs)

        # make sure directory exists for plots
        g.set_subdir(station)
        # where plots will go
        fdir = os.environ['REFL_CODE'] + '/Files/' + station 
        tt = 'GNSS-IR: ' + station.upper() + ' Freq:' + g.ftitle(f) + ' Year/DOY:' + str(year) + ',' + str(doy) + ' elev: ' + str(e1) + '-' +  str(e2)
        fig.suptitle(tt, fontsize=FS)
        # if you have no results, no point plotting them!
        if hires_figs:
            filename = fdir + '/quickLook_lsp.eps'
        else:
            filename = fdir + '/quickLook_lsp.png'
        print('Plot saved to ', filename)

        plt.savefig(filename)
        # now make second plot
        goodbad(quicklog,station,year,doy,minH,maxH,PkNoise,reqAmp,f,e1,e2,hires_figs)

        if pltscreen:
            plt.show()

    return data,datakey

def goodbad(fname,station,year,doy,h1,h2,PkNoise,reqAmp,freq,e1,e2,hires_figs):
    """
    makes a plot that shows "good" and "bad" refletor height retrievals as a 
    function of azimuth

    Parameters
    ----------
    fname : str
        filename
    station : str
        4 char station name
    year : int
        full year
    doy : int
        day of year
    h1 : float
        minimum reflector height (m)
    h2 : float
        max reflector height (m)
    PkNoise : float
        peak 2 noise QC
    reqAmp : float
        required LSP amplitude
    freq : int
        frequency
    e1 : float
        minimum elevation angle (deg)
    e2 : float
        maximum elevation angle (deg)
    hires_figs : bool
        whether to use eps instead of png

    Returns
    -------
    plot is written $REFL_CODE/Files/station/quickLook_summary.png

    """
    try:
        # added this to get rid of the warning when the file has no bad points in it
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            a = np.loadtxt(fname,comments='%')
    except:
        print('No results in the file')

    #print(a.ndim, len(a))
    if (a.ndim == 1) or (len(a) == 0):
        print('No results in the file')
        return

    ij = (a[:,6] == 1) # good retrievals
    ik = (a[:,6] == -1) # bad retrievals
    fs = 12
    plt.figure(figsize=(10,6))
    plt.subplot(3,1,1)
    plt.plot(a[ij,0], a[ij,1], 'o',color='blue',label='good')
    plt.plot(a[ik,0], a[ik,1], 'o',color='gray', label='bad')
    ydoy = ' ' + str(year) + '/' + str(doy) + ' '
    #print(freq, g.ftitle(freq))
    plt.title('quickLook Retrieval Metrics: ' + station + ' Freq:' + g.ftitle(freq) + ydoy + ' elev:' + str(e1) + '-' + str(e2) ,fontsize=fs)
    plt.legend(loc="upper right")
    plt.ylabel('Refl. Ht. (m)',fontsize=fs)
    plt.grid()
    plt.xlim((0, 360))
    plt.ylim((h1, h2))
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)

    ax = plt.gca()
    ax.axes.xaxis.set_ticklabels([])


    plt.subplot(3,1,2)
    plt.plot([0, 360], [PkNoise, PkNoise], 'k--',label='QC value used')
    plt.plot(a[ij,0], a[ij,4], 'o',color='blue')
    plt.plot(a[ik,0], a[ik,4], 'o',color='gray')
    plt.legend(loc="upper right")
    plt.ylabel('peak2noise',fontsize=fs)
    plt.grid()
    plt.xlim((0, 360))
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    ax = plt.gca()
    ax.axes.xaxis.set_ticklabels([])

    plt.subplot(3,1,3)
    plt.plot([0, 360], [reqAmp, reqAmp], 'k--',label='QC value used')
    plt.plot(a[ij,0], a[ij,3], 'o',color='blue')
    plt.plot(a[ik,0], a[ik,3], 'o',color='gray') 
    plt.legend(loc="upper right")
    plt.ylabel('Spectral Peak Ampl.',fontsize=fs)
    plt.xlabel('Azimuth (degrees)',fontsize=fs)
    plt.grid()
    plt.xticks(fontsize=fs)
    plt.yticks(fontsize=fs)
    plt.xlim((0, 360))

    # existence of the output directory is checked earlier
    fdir = os.environ['REFL_CODE'] + '/Files/' + station 
    if hires_figs:
        f = fdir + '/quickLook_summary.eps'
    else:
        f = fdir + '/quickLook_summary.png'

    print('Plot saved to ', f)
    plt.savefig(f)

def colorful(a,px,pz,lw,fullcolor,ax):
    """
    plots the quadrant periodograms

    Parameters
    ----------
    a : int
    px : numpy array of floats
        x axis of amplitude power spectrum
    pz : numpy array of floats
        y axis of amplitude power spectrum
    lw : float
        line width
    fullcolor :
        whether you want full color (if not, it is gray)
    ax : axis handle
    """
    # which quadrant
    axisV = ax[str(a)]

    if fullcolor:
        axisV.plot(px,pz,linewidth=lw)
    else:
        axisV.plot(px,pz,'gray',linewidth=lw)


def set_labels(ax,axisSize,fs):
    """
    try to set the appropriate labels depending on the quadrant

    Parameters
    ----------
    ax : dictionary
        plot handles
    axisSize : numpy array of floats
        lists the amplitudes of the various periodograms in a given quadrant
        pairs of quad (0-3), amplitude
    fs : int
        font size
    """
    setA = False # want to set the axes based on good retrieval amplitudes
    # start maxv with at least something
    maxv=2
    for a in range(0,4):
        axisV = ax[str(a)]

        axisV.grid()
        if (a == 3) or (a==1):
            axisV.set_xlabel('reflector height (m)',fontsize=fs)
        if (a == 1) or (a==0):
            axisV.set_ylabel('volts/volts',fontsize=fs)

        ii = (axisSize[:,0] == a)
        thisquad = axisSize[ii,1]
        if len(thisquad) > 0:
            # found at least one good periodogram 
            setA = True
            thismax = max(thisquad)
            if (thismax > maxv):
                maxv = thismax
    # now apply it
    maxv = maxv*1.1
    if setA:
        for a in range(0,4):
            axisV = ax[str(a)]
            axisV.set_ylim(0,maxv)  

def whichquad(iaz):
    """
    Parameters
    ----------
    iaz : float
        azimuth of the arc, degrees
    a : int
        quad number in funny system
        
    """
    if (iaz >= 270):
        a = 0
    elif (iaz >= 180) & (iaz < 270):
        a = 1
    elif (iaz >= 0) & (iaz < 90):
        a = 2
    elif (iaz >= 90) &(iaz < 180):
        a =3

    return a

def quick_refraction(station):
    """
    refraction correction used in quickLook. no time dependence.

    Parameters
    ----------
    station : string
        4 character station name

    Returns
    -------
    p : float
        pressure, hPa
    T : float
        temperature, Celsius
    irefr : int
        refraction model number I believe, which is also sent, so not needed
    e : float
        water vapor pressure, hPa

    """

    xdir = os.environ['REFL_CODE']
    refraction_model = 1
    lat,lon,ht=g.queryUNR_modern(station.lower())
    # default values
    p = 0; T = 0; irefr = 1; e=0 ; it = 1 #?
    dmjd = 0
    if (lat == 0) & (lon == 0):
        #print('no coordinates found')
        irefr = 0
        return p,T,irefr, e

    refr.readWrite_gpt2_1w(xdir, station, lat, lon)
    dlat = lat*math.pi/180; dlong = lon*math.pi/180;
    p,T,dT,Tm,e,ah,aw,la,undu = refr.gpt2_1w(station, dmjd,dlat,dlong,ht,it)

    return p,T,irefr, e

