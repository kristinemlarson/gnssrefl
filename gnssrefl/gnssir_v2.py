import datetime
import json
import matplotlib.pyplot as plt
import math
import numpy as np
import os
import pickle
import scipy.interpolate
import scipy.signal
import subprocess
import sys
import time
import warnings

from importlib.metadata import version

import gnssrefl.gps as g
import gnssrefl.read_snr_files as snr
import gnssrefl.refraction as refr
import gnssrefl.retrieve_rh as r

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
        
    debug : bool
        debugging value to help track down bugs

    """

    #   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    # make sure REFL_CODE/Files/station directory exists ... 
    g.checkFiles(station, '')
    midnite = lsp['midnite']

    if 'azlist' in lsp.keys():
        azlist = lsp['azlist']
        if len(azlist) > 0:
            print('Using an augmented azimuth angle list', azlist)
    else:
        azlist = [];
        #print('no augmented elevation angle list')

    if 'ellist' in lsp.keys():
        ellist = lsp['ellist']
        if len(ellist) > 0:
            print('Using an augmented elevation angle list', ellist)
    else:
        ellist = [];
        #print('no augmented elevation angle list')

    # this must have been experimental and it does not seem to be used ...
    variable_azel = False
    if (len(ellist) >0) & (len(azlist) & 0) :
        if len(ellist) == len(azlist) :
            print('You are using a beta version of the code that sets')
            print('variable elevation angle limits for different azimuth regions.')
            print('Be careful! Especially for tall sites.')
            variable_azel = True
        
    if (len(ellist) > 0) and midnite:
        print('You have invoked multiple elevation angle bins and the midnite crossing option.')
        print('This has not been implemented yet.  Please submit a PR if you speak python or ')
        print('an Issue if your project needs this.')
        midnite = False

    # this is also checked in the command line - but for people calling the code ...
    if ((lsp['maxH'] - lsp['minH']) < 5):
        print('Requested reflector heights (', lsp['minH'], ',', lsp['maxH'], ') are too close together. Exiting.')
        print('They must be at least 5 meters apart - and preferably further than that.')
        return

    e1=lsp['e1']; e2=lsp['e2']; minH = lsp['minH']; maxH = lsp['maxH']
    ediff = lsp['ediff']; NReg = lsp['NReg']  
    PkNoise = lsp['PkNoise']; prec = lsp['desiredP']; delTmax = lsp['delTmax']
    if 'azval2' in lsp.keys():
        azval2 = lsp['azval2']; 
        naz = int(len(azval2)/2)
    else:
        print('This module requires azval2 to be set in gnssir_input. This record is not present in your json.')
        sys.exit()

    pele = lsp['pele'] ; pfitV = lsp['polyV']

    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp'] 

    # allows negative azimuth value for first pair
    azvalues = rewrite_azel(azval2)

    ok = g.is_it_legal(freqs)
    if not ok:
        print('There is something wrong. Fix your json list of frequencies. Exiting')
        sys.exit()

    plot_screen = lsp['plt_screen'] 
    onesat = lsp['onesat']; screenstats = lsp['screenstats']
    # testing this out - turned out not to be useful/needed
    #new_direct_signal = False

    gzip = lsp['gzip']
    if 'dec' in lsp.keys():
        dec = int(lsp['dec'])
    else:
        dec = 1 # so Jupyter notebooks do not need to be rewritten

    # no need to print to screen if default
    if (dec != 1):
        print('Using decimation value: ', dec)

    if 'savearcs' in lsp:
        test_savearcs = lsp['savearcs']
    else:
        test_savearcs = False

    # default will be plain txt
    if 'savearcs_format' in lsp:
        savearcs_format = lsp['savearcs_format']
    else:
        savearcs_format = 'txt'

    # this is for savearcs, txt
    docstring = 'arrays are eangles (degrees), dsnrData is SNR with/DC removed, and sec (seconds of the day),\n'

    xdir = os.environ['REFL_CODE']
    cdoy = '{:03d}'.format(doy)
    sdir = xdir + '/' + str(year) + '/arcs/' + station + '/' + cdoy + '/'
    if test_savearcs:
        print('Writing individual arcs (elevation angle, SNR) to ', sdir)
        if not os.path.isdir(sdir):
            print('Make output directories for arcs files')
            subprocess.call(['mkdir', '-p', sdir])
        if not os.path.isdir(sdir + 'failQC/'):
            subprocess.call(['mkdir', '-p', sdir + 'failQC'])
    d = g.doy2ymd(year,doy); month = d.month; day = d.day
    dmjd, fracS = g.mjd(year,month,day,0,0,0)
    ann = g.make_nav_dirs(year) # make sure directories are there for orbits
    g.result_directories(station,year,extension) # make directories for the LSP results

   # this defines the minimum number of points in an arc.  This depends entirely on the sampling
    all_lsp = []
   # rate for the receiver, so you should not assume this value is relevant to your case.
    minNumPts = 20
    p,T,irefr,humidity,Tm, lapse_rate = set_refraction_params(station, dmjd, lsp)
    TempK = T + 273.15 # T is in celsius ... I think.
    vapor = humidity
    pressure = p
    temperature = TempK
    # peng used these variables. eventually consolidate
    lat1=lsp['lat']; lon1=lsp['lon']; height1=lsp['ht'] ; mjd1 = dmjd
    lat1R = math.radians(lat1); lon1R = math.radians(lon1); 

    # only used by NITE
    if 'apriori_rh' in lsp.keys():
        RH_apriori = lsp['apriori_rh']  # a priori reflector height used in NITE
    else:
        RH_apriori = 5 # completely made up


    if (irefr >= 3) & (irefr <= 6):
        # N_ant is the index of refraction
        # apparently this is wrong ?
        #N_ant=refr.refrc_Rueger(p,humidity,TempK)[0]    #
        N_ant = refr.refrc_Rueger(pressure-vapor, vapor, TempK)[0]   #get antenne refractivity
        #ztd=2.3                                             #zenith total delay from PPP
        # hydrostatic delay, Saastamoinen
        zhd = refr.saastam2(pressure, lat1, height1)             
        # wet delay 
        zwd = refr.asknewet(humidity, Tm, lapse_rate)
        print('Dry and wet zenith delays, meters ', round(zhd,3),round(zwd,3))
        # if you had estimated total delay, you could get wet delay by 
        ztd = zhd + zwd 

# only doing one day at a time for now - but have started defining the needed inputs for using it
    twoDays = False
    obsfile2= '' # dummy value for name of file for the day before, when we get to that
    fname, resultExist = g.LSPresult_name(station,year,doy,extension) 
    if screenstats:
        logid, logfilename = open_gnssir_logfile(station,year,doy,extension)
    else:
        logid = None 
        logfilename = None

    if (lsp['nooverwrite'] ) & (resultExist ):
        allGood = 0
        print('>>>>> The result file already exists for this day and you have selected the do not overwrite option')
        obsfile = ''; obsfile2 = ''
    else:
        print('LSP Results will be written to:', fname)
        print('Refraction parameters (pressure, temp, humidity, ModelNum)',np.round(p,3),np.round(T,3),np.round(humidity,3),irefr)
        # uncompress here so you should not have to do it in read_snr_multiday ...
        obsfile, obsfileCmp, snre = g.define_and_xz_snr(station,year,doy,snr_type) 


        allGood, snrD, nrows, ncols = read_snr(obsfile)
        if allGood:
            snrD = decimate_snr(snrD, allGood, dec)

        # if primary file exists and you want to invoke midnite
        if midnite and allGood: 
            # keep first two hours on normal day
            ii = snrD[:,3] < 2*3600
            outD = snrD[ii,:]
            print(outD.shape)
            print('invoking midnite option. Need to pick up and look at day before')
            if doy == 1:
                test_obsfile, test_obsfileCmp, test_snre = g.define_and_xz_snr(station,year-1,g.dec31(year-1),snr_type) 
            else:
                test_obsfile, test_obsfileCmp, test_snre = g.define_and_xz_snr(station,year,doy-1,snr_type) 
            print('Second observation file ', test_obsfile, test_snre)
            # if it exists
            if test_snre: 
                # load it and decimate
                test_allGood, test_snrD, nnrows, nncols = read_snr(test_obsfile)
                test_snrD = decimate_snr(test_snrD, test_allGood, dec)
                # only last hour or so
                ii = test_snrD[:,3] > 22*3600
                test_snrD = test_snrD[ii,:]
            # offset wrt to main code so that time is not repeated (file format unfortunately 
            # is seconds within a day
                test_snrD[:,3] = test_snrD[:,3] -86400
            # now merge the last two hours of this file with the primarily file (hours 0-22)
                c1,c2 = test_snrD.shape
                d1,d2 = outD.shape
                if (c2 != d2):
                    print('The two SNR files do not have the same number of columns. This likely means one was ')
                    print('GPS only and the other was GNSS. You need to remake one of the two files so they are ')
                    print('consistent.  Changing your request for midnite crossing to False.')
                    midnite = False
                else:
                    outD =  np.vstack((test_snrD,outD))
            else:
                print('The SNR file for the day before does not exist. midnite crossing option is turned off')
                midnite = False

        # only compress if result was not found ...
        snr.compress_snr_files(lsp['wantCompression'], obsfile, obsfile2,midnite,gzip) 

    if allGood:
        print('SNR data were read from: ', obsfile)
        minObsE = min(snrD[:,1])
        print(f'Min observed elev. angle {minObsE} for {station} {year}:{doy}/ Requested e1-e2: of {e1}-{e2}')
        #if midnite:
        #    test_minObsE = min(outD[:,1])
            #print(f'Min observed elev. angle {test_minObsE} for SNR file the day before Requested e1-e2: of {e1}-{e2}')

        # only apply this test for simple e1 and e2
        if len(ellist) == 0:
            if minObsE > (e1 + ediff):
                print('You literally have no data above the minimum elevation angle setting')
                print('which is e1 + ediff: ', e1 + ediff, ' If you do not like')
                print('this QC constraint, then set ediff to be very large (10 degrees) in the json or use ')
                print('the minimum elevation angle your receiver used. Exiting.')
                sys.exit()

        if (irefr == 3) or (irefr == 4):
            # elev refraction, lsp, pressure, temperature- units?, time, sat
            if irefr == 3:
                print('Ulich refraction correction')
            else:
                print('Ulich refraction correction, time-varying')
            # I do not understand why all these extra parameters are sent to this 
            # function as they are not used. Maybe I was doing some testing.
            ele=refr.Ulich_Bending_Angle(snrD[:,1],N_ant,lsp,p,T,snrD[:,3],snrD[:,0])
            if midnite:
                ele_midnite = refr.Ulich_Bending_Angle(outD[:,1],N_ant,lsp,p,T,outD[:,3],outD[:,0])
                ele = ele + dE_MPF 
        elif (irefr == 5 ) or (irefr == 6):
            ele,snrD = refraction_nite_mpf(irefr,snrD,mjd1,lat1R,lon1R,height1,RH_apriori,N_ant,zhd,zwd)
            if midnite: 
                ele_midnite,outD = refraction_nite_mpf(irefr,outD,mjd1,lat1R,lon1R,height1,RH_apriori,N_ant,zhd,zwd)
          
            # NITE MODEL
            # remove ele < 1.5 cause it blows up
            #i=snrD[:,1] > 1.5
            #snrD = snrD[i,:]
            #N = len(snrD[:,1])
            ## elevation angles, degrees
            #ele=snrD[:,1]
            # zenith angle in radians
            #zenithA = 0.5*np.pi - np.radians(ele)
            #get mapping function and derivatives
            #[gmf_h,dgmf_h,gmf_w,dgmf_w]=refr.gmf_deriv(mjd1, lat1R, lon1R,height1,zenithA)
            #[mpf, dmpf]=[refr.mpf_tot(gmf_h,gmf_w,zhd,zwd),refr.mpf_tot(dgmf_h,dgmf_w,zhd,zwd)]

            # inputs apriori RH, elevation angle, refractive index, zenith delay, mpf ?, dmpf?
            #if irefr == 5:
            #    print('NITE refraction correction, Peng et al. remove data < 1.5 degrees')
            #    dE_NITE=refr.Equivalent_Angle_Corr_NITE(RH_apriori, ele, N_ant, ztd, mpf, dmpf)
            #    ele = ele + dE_NITE 
            #else: 
            #    print('MPF refraction correction, Wiliams and Nievinski')
            #    dE_MPF= refr.Equivalent_Angle_Corr_mpf(ele,mpf,N_ant,RH_apriori)

        elif irefr == 0:
            print('No refraction correction applied ')
            ele = snrD[:,1]
            if midnite: 
                ele_midnite = outD[:,1]
        else :
            if irefr == 1:
                if screenstats:
                    print('Standard Bennett refraction correction')
            else:
                if screenstats:
                    print('Standard Bennett refraction correction, time-varying')
            ele = snrD[:,1]
            ele=apply_refraction_corr(lsp,ele,p,T)
            if midnite:
                ele_midnite = outD[:,1]
                ele_midnite=apply_refraction_corr(lsp,ele_midnite,p,T)

        # apply an elevation mask for all the data for the polynomial fit
        i= (ele >= pele[0]) & (ele < pele[1])
        ele = ele[i]
        snrD = snrD[i,:]
        sats = snrD[:,0]
        snrD[:,1] = ele # ????

        if midnite:
            i= (ele_midnite >= pele[0]) & (ele_midnite < pele[1])
            ele_midnite = ele_midnite[i]
            outD = outD[i,:]
            sats_midnite = outD[:,0]
            outD[:,1] = ele_midnite
        else:
            outD = None

        # testing out a new function that does ... everything

        r.retrieve_rh(station,year,doy,extension, midnite,lsp,snrD, outD, screenstats, irefr,logid,logfilename)

        return

def set_refraction_params(station, dmjd,lsp):
    """
    set values used in refraction correction

    2024-aug-20, fixed the case where refraction is set to zero

    Parameters
    ----------
    station : str
        4 character station name

    dmjd : float
        modified julian date

    lsp : dictionary with information about the station
        lat : float
            latitude, deg
        lon : float
            longitude, deg
        ht : float
            height, ellipsoidal

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
    Tm : float
        temperature in Kelvin
    la : float
        lapse rate

    """
    # default values in case you have set refraction to zero.
    # which you should not do ... but 
    p = 0; T = 0; Tm = 0; la = 0



    if 'refr_model' not in lsp.keys():
        # default is always to use refraction model 1
        # if for some reason it is missing ...
        refraction_model = 1
    else:
        refraction_model = lsp['refr_model']


    xdir = os.environ['REFL_CODE']
    # default values
    p = 0; T = 0; irefr = 0; e=0
    if lsp['refraction']:
        irefr = refraction_model
        refr.readWrite_gpt2_1w(xdir, station, lsp['lat'], lsp['lon'])
        # time varying was originally set to no for now (it = 1)
        # now allows time varying for models 2, 4 and now MPF and NITE
        if refraction_model in [2, 4, 5, 6]:
            it = 0
            print('Using time-varying refraction parameter inputs')
        #elif (refraction_model == 5):
        else:
            it = 1
        dlat = lsp['lat']*np.pi/180; dlong = lsp['lon']*np.pi/180; ht = lsp['ht']
        p,T,dT,Tm,e,ah,aw,la,undu = refr.gpt2_1w(station, dmjd,dlat,dlong,ht,it)
        # e is water vapor pressure, so humidity ??
        #print("Pressure {0:8.2f} Temperature {1:6.1f} \n".format(p,T))
    else:
        irefr = 0 # ???

    print('refraction model', refraction_model)
    return p,T,irefr, e, Tm, la

def apply_refraction_corr(lsp,ele,p,T):
    """

    Parameters
    ----------
    lsp : dictionary
        info from make_json_input such as station lat and lon
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
    lsp = {} # 
    # pick up a new parameter - that will be True for people looking
    # for the json but that aren't upset it does not exist.
    noexit = kwargs.get('noexit',False)
    # leftover from when i was using None
    if len(extension) == 0:
        useextension = False
        instructions_ext = ''
    else:
        useextension = True 
        instructions_ext = str(os.environ['REFL_CODE']) + '/input/' + station + '.' + extension + '.json'

    instructions = str(os.environ['REFL_CODE']) + '/input/' + station + '.json'

    if useextension and not os.path.isfile(instructions_ext):
        print('You asked to use : ', instructions_ext, ' but it does not exist.')
        print('Will try the non-extension json file: ', instructions)

    if useextension and os.path.isfile(instructions_ext):
        usefile = instructions_ext
        print('Using these instructions ', usefile)
        with open(instructions_ext) as f:
            lsp = json.load(f)
    else:
        usefile = instructions
        if os.path.isfile(instructions):
            print('Using these instructions ', usefile)
            with open(instructions) as f:
                lsp = json.load(f)
        else:
            if noexit:
                print('No json file found - but you have requested the code not exit')
                lsp = {}
                return lsp
            else:
                print('The json instruction file does not exist: ', instructions)
                print('Please make with gnssir_input and run this code again.')
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
                    add = ' violates ediff'
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

def read_snr(obsfile):
    """
    Simple function to load the contents of a SNR file into a numpy array

    Parameters
    ----------
    obsfile : str
        name of the snrfile 

    Returns
    -------
    allGood : int 
        1, file was successfully loaded, 0 if not.
        apparently this variable was defined when I did not know about booleans....
    f : numpy array
        contents of the SNR file
    r : int
        number of rows in SNR file
    c : int
        number of columns in SNR file

    """
    allGood = 1
    if os.path.isfile(obsfile):
        f = np.genfromtxt(obsfile,comments='%')
    else:
        print('No SNR file found')
        allGood = 0
        return allGood, 0, 0, 0
    r,c = f.shape
    if (r > 0) & (c > 0):
        i= f[:,1] > 0
        f=f[i,:]
    if r == 0:
        print('No rows in this file!')
        allGood = 0
    if c == 0:
        print('No columns in this file!')
        allGood = 0 

    return allGood, f, r, c


def window_new(snrD, f, satNu,ncols,pfitV,e1,e2,azlist,screenstats,fileid):
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
            # change to linear units
            data = np.power(10,(data/20))
            if len(ele) > 20:
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

def check_azim_compliance(initA,azlist):
    """
    Check to see if your arc is in one of the requested regions

    Parameters
    ----------
    initA : float
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
        if (initA>= azim1) & (initA <= azim2):
            keeparc = True
            #print('found one in requested region', azim1, azim2)

    return keeparc

def new_rise_set_again(elv,azm,dates, e1, e2, ediff,sat, screenstats,logid,**kwargs ):
    """
    This provides a list of rising and setting arcs 
    for a given satellite in a SNR file
    based on using changes in elevation angle
    (though it seems primarily driven by time change TBF)

    Parameters
    ----------
    elv : numpy array  of floats
        elevation angles from SNR file
    azm : numpy array  of floats
        azimuth angles from SNR file
    dates : numpy array  of floats
        seconds of the day from SNR file
    e1 : float
        min elevation angle (deg)
    e2 : float
        max elevation angle (deg)
    ediff : float
        el angle difference required, deg, QC
    sat : int
        satellite number
    screenstats : bool
        whether you want info printed to the screen
    logid: fileid
        where the screen stat info is stored as a file

    Returns
    -------
    tv : numpy array
        beginning and ending indices of the arc
        satellite number, arc number, elev min, elev max

    flag_midnite : bool

    """
    flag_midnite = False
    # whether you want to look for a midnite crossing ...
    midnite = kwargs.get('midnite',False)

    # require arcs to be this length in elev angle
    min_deg = (e2-ediff)   - (e1 + ediff)

#   time limit in seconds - taken from david purnell
    gaptlim = 5*60 # seems awfully small
    #newf = np.array(f[i, :], dtype=float)
    iarc = 0
    ddate = np.ediff1d(dates)
    delv = np.ediff1d(elv)
    bkpt = len(ddate)
    bkpt = np.append(bkpt, np.where(ddate > gaptlim)[0])
    bkpt = np.append(bkpt,  np.where(np.diff(np.sign(delv)))[0])
    aa = np.where(ddate > gaptlim)[0]
    bb = np.where(np.diff(np.sign(delv)))[0]

    bkpt = np.unique(bkpt)
    bkpt = np.sort(bkpt)
    N=len(bkpt)
    tv = np.empty(shape=[0,6])

    flag_midnite = False # this is for the whole file - so should not be reset in hte loop
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
        #print('min/max obs e ', minObse, maxObse)
        # how to get the azimuth?
        minA = min(nazm)
        maxA = max(nazm)


        nogood = False
        verysmall = False
        ediff_violation = False
        if (minObse - e1) > ediff:
            nogood = True
            ediff_violation = True 
            #print('v1')
        if (maxObse - e2) < -ediff:
            nogood = True
            ediff_violation = True
            #print('v2')
        if (eind-sind) == 1 :
            nogood = True
            verysmall = True
            #print('v3')
        if ((maxObse - minObse) < min_deg):
            nogood = True
            #print('v4')
        if (dates[sind] == 0) and midnite:
            logid.write('Remove this arc to allow midnite crossing track for satellite {0:3.0f} \n'.format(sat))
            nogood = True
            flag_midnite = True

        if screenstats:
            if nogood:
                # do not write out warning for these tiny arcs which should not even be there.
                # i am likely reading the code incorrectly
                add = ''
                if ediff_violation:
                    add = ' violates ediff'
                if flag_midnite:
                    add = ' flag midnite'
                if not verysmall:
                    logid.write('Failed sat/arc {0:3.0f} {1:3.0f}/indices {2:7.0f}-{3:7.0f} min/max obs elev: {4:7.3f} {5:7.3f} Azims: {6:6.2f} {7:6.2f} {8:15s}  \n'.format( sat,iarc+1, sind,eind, minObse, maxObse, minA,maxA,add))
            else:
                logid.write('Keep sat/arc {0:3.0f} {1:3.0f}/indices {2:7.0f}-{3:7.0f} min/max obs elev: {4:7.3f} {5:7.3f} Azims: {6:6.2f} {7:6.2f}  \n'.format( sat,iarc+1, sind,eind,minObse, maxObse, minA,maxA))

        if not nogood :
            iarc = iarc + 1
            newl = [sind, eind, int(sat), iarc,e1,e2]
            tv = np.append(tv, [newl],axis=0)

            if midnite:
                if len(dates) == eind:
                    eind = eind - 1
                logid.write('{0:4.0f} {1:4.0f} {2:5.0f} {3:5.0f} {4:5.2f} {5:5.2f} {6:5.1f} {7:5.1f}\n'.format(sind, eind, dates[sind], dates[eind],elv[sind], elv[eind],azm[sind],azm[eind])) 

    return tv , flag_midnite

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

def arc_name(sdir,satNu,f,arcnum,avgAzim):
    """
    creates filename for SNR arc output

    Parameters
    ----------
    sdir: str
        output directory
    satNu : int
        satellite number
    f : int
        frequency
    arcnum : int
        arc number
    avgAzim: float
        average azimuth, degrees

    Returns
    -------
    newffile : str
        filename of outputs
    """
    # 
    cazim = '_az' + '{:03d}'.format(round(avgAzim))
    #cazim = '_az' + '{:03d}'.format(int(np.rint(avgAzim)))
    csat = '{:03d}'.format(satNu)
    cf = ''
    # must have a function that does this ... but in the meantime
    if (f < 100):
        constell = 'G'
        fout = f
    elif (f > 100) & (f < 200):
        constell = 'R'
        fout = f - 100
    elif (f > 200) & (f < 300):
        fout = f - 200
        constell = 'E'
    else: 
        fout = f - 300
        constell = 'C'

    # take care of L2C special frequency
    if (f == 20):
        cf = '_L2_'          
    # otherwise
    else:
        cf = '_L' + str(fout)  + '_'

    cf = cf + constell  + cazim

    if len(cf) > 0:
        newffile = sdir + 'sat' + csat + cf + '.txt'
    else:
        newffile = ''

    return newffile

def write_out_arcs(newffile,eangles,dsnrData,sec,file_info,savearcs_format):
    """
    Writes out files of rising and setting arcs analyzed in gnssir.  Saved 
    data are elevation angles, and SNR data with direct signal remoevd.
    The file location is the first input. 

    Parameters
    ----------
    newffile : str
        name of the output file
    eangles : numpy array of floats
        elevation angles in degrees
    dsnrData : numpy array of floats
        SNR data, with DC removed
    sec : numpy array of floats
        seconds of the day (UTC, though really GPS time)
    file_info: list
        satNu, f, avgAzim, year,doy,meanTime, docstring
    savearcs_format : str
        whether file is txt or pickle

    """
    headerline = ' elev-angle (deg), dSNR (volts/volts), sec of day'
    [station,satNu,f,avgAzim,year,month,day,doy,meanTime,docstring] = file_info
    # gotta be a better way ... but in the mean time
    MJD = g.getMJD(year,month,day, meanTime)

    fm = '%12.7f  %12.7f  %10.0f'
    xyz = np.vstack((eangles,dsnrData,sec)).T
    if savearcs_format == 'txt':
        np.savetxt(newffile, xyz, fmt=fm, delimiter=' ', newline='\n',comments='%',header=headerline)
    else:
        pname = newffile[:-4] + '.pickle'
        fff = open(pname, 'wb')
        pickle.dump([station,eangles,dsnrData,sec,satNu,f,avgAzim,year,doy,meanTime,MJD,docstring], fff)
        fff.close()

#   doc1 = 'arrays are eangles (degrees), dsnrData is SNR with/DC removed, and sec (seconds of the day),\n'
#   doc2 = 'avgAzim is arc azimuth in degrees , doy is day of year,\n'
#   doc3 = 'f is frequency, meanTime is avg hours in UTC for the arc.'
#   docstring = doc1+doc2+doc3

def decimate_snr(snrD, allGood, dec):
    """
    Parameters
    ----------
    snrD : numpy array of floats
        loadtxt input of a snr file
    allGood : bool
        whether file exists?

    dec : int
        decimation value

    Returns
    -------
    snrD : numpy array of floats
        decimated array

    """

    if allGood and (dec != 1):
        print('Invoking decimation option')
        # does dec need to be a list??? was in original code
        # get the indices
        rem_arr = np.remainder( snrD[:,3], dec)
        # find out where they are zero
        iss =  (rem_arr == 0)
        # and apply
        snrD = snrD[iss,:]
        # not sure nrows and ncols is being used ... so not redoing it

    return snrD

def refraction_nite_mpf(irefr,snrD,mjd1,lat1R,lon1R,height1,RH_apriori,N_ant,zhd,zwd):
    """
    Parameters
    ----------
    irefr: int
    snrD : numpy array
        contents of SNR file
    mjd1 : float
        modified julian day?
    lat1R : float
        latitude in radians
    lon1R : float
        longitude in radians
    height : float
        ellipsoidal ? height in meters
    RH_apriori : float
        aprori RH in meters
    N_ant : float
        refraction index I think
    zhd : float
        hydrostatic zenith tropo dely in meters
    zwd : float
        wet zenith tropo dely in meters
    Returns
    -------
    ele : numpy array
        corrected elevation angles, deg
        
    """
    # NITE MODEL
    # remove ele < 1.5 cause it blows up
    i=snrD[:,1] > 1.5
    snrD = snrD[i,:]
    N = len(snrD[:,1])
            # elevation angles, degrees
    ele=snrD[:,1]
    # zenith angle in radians
    zenithA = 0.5*np.pi - np.radians(ele)
    #get mapping function and derivatives

    [gmf_h,dgmf_h,gmf_w,dgmf_w]=refr.gmf_deriv(mjd1, lat1R, lon1R,height1,zenithA)
    [mpf, dmpf]=[refr.mpf_tot(gmf_h,gmf_w,zhd,zwd),refr.mpf_tot(dgmf_h,dgmf_w,zhd,zwd)]

    ztd = zhd + zwd
    # inputs apriori RH, elevation angle, refractive index, zenith delay, mpf ?, dmpf?
    if irefr == 5:
        print('NITE refraction correction, Peng et al. remove data < 1.5 degrees')
        dE_NITE=refr.Equivalent_Angle_Corr_NITE(RH_apriori, ele, N_ant, ztd, mpf, dmpf)
        ele = ele + dE_NITE 
    else: 
        print('MPF refraction correction, Wiliams and Nievinski')
        dE_MPF= refr.Equivalent_Angle_Corr_mpf(ele,mpf,N_ant,RH_apriori)
        ele = ele + dE_MPF 

    return ele,snrD

