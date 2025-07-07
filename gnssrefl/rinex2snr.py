import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
from scipy.interpolate import interp1d
import subprocess
import sys
import time


# progress bar for RINEX translation/orbits
from progress.bar import Bar

# my gps libraries
import gnssrefl.gps as g
import gnssrefl.rinpy as rinpy
import gnssrefl.karnak_libraries as k
import gnssrefl.highrate as ch

# fortran codes for translating RINEX
import gnssrefl.gpssnr as gpssnr
import gnssrefl.gnsssnr as gnsssnr
import gnssrefl.gnsssnrbigger as gnsssnrbigger

class constants:
    omegaEarth = 7.2921151467E-5 #      %rad/sec
    mu = 3.986005e14 # Earth GM value
    c= 299792458 # m/sec

#
#
def quickname(station,year,cyy, cdoy, csnr):
    """
    creates full filename (including directory) for a local SNR file

    Parameters
    ----------
    station : str
        station name, 4 character
    year : int
        full year
    cyy : str
        two character year
    cdoy : str
        three character day of year
    csnr : str
        snr ending, i.e. '66' or '99'

    Returns
    -------
    fname : str
        full filename including the directory

    """
    xdir  = os.environ['REFL_CODE'] + '/'
    fname =  xdir + str(year) + '/snr/' + station + '/' + station + cdoy + '0.' + cyy + '.snr' + csnr

    return fname

def run_rinex2snr(station, year, doy,  isnr, orbtype, rate,dec_rate,archive, nol,overwrite,translator,srate, 
                  mk, stream,strip,bkg,screenstats,gzip,timeout):
    """
    main code to convert RINEX files into SNR files.
    It works on a single year and doy.

    Parameters
    ----------
    station : str
        4 or 9 character station name. 6 ch allowed for japanese archive
        9 means it is a RINEX 3 file

    year : int
        full year 
    doy : int 
        day of year
    isnr : int
        SNR file type choice, i.e. 66, 88
    orbtype : str
        orbit type, e.g. nav, rapid, gnss
    rate : str
        general sample rate.
        high: use 1-Hz area in the archive
        low: use default area in the archive
    dec_rate : integer
         decimation value
    archive : str
        choice of GNSS archive, of which there are many
    nol: bool
        True: assumes RINEX files are in local directory
        False (default): will look at multiple - or specific archive
    overwrite: bool
        False (default): if SNR file exists, SNR file not made
        True: make a new SNR file
    translator : str
        hybrid (default), fortran, or python
        hybrid uses fortran within he python code
    srate : int
        sample rate for RINEX 3 files
    mk : bool
        makan option
    stream : str
        naming parameter for RINEX 3 files (R or S)
    strip : bool
        reduces observables to only SNR (too many observables, particularly in RINEX 2 files
        will break the RINEX translator)
    bkg : str
        location of bkg files, EUREF or IGS
    screenstats: bool
        whether print statements come to screen
    gzip: bool
        whether SNR files are gzipped after creation
    timeout : int
        optional parameter I am testing out for requests timeout parameter
        in seconds
    """
    #
    xdir = os.environ['REFL_CODE']
    gpsonly = False

    NS = len(station)
    if (NS == 4):
        version = 2
        if not mk:
            station = station.lower()
    elif (NS == 6 and archive == 'jp') :
        version = 2
        if not mk:
            station = station[-4:].upper()
    elif (NS == 9):
        version = 3
        station9ch = station.upper()
        if not mk:
            station = station[0:4].lower()
        else:
            station = station[0:4].upper()
    else:
        print('Illegal station input - Station must have 4,6,or 9 characters. Exiting')
        return

    # a kluge of sorts - but hey
    if (version == 3):
        if (rate == 'low') & (archive == 'kadaster'):
            print('Sorry - gnssrefl does not support 30 sec RINEX 3 files from kadaster.nl')
            print('Please submit a PR if you have time or interest.')
            return



# old loop thru years and days - will fix later. now avoiding retyping
    if True:

        ann = g.make_nav_dirs(year)
        cyyyy = str(year)
        dec31 = g.dec31(year)
        if True:
            csnr = str(isnr)
            cdoy = '{:03d}'.format(doy)
            cyy = cyyyy[2:4]
            # first, check to see if the SNR file exists
            fname =  quickname(station,year,cyy,cdoy,csnr)
            if screenstats:
                print(fname)
            # now it unzips if that version exists
            snre = g.snr_exist(station,year,doy,csnr)
            if snre:
                if overwrite:
                    print('SNR file exists/you requested overwriting, existing file will be deleted')
                    if os.path.isfile(fname):
                        subprocess.call(['rm', fname]); 
                    if os.path.isfile(fname + '.gz'):
                        subprocess.call(['rm', fname + '.gz']); 
                    snre = False
                else:
                    print('SNR file already exists', fname, '\n')
            else:
                print('SNR file does not already exist. Which means I will try to make it.')


            illegal_day = False
            if (doy > dec31):
                illegal_day = True

            if (not illegal_day) and (not snre):
                # make log directory ... 
                log, errorlog, exedir,gen_log = set_rinex2snr_logs(station,year,doy)
                print('Fortran translation log: ', errorlog)
                print('General log: ', gen_log)

                r = station + cdoy + '0.' + cyy + 'o'
                rgz = station + cdoy + '0.' + cyy + 'o.gz'
                localpath2 =  xdir + '/' + cyyyy + '/rinex/' + station + '/'
                #if screenstats:
                log.write(localpath2)
                if nol:
                    current_local = os.getcwd()
                    log.write('Looking for the RINEX file on your machine \n')
                    print('Will first assume station ', station, ' year:', year, ' doy:', doy, 'is located here :', current_local)
                    # this assumes RINEX file is in local directory or "nearby"
                    if version == 2:
                        if mk:
                            # this code was written by someone who did not like the gnssrefl directory structure.
                            # please look in the_makan_option to find out more about it
                            print('First using the_makan_option')
                            the_makan_option(station,cyyyy,cyy,cdoy) # looks various places in your local directories
                        if not os.path.exists(r):
                            print('Looked for ', current_local+'/'+r)
                            print('Failed, will search other names/directories')
                            allgood = get_local_rinexfile(r,localpath2)
                        if os.path.exists(r):
                            log.write('Found the RINEX 2.11 file {0:s} \n'.format(r))

                            try:
                                rinext =float(np.loadtxt(r,usecols=0,dtype='str',max_rows=1))
                                log.write('Apparent RINEX version {0:4.2f} \n'.format(rinext))
                                #print('Apparent Rinex version', rinext)
                                if (rinext != 2.11):
                                    log.write('Your file is not RINEX v2.11 which is what you told the code it was.\n')
                                    #sys.exit()

                            except:
                                log.write('I had problems confirming RINEX version. Will ignore that for now.\n')

                            if strip:
                                log.write('Testing out stripping the RINEX 2 file here\n')
                                k.strip_rinexfile(r)
                            conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,translator,log,errorlog,rinex2_filename=r)
                        else:
                            print('You Chose the No Look Option, but did not provide the needed RINEX file.')
                    if version == 3:

                        log.write('RINEX Version 3 \n')
                        #if rate == 'high':
                        #    csrate = '01' # high rate assumes 1-sec
                        #else:
                        csrate = '{:02d}'.format(srate)
                        print(csrate)
                        streamid = '_' + stream  + '_'
                        # this can be done in a function now ...
                        r3cmpgz = station9ch + streamid + str(year) + cdoy + '0000_01D_' + csrate + 'S_MO.crx.gz'
                        r3 = station9ch + streamid + str(year) + cdoy + '0000_01D_' + csrate + 'S_MO.rnx'
                        r3gz = station9ch + streamid + str(year) + cdoy + '0000_01D_' + csrate + 'S_MO.rnx.gz'
                        r2 = station + cdoy + '0.' + cyy + 'o'
                        if os.path.exists(r3cmpgz):
                            log.write('Trying to translate  {0:s} \n'.format(r3cmpgz))
                            deletecrx = True
                            translated, rnx_filename = go_from_crxgz_to_rnx(r3cmpgz,deletecrx)
                        if os.path.exists(r3gz):
                            log.write('Trying to gunzip {0:s} \n'.format( r3gz))
                            subprocess.call(['gunzip', r3gz])
                        # have not found the rinex 3 file
                        if not os.path.exists(r3):
                            local_rinex3_dir  = xdir + '/' + cyyyy + '/rinex/' + station + '/'
                            log.write('Trying  to look for RINEX 3 file in {0:s} \n'.format( local_rinex3_dir))
                            lrinex3 = local_rinex3_dir+r3
                            if os.path.exists(lrinex3):
                                subprocess.call(['cp', lrinex3, '.'])
                            else:
                                lrinex3 = local_rinex3_dir+r3cmpgz
                                if os.path.exists(lrinex3):
                                    subprocess.call(['cp', lrinex3, '.']); 
                                    deletecrx = True
                                    translated, rnx_filename = go_from_crxgz_to_rnx(r3cmpgz,deletecrx)
                        if os.path.exists(r3):
                            rinext =float(np.loadtxt(r3,usecols=0,dtype='str',max_rows=1))
                            log.write('Apparent Rinex version {0:4.2f} \n'.format( rinext))
                            if (rinext < 3):
                                log.write('Your file is not RINEX v3 or higher which is I was expecting. Exiting.\n')
                                sys.exit()

                            log.write('The RINEX 3 file exists locally {0:s} \n'.format( r3))
                            # convert to RINEX 2.11
                            fexists = g.new_rinex3_rinex2(r3,r2,dec_rate,gpsonly,log)
                            # this is so flawed.  If file exists, it should not look for it via conv2snr
                            # It looks like i was just trying to use old code here. Have added rinex2_filename parameter 
                            if fexists:
                                conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,translator, 
                                         log,errorlog, rinex2_filename=r2)
                            else:
                                log.write('Something about the RINEX 3-2 conversion did not work. No SNR file created.\n')
                        else:
                            print('You Chose the No Look Option, but did not provide the needed RINEX3 file ', r3)
                            print('I looked for files ending with rnx, rnx.gz, and crx.gz in the local directory')
                            print('I looked for files ending with rnx and crx.gz in $REFL_CODE/YYYY/rinex for your station')

                else:
                    log.write('Will seek the RINEX file from an external archive\n')
                    if version == 3:
                        fexists = False
                        rnx_filename = '' # just in  case?
                        print(station9ch, ' year:', year, ' doy:', doy, 'from: ', archive)
                        r2 = station + cdoy + '0.' + cyy + 'o'
                        rinex2exists = False; rinex3name = '';
                        if (rate == 'high'):
                            #print('Looks for 1-Hz Rinex 3 data at BKG, CDDIS, GA, the Spanish IGN, and GNET')
                            if archive == 'ga':
                                deleteOld = True
                                # this downloads RINEX 3 and converts to Rinex 2
                                r2, fexists= g.ga_highrate(station9ch,year,doy,dec_rate,deleteOld)
                                log.write('RINEX 2 file derived from the GA archive should now exist: {0:s} \n'.format(r2))
                            if archive == 'gnet':
                                rnx_filename,foundit = g.greenland_rinex3(station9ch, year, doy,stream,srate)
                                #print(rnx_filename,foundit)
                                if foundit: 
                                    log.write('The RINEX 3 file has been downloaded. Try to make {0:s} \n '.format(r2))
                                    subprocess.call(['gunzip', rnx_filename])
                                    # take off gz on the name
                                    fexists = g.new_rinex3_rinex2(rnx_filename[0:-3],r2,dec_rate,gpsonly,log)
                            if archive == 'kadaster':
                                # this code only does 1-hz data for now, so samplerate (srate) is not needed
                                rnx_filename,foundit = ch.kadaster_highrate(station9ch, year, doy,stream,dec_rate)
                                if foundit: 
                                    log.write('The RINEX 3 file has been downloaded. Try to make {0:s} \n '.format(r2))
                                    # take off gz on the name
                                    fexists = g.new_rinex3_rinex2(rnx_filename,r2,dec_rate,gpsonly,log)
                                    # delete the merged RINEX 3 if the RINEX 2.11 was made properly
                                    if fexists: 
                                        subprocess.call(['rm',rnx_filename])

                            if archive == 'cddis':
                                bad_day = g.cddis_restriction(year, doy,'cddis')
                                if not bad_day:
                                    rnx_filename,foundit = ch.cddis_highrate(station9ch, year, doy, 0,stream,dec_rate)
                                else: 
                                    log.write('Will Check for the tar version')
                                    rnx_filename,foundit = ch.cddis_highrate_tar(station9ch, year, doy, 0,stream,dec_rate)
                                    log.write('{0:s}  is returned from tar version \n'.format( rnx_filename))
                                if not foundit:
                                    print('No high-rate RINEX data were found ')
                                    foundit = False; fexists = False; rnx_file = ''
                                else:
                                    log.write('The RINEX 3 file has been downloaded from CDDIS. Now try to make {0:s} \n'.format(r2))
                                    fexists = g.new_rinex3_rinex2(rnx_filename,r2,dec_rate,gpsonly,log)
                            if archive == 'bkg':
                                # this is confusing - so the bkg variable is either IGS or EUREF
                                bad_day = g.cddis_restriction(year, doy,'bkg')
                                if not bad_day:
                                    rnx_filename,foundit = ch.bkg_highrate(station9ch, year , doy, 
                                                                           0,stream,dec_rate,bkg,timeout=timeout)
                                else:
                                    log.write('Will Check for the tar version')
                                    rnx_filename,foundit = ch.bkg_highrate_tar(station9ch, year, doy, 
                                                                               0,stream,dec_rate,bkg,timeout=timeout)
                                if foundit:
                                    log.write('The RINEX 3 file has been downloaded from BKG. Now try to make {0:s} \n'.format(r2))
                                    fexists = g.new_rinex3_rinex2(rnx_filename,r2,dec_rate,gpsonly,log)
                            if archive == 'ignes':
                                bad_day = g.cddis_restriction(year, doy,'bkg')
                                if not bad_day:
                                    rnx_filename,foundit = ch.esp_highrate(station9ch, year, doy, 0,stream,dec_rate)
                                else:
                                    print('No high-rate RINEX data will be downloaded from IGN ES')
                                    foundit = False; fexists = False; rnx_file = ''
                                if foundit:
                                    log.write('The RINEX 3 file has been downloaded from IGN ES. Now try to make {0:s} \n'.format(r2))
                                    fexists = g.new_rinex3_rinex2(rnx_filename,r2,dec_rate,gpsonly,log)

                        else:
                            log.write('Looking for lowrate RINEX 3 files')
                            #  I do not think this 'all' option is even allowed anymore.  
                            #if (archive == 'all'):
                            if False:
                                file_name,foundit = k.universal_all(station9ch, year, doy,srate,stream,screenstats)
                                if (not foundit): # try again
                                    file_name,foundit = k.universal_all(station9ch, year, doy, srate,k.swapRS(stream),screenstats)
                            else:
                                # check both stream parameters
                                file_name,foundit = k.universal(station9ch, year, doy, archive,srate,stream)
                                if (not foundit): # try again
                                    file_name,foundit = k.universal(station9ch, year, doy, archive,srate,k.swapRS(stream))
                            if foundit: # version 3 found - now need to gunzip, then hatanaka decompress
                                if archive == 'nz':
                                    rnx_filename = file_name
                                    log.write('Skip Hatanaka/gunzip, {0:s}'.format(rnx_filename))
                                    translated = True
                                else:
                                    deletecrx = True # no point keeping this around
                                    translated, rnx_filename = go_from_crxgz_to_rnx(file_name,deletecrx)
                            # now make rinex2
                                if translated:
                                    log.write('The RINEX 3 file has been downloaded. Now try to make {0:s} \n'.format(r2))
                                    fexists = g.new_rinex3_rinex2(rnx_filename,r2,dec_rate,gpsonly,log)
                        # this means the rinex 2 version exists
                        if fexists:
                            log.write('RINEX 2 created from v3 and {0:4.0f} {1:3.0f}. Now remove RINEX 3 files and convert \n'.format(year,doy))
                            subprocess.call(['rm', '-f',rnx_filename]) # rnx
                             # should send it the version 2 name
                            conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,
                                      translator,log,errorlog,rinex2_filename=r2)
                        else:
                            log.write('Unsuccessful RINEX 3 retrieval/translation for year-doy {0:4.0f} {1:3.0f} \n'.format(year, doy))
                    else:
                        print(station, ' year:', year, ' doy:', doy, ' from: ', archive, ' rate:', rate, ' orb:', orbtype)
                        # for version 2, since i was using old code, the RINEX 2.11 searching goes on in conv2snr
                        conv2snr(year, doy, station, isnr, orbtype,rate,dec_rate,archive,translator,log,errorlog)


def conv2snr(year, doy, station, option, orbtype,receiverrate,dec_rate,archive,translator,log,errorlog,**kwargs):
    """
    This code originally picked up and translated files. You can now optionally send 
    a parameter called rinex2_filename if the file exists. This needs to be done especially for RINEX 3
    which have been converted to RINEX 2.11


    2024 March 29: change location of logs directory to below REFL_CODE

    2024 October 16: logs are created earlier now and locations are sent to this file


    Parameters
    ----------
    year : int
        full year
    doy : int
        day of year
    option : int
        snr choice (66, 99 etc)
    orbtype : str
        orbit source (nav, gps, gnss, etc)
    receiverrate : int
        sampling interval of the GPS receiver, e.g. 1, 30, 15
    dec_rate : int
        decimation value to reduce file size
    archive : str
        external location (archive) of the rinex files
    translator : str
         hybrid, python, or fortran
    log : fileid
        for screen messages
    errorlog : str
        location of fortran logs

    """

    r2_filename = kwargs.get('rinex2_filename','')

    xdir = os.environ['REFL_CODE']

    # universal location for the log directory
    #logdir, logname = g.define_logdir(station,year,doy)

    exedir = os.environ['EXE'] # location of executables for fortran people

    screenstats = True # hopefully most goes to a file now

    #general_log = logdir + '/' + logname + '.gen'
    #print('Minimal feedback is written to ', general_log)
    #errorlog = logdir + '/' + logname

    #log = open(general_log, 'w+') this file is now opened earlier
    log.write("Receiver rate: {0:5s} \n".format(receiverrate))
    log.write("Decimation rate: {0:3.0f} \n".format(dec_rate))
    log.write("Archive : {0:10s} \n".format(archive))
    log.write("Orbit option : {0:10s} \n".format(orbtype))
    log.write("Translator : {0:10s} \n".format(translator))
    csnr = str(option)
    # should be using a function for this
    cyyyy,cyy,cdoy = g.ydoych(year,doy)

    snrname_full =  quickname(station,year,cyy,cdoy,csnr)
    log.write("Creating : {0:s} \n".format(snrname_full))

    snrname_compressed = ''

    # if it exists, you should not have gotten to this code...
    snre = False
    #snrname_full, snrname_compressed, snre = g.define_and_xz_snr(station,year,doy,option)

    # use a local definition of fortran now that we are only using translator variable from
    # the functions that call conv2snr
    # 
    fortran = False
    if translator == 'fortran':
        fortran == True

    if (snre == True):
        log.write("The snrfile already exists: {0:50s} \n".format(snrname_full))
        #print("The snrfile already exists: ", snrname_full)
    else:
        log.write("The snrfile does not exist: {0:50s} \n".format(snrname_full))
        d = g.doy2ymd(year,doy);
        month = d.month; day = d.day
        # new function to do the whole orbit thing - but it assumes ultra is hour zero?
        foundit, f, orbdir, snrexe = g.get_orbits_setexe(year,month,day,orbtype,fortran)
        # if you have the orbit file, you can get the rinex file. First lets define the expected names
        if foundit:
            print('Orbit file: ', f)
            # now you can look for a rinex file
            rinexfile,rinexfiled = g.rinex_name(station, year, month, day)
            # This goes to find the rinex file. I am changing it to allow
            # an archive preference
            if len(r2_filename) > 0:
                log.write('In principle this RINEX 2.11 file exists: {0:s} \n'.format(r2_filename))
                # further down code wnats it called rinexfile ... so let's play along
                rinexfile = r2_filename
            else:
                print('the RINEX 2.11 file does not yet exist, so will look for it')
                if receiverrate == 'high':
                    strip_snr = False # for now -
                    file_name, foundit = k.rinex2_highrate(station, year, doy,archive,strip_snr)
                else:
                # added karnak librariies
                    if (archive == 'all'):
                        foundrinex = False
                        # removed sonel from all option in version 3.10.1
                        for archivechoice in ['unavco','sopac']:
                            if (not foundrinex):
                                file_name,foundrinex = k.universal_rinex2(station, year, doy, archivechoice,screenstats)
                    else:
                        file_name,foundrinex = k.universal_rinex2(station, year, doy, archive,screenstats)

                    if foundrinex: #uncompress etc  to make o files ...
                        rinexfile, foundit2 = k.make_rinex2_ofiles(file_name) # translate

#           define booleans for various files
            oexist = os.path.isfile(orbdir + '/' + f) == True
            rexist = os.path.isfile(rinexfile) == True
            exc = exedir + '/teqc'
            texist = os.path.isfile(exc) == True
            if rexist:
                # decimate using teqc  if you have it
                if (texist) and (fortran) and (dec_rate > 0):
                    log.write("Decimating using teqc:  {0:3.0f}  seconds \n".format(dec_rate))
                    log.write('Unfortunately teqc removes Beidou data. Eventually I will remove this. \n')
                    rinexout = rinexfile + '.tmp'; cdec = str(dec_rate)
                    fout = open(rinexout,'w')
                    subprocess.call([exc, '-O.dec', cdec, rinexfile],stdout=fout)
                    fout.close() # needed?
                    status = subprocess.call(['mv','-f', rinexout, rinexfile])
            # if orbits and rinexfile exist
            if (oexist) and (rexist):
                snrname = g.snr_name(station, year,month,day,option)
                orbfile = orbdir + '/' + f
                # almost everyone uses hybrid. python only is heavily discouraged because
                # it is too slow. 
                if translator == 'hybrid':
                    g.make_snrdir(year,station) # make sure output directory exists
                    in1 = g.binary(rinexfile)
                    in2 = g.binary(snrname) # this file is made locally and moved later
                    in3 = g.binary(orbfile)
                    if (len(snrname) > 132) or (len(orbfile) > 132):
                        print('The orbit or SNR file name you are using is too long.')
                        print('Make your environment variable names shorter.')
                        return
                    in4 = g.binary(str(option))
                    if (dec_rate > 0):
                        decr = str(dec_rate)
                    else:
                        decr = '0'
                    in5 = g.binary(decr) # decimation can be used in hybrid option
                    message = 'None '

                    in6 = g.binary(errorlog)
                    log.write('SNR file {0:50s} \n will use hybrid of python and fortran to make \n'.format( snrname))
                    # these are calls to the fortran codes that are called from python
                    if (orbtype  == 'gps') or ('nav' in orbtype):
                        gpssnr.foo(in1,in2,in3,in4,in5,in6)
                    else:
                        if orbtype in ['ultra', 'wum', 'wum2']:
                            print('Using an ultrarapid orbit')
                            gnsssnrbigger.foo(in1,in2,in3,in4,in5,in6)
                        else:
                            gnsssnr.foo(in1,in2,in3,in4,in5,in6)
                else:
                    if (translator == 'fortran'):
                        t1=time.time()
                        try:
                            #subprocess.call([snrexe, rinexfile, snrname, orbfile, str(option)])
                            log.write('Using standalone fortran for translation  - separate log is used for stdout \n')
                            flogname = errorlog

                            flog = open(flogname, 'w+')
                            a=subprocess.run([snrexe, rinexfile, snrname, orbfile, str(option)],capture_output=True,text=True)
                            ddd = a.stdout; flog.write(ddd); flog.close()
                            status = subprocess.call(['rm','-f', rinexfile ])
                            status = subprocess.call(['xz', orbfile])
                        except:
                            log.write('Problem with making SNR file, check log {0:50s} \n'.format(flogname))
                        t2=time.time()
                    else:
                        log.write('SNR file {0:50s} \n will use python to make \n'.format( snrname))
                        log.write('Decimating will be done here instead of using teqc \n')
                        t1=time.time()
                        # i think this uses the strandberg way
                        rnx2snr(rinexfile, orbfile,snrname,option,year,month,day,dec_rate,log)
                        t2=time.time()

                # remove the rinex file
                subprocess.call(['rm', '-f',rinexfile])

                if os.path.isfile(snrname):
#                make sure it exists and is non-zero size before moving it
                    if (os.stat(snrname).st_size == 0):
                        log.write('you created a zero file size which could mean a lot of things \n')
                        log.write('bad exe, bad snr option, do not really have the orbit file \n')
                        status = subprocess.call(['rm','-f', snrname ])
                    else:
                        log.write('A SNR file was created : {0:50s}  \n'.format(snrname_full))
                        print('\n')
                        print('SUCCESS: SNR file was created \n', snrname_full)
                        g.store_snrfile(snrname,year,station)
                        subprocess.call(['gzip', snrname_full])

                else:
                    # not sure why this is made here??? wasn't it created earlier?
                    print('No SNR file created - check error logs - locations were printed to screen')
            else:
                print('Either the RINEX file or orbit file does not exist, so there is nothing to convert')
                log.write('Either the RINEX file or orbit file does not exist, so there is nothing to convert \n')
        else:
            print('The orbit file you requested does not exist.')

    log.close()
    # 

    return True

def satorb(week, sec_of_week, ephem):
    """
    Calculate GPS satellite orbits

    Parameters
    ----------
    week : integer
        GPS week

    sec_of_week : float
        GPS seconds of the week

    ephem : ephemeris block

    Returns
    -------
    numpy array
         the x,y,z, coordinates of the satellite in meters
         and relativity correction (also in meters), so you add, not subtract

    """

# redefine the ephem variable
    prn, week, Toc, Af0, Af1, Af2, IODE, Crs, delta_n, M0, Cuc,\
    ecc, Cus, sqrta, Toe, Cic, Loa, Cis, incl, Crc, perigee, radot, idot,\
    l2c, week, l2f, sigma, health, Tgd, IODC, Tob, interval = ephem
    sweek = sec_of_week
    # semi-major axis
    a = sqrta**2
    t = week*7*86400+sweek
    tk = t-Toe
    # no idea if Ryan Hardy is doing this correctly - it should be in a function
    tk  =  (tk - 302400) % (302400*2) - 302400
    n0 = np.sqrt(constants.mu/a**3)
    n = n0+ delta_n
    Mk = M0 + n*tk
    i = 0
    Ek = Mk
    E0 = Mk + ecc*np.sin(Mk)
    # solve kepler's equation
    while(i < 3 or np.abs(Ek-E0) > 1e-12):
        i +=1
        Ek = Mk + ecc*np.sin(E0)
        E0 = Mk + ecc*np.sin(Ek)
    nuk = np.arctan2(np.sqrt(1-ecc**2)*np.sin(Ek),np.cos(Ek)-ecc)
    Phik = nuk + perigee
    duk = Cus*np.sin(2*Phik)+Cuc*np.cos(2*Phik)
    drk = Crs*np.sin(2*Phik)+Crc*np.cos(2*Phik)
    dik = Cis*np.sin(2*Phik)+Cic*np.cos(2*Phik)
    uk = Phik + duk
    rk = a*(1-ecc*np.cos(Ek))+drk

    ik = incl+dik+idot*tk
    xkp = rk*np.cos(uk)
    ykp = rk*np.sin(uk)
    Omegak = Loa + (radot-constants.omegaEarth)*tk -constants.omegaEarth*Toe
    xk = xkp*np.cos(Omegak)-ykp*np.cos(ik)*np.sin(Omegak)
    yk = xkp*np.sin(Omegak)+ykp*np.cos(ik)*np.cos(Omegak)
    zk = ykp*np.sin(ik)
    # try this
    return np.array([xk, yk, zk])


def rnx2snr(obsfile, navfile,snrfile,snroption,year,month,day,dec_rate,log):
    """
    Converts a rinex v2.11 obs file using Joakim's rinex reading code

    Parameters
    ----------
    obsfile : str
        RINEX 2.11 filename
    navfile : str
        navigation file

    snrfile : str
        SNR filename

    snroption: integer
        kind of SNR file requested

    year : int
        full year
    month : int
        calendar month
    day : int
        calendar day
    dec_rate : int
        decimation rate in seconds

    """
    station = obsfile[0:4]
    #logname = 'logs/' + station + 'python.txt'
    #log = open(logname, 'w+')
    last3 = navfile[-3::]
    # figure out if you have a nav file or a sp3 file
    orbtype = 'sp3' # assume it is sp3
    if (last3 != 'SP3') and (last3 != 'sp3'):
        orbtype = 'nav'
    log.write("Orbit type {0:4s} \n".format(orbtype))
    log.write("File name {0:50s} \n".format(navfile))
    # these are the elevation angle limits I have been using for the various SNR formats
    emin,emax = elev_limits(snroption)

    exitQ = False
    obsdata, systemsatlists, prntoidx, obstypes, header, obstimes,gpstime = rinpy.processrinexfile(obsfile)
    obsdata = rinpy.separateobservables(obsdata, obstypes)
    obslist = obstypes['G'][:]
    # need to check to see what happens without coordinates
    key = 'APPROX POSITION XYZ'
    if key in header.keys():
        log.write('Cartesian coordinates are in the RINEX Header \n')
    else:
        log.write('RINEX file does not have station coordinates. Exiting \n')
        print('RINEX file does not have station coordinates. This is illegal. Exiting')
        return
    rv =  header['APPROX POSITION XYZ']
    recv = [float(i) for i in rv.split()]
    recv = np.array(recv)
    log.write("XYZ from header {0:15.5f} {1:15.5f} {2:15.5f} \n".format(recv[0],recv[1],recv[2]))
    if np.sum(np.abs(recv)) < 5:
        print('Your receiver coordinates are in the middle of the Earth. Exiting.')
        exitQ = True
        return

    lat, lon, h = g.xyz2llh(recv,1e-8) # returns lat/lon in radians
    up,East,North = g.up(lat,lon) # returns unit vector for UP


# set defaults
    s5exist = False; s1exist = False; s2exist = False;
    if 'S1' in obslist :
        s1exist = True
    if 'S2' in obslist :
        s2exist = True
    if 'S5' in obslist :
        s5exist = True
    if not s1exist and not s2exist:
        log.write('There are no S1 and no S2 data - this file is not useful for reflectometry \n')
        exitQ = True
    if (orbtype == 'nav'):
        gpssatlist = systemsatlists['G'][:]
        #print('GPS satellite list', gpssatlist)
        navorbits(navfile,obstimes,obsdata,obslist,prntoidx,gpssatlist,snrfile,s1exist,s2exist,s5exist,up,East,North,emin,emax,recv,dec_rate,log)
    else:
        log.write('Read the sp3 file \n'); sp3 = g.read_sp3file(navfile)
        _testing_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day,emin,emax,snrfile,up,East,North,recv,dec_rate,log)
        #_test_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day,emin,emax,snrfile,up,East,North,recv,dec_rate,log)

    #print('Closing python RINEX conversion log file:',logname)
    #log.close()

def navorbits(navfile,obstimes,observationdata,obslist,prntoidx,gpssatlist,snrfile,s1exist,s2exist,s5exist,up,East,North,emin,emax,recv,dec_rate,log):
    """
    Strandberg nav reading file?

    Parameters
    ---------
    navfile : string

    obstimes : ??

    observationdata :

    obslist :

    prn2oidx :

    gpssatlist :

    snrfile : str
        name of the output file

    s1exist :

    s2exist :

    s5exist :

    This is for GPS only files !
    navfile is nav broadcast ephemeris in RINEX format
    inputs are rinex info, obstimes, observationdata,prntoidx,gpssatlist
    various bits about SNR existence
    snrfile is output name
    log is for screen outputs - now going to a file
    """
    log.write('reading the ephemeris data \n')
    ephemdata = g.myreadnav(navfile)
    if len(ephemdata) == 0:
        log.write("Empty ephemeris or the file does not exist \n")
        return

    # change variable name to save typing
    a=obstimes
    if True:
        log.write('Opening output file for the SNR data \n')
        fout = open(snrfile, 'w+')
        K=len(obstimes)
        log.write('Number of epochs in the RINEX file {0:6.0f} \n '.format( K))
        log.write('Decimation rate {0:3.0f} \n'.format(dec_rate))

        with Bar('Processing RINEX', max=K,fill='@',suffix='%(percent)d%%') as bar:
            for i in range(0,K):
                bar.next()
                if np.remainder(i,200) == 0:
                    log.write('Epoch {0:6.0f} \n'.format( i))
            # sod is seconds of the day
                sod = 3600*a[i].hour + 60*a[i].minute + a[i].second
                if dec_rate > 0:
                    rem = sod % dec_rate
                else:
                    rem = 0
                if (rem == 0):
                    gweek, gpss = g.kgpsweek(a[i].year, a[i].month, a[i].day, a[i].hour, a[i].minute, a[i].second)
                    for sat in gpssatlist:
                        s1,s2,s5 = readSNRval(s1exist,s2exist,s5exist,observationdata,prntoidx,sat,i)
                        if (s1 > 0):
                            closest = g.myfindephem(gweek, gpss, ephemdata, sat)
                            if len(closest) > 0:
                                satv = satorb_prop(gweek, gpss, sat, recv, closest)
                                r=np.subtract(satv,recv) # satellite minus receiver vector
                                eleA = g.elev_angle(up, r)*180/np.pi
                                azimA = g.azimuth_angle(r, East, North)
                                if (eleA >= emin) and (eleA <= emax):
                                    fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} \n".format(sat,eleA, azimA, sod,0, 0, s1,s2, s5))
        fout.close()
    else:
        log.write('There was some kind of problem with your file, exiting ...\n')
        print('There was some kind of problem with your file, exiting ...')

def readSNRval(s1exist,s2exist,s5exist,observationdata,prntoidx,sat,i):
    """
    what it looks like only reads GPS data for now
    interface between Joakim's code and mine ...

    Parameters
    ----------
    s1exist : boolean

    s2exist : boolean

    s5exist : boolean

    Returns
    -------
    s1 :
    s2 :
    s5 :

    """
    s1 = 0; s2 = 0; s5 = 0 # set defaults
    if s1exist:
        s1 = observationdata['G']['S1'][i, prntoidx['G'][sat]]
        if np.isnan(s1):
           s1 = 0
    if s2exist:
        s2 = observationdata['G']['S2'][i, prntoidx['G'][sat]]
        if np.isnan(s2):
            s2 = 0
    if s5exist:
        s5 = observationdata['G']['S5'][i, prntoidx['G'][sat]]
        if np.isnan(s5):
            s5 = 0
    return s1, s2, s5


def satorb_prop(week, secweek, prn, rrec0, closest_ephem):
    """
    Calculates and returns geometric range (in metres) given
    time (week and sec of week), prn, receiver coordinates (cartesian, meters)
    this assumes someone was nice enough to send you the closest ephemeris
    returns the satellite coordinates as well, so you can use htem
    in the A matrix

    Parameters
    ----------
    week : integer
        GPS week

    secweek : integer
        GPS second of the week

    prn : integer
        satellite number

    rrec0 : 3vector
        receiver coordinates, meters

    Returns
    -------
    SatOrbn : 3vector
        floats, Cartesian location of satellite in meters [x,y,z]

    """
    error = 1

    # might as well start with 70 milliseconds
    SatOrb = satorb(week, secweek-0.07, closest_ephem)
    # first estimate of the geometric range
    geo= g.norm(SatOrb-rrec0)

    deltaT = g.norm(SatOrb - rrec0)/constants.c
    k=0
    #while (error > 1e-8) or (k < 2):
    # should not need more than two iterations, since i am
    #starting with 70 msec
    while (k < 2):
        SatOrb = satorb(week, secweek-deltaT, closest_ephem)
        Th = -constants.omegaEarth * deltaT
        xs = SatOrb[0]*np.cos(Th)-SatOrb[1]*np.sin(Th)
        ys = SatOrb[0]*np.sin(Th)+SatOrb[1]*np.cos(Th)
        SatOrbn = [xs, ys, SatOrb[2]]
        # try this ???
        geo = g.norm(SatOrbn-rrec0)
        deltaT_new = g.norm(SatOrbn-rrec0)/constants.c
        error = np.abs(deltaT - deltaT_new)
        deltaT = deltaT_new
        k += 1
    return SatOrbn


def satorb_prop_sp3(iX,iY,iZ,recv,Tp,ij):
    """
    for satellite number prn
    and receiver coordinates rrec0
    find the x,y,z coordinates at time secweek

    Parameters
    ----------
    iX : float

    iY : float

    iZ : float
    recv : 3 vector, float

    Tp :

    ij :

    sp3 has the orbit information in it
    """
    # start wit 70 milliseconds as the guess for the transmission time
    nx = iX(Tp[ij]-0.07); ny = iY(Tp[ij]-0.07); nz = iZ(Tp[ij]-0.07)
    oE = constants.omegaEarth
    c = constants.c
    # get initial deltaA
    SatOrb=np.array([nx,ny,nz]).T
    r=np.subtract(SatOrb,recv)
    tau = g.norm(r)/c

    error = 0
    k = 0
    while (k < 2):
        nx = iX(Tp[ij]-tau); ny = iY(Tp[ij]-tau); nz = iZ(Tp[ij]-tau)
        SatOrb=np.array([nx,ny,nz]).T
        Th = -oE * tau
        xs = SatOrb[0]*np.cos(Th)-SatOrb[1]*np.sin(Th)
        ys = SatOrb[0]*np.sin(Th)+SatOrb[1]*np.cos(Th)
        SatOrbn = np.array([xs, ys, SatOrb[2]]).T
        tau=g.norm(SatOrbn-recv)/c
        k+=1

    return SatOrbn

def _test_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day, emin,emax,outputfile,up,East,North,recv,dec_rate,log):
    """
    inputs are gpstime( numpy array with week and sow)
    sp3 is what has been read from the sp3 file
    columsn are satNu, week, sow, x, y, z (in meters)
    log is for comments
    """
    checkD = False
    if dec_rate > 0:
        checkD = True
        log.write('You are decimating \n')
    # epoch at the beginning of the day of your RINEX file
    gweek0, gpssec0 = g.kgpsweek(year, month,day,0,0,0 )

    ll = 'quadratic'
#   will store in this variable, then sort it before writing out to a file
    saveit = np.empty(shape=[0,11] )
    fout = open(outputfile, 'w+')
    for con in ['G','E','R','C']:
        if con in obstypes:
            log.write('Good news - found data for constellation {0:s} \n'.format( con))
            obslist = obstypes[con][:]
            satlist = systemsatlists[con][:]
            #print(satlist)
            for prn in satlist:
                addon = g.findConstell(con) # 100,200,or 300 for R,E, and C
                log.write('Constellation {0:1s} Satellite {1:2.0f}  Addon {2:3.0f} \n'.format( con, prn, addon))
                # window out the data for this satellite
                m = sp3[:,0] == prn + addon
                x = sp3[m,3]
                if len(x) > 0:
                    sp3_week = sp3[m,1] ; sp3_sec = sp3[m,2]
                    x = sp3[m,3] ; y = sp3[m,4] ; z = sp3[m,5]
                # fit the orbits for this satellite
                    t=sp3_sec
                    iX= interp1d(t, x, ll,bounds_error=False,fill_value='extrapolate')
                    iY= interp1d(t, y, ll,bounds_error=False,fill_value='extrapolate')
                    iZ= interp1d(t, z, ll,bounds_error=False,fill_value='extrapolate')
        # get the S1 data for this satellite
                    if 'S1' in obslist:
                        s1 = obsdata[con]['S1'][:, prntoidx[con][prn]]

        # indices when there are no data for this satellite
                    ij = np.isnan(s1)
        # indices when there are data in the RINEX file - this way you do not compute
        # orbits unless there are data.
                    not_ij = np.logical_not(ij)
                    Tp = gpstime[not_ij,1] # only use the seconds of the week for now
                    s1 = s1[not_ij];
                    #print(s1.shape)
                    emp = np.zeros(shape=[len(s1),1],dtype=float)
        # get the rest of the SNR data in a function
                    s2,s5,s6,s7,s8 = extract_snr(prn, con, obslist,obsdata,prntoidx,not_ij,emp)

        # make sure there are no nan values in s2 or s5

                    nepochs = len(Tp)
                    for ij in range(0,nepochs):
                        TT = 0 # default value
                        if checkD:
                            TT = Tp[ij]  % dec_rate # get the modulus
                        if TT == 0:
                            SatOrb = satorb_prop_sp3(iX,iY,iZ,recv,Tp,ij)
                            r=np.subtract(SatOrb,recv)
                            azimA = g.azimuth_angle(r, East, North)
                            eleA = g.elev_angle(up, r)*180/np.pi
                            # 2021 october 26
                            # thank you to andrea gatti for pointing out the mistake
                            if (eleA >= emin) and (eleA <= emax):
                                fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} {9:7.2f} {10:7.2f} \n".format(
                                    prn+addon,eleA,azimA,Tp[ij]-gpssec0, 0,float(s6[ij]),s1[ij],float(s2[ij]),float(s5[ij]),float(s7[ij]),float(s8[ij]) ))
                                #fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} {9:7.2f} {10:7.2f} \n".format(
                                #    prn+addon,eleA,azimA,Tp[ij]-gpssec0, 0,float(s6[ij]),s1[ij],float(s2[ij]),float(s5[ij]),float(s6[ij]),float(s7[ij]) ))
                else:
                    log.write('This satellite is not in the orbit file. {0:3.0f} \n'.format(prn))
        else:
            log.write('No data for constellation {0:1s} \n'.format(con))
    # print('sort by time')
    # tried saving to variable but it was very slow
    #ne = np.array([prn,eleA,azimA,Tp[ij],0,0,s1[ij],s2[ij],s5[ij],0,0])
    #saveit = np.vstack((saveit,ne))
    #i = np.argsort(saveit[:,3])
    # apply that sort to variable with shorter name
    #s = saveit[i,:]
    log.write('write SNR data to file \n')
    fout.close()


def extract_snr(prn, con, obslist,obsdata,prntoidx,not_ij,emp):
    """
    """
    # defaults are zero arrays
    s2 = emp; s5 = emp; s6 = emp; s7 = emp; s8 = emp
    if 'S2' in obslist:
        s2 = obsdata[con]['S2'][:, prntoidx[con][prn]]
        s2 = s2[not_ij] ; is2 = np.isnan(s2); s2[is2] = 0
    if 'S5' in obslist:
        s5 = obsdata[con]['S5'][:, prntoidx[con][prn]]
        s5 = s5[not_ij]
        is5 = np.isnan(s5); s5[is5] = 0
    if 'S6' in obslist:
        s6 = obsdata[con]['S6'][:, prntoidx[con][prn]]
        s6 = s6[not_ij]
        is6 = np.isnan(s6); s6[is6] = 0
    if 'S7' in obslist:
        s7 = obsdata[con]['S7'][:, prntoidx[con][prn]]
        s7 = s7[not_ij]
        is7 = np.isnan(s7); s7[is7] = 0
    if 'S8' in obslist:
        s8 = obsdata[con]['S8'][:, prntoidx[con][prn]]
        s8 = s8[not_ij]

    return s2,s5,s6,s7,s8

def elev_limits(snroption):
    """
    For given SNR option, returns elevation angle limits

    Parameters
    ------------
    snroption : integer
        snr file delimeter

    Returns
    ----------
    emin: float
        minimum elevation angle (degrees)
    emax: float
        maximum elevation angle (degrees)

    """

    if (snroption == 99):
        emin = 5; emax = 30
    elif (snroption == 50):
        emin = 0; emax = 10
    elif (snroption == 66):
        emin = 0; emax = 30
    elif (snroption == 88):
        emin = 5; emax = 90
    else:
        emin = 5; emax = 30

    return emin, emax


def _testing_sp3(gpstime,sp3,systemsatlists,obsdata,obstypes,prntoidx,year,month,day, emin,emax,outputfile,up,East,North,recv,dec_rate,log):
    """
    inputs are gpstime( numpy array with week and sow)
    sp3 is what has been read from the sp3 file
    columsn are satNu, week, sow, x, y, z (in meters)
    log is for comments
    """
    checkD = False
    if dec_rate > 0:
        checkD = True
        log.write('You are decimating \n')
    # epoch at the beginning of the day of your RINEX file
    gweek0, gpssec0 = g.kgpsweek(year, month,day,0,0,0 )

    ll = 'quadratic'
#   will store in this variable, then sort it before writing out to a file
    saveit = np.empty(shape=[0,11] )
    fout = open(outputfile, 'w+')
    NsatT = 0
    # make a dictionary for constellation name
    sname ={}; sname['G']='GPS' ; sname['R'] = 'GLONASS'; sname['E'] = 'GALILEO'; sname['C']='BEIDOU'
    for con in ['G','E','R','C']:
        if con in obstypes:
            satL = len(systemsatlists[con][:])
            satS = 'Processing ' + sname[con]
            with Bar(satS, max=satL,fill='@',suffix='%(percent)d%%') as bar:
                log.write('Good news - found data for constellation {0:s} \n'.format( con))
                obslist = obstypes[con][:]
                satlist = systemsatlists[con][:]
                for prn in satlist:
                    bar.next()
                    addon = g.findConstell(con) # 100,200,or 300 for R,E, and C
                    log.write('Constellation {0:1s} Satellite {1:2.0f}  Addon {2:3.0f} \n'.format( con, prn, addon))
                # window out the data for this satellite
                    m = sp3[:,0] == prn + addon
                    x = sp3[m,3]
                    if len(x) > 0:
                        sp3_week = sp3[m,1] ; sp3_sec = sp3[m,2]
                        x = sp3[m,3] ; y = sp3[m,4] ; z = sp3[m,5]
                # fit the orbits for this satellite
                        t=sp3_sec
                        iX= interp1d(t, x, ll,bounds_error=False,fill_value='extrapolate')
                        iY= interp1d(t, y, ll,bounds_error=False,fill_value='extrapolate')
                        iZ= interp1d(t, z, ll,bounds_error=False,fill_value='extrapolate')
        # get the S1 data for this satellite
                        if 'S1' in obslist:
                            s1 = obsdata[con]['S1'][:, prntoidx[con][prn]]

        # indices when there are no data for this satellite
                        ij = np.isnan(s1)
        # indices when there are data in the RINEX file - this way you do not compute
        # orbits unless there are data.
                        not_ij = np.logical_not(ij)
                        Tp = gpstime[not_ij,1] # only use the seconds of the week for now
                        s1 = s1[not_ij];
                    #print(s1.shape)
                        emp = np.zeros(shape=[len(s1),1],dtype=float)
        # get the rest of the SNR data in a function
                        s2,s5,s6,s7,s8 = extract_snr(prn, con, obslist,obsdata,prntoidx,not_ij,emp)
        # make sure there are no nan values in s2 or s5

                        nepochs = len(Tp)
                        for ij in range(0,nepochs):
                            TT = 0 # default value
                            if checkD:
                                TT = Tp[ij]  % dec_rate # get the modulus
                            if TT == 0:
                                SatOrb = satorb_prop_sp3(iX,iY,iZ,recv,Tp,ij)
                                r=np.subtract(SatOrb,recv)
                                azimA = g.azimuth_angle(r, East, North)
                                eleA = g.elev_angle(up, r)*180/np.pi
                                if (eleA >= emin) and (eleA <= emax):
                                    # bug reported by Andrea Gatti. 2021 October 26
                                    fout.write("{0:3.0f} {1:10.4f} {2:10.4f} {3:10.0f} {4:7.2f} {5:7.2f} {6:7.2f} {7:7.2f} {8:7.2f} {9:7.2f} {10:7.2f} \n".format(
                                        prn+addon,eleA,azimA,Tp[ij]-gpssec0, 0,float(s6[ij]),s1[ij],float(s2[ij]),float(s5[ij]),float(s7[ij]),float(s8[ij]) ))
                    else:
                        log.write('This satellite is not in the orbit file. {0:3.0f} \n'.format(prn))
        else:
            log.write('No data for constellation {0:1s} \n'.format(con))
    log.write('write SNR data to file \n')
    fout.close()


def the_makan_option(station,cyyyy,cyy,cdoy):
    """
    this code checks many versions of RINEX files 
    (Z, gz, regular, hatanaka) both in the working directory and in an external rinex area
    $REFL_CODE/rinex/station/year

    turns whatever it finds into a regular RINEX file in the working directory
    that file WILL be deleted, but it will not delete those stored externally.

    Parameters
    ----------
    station : str
        station name (4 ch)
    cyyyy : str
        4 ch year
    cyy : str
        two ch year
    cdoy : str
        three ch day of year
    """
    missing = True
    crnxpath = g.hatanaka_version()  # where hatanaka will be
    r = station + cdoy + '0.' + cyy + 'o'
    rd = station + cdoy + '0.' + cyy + 'd'
    #print(r,rd)

    # this is the preferred Makan structure
    locdir=  os.environ['REFL_CODE'] + '/rinex/' + station + '/' + cyyyy + '/'
    # this is the preferred gnssrefl structure
    locdir2= os.environ['REFL_CODE'] + '/' + cyyyy + '/rinex/' + station + '/'
    #
    #locdir2= os.environ['RINEX'] + station + '/' + cyyyy + '/'
    #locdir3= os.environ['RINEX'] + station.upper() + '/' + cyyyy + '/'

    print('Will look for files in the working directory and ', locdir )
    # I was testing this ... but have not finished
    #so_many_permutations(r,rd,locdir, crnxpath)

    if os.path.exists(r):
        missing = False
        return

    if os.path.exists(r + '.gz') and missing:
        subprocess.call(['gunzip', r + '.gz'])
        missing = False
        return

    if os.path.exists(r + '.Z') and missing:
        subprocess.call(['uncompress', r + '.Z'])
        missing = False
        return

    if os.path.exists(rd) and missing:
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
            return
        else:
            g.hatanaka_warning(); 
            return

    if os.path.exists(rd + '.gz') and missing:
        subprocess.call(['gunzip', rd + '.gz'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False
            return
        else:
            g.hatanaka_warning(); return

    if os.path.exists(rd + '.Z') and missing:
        subprocess.call(['uncompress', rd + '.Z'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False; return
        else:
            g.hatanaka_warning() ; return

    makan_warning(missing, locdir + r )

    if os.path.exists(locdir + r) and missing:
        subprocess.call(['cp', '-f',locdir + r,'.'])
        missing = False
        return

    makan_warning(missing, locdir + r + '.gz')

    if os.path.exists(locdir + r + '.gz') and missing:
        #print('type 8')
        subprocess.call(['cp', '-f',locdir + r + '.gz' ,'.'])
        subprocess.call(['gunzip', r + '.gz'])
        missing = False; return

    makan_warning(missing, locdir + r + '.Z')

    if os.path.exists(locdir + r + '.Z') and missing:
        subprocess.call(['cp', '-f',locdir + r + '.Z','.'])
        subprocess.call(['uncompress', r + '.Z'])
        missing = False ; return

    makan_warning(missing, locdir + rd )

    if os.path.exists(locdir + rd) and missing:
        subprocess.call(['cp','-f',locdir + rd,'.'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False ; return
        else:
            g.hatanaka_warning(); return

    makan_warning(missing, locdir + rd + '.Z')

    if os.path.exists(locdir + rd + '.Z') and missing:
        subprocess.call(['cp','-f',locdir + rd + '.Z','.'])
        subprocess.call(['uncompress', rd + '.Z'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False ; return
        else:
            g.hatanaka_warning();

    makan_warning(missing, locdir + rd + '.gz')

    if os.path.exists(locdir + rd + '.gz') and missing:
        subprocess.call(['cp','-f',locdir + rd + '.gz','.'])
        subprocess.call(['gunzip',rd + '.gz'])
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            subprocess.call(['rm',rd])
            missing = False ; return
        else:
            g.hatanaka_warning() ; return

def makan_warning(missing, f):
    """
    Writes a warning for the makan option which checks for non-standard RINEX file names

    Parameters
    ----------
    missing: bool
        whether file is missing
    f : str
        filename as defined by Makan

    """
    if missing:
        print('Makan option, checking : ', f)

    return

def go_from_crxgz_to_rnx(c3gz,deletecrx=True):
    """
    checks to see if rinex3 file exists, gunzip if necessary,
    run hatanaka, if necessary

    Parameters
    ----------
    c3gz : str
        filename for a gzipped RINEX 3 Hatanaka file

    deletecrx = bool
        whether to delete the crx file

    Returns
    -------
    translated : bool
        if file successfully found and available

    rnx : str
        name of gunzipped and decompressed RINEX 3

    """
    translated = False # assume failure
    c3 = c3gz[:-3] # crx filename
    rnx = c3.replace('crx','rnx') # rnx filename
    # gunzip
    if os.path.exists(c3gz):
        subprocess.call(['gunzip', c3gz])

    # executable
    crnxpath = g.hatanaka_version()
    if not os.path.exists(crnxpath):
        g.hatanaka_warning()
    else:
        if os.path.exists(c3): # file exists
            subprocess.call([crnxpath,c3])
    if os.path.exists(rnx): # file exists
        translated = True
        if deletecrx:
            #print('remove Hatanaka compressed file')
            subprocess.call(['rm','-f',c3])

    return translated, rnx

def get_local_rinexfile(rfile,localpath2):
    """
    look for a plain or gzipped version of the RINEX 2.11 file in the year subdirectories
    copies it to the local directory.  this method stops the code from deleting your rinex 
    files. As of 2023 September 19, it should also look for Hatanaka files.

    localpath2 =  os.environ['REFL_CODE'] + '/' + cyyyy + '/rinex/' + station + '/'

    This is unlikely to work for uppercase RINEX files. Try the mk option

    Parameters
    ----------
    rfile : str
        version2 rinexfile name

    localpath2 : str
        another location of the file (meant to be as defined above)

    Returns
    -------
    allgood : bool
        whether file found
    """
    crnxpath = g.hatanaka_version()
    allgood = False
    # hatanaka filename has d at end instead of o
    rd = rfile[0:-1] + 'd'
    curlocal= os.getcwd() + '/'

    # look for gzip version in local directory first
    print('Looking for file: ', curlocal + rfile + '.gz')
    if os.path.exists(rfile + '.gz'):
        print('found ', curlocal + rfile + '.gz')
        subprocess.call(['gunzip', rfile + '.gz'])
        allgood = True; return allgood


    # then look for unix compressed version local directory 
    if not allgood:
        print('Looking for file: ', curlocal + rfile + '.Z')
    if os.path.exists(rfile + '.Z') and not allgood:
        print('found ', rfile + '.Z')
        subprocess.call(['uncompress', rfile + '.Z'])
        allgood = True  ; return allgood

    if not allgood:
        print('Looking for file: ', curlocal+rd)
    # then look for hatanaka compressed version local directory 
    if os.path.exists(rd) and not allgood:
        print('found ', curlocal+rd)
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath,rd])
            if os.path.exists(rfile):
                allgood = True
                subprocess.call(['rm',rd])
                return allgood

    # then look for hatanaka compressed and unix compressed version local directory 
    if os.path.exists(rd + '.Z') and not allgood:
        print('found ', curlocal +rd + '.Z')
        if os.path.exists(crnxpath):
            subprocess.call(['uncompress', rd + '.Z'])
            subprocess.call([crnxpath,rd])
            if os.path.exists(rfile):
                allgood = True
                subprocess.call(['rm',rd])
                return allgood

    # now check in 
    if not allgood:
        r = localpath2 + rfile
        print('Now looking for the file in : ', r)
        # hatanaka version in REFL_CODE
        rdd = localpath2 + rd

        if os.path.exists(r):
            allgood = True
        # cp to the local directory
            print('copying RINEX file to local area')
            subprocess.call(['cp',r,'.'])
            return allgood
        else:
       # did not find normal rinex, so look for gzip version
            print('Now looking for the file in : ', r + '.gz')
            if os.path.exists(r + '.gz'):
                subprocess.call(['gunzip', r + '.gz'])
                if os.path.exists(r):
                    print('copying RINEX file to local area')
                    subprocess.call(['cp',r,'.'])
                    # now gzip the original file ...
                    subprocess.call(['gzip', r ])
                    allgood = True; return allgood
            # if hatanaka is stored locally
            if not allgood:
                print('Now looking for the file in : ', rdd )
            if os.path.exists(rdd) and not allgood:
                # copy from REFL_CODE to local dir
                # and convert
                print('found ', rdd)
                print('copying Hatanaka file to local area')
                subprocess.call(['cp',rdd,'.'])
                subprocess.call([crnxpath,rd])
                if os.path.exists(rfile):
                    allgood = True
                    subprocess.call(['rm',rd])
                    return allgood

    return allgood

def print_archives():
    """
    feeble attempt to print list of archives to screen ...

    """
    archive_list_rinex3 = ['unavco', 'cddis', 'bev', 'bkg', 'ga', 'epn', 'bfg','sonel','all','nrcan','gfz','ignes']
    archive_list = ['sopac', 'unavco', 'sonel',  'nz', 'ga', 'bkg', 'jeff',
                    'ngs', 'nrcan', 'special', 'bev', 'jp', 'all','cddis']
    w = 'RINEX 3 archives '
    for i in range(0,len(archive_list_rinex3)):
        w = w + archive_list_rinex3[i] + ' '
    w = w + '\n RINEX 2.11 archives '
    for i in range(0,len(archive_list)):
        w = w + archive_list[i] + ' '
    msg = w
    return msg

def set_rinex2snr_logs(station,year,doy):
    """

    Open a file for screen messages. Return the file ID
    (was previously created elsewhere). Also determine name
    of the log used for fortran translation.

    Parameters
    ----------
    station : str
        4 ch station name
    year : int
        full year
    doy : int
        day of year

    Returns
    -------
    log : file ID

    errorlog : str
        name of the error log for fortran code

    exedir : str
        location of the executable directdory

    general_log : str
        name of the more general error log
    """

    print(station,year,doy)
    xdir = os.environ['REFL_CODE']

    # universal location for the log directory
    logdir, logname = g.define_logdir(station,year,doy)

    exedir = os.environ['EXE'] # location of executables for fortran people


    general_log = logdir  + logname + '.gen'
    #print('Feedback about the RINEX translation: ', general_log)

    errorlog = logdir +  logname
    #print('Log created by the fortran code: ', errorlog)

    log = open(general_log, 'w+')

    return log, errorlog, exedir, general_log

