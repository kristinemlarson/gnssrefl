"""
called by quickLook_cl.py
quickLook functions 
"""
import sys
import os
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.figure import Figure
import subprocess
import warnings

import scipy.interpolate
import scipy.signal

import gnssrefl.gps as g
import gnssrefl.rinex2snr as rinex


def quickLook_function(station, year, doy, snr_type,f,e1,e2,minH,maxH,reqAmp,pele,satsel,PkNoise,fortran,pltscreen,azim1,azim2,ediff,**kwargs):
    """
    This is the main function to compute spectral characteristics of a SNR file.
    It takes in all user inputs and calculates reflector heights. It makes two png files to summarize
    the data.

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

    """

    if ((maxH - minH) < 5.5):
        print('Requested reflector heights (', minH, ',', maxH, ') are too close together. ')
        print('They must be at least 5.5 meters apart - and preferably further than that. Exiting')
        return

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

    webapp = False 
    # orbit directories
    ann = g.make_nav_dirs(year)
    # titles in 4 quadrants - for webApp
    titles = ['Northwest', 'Southwest','Northeast', 'Southeast']
    stitles = ['NW', 'SW','NE', 'SE']
    # define where the axes are located
    bx = [0,1,0,1]; by = [0,0,1,1]; bz = [1,3,2,4]

    #  fontsize
    fs = 10
    # various defaults - ones the user doesn't change in this quick Look code
    # changed this december 4, 2022
    # changed it back on december 20, 2022
    delTmax = 75 # this is how long an arc can be in minutes
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
    FS = 12

# to avoid having to do all the indenting over again
# this allows snr file to live in main directory
# not sure that that is all that useful as I never let that happen
    obsfile = g.define_quick_filename(station,year,doy,snr_type)
    if os.path.isfile(obsfile):
        print('>>>> The snr file exists ',obsfile)
    else:
        if True:
            obsfile, obsfileCmp, snre =  g.define_and_xz_snr(station,year,doy,snr_type)
            if snre:
                dkfjaklj = True
            else:
                print('>>>> The SNR the file needs does not exist ',obsfile)
                print('Please use rinex2snr to make a SNR file')
                sys.exit()
    allGood,sat,ele,azi,t,edot,s1,s2,s5,s6,s7,s8,snrE = read_snr_simple(obsfile)
    # this just means the file existed ... not that it had the frequency you want to use
    if allGood == 1:
        # make output file for the quickLook RRH values, just so you can give them a quick look see
        quicklog = 'logs/rh_' + station + '.txt'
        rhout = open(quicklog,'w+')
        amax = 0
        minEdataset = np.min(ele)

        sats = sat 
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

        print('minimum elevation angle (degrees) for this dataset: ', minEdataset)
        if minEdataset > (e1+0.5):
            print('It looks like the receiver had an elevation mask. Overriding e1 to this value.')
            e1 = minEdataset
        if pltscreen:
            plt.figure(figsize=(10,6))
        allpoints = 0

        # try to normalize the periodogram yaxes
        axisSize =np.empty(shape=[0, 2])

        for a in range(naz):
            if pltscreen:
                if a==0:
                    ax1=plt.subplot(2,2,bz[a])
                if a==1:
                    ax2=plt.subplot(2,2,bz[a])
                if a==2:
                    ax3=plt.subplot(2,2,bz[a])
                if a==3:
                    ax4=plt.subplot(2,2,bz[a])

                plt.title(titles[a],fontsize=fs)
            az1 = azval[(a*2)] ; az2 = azval[(a*2 + 1)]

            # this means no satellite list was given, so get them all
            if satsel == None:
                #satlist = g.find_satlist(f,snrE)
                #march 29, 2021 made l2c and l5 time dependent
                satlist = g.find_satlist_wdate(f,snrE,year,doy)
                #print(f,year,doy)
                #print(satlist)
            else:
                satlist = [satsel]

            for satNu in satlist:
                x,y,Nv,cf,UTCtime,avgAzim,avgEdot,Edot2,delT= g.window_data(s1,s2,s5,s6,s7,s8,sat,ele,azi,t,edot,f,az1,az2,e1,e2,satNu,polyV,pele,screenstats) 
                allpoints = allpoints + Nv
                # if screenstats:
                    #print('ALL tracks: Azim {0:5.1f} Satellite {1:2.0f} UTC {2:5.2f} Npts {3:3.0f} between Azimuths {4:3.0f}-{5:3.0f}'.format( avgAzim,satNu,UTCtime,Nv, az1, az2))
                if Nv > minNumPts:
                    maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,desiredP,polyV,minH) 
                    iAzim = int(avgAzim)
                    Noise = 1
                    if maxF == 0:
                        print('invalid LSP')
                        tooclose = True
                    else:
                        nij =   pz[(px > NReg[0]) & (px < NReg[1])]
                    # 2022 march 26
                    # introduce boolean for RH peaks that are too close to the edges of the RH periodogram
                        tooclose = False
                        if (abs(maxF - minH) < 0.05):
                            tooclose = True
                        if (abs(maxF - maxH) < 0.05):
                            tooclose = True 
                        if (len(nij) > 0):
                            Noise = np.mean(nij)
                        else:
                            Noise = 1;  iAzim = 0 # i think this is set to zero so something down the line doesn't fail
                    # add azimuth constraints. default is 0-360
                    if (not tooclose) & (delT < delTmax) & (eminObs < (e1 + ediff)) & (emaxObs > (e2 - ediff)) & (maxAmp > requireAmp) & (maxAmp/Noise > PkNoise) & (iAzim >= azim1) & (iAzim <= azim2):
                        T = g.nicerTime(UTCtime)
                        # az, RH, sat, amp, peak2noise, Time
                        rhout.write('{0:3.0f} {1:6.3f} {2:3.0f} {3:4.1f} {4:3.1f} {5:6.2f} {6:2.0f} \n '.format(iAzim,maxF,satNu,maxAmp,maxAmp/Noise,UTCtime,1))
                        if pltscreen:
                            plt.plot(px,pz,linewidth=1.5)
                        idc = stitles[a]
                        data[idc][satNu] = [px,pz]
                        datakey[idc][satNu] = [avgAzim, maxF, satNu,f,maxAmp,maxAmp/Noise, UTCtime]
                        if screenstats:
                            print('SUCCESS for Azimu {0:5.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:7.3f} PkNoise {4:6.2f}'.format( avgAzim,satNu,UTCtime,maxF,maxAmp/Noise))
                        # try to track the maximum amplitude in each quadrant this way
                        newl=[a,maxAmp]
                        axisSize =np.append(axisSize,[newl], axis=0)

                    else:
                        # these are failed tracks
                        if (iAzim > azim1) & (iAzim < azim2):
                            if pltscreen:
                                plt.plot(px,pz,'gray',linewidth=0.5)
                            if screenstats:
                                print('FAILED QC for Azimuth {0:5.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:7.3f} '.format( avgAzim,satNu,UTCtime,maxF))
                                g.write_QC_fails(delT,delTmax,eminObs,emaxObs,e1,e2,ediff,maxAmp, Noise,PkNoise,requireAmp,tooclose)

                            idc = 'f' + stitles[a]
                            data[idc][satNu] = [px,pz]
                            datakey[idc][satNu] = [avgAzim, maxF, satNu,f,maxAmp,maxAmp/Noise, UTCtime]
                            rhout.write('{0:3.0f} {1:6.3f} {2:3.0f} {3:4.1f} {4:3.1f} {5:6.2f} {6:2.0f} \n '.format(iAzim,maxF,satNu,maxAmp,maxAmp/Noise,UTCtime,-1))

            # i do not know how to add a grid using these version of matplotlib
            tt = 'GNSS-IR: ' + station.upper() + ' Freq:' + g.ftitle(f) + ' Year/DOY:' + str(year) + ',' + str(doy) + ' elev: ' + str(e1) + '-' +  str(e2)
            if pltscreen:
                aaa, bbb = plt.ylim()
                # see if this works
                plt.grid()
                amax = max(amax,  bbb) # do not know how to implement this ...
                if (a == 3) or (a==1):
                    plt.xlabel('reflector height (m)',fontsize=fs)
                if (a == 1) or (a==0):
                    plt.ylabel('volts/volts',fontsize=fs)
                # try putting this label on all of them
                #plt.xlabel('reflector height (m)',fontsize=fs)
                plt.xticks(fontsize=fs)
                plt.yticks(fontsize=fs)

        rhout.close()
        setA = False # want to set the axes based on good retrieval amplitudes
        # this boolean set when it finds such a quadrant
        if pltscreen:
            maxv=2
            for q in range(0,4):
                ii = (axisSize[:,0] == q)
                thisquad = axisSize[ii,1]
                if len(thisquad) > 0:
                    # found at least one good periodogram in this quadrant
                    setA = True
                    maxv = max(max(thisquad), maxv)
            maxv = maxv*1.1
            if setA:
                ax1.set_ylim(0,maxv) ; ax2.set_ylim(0,maxv) ;
                ax3.set_ylim(0,maxv) ; ax4.set_ylim(0,maxv)

            else:
            # old way was often dominated by bad retrievals
            # but if no good retrievals ... 
                d1=ax1.get_ylim() ; d2=ax2.get_ylim() ; d3=ax3.get_ylim() ; d4=ax4.get_ylim()
                minv = min([d1[0], d2[0], d3[0], d4[0]])
                maxv = max([d1[1], d2[1], d3[1], d4[1]])
                ax1.set_ylim(minv,maxv) ; ax2.set_ylim(minv,maxv) ;
                ax3.set_ylim(minv,maxv) ; ax4.set_ylim(minv,maxv)

        #print('preliminary reflector height results are stored in a file called logs/rh.txt')
        # this file seems to have an empty line at the end.  i do not know why.

        # make sure directory exists for plots
        g.set_subdir(station)
        # where plots will go
        fdir = os.environ['REFL_CODE'] + '/Files/' + station 
        plt.suptitle(tt, fontsize=FS)
            # if you have no results, no point plotting them!
        if (allpoints > 0):
            filename = fdir + '/quickLook_lsp.png'
            print('plot saved to ', filename)
            plt.savefig(filename)
        # make second plot
            goodbad(quicklog,station,year,doy,minH,maxH,PkNoise,reqAmp,f,e1,e2)
        else:
            print('You made a selection that does not exist (i.e. frequency or satellite or constellation)')

        if pltscreen:
            plt.show()
    else: 
        print('some kind of problem with SNR file, so I am exiting the code politely.')

    # returns multidimensional dictionary of lomb scargle results so 
    # that the jupyter notebook people can replot them
    # 21mar26 added a key

    return data,datakey

def goodbad(fname,station,year,doy,h1,h2,PkNoise,reqAmp,freq,e1,e2):
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
    f = fdir + '/quickLook_summary.png'
    print('plot saved to ', f)
    plt.savefig(f)

def read_snr_simple(obsfile):
    """
    Loads the data from a SNR file into memory 

    Parameters
    ----------
    obsfile : string
        name of the SNR file

    Returns
    -------
    allGood :  int
        one for all is well, zero is for all is bad
    sat : numpy array of floats
        satellite numbers
    ele  : numpy array of floats
        elevation angle (deg)
    azi : numpy array of float 
        azimuth (deg)
    t  : numpy array of floats
        seconds of the day (no leap seconds)
    edot : numpy array of floats
        derivative of elevation angle wrt time deg/sec
    s1 : numpy array of floats
        L1 SNR
    s2 : numpy array of floats 
        L2 SNR
    s5 :  numpy array of floats 
        L5 SNR
    s6 :  numpy array of floats
        L6 SNR
    s7 :  numpy array of floats
        L7 SNR 
    s8 :  numpy array of floats
        L8 SNR
    snrE : numpy array of booleans 
        whether SNR exists 

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
        # put in a positive elev mask
        #print(np.min(f[:,1]))
        i= f[:,1] > 0
        f=f[i,:]

        #print('read_snr_simple, Number of rows:', r, ' Number of columns:',c)
        sat = f[:,0]; ele = f[:,1]; azi = f[:,2]; t =  f[:,3]
        edot =  f[:,4]; s1 = f[:,6]; s2 = f[:,7]; s6 = f[:,5]
        #print(np.min(ele))
        # 
        s1 = np.power(10,(s1/20))  
        s2 = np.power(10,(s2/20))  
        s6 = s6/20; s6 = np.power(10,s6)  
#   make sure s5 has default value?
        s5 = []
        if c > 8:
            s5 = f[:,8]
            if (sum(s5) > 0):
                s5 = s5/20; s5 = np.power(10,s5)  
            #print(len(s5))
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
    #print('min e', min(ele))
    return allGood, sat, ele, azi, t, edot, s1, s2, s5, s6, s7, s8, snrE
