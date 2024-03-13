# -*- coding: utf-8 -*-
from __future__ import division
import json
import numpy as np 
import os, datetime, traceback, gzip
import subprocess
import sys
from scipy.interpolate import interp1d

import gnssrefl.gps as g
import gnssrefl.decipher_argt as gt

#Last modified Feb 22, 2023 by Taylor Smith (git: tasmi) for additional constellation support

def NMEA2SNR(locdir, fname, snrfile, csnr, dec, year, doy, llh, sp3, gzip):
    """
    Reads and translates the NMEA file stored in locdir + fname

    Naming convention assumed for NMEA files :  SSSS1520.23.A

    where SSSS is station name, day of year is 152 and year is 2023

    locdir is generally $REFL_CODE/nmea/SSSS/yyyy where yyyy is the year number and SSSS is the station name

    I believe lowercase is also allowed, but the A at the end is still set to be upper case

    (I believe) The SNR files are stored with upper case if given upper case, lower case if given lower case.


    Parameters
    -----------
    locdir : str
        directory where your NMEA files are kept
    fname : str
        NMEA filename 
    snrfile : str
        name of output file for SNR data
    csnr : str
        snr option, i.e. '66' or '99'
    dec : int
        decimation value in seconds
    year : int
        full year
    doy : int
        day of year
    llh : list of floats
        station location, lat (deg), lon(deg), height (m)
    sp3 : bool
        whether you use multi-GNSS sp3 file to do azimuth elevation angle calculations
        currently this only uses the GFZ rapid orbit.  
    gzip: bool
        gzip compress snrfiles. No idea if it is used here ...
        as this compression should happen in the calling function, not here
        
    """
    
    idec = int(dec)
    missing = True
    station = fname.lower() ; station = station[0:4]
    yy,month,day, cyyyy, cdoy, YMD = g.ydoy2useful(year,doy)
    
    foundcoords = False
    if (llh[0] != 0):
        # compute Cartesian receiver coordinates in meters
        x,y,z = g.llh2xyz(llh[0],llh[1],llh[2])
        recv = [x,y,z]
        foundcoords = True

    if sp3 and (not foundcoords):
        # try to get the LLH from json file
        jfile1  = os.environ['REFL_CODE'] + '/input/' + station.upper() + '.json'
        jfile2  = os.environ['REFL_CODE'] + '/input/' + station.lower() + '.json'
        fexists = False
        if os.path.isfile(jfile1):
            jfile = jfile1 ; fexists = True
            print('json file found (using for station coordinates)',jfile1)
        elif os.path.isfile(jfile2):
            jfile = jfile2 ; fexists = True
            print('json file found (using for station coordinates)',jfile2)

        if fexists:
            with open(jfile, 'r') as my_json:
                fcont = json.load(my_json)

            llh[0] = fcont['lat']; llh[1] = fcont['lon'] ; llh[2] = fcont['ht']
            x,y,z = g.llh2xyz(llh[0],llh[1],llh[2])
            recv = [x,y,z]
            foundcoords = True
        else:
            print('This code requires lat/lon/ht inputs. Provide on the command line or')
            print('make a json file using gnssir_input.  Exiting')
            sys.exit()

    if sp3:
        # first try to find precise because they have beidou
        xf,orbdir,foundit=g.gbm_orbits_direct(year,month,day)
        if not foundit: 
            print('Could not find the precise GNSS orbits from GFZ. ')
            xf,orbdir,foundit=g.rapid_gfz_orbits(year,month,day)
            if not foundit: 
                print('Could not find the rapid orbits from GFZ. Exiting')
            return
        else:
            orbfile = orbdir + '/' + xf # hopefully

    # this is to help a colleague 
    if station == 'argt':
        gt.decipher_argt(station,'jul01.txt',idec,snrfile,orbfile,recv,csnr,year,month,day)
        if os.path.isfile(snrfile):
            print('File made, ignoring the rest of the code')
            return
        else:
            print('Translation was unsuccessful'); return


    #check whether the input file is a uncompressed or compressed     
    if os.path.exists(locdir + fname):
        subprocess.call(['cp', '-f',locdir + fname ,'.'])
        t, prn, az, elv, snr, freq = read_nmea(fname)#read nmea files
        subprocess.call(['rm',fname])
        missing = False

    if os.path.exists(locdir + fname + '.gz') and missing:
        subprocess.call(['cp', '-f',locdir + fname + '.gz' ,'.'])
        subprocess.call(['gunzip', '-f', fname + '.gz'])
        t, prn, az, elv, snr, freq = read_nmea(fname)#read nmea files
        subprocess.call(['rm',fname])
        missing = False
        
    if os.path.exists(locdir + fname + '.Z') and missing:
        subprocess.call(['cp', '-f',locdir + fname + '.Z','.'])
        subprocess.call(['uncompress', fname + '.Z'])
        t, prn, az, elv, snr, freq = read_nmea(fname)#read nmea files
        subprocess.call(['rm',fname])
        missing = False
        

    # why is there all this going back and forth between lists and np arrays?

    t = np.array(t);az = np.array(az);elv = np.array(elv);snr = np.array(snr);prn = np.array(prn); freq=np.array(freq)
    #remove empty records
    if (station != 'argt'):
        #????
        t = t[az !=''];snr = snr[az !=''];prn = prn[az !=''];elv = elv[az !=''];freq = freq[az != ''];az = az[az !=''];
        t = t[elv !=''];az = az[elv !=''];snr = snr[elv !=''];prn = prn[elv !=''];freq = freq[elv != ''];elv = elv[elv !='']
        t = t[snr !=''];az = az[snr !=''];prn = prn[snr !=''];elv = elv[snr !=''];freq = freq[snr != ''];snr = snr[snr !='']
        t = t[prn !=''];az = az[prn !=''];elv = elv[prn !=''];snr = snr[prn !=''];freq = freq[prn != ''];prn = prn[prn !=''] 
        t = t[freq !=''];az = az[freq !=''];elv = elv[freq !=''];snr = snr[freq !=''];prn = prn[freq !='']; freq = freq[freq != '']
    
    az = az.astype(float)
    elv = elv.astype(float)
    snr = snr.astype(float)
    prn = prn.astype(int)

    prn_unique = np.unique(prn) 
    #print(prn_unique)

    T = []; PRN = []; AZ = []; ELV = []; SNR = []; FREQ = []        
    for i_prn in prn_unique:
        # the original code added 100 - but did not take into account the 
        # satellite numbers have been shifted for glonass.
        # also there is an illegal signal at satellite "48" 
        # i do not know what that is, but i am ignoring it.
        #if (i_prn > 32):
        #    print(i_prn, 'looks like an illegal satellite number')
        time = t[prn == i_prn];angle = elv[prn == i_prn];azimuth = az[prn == i_prn]; frequency = freq[prn == i_prn]
        Snr = snr[prn == i_prn];Prn = prn[prn == i_prn]
        
        angle_fixed, azim_fixed = fix_angle_azimuth(time, angle, azimuth)#fix the angles 
        if (len(angle_fixed) == 0 and len(azim_fixed) == 0):
            continue
            
        T.extend(time);AZ.extend(azim_fixed);ELV.extend(angle_fixed);SNR.extend(Snr);PRN.extend(Prn); FREQ.extend(frequency)
        
        del  time, angle, azimuth, Snr, Prn, angle_fixed, azim_fixed, frequency
        
    # It is easier for the sp3 option to write out the time, satellite, and SNR data into a plain file.
    # then the fortran can read that file and calculate the orbits from teh SP3 file and write out a new 
    # file with the correct azimuth and elevation angle.
    leap_mjd = g.getMJD(year,month,day,0)

    offset = g.read_leapsecond_file(leap_mjd)
    print('Leap second offset ', offset)

    if sp3 :
        tmpfile =  station + 'tmp.txt'
        timetags = np.unique(T)

        xT = np.asarray(T)
        xPRN = np.asarray(PRN)
        xSNR = np.asarray(SNR)
        xfreq = np.asarray(FREQ)

        print('Opening temporary file : ', tmpfile)
        fout = open(tmpfile, 'w+')
        fout.write('{0:15.4f}{1:15.4f}{2:15.4f} \n'.format(recv[0], recv[1],recv[2]) )
        fout.write('{0:6.0f}{1:6.0f}{2:6.0f} \n'.format(year, month, day) )
        #(t[i], prn[i], snr[i],freq[i])
        # look thru the unique time tags
        for i in range(0,len(timetags)):
            if ( (timetags[i] % idec) == 0):
                # for this timetag and if pass decimation test
                jj = (xT == timetags[i])
                # satellites at the epoch
                unique_sats_epoch = np.unique(xPRN[jj])
                epoch_sat = xPRN[jj]
                # snr data at the epoch
                epoch_snr = xSNR[jj]
                # fr data at the epoch
                epoch_freq = xfreq[jj]
                # go thru the unique satellite numbers at this epoch... 
                for ij in range(0,len(unique_sats_epoch)):
                    # pick out that satellite number
                    sat = int(unique_sats_epoch[ij])
                    # find all data that go with this 
                    ijk = (sat == epoch_sat)
                    # store the SNR data ..
                    snrdata = epoch_snr[ijk]
                    # store the freq data ..
                    frdata = epoch_freq[ijk]
                    # to fix the long-lived glonass mistake
                    if (sat > 100) & (sat < 200):
                        sat = sat - 64

                    #print(timetags[i], sat, snrdata, frdata)
                    # now write them out ... first assume all SNR data are zero
                    # then reassign based on frequency
                    s1=0; s2=0; s5=0  
                    for iugh in range(0,len(frdata)):
                        if (frdata[iugh] == '1'):
                            s1 = snrdata[iugh]
                        elif (frdata[iugh] == '2'):
                            s2 = snrdata[iugh]
                        elif (frdata[iugh] == '5'):
                            s5 = snrdata[iugh]
                    #print(timetags[i], sat, s1, s2, s5)
                    # testing for leap seconds, not good for all time
                    fout.write('{0:8.0f} {1:3.0f} {2:6.2f} {3:6.2f} {4:6.2f} \n'.format(timetags[i]+offset, sat, s1, s2, s5) )
                    
        fout.close()
        gt.new_azel(station,tmpfile,snrfile,orbfile,csnr)
        print('Az/El Updated...')
        return # translation has taken place in new_azel, so return to main code 

    # this was my first effort.  It only allowed L1 data. I am not deleting it - but
    # it is no longer valid.
    if sp3 and False:
        tmpfile =  station + 'tmp.txt'
        print('Opening temporary file : ', tmpfile)
        fout = open(tmpfile, 'w+')
        fout.write('{0:15.4f}{1:15.4f}{2:15.4f} \n'.format(recv[0], recv[1],recv[2]) )
        fout.write('{0:6.0f}{1:6.0f}{2:6.0f} \n'.format(year, month, day) )
        #(t[i], prn[i], snr[i],freq[i])
        for i in range(0,len(T)):
            if ( (int(t[i]) % idec) == 0):
                sat = PRN[i]
                # glonass satellites are misnamed by the code
                if (sat > 100) & (sat < 200):
                    sat = sat - 64
                fout.write('{0:8.0f} {1:3.0f} {2:6.2f} {3:s} \n'.format(T[i], sat, SNR[i], freq[i]) )
                newl = [T[i], sat, SNR[i], int(freq[i])]
        fout.close()
        #subprocess.call(['cp', tmpfile,'k_debug.txt']) 
        # make the snrfile
        gt.new_azel(station,tmpfile,snrfile,orbfile,csnr)
        print('Az/El Updated...')

        return # - in theory the fortran called in new_azel took care of everything
    
    inx = np.argsort(T)  #Sort data by time
    
    T = np.array(T);PRN = np.array(PRN);ELV = np.array(ELV);SNR = np.array(SNR);AZ = np.array(AZ); FREQ=np.array(FREQ)
    
    T = T[inx];PRN = PRN[inx];ELV = ELV[inx];SNR = SNR[inx];AZ = AZ[inx]; FREQ=FREQ[inx]
                               
    emin,emax = elev_limits(int(csnr))#select snr option 50, 66, 88, 99
    #write to an output file 
    with open(snrfile, 'w') as fout:
        for i in range(len(T)):
            if (float(ELV[i]) >= emin) and (float(ELV[i]) <= emax):
                
                #Via: https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_GSV.html
                
                #Note - Not sure if this is the best way to do this, or rather do it below when we can decide what
                #constellation we're looking at from the GxGSV line, and then add/subtract from the PRN there?
                #That might make it easier to keep straight
                
                #GPS
                if PRN[i] < 100:
                    p = float(PRN[i])
                    #if p > 32:
                        #$GPGSV indicates GPS and SBAS satellites. If the PRN is greater than 32, 
                        #this indicates an SBAS PRN, 87 should be added to the GSV PRN number to determine the 
                        #SBAS PRN number.
                        ##p += 87 ### Not sure how this could interact with future processing steps...
                
                #GLONASS
                elif (PRN[i] > 100 and PRN[i] < 200):
                    #$GLGSV indicates GLONASS satellites. 64 should be subtracted from the GSV PRN number 
                    #to determine the GLONASS PRN number.
                    p = float(PRN[i]) - 64
                
                #GALILEO
                elif (PRN[i] > 200 and PRN[i] < 300): 
                    #$GAGSV indicates Galileo satellites.
                    p = float(PRN[i])
                    
                #BEIDOU    
                elif (PRN[i] > 300 and PRN[i] < 400): 
                    #$GBGSV indicates BeiDou satellites. 100 should be subtracted from the 
                    #GSV PRN number to determine the BeiDou PRN number.
                    p = float(PRN[i]) # -100 ###Not sure how this could interact with future processing steps...
    
                #Final output format (https://github.com/kristinemlarson/gnssrefl/blob/master/docs/pages/rinex2snr.md)
                #Satellite number (remember 100 is added for Glonass, etc)
                #Elevation angle, degrees
                #Azimuth angle, degrees
                #Seconds of the day, GPS time
                #elevation angle rate of change, degrees/sec.
                #S6 SNR on L6
                #S1 SNR on L1
                #S2 SNR on L2
                #S5 SNR on L5
                #S7 SNR on L7
                #S8 SNR on L8        
                
                # it is not necessary to write out l7 and l8.  or l6. zero can be put there.
                l1 = 0; l2 = 0; l5 = 0; l6 = 0; l7 = 0; l8 = 0
                
                #Check what frequency we are at to know where to write each line
                f_store = FREQ[i]
                # this will create extremely large files ...
                #print(t[i], f_store, SNR[i])
                if f_store == '1':
                    l1 = float(SNR[i])
                elif f_store == '2':
                    l2 = float(SNR[i])
                elif f_store == '5':
                    l5 = float(SNR[i])
                # remove l6 and l7 ... we can add back in if a cheap instrument ever produces these obs
                #elif f_store == '6':
                #    l6 = float(SNR[i])
                #elif f_store == '8':
                #    l8 = float(SNR[i])
                    
                #NOTE -- All satellites have a 'mixed/undefined' frequency 0 for 
                # NMEA 4.11 (https://gpsd.gitlab.io/gpsd/NMEA.html#_nmea_4_11_system_id_and_signal_id)
                #This is never used here so could leave blank snr lines!
                
                outline = "%3g %10.4f %10.4f %10g %4s " % (p, float(ELV[i]), float(AZ[i]), float(T[i]), '0')
                snrline = "%7.2f %7.2f %7.2f %7.2f " % (l6, l1, l2, l5 )
                 
                # apply decimating here
                if ( (int(T[i]) % idec) == 0):
                    fout.write(outline + snrline + '\n')
                #fout.write("%3g %10.4f %10.4f %10g %4s %4s %7.2f %4s %4s\n" % (p, float(ELV[i]), float(AZ[i]), float(T[i]),'0', '0', float(SNR[i]),'0', '0')) 
        
def read_nmea(fname):
    """
    reads a NMEA file.
    it only reads the GPGGA sentence (includes snr data) in NMEA files    

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

    freq : list of ???
        apparently frequency values - 

    """
    
    ### SOME USEFUL LINKS
    #https://cddis.nasa.gov/sp3c_satlist.html
    #https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_MessageOverview.html
    #https://receiverhelp.trimble.com/alloy-gnss/en-us/NMEA-0183messages_GSV.html
    
    #Could also go directly to reading the file via gzip.open(fname, 'rb') or gzip.open(fname, 'rt') for text
    with open(fname, 'rb') as f:
        lines = f.readlines()

    t = []; prn = []; az = []; elv = []; snr = []; freq = []
    
    curdt = None #Empty starting date to ensure only get data with proper timing
    t_sec = None #Empty starting time
    for i, line in enumerate(lines):
        line = line.decode('utf-8')
        
        if '$' in line[1:-1]: #Skip line if misplaced $ via https://github.com/purnelldj/gnssr_lowcost
            continue
        if not line.startswith('$G'): #Skip line if improper start
            continue
        if len(line.split('*')) > 2: #Additional error checking for misplaced * or combined lines
            continue
        
        #line = line.replace('$', '') #Strip leading $
        
        if 'RMC' in line: #Get timing info
            row = line.split(',')
            #sect = int(float(row[1][0:2]) * 60 * 60 + float(row[1][2:4]) * 60 + float(row[1][4:])) #Time in seconds
            try:
                curdt = datetime.datetime(int(row[9][4:6])+2000,int(row[9][2:4]),int(row[9][0:2])) #Current date
            except:
                pass
        
        if not curdt: #Skip forward until the first 'RMC' instance which gives a proper date to store
            continue
        
        if 'GGA' in line: #read GPGGA sentence: Global Positioning System Fix Data 
            try:
                hr = int(line.split(",")[1][0:2])
                mn = int(line.split(",")[1][2:4])
                sc = float(line.split(",")[1][4:8])
                t_sec = hr*3600 + mn*60 + sc
                if (i > 100 and t_sec == 0):                   #set t to 86400 for the midnight data
                    t_sec = 86400
            except:
                t_sec = None
                continue # skip invalid GGA sentence
            #This could be added if positioning info is interesting/needed. Via https://github.com/purnelldj/gnssr_lowcost
            #   row = line.split(',')
            #   if row[3] == 'S': #Northern or southern hemisphere
            #        latt = -latt
            #   lont = float(row[4][0:3]) + float(row[4][3:])/60 #Longitude
            #   if row[5] == 'W':
            #        lont = -lont #Eastern or Western hemisphere
            #   hgtt = float(row[9])+float(row[11]) #Orthometric height (MSL ref)

        #Read Satellite positions (GSV) - The GSV message string identifies the number of SVs in view, the PRN numbers, 
        #elevations, azimuths, and SNR values.
        elif 'GSV' in line:                    #read GPGSV sentence: GPS Satellites in view in this cycle   
            if t_sec is None: # Discard line if there's no valid timestamp
                continue
            try:
                sent = line.split(",")         #GSV sentence 
                #ttl_ms = int(sent[1])          #Total number of messages in the GPGSV sentence 
                #ms = int(sent[2])              #Message number 
                
                #Check for a proper length GSV line (avoid mixed/incomplete lines)
                if len(sent) not in [21, 20, 17, 16, 13, 12, 9, 8]:
                    continue
            
                if "GPGSV" in line: #GPS
                    prn_offset = 0
                elif "GLGSV" in line: #Glonass
                    prn_offset = 100
                elif "GAGSV" in line: #Galileo
                    prn_offset = 200
                elif "BDGSV" in line: #Beidou
                    prn_offset = 300
                elif 'GBGSV' in line: #Also Beidou, depending on chip
                    prn_offset = 300
                else:
                    print('Undefined constellation')
                    continue
                
                #Note: $GNGSV uses PRN in field 4. Other $GxGSV use the satellite ID in field 4. 
                    #Jackson Labs, Quectel, Telit, and others get this wrong, in various conflicting ways.
                #GNGSV is not currently supported in this code!
                
                if len(sent) in [21, 17, 13, 9]: #Some chips spit out an extra piece of info at the end 
                    #Ublox-9 etc has a signal ID which can be used to split between L1, L2, etc
                    #    #https://gpsd.gitlab.io/gpsd/NMEA.html#_nmea_4_11_system_id_and_signal_id
                    #This seems to be a NMEA 4.11 feature -- not all chips will have this!
                    
                    sig_id = sent[-1].split('*')[0] #Store that signal ID to check frequency
                    sent = sent[:-1] #Remove the last line for subsequent SNR data gatheriing
                    if "GPGSV" in line:
                        if sig_id in ['0','1','2','3']:
                            sig_id = 1
                        elif sig_id in ['5', '6']:
                            sig_id = 2
                        elif sig_id in ['7', '8']:
                            sig_id = 5
                    if 'GLGSV' in line:
                        if sig_id in ['0', '1', '2']:
                            sig_id = 1
                        elif sig_id in ['3', '4']:
                            sig_id = 2
                    if 'GAGSV' in line:
                        if sig_id in ['6', '7']:
                            sig_id = 1
                        elif sig_id in ['1', '2', '3']:
                            sig_id = 5
                        elif sig_id in ['4', '5']:
                            sig_id = 6
                    if ('GBGSV' in line or 'BDGSV' in line): #Beidou has two possible calls in NMEA (and weird frequency codes)...
                        if sig_id in ['0','1','2','3','4']:
                            sig_id = 1
                        elif sig_id in ['5','6','7','B','C']:
                            sig_id = 2
                        elif sig_id in ['8','9','A']:
                            sig_id = 3
            
                else:
                    sig_id = 1 #Default is L1 -- this is most data/chips that return NMEA by default
                    
                for inds in [4, 8, 12, 16]: #Check for a max of four satellites in view per line
                    try:
                        sat_prn = int(sent[inds]) + prn_offset #field 4,8,12,16 :  SV PRN number
                        elev = sent[inds + 1] #field 5,9,13,17 :  Elevation in degrees, 90 maximum
                        azi = sent[inds + 2] #field 6,10,14,18:  Azimuth in degrees
                        snr_ = sent[inds + 3] #field 7,11,15,19:  SNR, 00-99 dB (null when not tracking)
                        
                        #Note: NMEA 4.1+ systems (u-blox 9, Quectel LCD79) may emit an extra field, Signal ID, 
                            #just before the checksum -- via: https://gpsd.gitlab.io/gpsd/NMEA.html#_gsv_satellites_in_view
                        #Hence .split('*')[0]
                        snr_ = snr_.split('*')[0]
                        
                        prn.append(str(sat_prn))
                        elv.append(elev)
                        az.append(azi)
                        snr.append(snr_)
                        freq.append(str(sig_id))
                        t.append(t_sec)
                        
                    except: #Error handle for poorly captured data (e.g., no PRN, or at max nr of satellites in line)
                        pass
                    
            except:
                #Sometimes you might have a mixed line due to sensors turning on/off unexpectedly
                print(line, 'Failed! Skipping...')
                #traceback.print_exc()
    return t, prn, az, elv, snr, freq

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
    someone should document this

    Parameters
    ----------
    azim1 : ??

    azim2 : ??

    Returns
    -------
    ???

    """
    if not(azim2.size):
        diff = azimuth_diff1 (azim1)
    else:
        diff = azimuth_diff2 (azim1, azim2)
#    diff = np.abs(diff)
    return diff
     
def angle_range_positive(ang):
    """
    someone should document this

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
    someone should document this

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
    Creates a full name of the snr file name (i.e. including the path) 
    >>>> Checks that directories exist.

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
    cyyyy = str(year)
    fname =  xdir + cyyyy + '/snr/' + station + '/' + station + cdoy + '0.' + cyy + '.snr' + csnr
    d = xdir + cyyyy
    if not os.path.isdir(d):
        subprocess.call(['mkdir', d])
    d = xdir + cyyyy + '/snr'
    if not os.path.isdir(d):
        subprocess.call(['mkdir', d])
    d = xdir + cyyyy + '/snr/' + station
    if not os.path.isdir(d):
        subprocess.call(['mkdir', d])

    return fname

def elev_limits(snroption):
    """

    Given a snr option, return the elevation angle limits

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
        emin = 0; emax = 90
    else:
        emin = 5; emax = 30

    return emin, emax
  
def run_nmea2snr(station, year_list, doy_list, isnr, overwrite, dec, llh, sp3, gzip):
    """
    runs the nmea2snr conversion code

    Looks for NMEA files in $REFL_CODE/nmea/ssss/2023 for station ssss and year 2023.
    I prefer lowercase station names, but I believe the code allows both upper and lower
    case. 

    Files are named:  SSSS1520.23.A 

    where SSSS is station name, day of year 152 and 
    the last two characters of the 2023 as the middle value.

    The SNR files are stored with upper case if given upper case, lower case if given lower case.

    Parameters
    ----------
    station : str
        4 ch name of station 
    year_list : list of integers
        years 
    doy_list : list of days of year
        days of years
    isnr : int
        snr file type
    overwrite : bool
        whether make a new SNR file even if one already exists
    dec : int
        decimation in seconds
    llh : list of floats
        lat and lon (deg) and ellipsoidal ht (m)
    sp3 : bool
        whether you want to use GFZ rapid sp3 file for the orbits
    gzip : bool
        whether snrfiles are gzipped after creation

    """
    # loop over years and day of years
    for yr in year_list:
        
        locdir= os.environ['REFL_CODE'] + '/nmea/' + station + '/' + str(yr) + '/'
        for dy in doy_list:
            csnr = str(isnr)
            cdoy = '{:03d}'.format(dy)
            if (yr < 2000):
                cyy = '{:02d}'.format(yr-1900)
            else:
                cyy = '{:02d}'.format(yr-2000)
            snrfile =  quickname(station,yr,cyy,cdoy,csnr)#snr filename
            snre = g.snr_exist(station,yr,dy,csnr)#check if snrfile already sxists
            if snre:
                if overwrite:
                    print('SNR file exists, but you requested it be overwritten')
                    # just in case you have a previously gunzipped version
                    if os.path.exists(snrfile):
                        subprocess.call(['rm', snrfile])
                        snre = False
                    if os.path.exists(snrfile + '.gz'):
                        subprocess.call(['rm', snrfile + '.gz'])
                        snre = False
                else:
                    print('SNR file already exists', snrfile)
        
            illegal_day = False
            if (float(dy) > g.dec31(yr)):
                illegal_day = True
        
            if (not illegal_day) and (not snre):
                r =  station + cdoy + '0.' + cyy + '.A'# nmea file name example:  WESL2120.21.A 
                if os.path.exists(locdir+r) or os.path.exists(locdir+r+'.gz') or os.path.exists(locdir+r+'.Z') or (station == 'argt'):
                    #print('Creating '+snrfile)
                    NMEA2SNR(locdir, r, snrfile, csnr, dec, yr, dy, llh, sp3, gzip)
                    if os.path.isfile(snrfile):
                        print('SUCCESS: SNR file created', snrfile)
                    if os.path.isfile(locdir + r ):
                        # gzip the NMEA file now
                        print('gzip the NMEA file', locdir + r)
                        subprocess.call(['gzip', locdir + r])
                        # otherwise it is already gzipped?
                    if gzip:
                        if not snrfile.endswith('.gz'):
                            subprocess.call(['gzip', snrfile])
                            print('SNR file gzip compressed')
                else:
                    print('NMEA file '+ locdir + r +' does not exist')
