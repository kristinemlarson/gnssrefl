# kristine Larson, February 2022
# library to support RINEX downloads.
# started with RINEX 3, and now adding RINEX 2
# this should replace the spaghetti code in gps.py
import datetime
import json
import os
import requests
import sys
import subprocess
import wget
from urllib.parse import urlparse
import gnssrefl.gps as g
import gnssrefl.cddis_highrate as ch

def gogetit(dir1, filename, ext):
    """
    The purpose of this function is to to download RINEX 2 files.
    The code will try to get the file and check to see if it was successful.

    Parameters
    ----------
    dir1 : str
        the main https directory address 
    filename : str
        name of the GNSS files
    ext : str
        kind of ending to the filename, (Z, gz etc)

    Returns 
    -------
    foundit : bool
        whether file was found
    f : str
        name of the file
    """
    foundit = False
    f= filename + ext
    print(dir1 + f)
    if os.path.exists(f):
        print('File is already on your disk')
        foundit = True
    else:
        try:
            wget.download(dir1+f,f)
        except:
            okok =1
        if os.path.exists(f):
            print('\n File has been found ',f)
            foundit = True

    return foundit, f

def swapRS(stream):
    """
    function that swaps R to S and vice versa for RINEX 3 files

    Parameters
    ----------
    stream : str
        RINEX 3 filename streaming acronym (S or R)

    Returns
    -------
    newstream : str
        the opposite of what was in stream

    """
    if stream == 'R':
        newstream = 'S'
    else:
        newstream = 'R'
    return newstream

def just_bkg(cyyyy, cdoy, file_name):
    """

    looks for RINEX files at BKG in two directories

    Parameters
    ----------
    cyyyy:  str
        four character year

    cdoy: str
        three character day of year

    file_name: str
        expected RINEX filename

    """
    dir1 = 'https://igs.bkg.bund.de/root_ftp/IGS/obs/' + cyyyy + '/' + cdoy + '/'
    dir2 = 'https://igs.bkg.bund.de/root_ftp/EUREF/obs/' + cyyyy + '/' + cdoy + '/'
    print('>>> Trying first : ',dir1+file_name)
    fexist = False
    try:
        wget.download(dir1+file_name,file_name)
        fexist = True
    except:
        print('did not find the file')
    if (not fexist):
        print('>>> Now trying: ',dir2+file_name)
        try:
            wget.download(dir2+file_name,file_name)
            fexist = True
        except:
            print('did not find it there either')

    return

def universal(station9ch, year, doy, archive,srate,stream,debug=False):
    """
    main code for seamless archive for RINEX 3 files ... 

    Parameters
    ----------
    station9ch : str
        nine character station name

    year : int
        year 

    doy : int
        day of year

    archive : str
        archive name

    srate : int
        receiver samplerate

    stream : str
        one character: R or S

    debug : bool
        whether debugging statements printed

    Returns
    -------
    file_name : str
        name of rinexfile

    foundit : boolean
        whether file was found

    """
    # define the file name
    print('Searching the ', archive, ' archive with rate/filetype', srate, stream)
    foundit = False

    file_name,cyyyy,cdoy = filename_plus(station9ch,year,doy,srate,stream)
    print('Filename:', file_name)
    cyy = cyyyy[2:4]
    dir1 = ''
    dir2 = ''

    # put this outside the try because I think there is one in the function
    if archive == 'bfg':
        station = station9ch[0:4] ; samplerate = srate; stream = 'R'
        g.bfg_data(station, year, doy, samplerate,debug)
        if os.path.exists(file_name):
            print('File was found: ', file_name )
            foundit = True
        else:
            print('File was not found: at bfg.')

        return file_name,foundit


    try:
        if (archive == 'ign'):
            dir1='ftp://igs.ensg.ign.fr/pub/igs/data/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif (archive == 'sonel'):
            dir1='ftp://ftp.sonel.org/gps/data/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif archive == 'bkg':
            just_bkg(cyyyy, cdoy, file_name)
        elif (archive == 'bev'):
            dir1 = 'https://gnss.bev.gv.at/at.gv.bev.dc/data/obs/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif (archive == 'epn'):
            dir1 = 'https://epncb.oma.be/ftp/obs/' + cyyyy + '/' + cdoy + '/'
            print(dir1)
            wget.download(dir1+file_name,file_name)
        elif (archive == 'ga'):
            QUERY_PARAMS, headers = ga_stuff(station9ch, year, doy)
            API_URL = 'https://data.gnss.ga.gov.au/api/rinexFiles/'  
            request = requests.get(API_URL, QUERY_PARAMS, headers=headers)
        #request.raise_for_status()
        # i don't know how to read this - so doing it the dumb way
            if len(json.loads(request.content)) == 1:
                for query_response_item in json.loads(request.content):
                    file_url = query_response_item['fileLocation']
                    file_name = urlparse(file_url).path.rsplit('/', 1)[1]
                    wget.download(file_url,file_name)
        elif (archive == 'nrcan'):
            dir1 = 'https://cacsa.nrcan.gc.ca/gps/data/gpsdata/' + cyy + cdoy  + '/' + cyy + 'd' + '/'
            wget.download(dir1+file_name,file_name)
        elif (archive == 'unavco'):
            dir1 = 'https://data.unavco.org/archive/gnss/rinex3/obs/' + cyyyy + '/' + cdoy + '/'
            wget.download(dir1+file_name,file_name)
        elif (archive == 'gfz'):
            # no idea
            dir1 = 'ftp://isdcftp.gfz-potsdam.de/gnss/data/daily/' + cyyyy + '/' + cdoy
            wget.download(dir1+file_name,file_name)
        elif (archive == 'cddis'):
            new_way_dir = '/gnss/data/daily/' + cyyyy + '/' + cdoy + '/' + cyy + 'd/'
            g.cddis_download_2022B(file_name,new_way_dir)
            #g.cddis_download(file_name,new_way_dir)
        else:
            return '', ''
    except:
        okokok = 1

    if os.path.exists(file_name):
        siz = os.path.getsize(file_name)
        if (siz == 0):
            subprocess.call(['rm',file_name])
            print('File was not found: ', file_name, ' at ', archive)
        else:
            print('File exists: ', file_name, ' at ', archive)
            foundit = True
    else:
        print('File was not found: ', file_name, ' at ', archive)

    return file_name,foundit

def filename_plus(station9ch,year,doy,srate,stream):
    """
    function to create RINEX 3 filenames for one day files.

    Parameters
    ----------
    station9ch : str
         9 character station name

    year : int

    doy : int
        day of year

    srate : int
         receiver sample rate 

    stream : str 
         R or S ; latter means the file was streamed.

    output : str
         compliant filename with crx.gz on the end as this is how the files 
         are stored at GNSS archives as far as I know.

    Returns
    -------
    file_name : str
        filename of the RINEX 3 file
    cyyyy : str
        4ch year 
    cdoy : str
        3ch day of year

    """
    cyyyy = str(year)
    cdoy = '{:03d}'.format(doy)
    crate = '{:02d}'.format(srate)
    upper = station9ch.upper()
    ff = upper + '_' + stream + '_' + cyyyy + cdoy + '0000_01D_' + crate + 'S_MO'
    ext = '.crx.gz'
    file_name = ff + ext

    return file_name, cyyyy, cdoy

def ga_stuff(station, year, doy,rinexv=3):
    """
    GA API requirements to download a Rinex 3 file

    Parameters
    ----------
    station : str
        9 character station name
    year : integer
        full year
    doy : int
        day of year
    rinexv : int
        rinex version        

    Returns
    -------
    QUERY_PARAMS : json
        I think
    headers : json
        I think

    """
    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    month = int(d.month); day = int(d.day)
    cmonth = '{:02d}'.format(month); cday = '{:02d}'.format(day)


    QUERY_PARAMS = {}
    QUERY_PARAMS['stationId'] = station[0:4].upper()
    QUERY_PARAMS['fileType'] = 'obs'
    QUERY_PARAMS['filePeriod'] = '01D'
    QUERY_PARAMS['rinexVersion'] = str(rinexv) 
    QUERY_PARAMS['startDate'] = str(year) + '-' + cmonth + '-' + cday + 'T00:00:00Z'
    QUERY_PARAMS['endDate'] =   str(year) + '-' + cmonth + '-' + cday + 'T23:59:30Z'

    headers = {}
    headers['Accept-Encoding'] = 'gzip'

    return QUERY_PARAMS, headers

def universal_all(station9ch, year, doy, srate,stream):
    """
    check multiple archives for RINEX 3 data

    Parameters
    ----------
    station9ch : str
        9 character station name

    year : int
        full year

    doy : int
        doy of year

    srate : int
        receiver sample rate 

    stream : str
        R or S

    Peturns
    -------
    file_name : str
        rinex filename

    foundit : bool
        whether rinex file was found

    """
    foundit = False

    for archive in ['unavco','cddis','bkg','bev','epn','ga']:
        if archive == 'unavco':
            srate_in = 15
        else:
            srate_in = srate
        # only look if you haven't found it
        if (not foundit):
            file_name,dd = universal(station9ch, year, doy, archive,srate_in,stream)
            if os.path.exists(file_name):
                foundit = True

    return file_name, foundit

def rinex2names(station,year,doy):
    """
    Creates the expected filename for rinex2 version files

    Parameters
    ----------
    station : string

    year : integer

    doy : integer
        day of year

    Results
    --------
    f1 : str
        hatanaka rinex filename
    f2 : str
        regular rinex filename
    cyyyy : str
        four character year 

    cdoy : string
        three character day of year

    """
    cyyyy = str(year)
    cdoy = '{:03d}'.format(doy)
    f1 = station  + cdoy + '0.' + cyyyy[2:4] + 'd'
    f2 = station  + cdoy + '0.' + cyyyy[2:4] + 'o'

    return f1, f2, cyyyy, cdoy


def universal_rinex2(station, year, doy, archive):
    """
    seamless archive for rinex 2 files ...

    Parameters
    ----------
    station : string
        four character station name
    year : integer

    doy : integer

    archive : string
        name of the GNSS archive

    Returns
    -------
    file_name : string
        filename that was downloaded

    foundit : boolean
        whether file was found

    """
    # define the file name

    foundit = False; dir1 = ''; file_name = ''

    dname, oname, cyyyy, cdoy = rinex2names(station,year,doy)
    if os.path.exists(oname):
        #print('RINEX o File is already on disk')
        return oname, True 

    print('Searching the ', archive, ' archive for ', station)

    cydoy = cyyyy + '/' + cdoy + '/'
    cyy = cyyyy[2:4]

    if (archive == 'jp'):
        # i did not want to rewrite the code
        gsi_data(station, year, doy)
        file_name = oname
        if os.path.exists(file_name):
            foundit = True
    elif (archive == 'unavco'):
        dir1 = 'https://data.unavco.org/archive/gnss/rinex/obs/' + cydoy
        foundit, file_name = gogetit(dir1, dname, '.Z'); 
        if not foundit:
            foundit, file_name = gogetit(dir1, oname, '.Z')
    elif (archive == 'special'):
        dir1 = 'https://data.unavco.org/archive/gnss/products/reflectometry/' + cydoy
        foundit, file_name = gogetit(dir1, oname, '.gz'); 
    elif archive == 'sopac':
        dir1 = 'ftp://garner.ucsd.edu/pub/rinex/' + cydoy
        foundit, file_name = gogetit(dir1, dname, '.Z');
    elif archive == 'sonel':
        dir1 = 'ftp://ftp.sonel.org/gps/data/' + cydoy
        foundit, file_name = gogetit(dir1, dname, '.Z');
    elif archive == 'nz':
        dir1 =  'https://data.geonet.org.nz/gnss/rinex/' + cydoy
        foundit, file_name = gogetit(dir1, oname, '.gz'); 
    elif archive == 'bkg':
        # are the old data with Z instead of gz?
        dir1 = 'https://igs.bkg.bund.de/root_ftp/IGS/obs/' + cydoy
        dir2 = 'https://igs.bkg.bund.de/root_ftp/EUREF/obs/' + cydoy

        foundit, file_name = gogetit(dir1, dname, '.Z');
        if not os.path.exists(file_name):
            foundit, file_name = gogetit(dir2, dname, '.Z')
        # not even sure this is a thing ???
        if not os.path.exists(file_name):
            foundit, file_name = gogetit(dir1, dname, '.gz')
        if not os.path.exists(file_name):
            foundit, file_name = gogetit(dir2, dname, '.gz')
    elif (archive == 'bev'):
        dir1 = 'https://gnss.bev.gv.at/at.gv.bev.dc/data/obs/' + cydoy
        foundit, file_name = gogetit(dir1, dname, '.gz');
    elif (archive == 'jeff'):
        dir1 = 'ftp://gps.alaska.edu/pub/gpsdata/permanent/C2/' + cydoy
        foundit, file_name = gogetit(dir1, oname, '.gz');
    elif (archive == 'ngs'):
        dir1 = 'https://geodesy.noaa.gov/corsdata/rinex/' + cydoy + '/' + station + '/'
        foundit, file_name = gogetit(dir1, oname, '.gz');
        if not foundit:
            foundit, file_name = gogetit(dir1, dname, '.gz')
    elif (archive == 'cddis'):
        foundit,file_name = serial_cddis_files(dname,cyyyy,cdoy); 
    elif (archive == 'ga'):
        QUERY_PARAMS, headers = ga_stuff(station, year, doy)
        API_URL = 'https://data.gnss.ga.gov.au/api/rinexFiles/'
        QUERY_PARAMS['rinexVersion'] = '2'
        request = requests.get(API_URL, QUERY_PARAMS, headers=headers)
        file_name = ''
        if len(json.loads(request.content)) == 1:
            foundit = True
            for query_response_item in json.loads(request.content):
                file_url = query_response_item['fileLocation']
                file_name = urlparse(file_url).path.rsplit('/', 1)[1]
                wget.download(file_url,file_name)
    elif (archive == 'nrcan'):
        dir1 = 'ftp://cacsa.nrcan.gc.ca/gps/data/gpsdata/' + cyy + cdoy  + '/' + cyy + 'd' + '/'
        foundit, f = gogetit(dir1, dname, '.Z'); file_name = f
    else:
         print('I do not recognize your archive')

    if not os.path.exists(file_name):
        print('Did not find the Rinex file')
    return file_name,foundit

def make_rinex2_ofiles(file_name):
    """
    take a rinex2 file, gunzip or uncompress it, and 
    then Hatanaka decompress it

    Parameters
    ----------
    file_name: string
        rinex2 filename

    Returns
    -------
    new_name : string
        filename after multiple decompression processes
    fexist : boolean
        whether file was successfully created

    """
    if (file_name[-1:] == 'Z'):
        subprocess.call(['uncompress', file_name])
        file_name = file_name[:-2]
    if (file_name[-2:] == 'gz'):
        subprocess.call(['gunzip', file_name])
        file_name = file_name[:-3]

    crnxpath = g.hatanaka_version()
    # take off the d and make it an o
    new_name = file_name[:-1] + 'o'

    if file_name[-1:] == 'd':
        if os.path.exists(crnxpath):
            subprocess.call([crnxpath, file_name])
            subprocess.call(['rm', '-f',file_name])
        else:
            g.hatanaka_warning()
    elif file_name[-1:] == 'o':
        thisisagoodthing = 1
    else:
        print('I only recognize d and o files')

    fexist = False
    if os.path.exists(new_name):
        fexist = True

    return new_name, fexist

def strip_rinexfile(rinexfile):
    """
    uses either teqc or gfzrnx to reduce observables

    Parameters
    ----------
    rinexfile : string
        name of the rinex2 file
    """
    print('You chose the strip option to reduce the number of observables in the RINEX file')
    teqcv = g.teqc_version()
    if os.path.isfile(teqcv):
        print('Use teqc to strip the RINEX 2 file')
        foutname = 'tmp.' + rinexfile
        fout = open(foutname,'w')
        subprocess.call([teqcv, '-O.obs','S1+S2+S5+S6+S7+S8', rinexfile],stdout=fout)
        fout.close()
        subprocess.call(['rm','-f',rinexfile])
        subprocess.call(['mv','-f',foutname, rinexfile])
    else:
        gfzrnxpath = g.gfz_version()
        if os.path.isfile(gfzrnxpath):
            print('Use gfzrnx to strip the RINEX 2 file')
            tempfile = rinexfile + '.tmp'
            # save yourself heartache down the way cause those doppler data are just clogging up the works
            subprocess.call([gfzrnxpath,'-finp', rinexfile, '-fout', tempfile, '-vo','2','-f', '-obs_types', 'S','-q'])
            subprocess.call(['mv', '-f', tempfile, rinexfile])

def gsi_data(station,year,doy):
    """
    get data from GSI

    Parameters
    ----------
    station : str
        6 char station name
    year : int
        full year
    doy : int
        day of yare

    """
    d = g.doy2ymd(year,doy);
    month = d.month; day = d.day
    g.rinex_jp(station, year, month, day)


def rinex2_highrate(station, year, doy,archive,strip_snr):
    """
    kluge to download highrate data since i have revamped the rinex2 code
    strip_snr is boolean as to whether you want to strip out the non-SNR data
    it can be slow with highrate data. it requires gfzrnx

    Parameters
    ----------
    station : string
         4 character station ID.  lowercase

    year : integer
        full year

    doy : integer
        day of year

    archive : string
        name of GNSS archive

    strip_snr : boolean
        whether you want to strip out the observables (leaving only SNR)

    """
    foundit = False
    d = g.doy2ymd(year,doy);
    month = d.month; day = d.day
    rinexfile,rinexfiled = g.rinex_name(station, year, month, day)
    if (archive == 'unavco') or (archive == 'all'):
        g.rinex_unavco_highrate(station, year, month, day)
    # file does not exist, so keep looking
    if not os.path.isfile(rinexfile):
        if (archive == 'nrcan') or (archive == 'all'):
            g.rinex_nrcan_highrate(station, year, month, day)
    # try new cddis for highrate rINex 2
    if not os.path.isfile(rinexfile):
        if (archive == 'cddis') or (archive == 'all'):
            stream = 'R'
            srate = 1 # one second
            ch.cddis_highrate(station, year, month, day,stream,srate)
    #if not os.path.isfile(rinexfile):
    #    if not os.path.isfile(rinexfile):
    #        if (archive == 'ga') or (archive == 'all'):
    #            g.rinex_ga_highrate(station, year, month, day)

    if os.path.isfile(rinexfile):
        foundit = True
        gfzrnxpath = g.gfz_version()
        if os.path.isfile(gfzrnxpath) and strip_snr:
            print('You chose the strip_snr option to reduce the number of observables')
            tempfile = rinexfile + '.tmp'
        # save yourself heartache down the way cause those doppler data are just clogging up the works
            subprocess.call([gfzrnxpath,'-finp', rinexfile, '-fout', tempfile, '-vo','2','-f', '-obs_types', 'S','-q'])
            subprocess.call(['mv', '-f', tempfile, rinexfile])

    return rinexfile, foundit

def ga_stuff_highrate(station, year, doy,rinexv=3):
    """
    This should be merged with existing ga_stuff code

    Parameters
    ----------
    station : str
        4 or 9 ch station name
    year : int
        full year
    doy : int
        day of year
    rinexv : int
        rinex version

    Returns
    -------
    QUERY_PARAMS : json
        i think
    headers : json
        i think
    """
    d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
    month = int(d.month); day = int(d.day)
    cmonth = '{:02d}'.format(month); cday = '{:02d}'.format(day)


    QUERY_PARAMS = {}
    QUERY_PARAMS['stationId'] = station[0:4].upper()
    QUERY_PARAMS['fileType'] = 'obs'
    QUERY_PARAMS['filePeriod'] = '15M'

    QUERY_PARAMS['rinexVersion'] = str(rinexv) 
    QUERY_PARAMS['startDate'] = str(year) + '-' + cmonth + '-' + cday + 'T00:00:00Z'
    QUERY_PARAMS['endDate'] =   str(year) + '-' + cmonth + '-' + cday + 'T23:59:30Z'

    headers = {}
    headers['Accept-Encoding'] = 'gzip'

    return QUERY_PARAMS, headers

def serial_cddis_files(dname,cyyyy,cdoy):
    """
    only looks in the hatanaka decompression section of cddis

    Parameters
    ----------
    dname : string
        rinex2 filename without compression extension
    cyyyy : string
        four character year
    cdoy : string
        three character day of yaer

    Returns
    -------
    foundit : bool
        whether file was found
    f : str
        filename

    """
    foundit = False
    f = ''
    # try gz, then Z.  so annoying
    gz_file_name = dname + '.gz'
    Z_file_name = dname + '.Z'
    new_way_dir = '/gnss/data/daily/' + cyyyy + '/' + cdoy + '/' + cyyyy[2:4] + 'd/'
    print(gz_file_name, new_way_dir)
    try:
        g.cddis_download_2022B(gz_file_name,new_way_dir) ;
    except:
        okok = 1

    if os.path.exists(gz_file_name):
        siz = os.path.getsize(gz_file_name)
        if siz == 0:
            subprocess.call(['rm',gz_file_name])
        else:
            foundit = True
            f = gz_file_name

    if (not foundit):
        print(Z_file_name, new_way_dir)
        # look for Z compressed file
        try:
            g.cddis_download_2022B(Z_file_name,new_way_dir) ;
        except:
            okok = 1

        if os.path.exists(Z_file_name):
            siz = os.path.getsize(Z_file_name)
            if siz == 0:
                subprocess.call(['rm',Z_file_name])
            else:
                foundit = True
                f = Z_file_name

    return foundit, f
