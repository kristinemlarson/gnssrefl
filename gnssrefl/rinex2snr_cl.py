# -*- coding: utf-8 -*-
"""
command line tool for the rinex2snr module
it translates rinex files and makes SNR files

compile the fortran first
f2py -c -m gnssrefl.gpssnr gnssrefl/gpssnr.f

"""

import argparse
import os
import time
import sys

import gnssrefl.gps as g
import gnssrefl.rinex2snr as rnx

from gnssrefl.utils import validate_input_datatypes, str2bool


def parse_arguments():

    #msg = rnx.print_archives()

    parser = argparse.ArgumentParser()
    #parser = argparse.ArgumentParser(epilog=msg)
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="start day of year", type=int)
    parser.add_argument("-snr", default=None, help="snr file ending, 99: 5-30 deg.; 66: < 30 deg.; 88: all data; 50: < 10 deg.", type=int)
    parser.add_argument("-orb", default=None, type=str,
                        help="orbit type, e.g. gps, gps+glo, gnss, rapid, ultra, gnss3")
    parser.add_argument("-rate", default=None, metavar='low', type=str, help="low or high (tells code which folder to search).  If samplerate is 1, this is set automatically to high.") 
    parser.add_argument("-dec", default=None, type=int, help="decimate (seconds)")
    parser.add_argument("-nolook", default=None, metavar='False', type=str,
                        help="True means only use RINEX files on local machine")
    parser.add_argument("-fortran", default=None, metavar='False', type=str,
                        help="True means use Fortran RINEX translators ")
    parser.add_argument("-archive", default=None, metavar='all',
                        help="specify archive", type=str)
    parser.add_argument("-doy_end", default=None, help="end day of year", type=int)
    parser.add_argument("-year_end", default=None, help="end year", type=int)
    parser.add_argument("-overwrite", default=None, help="boolean", type=str)
    parser.add_argument("-translator", default=None, help="translator(fortran,hybrid,python)", type=str)
    parser.add_argument("-samplerate", default=None, help="sample rate in sec (RINEX 3 only)", type=int)
    parser.add_argument("-stream", default=None, help="Set to R or S (RINEX 3 only)", type=str)
    parser.add_argument("-mk", default=None, help="use T for uppercase station names and non-standaard archives", type=str)
    parser.add_argument("-weekly", default=None, help="use T for weekly data translation", type=str)
    parser.add_argument("-monthly", default=None, help="use T for monthly data translation", type=str)
    parser.add_argument("-strip", default=None, help="use T to reduce number of obs", type=str)
    parser.add_argument("-screenstats", default=None, help="set to T see more info printed to screen", type=str)
    parser.add_argument("-gzip", default=None, help="boolean, default is SNR files are gzipped after creation", type=str)

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['nolook', 'fortran', 'overwrite', 'mk', 'weekly','strip','screenstats','gzip','monthly']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def rinex2snr(station: str, year: int, doy: int, snr: int = 66, orb: str = None, rate: str = 'low', dec: int = 0,
              fortran: bool = False, nolook: bool = False, archive: str = 'all', doy_end: int = None,
              year_end: int = None, overwrite: bool = False, translator: str = 'hybrid', samplerate: int = 30,
              stream: str = 'R', mk: bool = False, weekly: bool = False, strip: bool = False, 
              screenstats : bool = False, gzip : bool = True, monthly : bool = False ):
    """
    rinex2snr translates RINEX files to a new file in SNR format. This function will also fetch orbit files for you.
    RINEX obs files are provided by the user or fetched from a long list of archives. Although RINEX 3 is supported, 
    the default is RINEX 2.11 files

    Default orbits are GPS only until day of year 137, 2021 when rapid GFZ orbits became available.  If you still want to use
    the nav message, i.e. GPS only, you can request it.

    bkg no longer a boolean input - must be specified with archive name, i.e. bkg-igs or bkg-euref

    For the nolook option :

    If you have the RINEX 2.11 file, the file was originally required to be normal RINEX (ends in o) or 
    gzipped normal RINEX. It can be in the local directory which is where you are running the code 
    or it can be in $REFL_CODE/YYYY/rinex/ssss, where ssss is the lowercase directory name for your station. 
    nolook now allows RINEX 2.11 files that are Hatanaka compressed, Hatanaka compressed + unix compressed,  for 
    the local directory. It also allows Hatanaka compressed in the REFL_CODE directory.  

    If you are running the Docker, it can be a bit confusing to figure out where to put the files.  Please 
    see the discussion in the Docker installation section, as this is my best effort to help you with this.

    Beyond that, you can try the -mk T option which searches other places, i.e. $REFL_CODE/rinex/ etc. I do not recommend
    that you use this option, but it is there.

    For RINEX 3 files, I believe it checks for crx.gz, rnx, or rnx.gz endings in the local directory. It 
    checks the $REFL_CODE/YYYY/rinex directory for the crx.gz and rnx versions. 
    It looks like I do not delete the RINEX 3 files (though I do delete the RINEX 2.11 files).

    FAQ: what is rate anad srate?  rate is telling the code which folder to use because archives always have 
    files in different directories depending on sample rate.  srate is for RINEX 3 files only because RINEX 3 
    has the sample rate on the filename itself (not just the directory).  

    What is the stream parameter? It is a naming convention that is only used by RINEX 3 people. The allowed 
    file types are S or R.  I believe S stands for streamed.

    RINEX3 30 second archives supported  
        bev, bkg-euref, bkg-igs, cddis, epn, ga, gfz, nrcan, sonel

    RINEX3 15 sec archives
        bfg, unavco  - you may need to specify 15 second sample rate

    RINEX3 1 sec 
        bkg-igs, bkg-euref, cddis, ignes (spain), maybe nrcan 

    Examples
    --------
    rinex2snr mchn 2018 15  -archive sopac
        station mchn, year/doy 2022/15,sopac archive using GPS orbits

    rinex2snr mchn 2022 15  -archive sopac
        station mchn, year/doy 2022/15,sopac archive using multi-GNSS GFZ orbits

    rinex2snr mchn 2022 15  -archive sopac -orb gps
        station mchn, year/doy 2022/15,sopac archive using GPS orbits

    rinex2snr mchn 2022 15  -orb rapid -archive sopac
        now explicitly using rapid multi-GNSS orbits 

    rinex2snr mchn 2022 15  -orb rapid -archive sopac
        now explicitly using final multi-GNSS orbits (includes Beidou)

    rinex2snr mchn 2022 15  -orb rapid -archive sopac -overwrite T
        have an SNR file, but you want to make a new one

    rinex2snr p041 2022 15  -orb rapid -rate high -archive unavco
        now using high-rate data from unavco and multi-GNSS orbits

    rinex2snr p041 2022 15 -nolook T
        using your own data stored as p0410150.22o in the working directory 
        your RINEX o file may also be gzipped. I believe Hatanaka compressed is also allowed. 

    rinex2snr 940050 2021 31 -archive jp
        GSI archive in Japan - password required. Station names are six characters

    rinex2snr mchl00aus 2022 15  -orb rapid -archive ga 
        30 sec RINEX3 data for mchl00aus and Geoscience Australia

    rinex2snr mchl00aus 2022 15  -orb rapid -nolook T
        works if the RINEX 3 crx.gz or rnx files are in $REFL_CODE/2022/rinex/mchl

    rinex2snr mchl00aus 2022 15  -orb rapid -samplerate 30 -nolook T
        This should analyze a RINEX 3 file if it exists in your local working directory.
        it will not search anywhere else for the file.  It should be a 30 sec, 1 day file 
        for this example

    rinex2snr mchl00aus 2022 15  -orb rapid -samplerate 1 -nolook T -stream S
        This should analyze a RINEX 3 file if it exists in your local working directory.
        it will not search anywhere else for the file.  It should be a 1 sec, 1 day file 
        for this example with S being set for streaming in the filename.

    rinex2snr warn00deu 2023 87 -dec 5 -rate high -samplerate 1 -orb rapid -archive bkg-igs -stream S 
        1 sec data for warn00deu, 1 sec decimated to 5 sec, multi-GNSS, bkg IGS archive, streamed

    rinex2snr tgho  2019 1 -doy_end 365 -archive nz
        example for multiday SNR file creation

    Parameters
    ----------
    station : str
        4 or 9 character ID of the station, preferably lowercase
    year : int
        Year
    doy : int
        Day of year
    snr : int, optional
        SNR format. This tells the code what elevation angles to save data for. Will be the snr file ending.
        value options:

            66 (default) : saves all data with elevation angles less than 30 degrees

            99 : saves all data with elevation angles between 5 and 30 degrees

            88 : saves all data 
        
            50 : saves all data with elevation angles less than 10 degrees

    orb : str, optional
        Which orbit files to download. Value options:

            gps (default) : will use GPS broadcast orbit

            gps+glos : will use JAXA orbits which have GPS and Glonass (usually available in 48 hours)

            gnss : use GFZ final orbits, which is multi-GNSS (available in 3-4 days?), but from CDDIS archive

            gnss-gfz : GFZ orbits downloaded from GFZ instead of CDDIS, but do they include beidou?. Same as gnss3?

            nav : GPS broadcast, perfectly adequate for reflectometry. Same as gps.

            igs : IGS precise, GPS only

            igr : IGS rapid, GPS only

            jax : JAXA, GPS + Glonass, within a few days, missing block III GPS satellites

            gbm : GFZ Potsdam, multi-GNSS, not rapid, via CDDIS 

            grg : French group, GPS, Galileo and Glonass, not rapid

            esa : ESA, multi-GNSS

            gfr : GFZ rapid, GPS, Galileo and Glonass, since May 17 2021

            wum : Wuhan ultra-rapid, from CDDIS

            wum2 : Wuhan ultra-rapid, from Wuhan FTP

            rapid : GFZ rapid, multi-GNSS

            ultra: GFZ ultra-rapid, multi-GNSS

    rate : str, optional
        The data rate. Rather than numerical value, this tells the code which folder to use
        value options:

            low (default) : standard rate data. Usually 30 sec, but sometimes 15 sec.

            high : high-rate data

    dec : int, optional
        Decimation rate. 0 is default.

    fortran : bool, optional
        Whether to use fortran to translate the rinex files. 

    nolook : bool, optional
        tells the code to retrieve RINEX files from your local machine. default is False

    archive : str, optional
        Select which archive to get the files from. Default is all
        value options:

            bev : (Austria Federal Office of Metrology and Surveying)

            bfg : (German Agency for water research, only Rinex 3, requires password)

            bkg-igs : IGS data at the BKG (German Agency for Cartography and Geodesy)

            bkg-euref : EUREF data at the BKG (German Agency for Cartography and Geodesy)

            cddis : (NASA's Archive of Space Geodesy Data)

            epn : Belgium

            ga : (Geoscience Australia)

            gfz : (GFZ, Germany)

            ignes : IGN in Spain, only RINEX 3

            jp : (GSI, Japan requires password)

            jeff : (My good friend Professor Freymueller!)

            ngs : (National Geodetic Survey, USA)

            nrcan : (Natural Resources Canada)

            nz : (GNS, New Zealand)

            sonel : (GLOSS archive for GNSS data)

            sopac : (Scripps Orbit and Permanent Array Center)

            special : (set aside files at UNAVCO for reflectometry users)

            unavco : (University Navstar Consortium, now Earthscope)

            all : (searches sopac, unavco, and sonel )

    doy_end : int, optional
        end day of year to be downloaded. 

    year_end : int, optional
        end year. 

    overwrite : bool, optional
        Make a new SNR file even if one already exists (overwrite existing file).
        Default is False.

    translator : str, optional
        hybrid (default) : uses a combination of python and fortran to translate the files.

        fortran : uses fortran to translate (requires the fortran translator executable)

        python : uses python to translate. (Warning: This can be very slow)

    srate : int, optional
        sample rate for RINEX 3 files only. Default is 30.

    mk : bool, optional
        Default is False.
        Use True for uppercase station names and for the non-standard file structure preferred 
        by some users. Look at the function the_makan_option in rinex2snr.py for more information.  
        The general requirement is that your RINEX 2.11 file should be normal RINEX or 
        gzipped normal RINEX. This flag allows access to Hatanaka/compressed files 
        stored locally and in $REFL_CODE/YYYY/snr/ssss where YYYY is the year and 
        ssss is station name

    weekly : bool, optional
        Takes 1 out of every 7 days in the doy-doy_end range (one file per week) - used to save cpu time.
        Default is False.

    strip : bool, optional
        Reduces observables since the translator does not allow more than 25
        Default is False.

    screenstats: bool, optional
        if true, prints more information to the screen

    gzip: bool, optional
        default is true, SNR files are gzipped after creation.

    monthly : bool, optional
        default is false. snr files created every 30 days instead of every day

    """
    archive_list_rinex3 = ['unavco', 'epn','cddis', 'bev', 'bkg', 'ga', 'epn', 'bfg','sonel','all','unavco2','nrcan','gfz','ignes']
    archive_list = ['sopac', 'unavco', 'sonel',  'nz', 'ga', 'bkg', 'jeff',
                    'ngs', 'nrcan', 'special', 'bev', 'jp', 'all','unavco2','cddis']

    if False:
        print('RINEX 3 archives \n', archive_list_rinex3)
        print('\n')
        print('RINEX 2.11 archives \n', archive_list)
        sys.exit()

    # make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()
    #

    # when multi-GNSS orbits are reliably available
    gfz_avail = 2021 + 137/365.25

    if orb is None:
        # you asked for default
        if ((year + doy/365.25) > gfz_avail):
            orb = 'rapid'
        else:
            orb = 'nav'

    ns = len(station)
    if (ns == 4) or (ns == 6) or (ns == 9):
        pass
    else:
        print('Illegal input - Station name must have 4 (RINEX 2), 6 (GSI), or 9 (RINEX 3) characters. Exiting.')
        sys.exit()

    if len(str(year)) != 4:
        print('Year must be four characters long. Exiting.', year)
        sys.exit()

    # currently allowed orbit types - shanghai removed 2020sep08
    #
    orbit_list = ['gps', 'gps+glo', 'gnss', 'nav', 'igs', 'igr', 'jax', 'gbm',
                  'grg', 'wum', 'wum2', 'gfr', 'esa', 'ultra', 'rapid', 'gnss2',
                  'nav-sopac', 'nav-esa', 'nav-cddis', 'gnss3', 'gnss-gfz']
    if orb not in orbit_list:
        print('You picked an orbit type I do not recognize. Here are the ones I allow')
        print(orbit_list)
        print('Exiting')
        sys.exit()

    # if you choose GPS, you get the nav message
    if orb == 'gps':
        orb = 'nav'

    if orb == 'rapid':
        orb = 'gfr'

    # if you choose GNSS, you get the GFZ sp3 file  (precise)
    # I think gbm should be changed to 'gnss3' though perhaps not here
    if orb == 'gnss':
        orb = 'gbm'
        print('Using GBM orbit archived at CDDIS')


    # get orbit from IGS
    if orb == 'gnss2':
        # this code wants year month day....
        year, month, day = g.ydoy2ymd(year, doy)
        filename, fdir, foundit = g.avoid_cddis(year, month, day)
        orb = 'gbm'
        if not foundit:
            print('You picked the backup multi-GNSS option.')
            print('I tried to get the file from IGN and failed. Exiting')
            sys.exit()
        else:
            print('found GFZ orbits at IGN - warning, only a single file at a time')

    # if you choose GPS+GLO, you get the JAXA sp3 file 
    if orb == 'gps+glo':
        orb = 'jax'

    # default is to use hybrid for RINEX translator - UNLESS You chose fortran
    if translator is None:
        # the case when someone sets fortran to true and doesn't set translator also
        # but i do not think this happens because Kelly has made hybrid the default
        if fortran:
            translator = 'fortran'
        else:
            translator = 'hybrid'
    elif translator == 'hybrid':
        # override
        if fortran:
            translator = 'fortran'     
    elif translator == 'python':
        fortran = False  
    elif translator == 'fortran':
        fortran = True
    translator_accepted = [None, 'fortran', 'hybrid', 'python']
    if translator not in translator_accepted:
        print(f'translator option must be one of {translator_accepted}. Exiting.')
        sys.exit()

    # check that the fortran exe exist
    if fortran:
        if orb == 'nav':
            snrexe = g.gpsSNR_version()
            if not os.path.isfile(snrexe):
                print('You have selected the fortran and GPS only options.')
                print('However, the fortran translator gpsSNR.e has not been properly installed.')
                print('We are changing your choice to the hybrid translator option.')
                fortran = False
                translator = 'hybrid'
        else:
            snrexe = g.gnssSNR_version()
            if not os.path.isfile(snrexe):
                print('You have selected the fortran and GNSS options.')
                print('However, the fortran translator gnssSNR.e has not been properly installed.')
                print('We are changing your choice to hybrid option.')
                fortran = False
                translator = 'hybrid'

    rate = rate.lower()
    # default is set to low.  set to high for 1sec files so the user doesn't have to
    if samplerate == 1:
        rate = 'high'
    rate_accepted = ['low', 'high']

    if rate not in rate_accepted:
        print('rate not set to either "low" or "high". Exiting')
        sys.exit()

    if doy_end is None:
        doy2 = doy
    else:
        doy2 = doy_end


    bkg = 'EUREF' # just so the code doesn't crash later on when variable
    # is sent to rinex2snr
    if 'bkg' in archive:
        if (archive == 'bkg'):
            print('You have not specified which BKG archive you want.')
            print('You must select bkg-igs or bkg-euref.')
            sys.exit()
        if 'euref' in archive:
            bkg = 'EUREF'
        else:
            bkg = 'IGS'
        # change archive name back to original name
        archive = 'bkg'


    # no longer allow the all option
    # unavco is only rinex2
    # ga is only rinex3
    # bkg is only rinex 3
    # i cannot remember for nrcan. it is probably rinex2
    #highrate_list = ['unavco', 'nrcan', 'cddis','ga','bkg']  
    # adding spanish
    highrate_list = ['unavco', 'nrcan', 'ga','bkg','cddis','ignes']  

    if ns == 9:
        # rinex3
        if rate == 'high':
            if (archive not in highrate_list) and (nolook == False):
                print('You have chosen an archive not supported by the code.')
                print(highrate_list)
                sys.exit()
        else:
            if archive not in archive_list_rinex3:
                print('You have chosen an archive not supported by the code.')
                print(archive_list_rinex3)
                sys.exit()
    else:
        # rinex2
        if rate == 'high':
            if archive not in highrate_list:
                if nolook:
                    print('You have chosen nolook, so I will proceed assuming you have the RINEX file.')
                    # change to lowrate since the code only uses low vs high for retrieving files from
                    # an archive
                    rate = 'low'
                else:
                    print('You have chosen highrate option.  But I do not support this archive: ',archive)
                    sys.exit()
        else:
            if archive not in archive_list:
                print('You picked an archive that is not allowed. Exiting')
                print(archive_list)
                sys.exit()

    year1 = year
    if year_end is None:
        year2 = year 
    else:
        year2 = year_end

# the weekly option
    skipit = 1
    if weekly:
        print('You have invoked the weekly option')
        skipit = 7
    if monthly:
        print('You have invoked the monthly option')
        skipit = 30

    # this makes the correct lists in the function
    doy_list = [doy, doy2]
    year_list = list(range(year1, year2+1))

    # the Makan option
    if mk:
        print('You have invoked the Makan option')

    if stream not in ['R', 'S']:
        stream = 'R'

    args = {'station': station, 'year_list': year_list, 'doy_list': doy_list, 'isnr': snr, 'orbtype': orb,
            'rate': rate, 'dec_rate': dec, 'archive': archive, 'fortran': fortran, 'nol': nolook,
            'overwrite': overwrite, 'translator': translator, 'srate': samplerate, 'mk': mk,
            'skipit': skipit, 'stream': stream, 'strip': strip, 'bkg': bkg, 'screenstats': screenstats, 'gzip' : gzip}

    s1 = time.time()
    rnx.run_rinex2snr(**args)
    s2 = time.time()
    print('That took ', round(s2-s1,2), ' seconds')
    #print('Feedback written to subdirectory logs')


def main():
    args = parse_arguments()
    rinex2snr(**args)


if __name__ == "__main__":
    main()


