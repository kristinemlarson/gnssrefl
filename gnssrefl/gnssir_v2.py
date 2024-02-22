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

def gnssir_guts_v2(station,year,doy, snr_type, extension,lsp):
    """

    Computes lomb scargle periodograms for a given station, year, day of year etc.

    Arcs are determined differently than in the first version of the code, which
    was quadrant based. This identifies arcs and applies azimuth constraints after the fact.

    2023-aug-02 trying to fix the issue with azimuth print out being different than
    azimuth at lowest elevation angle

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
        e1 : float
            min elev angle, deg
        e2 : float
            max elev angle, deg
        freqs: list of floats
            list of frequencies to use 
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
        reqAmp : float
            required periodogram amplitude for QC
        ellist: list of floats
            added 23jun16, allow multiple elevation angle regions
        
    """

    #   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    # make sure REFL_CODE/Files/station directory exists ... 
    g.checkFiles(station, '')

    if 'ellist' in lsp.keys():
        ellist = lsp['ellist']
        if len(ellist) > 0:
            print('Using an augmented elevation angle list', ellist)
    else:
        ellist = [];
        #print('no augmented elevation angle list')



    # this is also checked in the command line - but for people calling the code ...
    if ((lsp['maxH'] - lsp['minH']) < 5):
        print('Requested reflector heights (', lsp['minH'], ',', lsp['maxH'], ') are too close together. Exiting.')
        print('They must be at least 5 meters apart - and preferably further than that.')
        return

    e1=lsp['e1']; e2=lsp['e2']; minH = lsp['minH']; maxH = lsp['maxH']
    ediff = lsp['ediff']; NReg = lsp['NReg']  
    PkNoise = lsp['PkNoise']; prec = lsp['desiredP']; delTmax = lsp['delTmax']
    if 'azval2' in lsp:
        azval2 = lsp['azval2']; 
        naz = int(len(azval2)/2)
    else:
        print('This module requires azval2 to be set in gnssir_input. This record is not present in your json.')
        sys.exit()

    pele = lsp['pele'] ; pfitV = lsp['polyV']

    freqs = lsp['freqs'] ; reqAmp = lsp['reqAmp'] 

    # allows negatiev az value for first pair
    azvalues = rewrite_azel(azval2)

    ok = g.is_it_legal(freqs)
    if not ok:
        print('Fix your json list of frequencies. Exiting')
        sys.exit()

    plot_screen = lsp['plt_screen'] 
    onesat = lsp['onesat']; screenstats = lsp['screenstats']
    gzip = lsp['gzip']
    if 'dec' in lsp.keys():
        dec = int(lsp['dec'])
    else:
        dec = 1 # so Jupyter notebooks do not need to be rewritten

    # no need to print to screen if default
    if (dec != 1):
        print('Using decimation value: ', dec)

    d = g.doy2ymd(year,doy); month = d.month; day = d.day
    dmjd, fracS = g.mjd(year,month,day,0,0,0)
    xdir = os.environ['REFL_CODE']
    ann = g.make_nav_dirs(year) # make sure directories are there for orbits
    g.result_directories(station,year,extension) # make directories for the LSP results

   # this defines the minimum number of points in an arc.  This depends entirely on the sampling
   # rate for the receiver, so you should not assume this value is relevant to your case.
    minNumPts = 20
    p,T,irefr,humidity = set_refraction_params(station, dmjd, lsp)
    print('Refraction parameters (press, temp, humidity, ModelNum)',np.round(p,3),np.round(T,3),np.round(humidity,3),irefr)

    if (irefr == 3) or (irefr == 4):
        TempK = T + 273.15 # T is in celsius ... I think.
        # N_ant is the refraction index
        N_ant=refr.refrc_Rueger(p,humidity,TempK)[0]    #


# only doing one day at a time for now - but have started defining the needed inputs for using it
    twoDays = False
    obsfile2= '' # dummy value for name of file for the day before, when we get to that
    fname, resultExist = g.LSPresult_name(station,year,doy,extension) 
    #print('Results are written to:', fname)

    if (lsp['nooverwrite'] == True) & (resultExist == True):
        allGood = 0
        print('>>>>> The result file already exists for this day and you have selected the do not overwrite option')
        #sys.exit()
    else:
        # uncompress here so you should not have to do it in read_snr_multiday ...
        obsfile, obsfileCmp, snre = g.define_and_xz_snr(station,year,doy,snr_type) 

        allGood, snrD, nrows, ncols = read_snr(obsfile)
        # added gzip option.  first input is xz compression
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


        snr.compress_snr_files(lsp['wantCompression'], obsfile, obsfile2,twoDays,gzip) 
    if (allGood == 1):
        print('Reading from: ', obsfile)
        print('Results will be written to:', fname)
        minObsE = min(snrD[:,1])
        print('Minimum observed elevation angle in this file ', minObsE, '/requested e1 and e2 ', e1,e2)
        # only apply this test for simple e1 and e2
        if len(ellist) == 0:
            if minObsE > (e1 + ediff):
                print('You literally have no data above the minimum elevation angle setting')
                print('which is e1 + ediff: ', e1 + ediff, ' If you do not like')
                print('this QC constraint, then set ediff to be very large (10 degrees) in the json or use ')
                print('the minimum elevation angle your receiver used. Exiting.')
                sys.exit()

        if (irefr == 3) or (irefr == 4):
            # elev refraction, lsp, pres, temp, time, sat
            if irefr == 3:
                print('Ulich refraction correction')
            else:
                print('Ulich refraction correction, time-varying')
            ele=refr.Ulich_Bending_Angle(snrD[:,1],N_ant,lsp,p,T,snrD[:,3],snrD[:,0])
        elif irefr == 0:
            print('No refraction correction applied ')
            ele = snrD[:,1]
        else :
            if irefr == 1:
                print('Standard Bennett refraction correction')
            else:
                print('Standard Bennett refraction correction, time-varying')
            ele = snrD[:,1]
            ele=apply_refraction_corr(lsp,ele,p,T)

        # apply an elevation mask for all the data for the polynomial fit
        i= (ele >= pele[0]) & (ele < pele[1])
        ele = ele[i]
        snrD = snrD[i,:]
        sats = snrD[:,0]
        # make sure the snrD array has elevation angles fixed
        snrD[:,1] = ele # ????

        # open output file
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
#           get the list of satellites for this frequency
            if onesat == None:
                satlist = find_mgnss_satlist(f,year,doy)
            else:
                # check that your requested satellite is the right frequency
                satlist = onesat_freq_check(onesat,f )

            # main satellite loop
            for satNu in satlist:
                if screenstats: 
                    print('Satellite', satNu)
                iii = (sats == satNu)
                thissat = snrD[iii,:]
                goahead = False

                if len(thissat) > 0:
                    # if there are data for this satellite, find all the arcs
                    # separate numpy array of elevation angles .... 

                    # allow more than one set of elevation angles
                    if len(ellist) > 0:
                        arclist = np.empty(shape=[0,6])
                        for ij in range(0,len(ellist),2):
                            te1 = ellist[ij]; te2 = ellist[ij+1]; newl = [te1,te2]
                            # poorly named inputs - elev, azimuth, seconds of the day, ...
                            # te1 and te2 are the requested elevation angles I believe
                            # satNu is the requested satellite number
                            tarclist = new_rise_set_again(thissat[:,1],thissat[:,2],thissat[:,3],te1, te2,ediff,satNu,screenstats)
                            arclist = np.append(arclist, tarclist,axis=0)

                    else:
                        arclist = new_rise_set_again(thissat[:,1],thissat[:,2],thissat[:,3],e1, e2,ediff,satNu,screenstats)

                    nr,nc = arclist.shape
                    if nr > 0:
                        goahead = True
                    else:
                        goahead = False

                if goahead:
                    found_results = True
                    # instead of az bins now go through each arc 
                    for a in range(0,nr):
                        sind = int(arclist[a,0]) ; eind = int(arclist[a,1])
                        #if screenstats:
                        #    print('Indices for this arc', a, sind, eind)
                        # create array for the requested arc
                        d2 = np.array(thissat[sind:eind, :], dtype=float)
                        # window the data - which also removes DC 
                        # this is saying that these are the min and max elev angles you should be using
                        e1 = arclist[a,4]; e2 = arclist[a,5]
                        x,y, Nvv, cf, meanTime,avgAzim,outFact1, Edot2, delT= window_new(d2, f, 
                                satNu,ncols,pele, lsp['polyV'],e1,e2,azvalues,screenstats)
                        Nv = Nvv # number of points
                        UTCtime = meanTime

                        if (delT != 0):
                            MJD = g.getMJD(year,month,day, meanTime)
                            maxF, maxAmp, eminObs, emaxObs,riseSet,px,pz= g.strip_compute(x,y,cf,maxH,prec,pfitV,minH)

                            tooclose = False
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

                            if False:
                                print(avgAzim, satNu, e1, e2)

                            if (not tooclose) & (delT < delTmax) & (maxAmp > reqAmp[ct]) & (maxAmp/Noise > PkNoise):
                            # request from a tide gauge person for Month, Day, Hour, Minute

                                if lsp['mmdd']:
                                    ctime = g.nicerTime(UTCtime); ctime2 = ctime[0:2] + ' ' + ctime[3:5]
                                    fout.write(" {0:4.0f} {1:3.0f} {2:6.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} {17:2.0f} {18:2.0f} {19:5s} \n".format(year,doy,maxF,satNu, UTCtime, avgAzim,maxAmp,eminObs,emaxObs,Nv, f,riseSet, Edot2, maxAmp/Noise, delT, MJD,irefr,month,day,ctime2)) 
                                else:
                                    fout.write(" {0:4.0f} {1:3.0f} {2:6.3f} {3:3.0f} {4:6.3f} {5:6.2f} {6:6.2f} {7:6.2f} {8:6.2f} {9:4.0f} {10:3.0f} {11:2.0f} {12:8.5f} {13:6.2f} {14:7.2f} {15:12.6f} {16:1.0f} \n".format(year,doy,maxF,satNu, UTCtime, avgAzim,maxAmp,eminObs,emaxObs,Nv, f,riseSet, Edot2, maxAmp/Noise, delT, MJD,irefr)) 
                                gj +=1
                                if screenstats:
                                    T = g.nicerTime(UTCtime)
                                    print('SUCCESS Azimuth {0:3.0f} Sat {1:3.0f} RH {2:7.3f} m PkNoise {3:4.1f} Amp {4:4.1f} Fr{5:3.0f} UTC {6:5s} DT {7:3.0f} '.format(iAzim,satNu,maxF,maxAmp/Noise,maxAmp, f,T,round(delT)))
                                if plot_screen:
                                    failed = False
                                    local_update_plot(x,y,px,pz,ax1,ax2,failed)
                            else:
                                rj +=1
                                if screenstats:
                                    #print(delT, tooclose,Noise,PkNoise)
                                    #35.0 False 3.682862189099345 2.8

                                    print('FAILED QC for Azimuth {0:.1f} Satellite {1:2.0f} UTC {2:5.2f} RH {3:5.2f}'.format( iAzim,satNu,UTCtime,maxF))
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
            if found_results and plot_screen:
                print('data found for this frequency: ',f)
                ax1.set_xlabel('Elevation Angles (deg)')
                ax1.grid(True, linestyle='-'); ax2.grid(True, linestyle='-')
                ax1.set_title(station + ' Raw Data/Periodogram for ' + g.ftitle(f) + ' Frequency')
                ax2.set_xlabel('Reflector Height (m)');
                ax2.set_ylabel('volts/volts') ; ax1.set_ylabel('volts/volts')
                plotname = xdir + '/Files/' + station + '/gnssir_freq' + str(f) + '.png'
                g.save_plot(plotname)
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

    """

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
        # now allows time varying for models 2 and 4
        if (refraction_model == 2) or (refraction_model == 4):
            it = 0
        else:
            it = 1
        dlat = lsp['lat']*np.pi/180; dlong = lsp['lon']*np.pi/180; ht = lsp['ht']
        p,T,dT,Tm,e,ah,aw,la,undu = refr.gpt2_1w(station, dmjd,dlat,dlong,ht,it)
        # e is water vapor pressure, so humidity ??
        #print("Pressure {0:8.2f} Temperature {1:6.1f} \n".format(p,T))

    #print('refraction model', refraction_model,irefr)
    return p,T,irefr, e

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


def new_rise_set(elv,azm,dates, e1, e2, ediff,sat, screenstats ):
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
        min eval
    e2 : float
        max eval
    ediff : float
        el angle difference QC
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
            nogood = True
            ediff_violation = True 
        if (maxObse - e2) < -ediff:
            nogood = True
            ediff_violation = True
        if (eind-sind) == 1:
            nogood = True
            verysmall = True
        if ((maxObse - minObse) < min_deg):
            nogood = True

        if screenstats:
            if nogood:
                # do not write out warning for these tiny arcs which should not even be there.
                # i am likely reading the code incorrectly
                add = ''
                if ediff_violation:
                    add = ' violates ediff'
                if not verysmall:
                    print('Failed sat/arc',sat,iarc+1, sind,eind,' min/max elev: ', np.round(minObse,2), np.round(maxObse,2), minA,maxA,add)
            else:
                print('Keep   sat/arc',sat,iarc+1, sind,eind,' min/max elev: ', np.round(minObse,2), np.round(maxObse,2),minA,maxA)

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


def window_new(snrD, f, satNu,ncols,pele,pfitV,e1,e2,azlist,screenstats):
    """
    retrieves SNR arcs for a given satellite. returns elevation angle and 
    detrended linear SNR

    2023-aug02 updated to improve azimuth calculation reported

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
    pele : list of floats
        elevation angles for polynomial fit
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

    """
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
    elif f in [5, 205]:
        column = 9
#   these are galileo frequencies (via RINEX definition)
    elif f in [206,306]:
        column = 6
    elif f in [207,307]:
        column = 10
    elif (f == 208):
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
                print('No useful data on frequency ', f , 'and sat ', satNu, ': all zeros')
            good = False
        else:
            if nzero > 0:
                #print('removing ', nzero, ' zero points on frequency ', f )
                # indices you are keeping ... 
                nn = (datatest > 0) ; 
                snrD = snrD[nn,:]

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
                    else:
                        if screenstats:
                            print('This azimuth is not in the azimuth region', initA, '(deg)')
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
    return x,y, Nvv, cf, meanTime,initA, outFact1, outFact2, delT


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

    print('Using azimuths: ', azelout)
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

def new_rise_set_again(elv,azm,dates, e1, e2, ediff,sat, screenstats ):
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
        min elevation angle (deg)
    e2 : float
        max elevation angle (deg)
    ediff : float
        el angle difference required, deg, QC
    sat : int
        satellite number
    screenstats : bool
        whether you want info printed to the screen

    Returns
    -------
    tv : numpy array
        beginning and ending indices of the arc
        satellite number, arc number, elev min, elev max

    """
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
    bkpt = np.unique(bkpt)
    bkpt = np.sort(bkpt)
    N=len(bkpt)
    tv = np.empty(shape=[0,6])

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
        if (maxObse - e2) < -ediff:
            nogood = True
            ediff_violation = True
        if (eind-sind) == 1:
            nogood = True
            verysmall = True
        if ((maxObse - minObse) < min_deg):
            nogood = True

        if screenstats:
            if nogood:
                # do not write out warning for these tiny arcs which should not even be there.
                # i am likely reading the code incorrectly
                add = ''
                if ediff_violation:
                    add = ' violates ediff'
                if not verysmall:
                    print('Failed sat/arc',sat,iarc+1, sind,eind,' min/max elev: ', np.round(minObse,2), np.round(maxObse,2), minA,maxA,add)
            else:
                print('Keep   sat/arc',sat,iarc+1, sind,eind,' min/max elev: ', np.round(minObse,2), np.round(maxObse,2),minA,maxA)

        if not nogood :
            iarc = iarc + 1
            newl = [sind, eind, int(sat), iarc,e1,e2]
            #print('indices ',sind, eind, elv[sind], elv[eind] )
            #print('indices ',sind, eind, elv[sind], elv[eind], azm[sind], azm[eind])
            tv = np.append(tv, [newl],axis=0)

    return tv 
