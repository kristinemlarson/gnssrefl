import datetime
import json
import matplotlib.pyplot as plt
import math
import numpy as np
import os
import scipy.interpolate
import scipy.signal
import subprocess
import sys
import time
import warnings

from importlib.metadata import version

import gnssrefl.gps as g
import gnssrefl.retrieve_rh as r
from gnssrefl.utils import FileManagement, FileTypes

def gnssir_guts_v2(station,year,doy, snr_type, extension,lsp, debug):
    """

    Computes lomb scargle periodograms for a given station, year, day of year etc.

    Arcs are determined differently than in the first version of the code, which
    was quadrant based. This identifies arcs and applies azimuth constraints after the fact.

    2023-aug-02 trying to fix the issue with azimuth print out being different than
    azimuth at lowest elevation angle

    if screenstats is True, it prints to a log file now, directory $REFL_CODE/logs/ssss


    Parameters
    ----------
    station : str
        4 character station name
    year : int
        full year
    doy : int
        day of year
    snr_type : int
        snr file type
    extension : str
        optional subdirectory to save results

    lsp : dictionary
        e1 : float
            min elev angle, deg
        e2 : float
            max elev angle, deg
        freqs: list of int
            frequencies to use 
        minH : float
            min reflector height, m
        maxH : float
            max reflector height, m 
        NReg : list of floats
            noise region for RH peak2noise , meters
        azval2 : list of floats
            new pairs of azimuth regions, i.e. [0 180 270 360]
        delTmax : float
            max allowed arc length in minutes
        pele: list of floats 
            min and max elev angle in DC removal
        PkNoise : float
            peak to noise value for QC
        ediff : float
            elev angle difference for arc length, QC
        reqAmp : list of floats
            list of required periodogram amplitude for QC for each frequency
        ellist: list of floats
            added 23jun16, allow multiple elevation angle regions
        apriori_rh : float
            a priori reflector height, used in NITE, meters
        savearcs : bool
            if true, elevation angle and detrended SNR data are saved for each arc
            default is False
        savearcs_format : str
            if arcs are to be saved, will they be txt or pickle format
        midnite : bool
            whether midnite arcs are alloweed 
        dbhz : bool
            whether db-hz (True) or volts/volts (False) are used for SNR data
        
    debug : bool
        debugging value to help track down bugs

    """

    #   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    # make sure REFL_CODE/Files/station directory exists ...
    g.checkFiles(station, '')
    midnite = lsp['midnite']

    if 'ellist' in lsp.keys():
        ellist = lsp['ellist']
        if len(ellist) > 0:
            print('Using an augmented elevation angle list', ellist)
    else:
        ellist = []

    if (len(ellist) > 0) and midnite:
        print('Testing midnite option on multiple elevation angle bins')

    # this is also checked in the command line - but for people calling the code ...
    if ((lsp['maxH'] - lsp['minH']) < 5):
        print('Requested reflector heights (', lsp['minH'], ',', lsp['maxH'], ') are too close together. Exiting.')
        print('They must be at least 5 meters apart - and preferably further than that.')
        return

    e1=lsp['e1']; e2=lsp['e2']
    azvalues = rewrite_azel(lsp.get('azval2'))
    if not azvalues:
        print('This module requires azval2 to be set in gnssir_input. This record is not present in your json.')
        sys.exit()

    pele = lsp['pele']

    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp']

    ok = g.is_it_legal(freqs)
    if not ok:
        print('There is something wrong. Fix your json list of frequencies. Exiting')
        sys.exit()

    screenstats = lsp['screenstats']
    gzip = lsp['gzip']
    dec = int(lsp.get('dec', 1))
    if dec != 1:
        print('Using decimation value: ', dec)

    ann = g.make_nav_dirs(year) # make sure directories are there for orbits
    g.result_directories(station,year,extension) # make directories for the LSP results

    fname, resultExist = g.LSPresult_name(station,year,doy,extension)
    if screenstats:
        logid, logfilename = open_gnssir_logfile(station,year,doy,extension)
    else:
        logid = None
        logfilename = None

    if (lsp['nooverwrite'] ) & (resultExist ):
        print('>>>>> The result file already exists for this day and you have selected the do not overwrite option')
        return

    print('LSP Results will be written to:', fname)
    irefr = lsp.get('refr_model', 1) if lsp.get('refraction', False) else 0

    buffer_hours = 2 if midnite else 0
    if midnite:
        print('Midnite option enabled: loading +/- 2 hours from adjacent days')

    from gnssrefl.extract_arcs import extract_arcs_from_station
    try:
        arcs = extract_arcs_from_station(
            station, year, doy, freq=freqs, snr_type=snr_type,
            buffer_hours=buffer_hours, dec=dec,
            e1=e1, e2=e2, ellist=ellist, azlist=azvalues,
            polyV=lsp['polyV'], pele=pele, dbhz=lsp['dbhz'],
            extension=extension,
            gzip=gzip, lsp=lsp,
            sat_list=lsp['onesat'],
        )
    except FileNotFoundError as e:
        print(str(e))
        return

    r.retrieve_rh(station,year,doy,extension,lsp,arcs,screenstats,irefr,logid,logfilename,lsp['dbhz'])

def local_update_plot(x,y,px,pz,ax1, ax2,failure):
    """
    updates optional result plot for SNR data and Lomb Scargle periodograms

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


def read_json_file(station, extension,**kwargs):
    """
    picks up json instructions for calculation of lomb scargle periodogram
    This was originally meant to be used by gnssir, but is now read by other functions.

    Uses new directory structure:
    - No extension: input/{station}/{station}.json with fallback to input/{station}.json
    - With extension: input/{station}/{extension}/{station}.json with fallback to input/{station}.{extension}.json

    Parameters
    ----------
    station : str
        4 character station name

    extension : str
        subdirectory - default is ''

    Returns
    -------
    lsp : dictionary

    """
    lsp = {} 
    # pick up a new parameter - that will be True for people looking
    # for the json but that aren't upset it does not exist.
    noexit = kwargs.get('noexit',False)
    silent = kwargs.get('silent',False)
    
    # Use FileManagement to find JSON file with proper fallback
    json_manager = FileManagement(station, 'make_json', extension=extension)
    json_path, format_type = json_manager.find_json_file()
    
    if json_path.exists():
        if not silent:
            if format_type in ['legacy_extension', 'legacy_station']:
                print(f'Using JSON file (legacy directory): {json_path}')
            else:
                print(f'Using JSON file: {json_path}')
        
        with open(json_path) as f:
            lsp = json.load(f)
    else:
        if noexit:
            print('No json file found - but you have requested the code not exit')
            lsp = {}
            return lsp
        else:
            print('The json instruction file does not exist: ', json_path)
            print('Please make with gnssir_input and run this code again.')
            sys.exit()

    if len(lsp['reqAmp']) < len(lsp['freqs']) :
        print('Number of frequencies found in json: ', len(lsp['freqs']))
        print('Number of required amplitudes found in json: ', len(lsp['reqAmp']))
        print('You need to have a required Amplitude for each frequency.')
        print('Please fix your json file: ', json_path)
        sys.exit()

    return lsp


def new_rise_set(elv,azm,dates, e1, e2, ediff,sat, screenstats):
    """
    This provides a list of rising and setting arcs 
    for a given satellite in a SNR file
    based on using changes in elevation angle

    Parameters
    ----------
    elv : numpy array  of floats
        elevation angles from SNR file
    azm : numpy array  of floats
        azimuth angles from SNR file
    dates : numpy array  of floats
        seconds of the day from SNR file
    e1 : float
        min elevation angle 
    e2 : float
        max elevation angle
    ediff : float
        el angle difference Quality control parameter
    sat : int
        satellite number

    Returns
    -------
    tv : numpy array
        beginning and ending indices of the arc
        satellite number, arc number

    """
    # require arcs to be this length in elev angle
    min_deg = (e2-ediff)   - (e1 + ediff)

#   time limit in seconds - taken from david
    gaptlim = 5*60 # seems awfully small
    #newf = np.array(f[i, :], dtype=float)
    iarc = 0
    ddate = np.ediff1d(dates)
    delv = np.ediff1d(elv)
    bkpt = len(ddate)
    bkpt = np.append(bkpt, np.where(ddate > gaptlim)[0])
    bkpt = np.append(bkpt,  np.where(np.diff(np.sign(delv)))[0])
    bkpt = np.unique(bkpt)
    bkpt = np.sort(bkpt)
    N=len(bkpt)
    tv = np.empty(shape=[0,4])

    for ii in range(N):
        if ii == 0:
            sind = 0
        else:
            sind = bkpt[ii - 1] + 1
        eind = bkpt[ii] + 1
        nelv = np.array(elv[sind:eind], dtype=float)
        nazm = np.array(azm[sind:eind], dtype=float)
        nt = np.array(dates[sind:eind], dtype=float)
        #nazm = azm[sind:eind]
        minObse = min(nelv)
        maxObse = max(nelv)
        minA = min(nazm)
        maxA = max(nazm)

        nogood = False
        verysmall = False
        ediff_violation = False
        if (minObse - e1) > ediff:
            #print('v1')
            nogood = True
            ediff_violation = True 
        if (maxObse - e2) < -ediff:
            #print('v2')
            nogood = True
            ediff_violation = True
        if (eind-sind) == 1:
            #print('v3')
            nogood = True
            verysmall = True
        if ((maxObse - minObse) < min_deg):
            nogood = True
            #print('v4')

        if screenstats:
            if nogood:
                # do not write out warning for these tiny arcs which should not even be there.
                # i am likely reading the code incorrectly
                add = ''
                if ediff_violation:
                    add = ' violates ediff or very small'
                if not verysmall:
                    print('Failed sat/arc',sat,iarc+1, sind,eind,' min/max observed elev: ', 
                          np.round(minObse,3), np.round(maxObse,3), minA,maxA,add)
            else:
                print('Keep   sat/arc',sat,iarc+1, sind,eind,' min/max observed elev: ', 
                      np.round(minObse,3), np.round(maxObse,3),minA,maxA,add)

        if not nogood :
            iarc = iarc + 1
            newl = [sind, eind, int(sat), iarc]
            tv = np.append(tv, [newl],axis=0)

    return tv


def window_new(snrD, f, satNu,ncols,pfitV,e1,e2,azlist,screenstats,fileid,dbhz,**kwargs):
    """
    retrieves SNR arcs for a given satellite. returns elevation angle and 
    detrended linear SNR

    2023-aug02 updated to improve azimuth calculation reported

    2024-aug-15 testing out imposing pele values for DC removal.
    2024-sep04 removed pele as input

    Parameters
    ----------
    snrD : numpy array (multiD)
        contents of the snr file, i.e. 0 column is satellite numbers, 1 column elevation angle ...
    f : int
        frequency you want
    satNu : int
        requested satellite number
    ncols : int
        how many columns does the SNR file have
    pfitV : float
        polynomial order
    e1 : float
        requested min elev angle (deg)
    e2 : float
        requested max elev angle (deg)
    azlist : list of floats (deg)
        non-continguous azimuth regions, corrected for negative regions
    screenstats : bool
        whether you want debugging information
        printed to the screen
    fileid : 
        log location
    dbhz : bool
        whether you want dbhz or linear SNR units

    Returns
    -------
    x : numpy array of floats
        elevation angle, degrees
    y : numpy array of floats
        linear SNR with DC removed
    Nvv :  int
        number of points in x/y array
    cf : float
        scale factor for requested frequency (used in LSP)
    meanTime : float
        UTC hour of the day (GPS time)
    avgAzim : float
        average azimuth of the arc (deg) 
        ### this will not be entirely consistent with other metric
    outFact1: float
        kept for backwards compatibility.  set to zero
    outFact2 : float
        edot factor used in RH dot correction
    delT : float
        arc length in minutes
    secxonds : numpy array of floats
        hopefully seconds of the day

    """
    fundy = kwargs.get('fundy',False)

    #print('Using polyfit ', pfitV)
    x=[]; y=[]; azi=[]; seconds = []; edot = [] ; sat = []
    Nvv= 0; meanTime = 0; avgAzim = 0 ; outFact2 = 0 ; delT = 0
    initA = 0;
    cf = g.arc_scaleF(f,satNu)
    outFact1 = 0 # backwards compatability
    good = True

    if f in [1,101,201,301]:
        column = 7
    elif f in [2,20,102,302]:
        column = 8
        # added beidou
    #elif f in [5, 205]:
    elif f in [5, 205,305]:
        column = 9
#   these are galileo frequencies (via RINEX definition)
    elif f in [206,306]:
        column = 6
    elif f in [207,307]:
        column = 10
        # added beidou
    #elif (f == 208):
    elif f in [208,308]:
        column = 11
    else:
        column = 0
        if screenstats:
            print('You asked for a frequency I do not recognize: ', f)
        good = False
    #python column
    icol = column - 1
    #print('using frequency ', f, ' columns ', ncols)


    if (column <= ncols) : 
        # at least there is a column where there should be
        # sep 26, 2023
        # these definitions used to be outside the if, but putting them inside now
        datatest = snrD[:,icol]
        ijk = (datatest == 0)
        nzero = len(datatest[ijk])
        if np.sum(datatest) < 1:
            if screenstats:
                fileid.write('No useful data on frequency {0:3.0f} /sat {1:3.0f} : all zeros\n'.format(f,satNu))
            good = False
        else:
            if nzero > 0:
                #print('removing ', nzero, ' zero points on frequency ', f )
                # indices you are keeping ... 
                nn = (datatest > 0) ; 
                snrD = snrD[nn,:]

        # I was trying something out here. #if False:
        #    Elen = len(snrD)
        #    if True:
        #        print(f, Elen, len(snrD),max(snrD[:,1]), min(snrD[:,1]))

        #    ijk = (snrD[:,1] > pele[0]) & (snrD[:,1] <= pele[1])
        #    snrD = snrD[ijk,:]
            #if (Elen != len(snrD)):
        #    if True:
        #        print(f, Elen, len(snrD),max(snrD[:,1]), min(snrD[:,1]),pele )

        sat = snrD[:,0]
        ele = snrD[:,1]
        azm = snrD[:,2]
        seconds = snrD[:,3]
        edot = snrD[:,4] # but does not have to exist?
        data = snrD[:,icol]


        # not really good - but at least the zeros have been removed
        if good:
            # change to linear units if dbhz is False
            if not dbhz : 
                data = np.power(10,(data/20))
            reqN = 20
            if fundy:
                reqN = 50
            # for high rate stations should not be using 20 ... 
            # this is a bit of a bandaid

            if len(ele) > reqN:
                #print(len(ele), len(data))
                model = np.polyfit(ele,data,pfitV)
                fit = np.polyval(model,ele)
                data = data - fit
                # apply elevation angle constraint
                i =  (ele > e1) & (ele <= e2)
                # arbitrary
                Nvv = len(ele[i])

                if Nvv > 15:
                    # get the index of the min elevation angle
                    ie = np.argmin(ele[i])
                    # find the azimuth of that first elevation angle 
                    initA = azm[i][ie]
                    #print('initial azimuth ostensibly for min eangle',initA)
                    keeparc = check_azim_compliance(initA,azlist)
                    if keeparc :
                        x = ele[i] ; y = data[i]
                        edot = edot[i]
                        sat = sat[i] ; azm = azm[i]
                        seconds = seconds[i]
                        if False:
                            print(f, initA, Elen, len(snrD),Nvv)
                    else:
                        if screenstats:
                            fileid.write('This azimuth is not in a requested azimuth region {0:7.2f} (deg)\n'.format(initA))
                        good = False
    else:
        if screenstats:
            print('Asked for data that are not there.')
        good = False
    
    # now calculate edot factor
    if good:
        if len(x) > 0:
            #Taylor Smith - Chasing down error:
            #...site-packages/gnssrefl/gnssir_v2.py", line 741, in window_new
                #model = np.polyfit(seconds,x*np.pi/180,1)
                #TypeError: can't multiply sequence by non-int of type 'float'
            #NOTE: FAILS ON EMPTY X -- Breaks any loops
    
            #sec_float = [float(x) for x in seconds]
            #model = np.polyfit(sec_float,x*np.pi/180,1)
        
            #dd = np.diff(seconds)
            # edot, in radians/sec
            model = np.polyfit(seconds,x*np.pi/180,1)
        
            avgEdot_fit = model[0]
            avgAzim = np.mean(azm)
            meanTime = np.mean(seconds)/3600
    #  delta Time in minutes
            delT = (np.max(seconds) - np.min(seconds))/60
    # average tan(elev)
            cunit = np.mean(np.tan(np.pi*x/180))
    #       return tan(e)/edot, in units of one over (radians/hour) now. used for RHdot correction
    #       so when multiplyed by RHdot - which would be meters/hours ===>>> you will get a meter correction
    
            outFact2 = cunit/(avgEdot_fit*3600)

    # This originally returned the average azimuth.
    # I think you can return the initA instead of avgAzim here
    #    return x,y, Nvv, cf, meanTime,avgAzim,outFact1, outFact2, delT
    #print('new ', initA, ' old ', avgAzim)
    # try reutrning seconds
    return x,y, Nvv, cf, meanTime,initA, outFact1, outFact2, delT, seconds


def find_mgnss_satlist(f,year,doy):
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

    """
    # get list of relevant satellites
    l2c_sat, l5_sat = g.l2c_l5_list(year,doy)

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
# only have 24 frequencies defined for glonass
    if (f == 101) or (f==102):
        satlist = np.arange(101,125,1)
#   galileo - 40 max?
    gfs = int(f-200)

    if (f >  200) and (f < 210):
        satlist = np.arange(201,241,1)
#   galileo has no L2 frequency, so set that always to zero
    if f == 202:
        satlist = []
#   pretend there are 32 Beidou satellites for now
    if (f > 300):
        satlist = np.arange(301,333,1)

    return satlist



def rewrite_azel(azval2):
    """
    Trying to allow regions that cross zero degrees azimuth

    Parameters
    ----------
    azval2 : list of floats
        input azimuth regions

    Returns
    -------
    azelout : list of floats
        azimuth regions without negative numbers ... 

    """

    # if nothing changes
    azelout = azval2
    #print('Requested azimuths: ', azval2)

    # check for negative beginning azimuths
    N2 = len(azval2) ; a1 = int(azval2[0]); a2 = int(azval2[1])

    if (N2 % 2) != 0:
        print('Azimuth regions must be in pairs. Please check the azval2 variable in your json input file')
        sys.exit()
    if (N2 == 2) & (a1 < 0):
        azelout = [a1+360, 360, 0,  a2]
    if (N2 == 4) & (a1 < 0):
        azelout = [a1+360, 360, 0,  a2, int(azval2[2]), int(azval2[3])]
    if (N2 == 6) & (a1 < 0):
        azelout = [a1+360, 360, 0,  a2, int(azval2[2]), int(azval2[3]), int(azval2[4]), int(azval2[5])]
    if (N2 == 8) & (a1 < 0):
        azelout = [a1+360, 360, 0,  a2, azval2[2], azval2[3], azval2[4], azval2[5], azval2[6], azval2[7]]
    if N2 > 8:
        print('Not going to allow more than four azimuth regions ...')
        sys.exit()

    #print('Using azimuths: ', azelout)
    return azelout

def check_azim_compliance(az_min_ele,azlist):
    """
    Check to see if your arc is in one of the requested regions

    Parameters
    ----------
    az_min_ele : float
        azimuth of selected arc (deg)
    azlist : list of floats
        list of acceptable azimuth regions

    Returns
    -------
    keeparc : bool
        whether the arc is in a selected azimuth range
    """
    keeparc = False
    N = int(len(azlist)/2)
    for a in range(0,N):
        azim1 = azlist[2*a]; azim2 = azlist[2*a+1]
        if (az_min_ele>= azim1) & (az_min_ele <= azim2):
            keeparc = True
            #print('found one in requested region', azim1, azim2)

    return keeparc

def make_parallel_proc_lists_mjd(year, doy, year_end, doy_end, nproc):
    """
    make lists of dates for parallel processing to spawn multiple jobs

    Parameters
    ----------
    year : int
        year processing begins
    doy : int
        start day of year
    year_end : int
        year end of processing 
    doy_end  : int
        end day of year
    nproc : int
        requested number of processes to spawn

    Returns
    =======
    datelist : dict
        list of MJD 
    numproc : int
        number of datelists, thus number of processes to be used

    """
#   d = { 0: [2020, 251, 260], 1:[2020, 261, 270], 2: [2020, 271, 280], 3:[2020, 281, 290], 4:[2020,291,300] }
    # number of days for spacing ... 
    MJD1 = int(g.ydoy2mjd(year,doy))
    MJD2 = int(g.ydoy2mjd(year_end,doy_end))
    if MJD1 == MJD2:
        return [MJD1, MJD2], None

    Ndays  = math.ceil((MJD2-MJD1)/nproc) 
    #print(Ndays)
    d = {}
    i=0
    for day in range(MJD1, MJD2+1, Ndays):
        end_day = day + Ndays - 1
        if (end_day > MJD2):
            l = [day, MJD2 ]
        else:
            l = [day, end_day]
        d[i] = l
        i=i+1

    datelist = d
    numproc = i
    return datelist, numproc

def make_parallel_proc_lists(year, doy1, doy2, nproc):
    """
    make lists of dates for parallel processing to spawn multiple jobs

    Parameters
    ----------
    year : int
        year of processing
    doy1 : int
        start day of year
    doy 2 : int
        end day of year

    Returns
    -------
    datelist : dict
        list of dates formatted as year doy1 doy2
    numproc : int
        number of datelists, thus number of processes to be used

    """
#   d = { 0: [2020, 251, 260], 1:[2020, 261, 270], 2: [2020, 271, 280], 3:[2020, 281, 290], 4:[2020,291,300] }
    # number of days for spacing ... 
    Ndays  = math.ceil((doy2-doy1)/nproc) 
    #print(Ndays)
    d = {}
    i=0
    for day in range(doy1, doy2+1, Ndays):
        end_day = day+Ndays-1
        if (end_day > doy2):
            l = [year, day, doy2] 
        else:
            l = [year, day, end_day] 
        d[i] = l
        i=i+1

    datelist = d
    numproc = i
    return datelist, numproc


def open_gnssir_logfile(station,year,doy,extension):
    """
    opens a logfile when asking for screen output

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
        if not set you should send empty string

    Returns
    -------
    fileid : ?
        I don't know the proper name of this - but what comes out
        when you open a file so you can keep writing to it

    """
    xdir = os.environ['REFL_CODE']
    if len(extension) == 0:
        logdir = xdir + '/logs/' + station + '/' + str(year) + '/'
    else:
        logdir = xdir + '/logs/' + station + '/' + extension + '/' + str(year) + '/'

    if not os.path.isdir(logdir):
        subprocess.call(['mkdir', '-p',logdir])
    fout = 0
    cdoy = '{:03d}'.format(doy)
#   extra file with rejected arcs

    filename = logdir + cdoy + '_gnssir.txt' 
    fileid = open(filename,'w+')
    v = str(g.version('gnssrefl'))
    fileid.write('gnssrefl version {0:s} \n'.format(v))

    return fileid, filename

def retrieve_Hdates(a):
    """
    Retrieves character strings of dates and attempts to QC
    them.  

    Parameters
    ----------
    a : list of str
        online input to gnssir_input for Hdates 

    Returns
    -------
    Hdate : list of str
        full dates (2024-10-11 15:12) of Hortho values

    """
    NV = len(a)

    Hdates = []
    if  NV % 2 != 0:
        print(a)
        print('Your Hdates have an uneven number of entries. There ')
        print('needs to be one date and one HH:MM for each Hortho entry')
        sys.exit()

    for i in range(0,int(NV/2)):
        index = i*2 + 1
        #print(i, index, a[index])
        if len(a[index]) != 5:
            print(a[index], ' is an invalid time. It must be exactly five characters long including the :')
            sys.exit()
        else:
            H= a[index-1] + ' ' + a[index]
            Hdates.append(H)
            #o=datetime.datetime.fromisoformat(H)
            #ts = datetime.datetime.utctimetuple(o)
            #year = ts.tm_year ; mm  = ts.tm_mon ; dd =  ts.tm_mday
            #hh = ts.tm_hour ; minutes = ts.tm_min ; sec = 0
            #print(year, mm, dd, hh, minutes)

    return Hdates

def convert_Hdates_mjd(Hdates,remove_hhmm):
    """
    takes a list of dates in format yyyy-mm-dd hh:mm and turns them into a list of mjd

    Parameters
    ----------
    Hdates : list of str
         date strings in the format yyyy-mm-dd hh:mm

    remove_hhmm : bool
         whether you want to ignore hh:mm

    Returns
    -------
    mjd_Hortho : list of floats
        modified julian dates of character string dates

    """
    mjd_Hortho = []
    print(Hdates)
    for i in range(0,len(Hdates)):
        # convert to mjd
        if remove_hhmm : 
            m  = g.datestring_mjd(Hdates[i][0:10])
        else:
            m  = g.datestring_mjd(Hdates[i])
        mjd_Hortho.append(m)

    return mjd_Hortho 


