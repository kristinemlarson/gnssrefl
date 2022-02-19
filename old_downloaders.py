def cddis3(station9ch, year, doy,srate):
    """
    author: kristine larson
    just gets RINEX - does not translate it to anything else
    """
    fexists = False
    ftp = 'ftp://cddis.nasa.gov/gnss/data/daily/'
    cyyyy, cyy, cdoy = ydoych(year,doy)

    f = cyyyy + '/' + cdoy + '/' + cyy + 'd'  + '/'
    new_way_f = '/gnss/data/daily/' + f
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + str(srate) + 'S_MO'
    smallff = station9ch[0:4].lower() + cdoy + '0.' + cyy + 'o'
    ending = '.crx' # compressed rinex3 ending
    rending = '.rnx' # rinex3 ending
    gzfilename = ff+ending + '.gz' # the crx.gz file
    filename = ff+ending  # the crx file
    rfilename = ff+rending # the rnx file
    url = ftp + f + gzfilename
    #print(url)
    crnxpath = hatanaka_version()
    print(gzfilename)
    print(new_way_f)
    try:
        cddis_download(gzfilename,new_way_f)
        subprocess.call(['gunzip',gzfilename])
        subprocess.call([crnxpath,filename])
        subprocess.call(['rm',filename])
    except:
        print('no rinex3 file at CDDIS')

    if os.path.isfile(rfilename):
        fexists = True

    return fexists

def unavco3(station9ch, year, doy,srate):
    """
    just gets rinex 3 file from unavco
    inputs 9 character station id, year, day of year, sample rate
    author: kristine larson
    21sep03: change from ftp to https
    """
    fexists = False
    cyyyy, cyy, cdoy = ydoych(year,doy)
    csrate = '{:02d}'.format(srate)
    ftp = 'ftp://data-out.unavco.org/pub/rinex3/obs/'
    ftp = 'https://data.unavco.org/archive/gnss/rinex3/obs/'


    f = cyyyy + '/' + cdoy + '/'
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO'
    smallff = station9ch[0:4].lower() + cdoy + '0.' + cyy + 'o'
    ending = '.crx' # compressed rinex3 ending
    rending = '.rnx' # rinex3 ending
    gzfilename = ff+ending + '.gz' # the crx.gz file
    filename = ff+ending  # the crx file
    rfilename = ff+rending # the rnx file
    url = ftp + f + gzfilename
    print(url)
    crnxpath = hatanaka_version()
    try:
        wget.download(url,gzfilename)
        subprocess.call(['gunzip',gzfilename])
        subprocess.call([crnxpath,filename])
        subprocess.call(['rm',filename])
    except:
        print('no rinex3 file at unavco')

    if os.path.isfile(rfilename):
        fexists = True

    return fexists

def version3(station,year,doy,NS,archive,streamvar):
    """
    subroutine to take care of RINEX version 3
    21april20 added BEV austria
    this code has been supplanted by karnak_sub.- keeping for unknown reasons
    """
    fexist = False
    if NS == 9:
        if archive == 'cddis':
            srate = 30 # rate supported by CDDIS
            fexist = g.cddis3(station, year, doy,srate)
        if archive == 'unavco':
            srate = 15
            fexist = g.unavco3(station, year, doy,srate)
        if archive == 'bkg':
            srate = 30
            fexist = g.bkg_rinex3(station, year, doy,srate,streamvar)
        if archive == 'ign':
            srate = 30
            fexist = g.ign_rinex3(station, year, doy,srate)
        if archive == 'bev':
            srate = 30
            fexist = g.bev_rinex3(station, year, doy,srate,streamvar)
        if archive == 'ga':
            srate = 30
            fexist = g.ga_rinex3(station, year, doy,srate)
        if fexist:
            print('SUCESSFUL RINEX3 DOWNLOAD:', archive)
        else:
            print('could not find the RINEX 3 file')
    else:
        print('exiting: station names must have 9 characters')

def ga_rinex3_to_rinex2(station9ch, year, doy,srate):
    """
    download rinex 3 from Geoscience Australia and translte to rinex 2
    inputs: 9 character station name, year, day of year and srate
    seconds
    kristine larson
    """
    fexist = False
    crnxpath = hatanaka_version()
    cyyyy, cyy, cdoy = ydoych(year,doy)

    csrate = '{:02d}'.format(srate)
    url = 'ftp://ftp.data.gnss.ga.gov.au/daily/' + cyyyy + '/' + cdoy + '/'

    ff = station9ch.upper() +    '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx.gz'
    ff1 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx'
    ff2 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.rnx'
    url = url + ff
    print(url)
    rinex2name = station9ch[0:4].lower() + cdoy + '0.' + cyy + 'o'
    try:
        wget.download(url,ff)
        subprocess.call(['gunzip',ff])
        if os.path.exists(ff1):
            print('uncompress Hatanaka')
            subprocess.call([crnxpath,ff1])
        else:
            print('compressed file does not exist')
        if os.path.exists(ff2):
            print(ff2, rinex2name)
            fexist = new_rinex3_rinex2(ff2,rinex2name)
    except:
        print('problem with geoscience australia download')

    # returns rinex3name by convention
    return fexist, ff2

def bev_rinex3(station9ch, year, doy,srate,streamvar):
    """
    download rinex 3 from BEV
    inputs: 9 character station name, year, day of year and srate
    is sample rate in seconds
    note: this code works - but it does not turn it into RINEX 2 for you
    added stream variable
    22feb09 changd to https
    """
    fexist = False
    crnxpath = hatanaka_version()
    cyyyy, cyy, cdoy = ydoych(year,doy)
    print('BEV rinex 3 download')

    csrate = '{:02d}'.format(srate)
    url = 'ftp://gnss.bev.gv.at/pub/obs/' + cyyyy + '/' + cdoy + '/'
    url = 'https://gnss.bev.gv.at/at.gv.bev.dc/data/obs/' + cyyyy + '/' + cdoy + '/'
    streamlink = '_' + streamvar + '_'
    print(url)
    ff = station9ch.upper() +   streamlink + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx.gz'
    ff1 = station9ch.upper() +  streamlink + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx'
    ff2 = station9ch.upper() +  streamlink + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.rnx'
    url = url + ff
    #print(url)
    try:
        wget.download(url,ff)
        subprocess.call(['gunzip',ff])
        subprocess.call([crnxpath,ff1])
        # get rid of compressed file
        subprocess.call(['rm','-f',ff1])
    except:
        print('problem with BEV rinex 3 download')

    if os.path.exists(ff2):
        fexist = True

    return fexist
def ign_rinex3(station9ch, year, doy,srate):
    """
    download rinex 3 from IGN
    inputs: 9 character station name, year, day of year and srate
    is sample rate in seconds
    note: this code works - but it does not turn it into RINEX 2 for you
    """
    fexist = False
    crnxpath = hatanaka_version()
    cyyyy, cyy, cdoy = ydoych(year,doy)

    csrate = '{:02d}'.format(srate)

    url = 'ftp://igs.ensg.ign.fr/pub/igs/data/' + cyyyy + '/' + cdoy + '/'
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx.gz'
    ff1 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx'
    ff2 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.rnx'
    url = url + ff
    #print(url)
    try:
        wget.download(url,ff)
        subprocess.call(['gunzip',ff])
        subprocess.call([crnxpath,ff1])
        # get rid of compressed file
        subprocess.call(['rm','-f',ff1])
    except:
        print('problem with IGN download')

    if os.path.exists(ff2):
        fexist = True

    return fexist

def ga_rinex3(station9ch, year, doy,srate):
    """
    download rinex 3 from Geoscience Australia
    inputs: 9 character station name, year, day of year and srate
    is sample rate in seconds
    note: this code works - but it does not turn it into RINEX 2 for you
    21sep02 failed attempt to update to https
    """
    fexist = False
    crnxpath = hatanaka_version()
    cyyyy, cyy, cdoy = ydoych(year,doy)

    csrate = '{:02d}'.format(srate)
    url = 'ftp://ftp.data.gnss.ga.gov.au/daily/' + cyyyy + '/' + cdoy + '/'
    #url = 'https://data.gnss.ga.gov.au/daily/' + cyyyy + '/' + cdoy + '/'
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx.gz'
    ff1 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx'
    ff2 = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.rnx'
    url = url + ff
    print(url)
    try:
        wget.download(url,ff)
        subprocess.call(['gunzip',ff])
        subprocess.call([crnxpath,ff1])
        # get rid of compressed file
        subprocess.call(['rm','-f',ff1])
    except:
        print('problem with geoscience australia download')


    if os.path.exists(ff2):
        fexist = True

    return fexist

def unavco_rinex3(station9ch, year, doy,srate,orbtype):
    """
    attempt to download Rinex3 files from UNAVCO
    and then translate them to something useful (Rinex 2.11)
    inputs: 9 character station name (can be upper or lower, as code will change to all
    uppercase)

    year, day of year (doy) and sample rate (in seconds)

    orbtype - nav, sp3 etc

    if nav file orbtype is used, no point writing out the non-GPS data

    returns file existence boolean and name of the RINEX 3 file (so it can be cleaned up)


    warning - i do not write out the L2P data - only the good L2C signals.

    21sep02 -change from ftp to https

    author: kristine larson
    """
    fexists = False
    cyyyy, cyy, cdoy = ydoych(year,doy)
    csrate = '{:02d}'.format(srate)
    ftp = 'ftp://data-out.unavco.org/pub/rinex3/obs/'
    # updated 21sep03
    ftp = 'https://data.unavco.org/archive/gnss/rinex3/obs/'

    f = cyyyy + '/' + cdoy + '/'
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO'
    smallff = station9ch[0:4].lower() + cdoy + '0.' + cyy + 'o'
    ending = '.crx' # compressed rinex3 ending
    rending = '.rnx' # rinex3 ending
    gzfilename = ff+ending + '.gz' # the crx.gz file
    filename = ff+ending  # the crx file
    rfilename = ff+rending # the rnx file
    url = ftp + f + gzfilename
#    print(url)
    # not sure i still neeed this
    exedir = os.environ['EXE']
    gexe = gfz_version()
    crnxpath = hatanaka_version()
    if (orbtype == 'nav') or (orbtype == 'gps'):
        # added this because weird Glonass data were making teqc unhappy
        gobblygook = 'G:S1C,S2X,S2L,S2S,S5'
    else:
    # I hate S2W  - so it is not written out
    # added Beidou 9/20/2020
    # tried again
        #gobblygook = 'G:S1C,S2X,S2L,S2S,S5+R:S1P,S1C,S2P,S2C+E:S1,S5,S6,S7,S8+C:S2C,S7C,S2I,S7I,S5,S6'
        gobblygook = myfavoriteobs()
    if os.path.isfile(rfilename):
        print('rinex3 file already exists')
    else:
        try:
            wget.download(url,gzfilename)
            # unzip and Hatanaka decompress
            subprocess.call(['gunzip',gzfilename])
            subprocess.call([crnxpath,filename])
            # remove the crx file
            subprocess.call(['rm',filename])
        except:
            print('no RINEX 3 file at unavco')

    # use new function
    if os.path.isfile(rfilename) and os.path.isfile(gexe):
        r2_filename = smallff
        fexists = new_rinex3_rinex2(rfilename,r2_filename)
        #print('making rinex 2.11')
        #try:
            #subprocess.call([gexe,'-finp', rfilename, '-fout', smallff, '-vo','2','-ot', gobblygook, '-f'])
            #print('woohoo!')
            #print('look for the rinex 2.11 file here: ', smallff)
            #fexists = True
        #except:
            #print('some kind of problem in translation to 2.11')
    else:
        print('either the rinex3 file does not exist OR the gfzrnx executable does not exist')

    return fexists, rfilename


def cddis_rinex3(station9ch, year, doy,srate,orbtype):
    """
    attempt to download Rinex3 files from CDDIS
    and then translate them to something useful (Rinex 2.11)

    inputs: 9 character station name (should be all capitals)
    year, day of year (doy) and sample rate (in seconds)
    station9ch can be lower or upper case - code changes it to upper case

    sending orbit type so that if nav file is used, no point writing out the non-GPS data

    returns file existence boolean and name of the RINEX 3 file (so it can be cleaned up)
    author: kristine larson
    """
    fexists = False
    ftp = 'ftp://cddis.nasa.gov/gnss/data/daily/'
    cyyyy, cyy, cdoy = ydoych(year,doy)

    f = cyyyy + '/' + cdoy + '/' + cyy + 'd'  + '/'
    new_way_f = '/gnss/data/daily/' + f
    ff = station9ch.upper() +   '_R_' + cyyyy + cdoy + '0000_01D_' + str(srate) + 'S_MO'
    smallff = station9ch[0:4].lower() + cdoy + '0.' + cyy + 'o'
    ending = '.crx' # compressed rinex3 ending
    rending = '.rnx' # rinex3 ending
    gzfilename = ff+ending + '.gz' # the crx.gz file
    filename = ff+ending  # the crx file
    rfilename = ff+rending # the rnx file
    url = ftp + f + gzfilename
    #print(url)
    # not sure i still neeed this
    #exedir = os.environ['EXE']
    gexe = gfz_version()
    crnxpath = hatanaka_version()
    if orbtype == 'nav':
        # added this bevcause weird Glonass data were making teqc unhappy
        gobblygook = 'G:S1C,S2X,S2L,S2S,S5'
    else:
    # I hate S2W
    # tried to add Beidou on September 19, 2020
        #gobblygook = 'G:S1C,S2X,S2L,S2S,S5+R:S1P,S1C,S2P,S2C+E:S1,S5,S6,S7,S8+C:S2C,S7C,S2I,S7I,S6,S5'
        gobblygook = myfavoriteobs()
        print(gobblygook)
    if os.path.isfile(rfilename):
        print('rinex3 file already exists')
    else:
        print(gzfilename)
        print(new_way_f)
        try:
            cddis_download(gzfilename,new_way_f)
            subprocess.call(['gunzip',gzfilename])
            subprocess.call([crnxpath,filename])
            subprocess.call(['rm',filename])
        except:
            print('no file at CDDIS')

    # try using my newfunction
    r2_filename = smallff
    fexists = new_rinex3_rinex2(rfilename,r2_filename)
    #if os.path.isfile(rfilename) and os.path.isfile(gexe):
    #    print('making rinex 2.11')
    #    try:
    #        subprocess.call([gexe,'-finp', rfilename, '-fout', smallff, '-vo','2','-ot', gobblygook, '-f'])
    #        print('woohoo!')
    #        print('look for the rinex 2.11 file here: ', smallff)
    #        fexists = True
    #    except:
    #        print('some kind of problem in translation to 2.11')
    #else:
    #    print('either the rinex3 file does not exist OR the gfzrnx executable does not exist')

    return fexists, rfilename

def pickup_pbay(year,month, day):
    """
    jeff freymueller's site. L2C, but GPS only.
    changed to year,month,day to be consistent with other
    """
    #print('downloading highrate PBAY')
    station = 'pbay'
    if (day == 0):
        doy = month
        year, month, day, cyyyy,cdoy, YMD = ydoy2useful(year,doy)
        cyy = cyyyy[2:4]
    else:
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)

    url = 'ftp://gps.alaska.edu/pub/gpsdata/permanent/C2/' + cyyyy + '/' + cdoy + '/'
    fname = station + cdoy + '0.' + cyyyy[2:4] + 'o.gz'
    url = url + fname
    try:
        wget.download(url,fname)
        subprocess.call(['gunzip', fname])
    except:
        print('problems downloading pbay')

    return True


def bkg_rinex3(station9ch, year, doy,srate,streamvar):
    """
    download rinex 3 from BKG
    inputs: 9 character station name, year, day of year and srate
    is sample rate in seconds
    note: this code works - but it does not turn it into RINEX 2 for you

    21sep03 moved from ftp to https
    22feb09 changed euref to IGS? also added stream variable
    """
    fexist = False
    crnxpath = hatanaka_version()
    cyyyy, cyy, cdoy = ydoych(year,doy)
    csrate = '{:02d}'.format(srate)

    url = 'ftp://igs.bkg.bund.de/EUREF/obs/' + cyyyy + '/' + cdoy + '/'
    # try this one now?
    url = 'https://igs.bkg.bund.de/root_ftp/EUREF/obs/' + cyyyy + '/' + cdoy + '/'
    url = 'https://igs.bkg.bund.de/root_ftp/IGS/obs/' + cyyyy + '/' + cdoy + '/'
    oo = '_' + streamvar + '_'
    ff = station9ch.upper()  + oo + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx.gz'
    ff1 = station9ch.upper() + oo  + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.crx'
    ff2 = station9ch.upper() + oo + cyyyy + cdoy + '0000_01D_' + csrate + 'S_MO' + '.rnx'
    url = url + ff
    print(url)
    try:
        wget.download(url,ff)
        subprocess.call(['gunzip',ff])
        subprocess.call([crnxpath,ff1])
        # get rid of compressed file
        subprocess.call(['rm','-f',ff1])
    except:
        print('problem with bkg download')

    if os.path.exists(ff2):
        fexist = True

    return fexist

def rinex_nrcan(station, year, month, day):
    """
    author: kristine larson
    inputs: station name, year, month, day
    picks up a RINEX file from GNS New zealand
    you can input day =0 and it will assume month is day of year

    2021june02, use new ftp site.
    """
    #exedir = os.environ['EXE']
    #crnxpath = exedir + '/CRX2RNX'
    crnxpath = hatanaka_version()

    # if doy is input
    if day == 0:
        doy=month
        d = doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    # was using this ...
    gns = 'ftp://gauss.geod.nrcan.gc.ca/data/ftp/naref/pub/rinex/'
    # user narefftp
    # password 4NAREF2use
    gns = 'ftp://gauss.geod.nrcan.gc.ca/data/ftp/naref/pub/data/rinex/'
    gns = 'ftp://rtopsdata1.geod.nrcan.gc.ca/gps/data/'
    # 2021 June 2
    gns = 'ftp://cacsa.nrcan.gc.ca/gps/data/'

    xxdir = gns + 'gpsdata/' + cyy + cdoy  + '/' + cyy + 'd'
    oname,fname = rinex_name(station, year, month, day)
    # only hatanaka files in canada and normal unix compression
    file1 = fname + '.Z'
    url = xxdir + '/' +  file1
    print(url)
#   all nrcan data are in hatanaka format
    if os.path.exists(crnxpath):
        try:
            wget.download(url,file1)
            subprocess.call(['uncompress', file1])
            subprocess.call([crnxpath, fname])
            subprocess.call(['rm', '-f',fname])
            #print('successful download from NRCAN ')
        except:
            print('some kind of problem with NRCAN download',file1)
            subprocess.call(['rm', '-f',file1])
    else:
        print('You cannot use the NRCAN archive without installing CRX2RNX.')



def rinex_nz(station, year, month, day):
    """
    author: kristine larson
    inputs: station name, year, month, day
    picks up a RINEX file from GNS New zealand
    you can input day =0 and it will assume month is day of year
    20jul10 - changed access point and ending
    21sep02 - chagned from ftp to https
    """
    # if doy is input
    #print('try to find the file in New Zealand')
    if day == 0:
        doy=month
        d = doy2ymd(year,doy);
        month = d.month; day = d.day
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    #gns = 'ftp://ftp.geonet.org.nz/gnss/rinex/'
    # new access point
    gns = 'https://data.geonet.org.nz/gnss/rinex/'
    oname,fname = rinex_name(station, year, month, day)
    file1 = oname + '.gz'
    url = gns +  cyyyy + '/' + cdoy +  '/' + file1
    try:
        wget.download(url,file1)
        subprocess.call(['gunzip', file1])
        #print('successful download from GeoNet New Zealand')
    except:
        print('some kind of problem with GeoNet download',file1)
        subprocess.call(['rm', '-f',file1])

def rinex_sonel(station, year, month, day):
    """
    author: kristine larson
    inputs: station name, year, month, day
    picks up a hatanaka RINEX file from SOPAC - converts to o
    hatanaka exe hardwired  for my machine
    """
    exedir = os.environ['EXE']
    crnxpath = hatanaka_version()
    doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    sonel = 'ftp://ftp.sonel.org'
    oname,fname = rinex_name(station, year, month, day)
    file1 = fname + '.Z'
    path1 = '/gps/data/' + cyyyy + '/' + cdoy + '/'
    url = sonel + path1 + file1


    if os.path.exists(crnxpath):
        try:
            wget.download(url,file1)
            # if successful download, uncompress and translate it
            if os.path.exists(file1):
                subprocess.call(['uncompress', file1])
                subprocess.call([crnxpath, fname])
                subprocess.call(['rm', '-f',fname])
            #print('successful Hatanaka download from SONEL ')
        except:
            #print('some kind of problem with Hatanaka download from SONEL',file1)
            subprocess.call(['rm', '-f',file1])
    else:
        hatanaka_warning()
        #print('WARNING WARNING WARNING WARNING')
        #print('You are trying to convert Hatanaka files without having the proper')
        #print('executable, CRX2RNX. See links in the gnssrefl documentation')


def rinex_special(station, year, month, day):
    """
    author: kristine larson
    picks up a RINEX file from special unavco area
    year, month, and day are INTEGERS

    WARNING: only rinex version 2 in this world
    march25,2021 added gz
    """
    exedir = os.environ['EXE']
    if day == 0:
        doy = month
        cyyyy, cyy, cdoy = ydoych(year,doy)
    else:
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    rinexfile,rinexfiled = rinex_name(station, year, month, day)
    unavco= 'ftp://data-out.unavco.org/pub/products/reflectometry/'
    filenamegz = rinexfile  + '.gz'
    filename1 = rinexfile
    # URL path for the o file
    url1 = unavco + cyyyy + '/' + cdoy + '/' + filenamegz

    try:
        wget.download(url1,filenamegz)
        status = subprocess.call(['gunzip', filenamegz])
    except:
        okokok =1

def rinex_unavco_old(station, year, month, day):
    """
    author: kristine larson
    picks up a RINEX file from default unavco area, i.e. not highrate.
    it tries to pick up an o file,
    but if it does not work, it tries the "d" version, which must be
    decompressed.  the location of this executable is defined in the crnxpath
    variable.
    year, month, and day are INTEGERS

    WARNING: only rinex version 2 in this world
    21sep01 - this is the old code - changing from ftp to https version
    (called rinex_unavco)
    """
    exedir = os.environ['EXE']
    crnxpath = hatanaka_version()  # where hatanaka will be
    if day == 0:
        doy = month
        cyyyy, cyy, cdoy = ydoych(year,doy)
    else:
        doy,cdoy,cyyyy,cyy = ymd2doy(year,month,day)
    rinexfile,rinexfiled = rinex_name(station, year, month, day)
    unavco= 'ftp://data-out.unavco.org'
    filename1 = rinexfile + '.Z'
    filename2 = rinexfiled + '.Z'
    # URL path for the o file and the d file
    url1 = unavco+ '/pub/rinex/obs/' + cyyyy + '/' + cdoy + '/' + filename1
    url2 = unavco+ '/pub/rinex/obs/' + cyyyy + '/' + cdoy + '/' + filename2

    #print('try regular RINEX at unavco')
    try:
        wget.download(url1,filename1)
        status = subprocess.call(['uncompress', filename1])
    # removed to keep jupyter notebooks clean.
    #except Exception as err:
    #    print(err)
    except:
        okokok =1

    #print('try hatanaka RINEX at unavco')
    if not os.path.exists(rinexfile):
        # look for hatanaka version
        if os.path.exists(crnxpath):
            try:
                wget.download(url2,filename2)
                status = subprocess.call(['uncompress', filename2])
                status = subprocess.call([crnxpath, rinexfiled])
                status = subprocess.call(['rm', '-f', rinexfiled])
            except:
                okokok =1
            #except Exception as err:
            #    print(err)
        else:
            hatanaka_warning()

