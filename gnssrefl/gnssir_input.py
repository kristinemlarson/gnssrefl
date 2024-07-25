import argparse
import json
import os
import subprocess
import sys

import gnssrefl.gps as g
import gnssrefl.gnssir_v2 as guts2

from gnssrefl.utils import str2bool


def parse_arguments():
    # user inputs the observation file information
    parser = argparse.ArgumentParser()
    # required arguments
    parser.add_argument("station", help="station (lowercase)", type=str)
    parser.add_argument("-lat", help="Latitude (degrees)", type=float)
    parser.add_argument("-lon", help="Longitude (degrees)", type=float)
    parser.add_argument("-height", help="Ellipsoidal height (meters)", type=float)
    parser.add_argument("-e1", default=None, type=float, help="Lower limit elevation angle (deg),default 5")
    parser.add_argument("-e2", default=None, type=float, help="Upper limit elevation angle (deg), default 25")
    parser.add_argument("-h1", default=None, type=float, help="Lower limit reflector height (m), default 0.5")
    parser.add_argument("-h2", default=None, type=float, help="Upper limit reflector height (m), default 8")
    parser.add_argument("-nr1",default=None, type=float, help="Lower limit RH used for noise region in QC(m)")
    parser.add_argument("-nr2",default=None, type=float, help="Upper limit RH used for noise region in QC(m)")
    parser.add_argument("-peak2noise", default=None, type=float, help="peak to noise ratio used for QC")
    parser.add_argument("-ampl", default=None, type=float, help="Required spectral peak amplitude for QC")
    parser.add_argument("-allfreq", default=None, type=str, help="Set to T to include all GNSS signals")
    parser.add_argument("-l1", default=None, type=str, help="Set to T to use only GPS L1")
    parser.add_argument("-l2c", default=None, type=str, help="Set to T to only use GPS L2C")
    parser.add_argument("-xyz", default=None, type=str, help="Set to True if using Cartesian coordinates instead of LLH")
    parser.add_argument("-refraction", default=None, type=str, help="Set to False to turn off refraction correction")
    parser.add_argument("-extension", default=None,type=str, help="Provide extension name so you can try different strategies")
    parser.add_argument("-ediff", default=None, type=float, help="Allowed min/max elevation diff from obs min/max elev angle (degrees) default is 2")
    parser.add_argument("-delTmax", default=None, type=float, help="max arc length (min) default is 75. Shorten for tides.")
    parser.add_argument("-frlist", nargs="*",type=int,  help="User defined frequencies using our nomenclature, e.g. 1 101 for GPS and Glonass L1")
    parser.add_argument("-azlist2", nargs="*",type=float,  default=None,help="list of azimuth regions, default is 0-360") 
    parser.add_argument("-ellist", nargs="*",type=float,  default=None,help="List of elevation angles, advanced users only!") 
    parser.add_argument("-refr_model", default="1", type=str, help="refraction model. default is 1, zero turns it off)")
    parser.add_argument("-apriori_rh", default=None, type=float, help="apriori reflector height (m) used by NITE model")
    parser.add_argument("-Hortho", default=None, type=float, help="station orthometric height (m)")
    parser.add_argument("-pele", nargs="*", type=float, help="min and max elevation angle in direct signal removal, default is 5-30")
    parser.add_argument("-daily_avg_medfilter", default=None, type=float, help="daily_avg, median filter, meters")
    parser.add_argument("-daily_avg_reqtracks", default=None, type=int, help="daily_avg, ReqTracks parameter ")
    parser.add_argument("-subdaily_alt_sigma", default=None, type=str, help="subdaily, Nievinski sigma")
    parser.add_argument("-subdaily_sigma", default=None, type=str, help="subdaily, sigma for part 1")
    parser.add_argument("-subdaily_ampl", default=None, type=float, help="subdaily, LSP amplitude override")
    parser.add_argument("-subdaily_delta_out", default=None, type=int, help="subdaily, spline output interval (sec)")
    parser.add_argument("-subdaily_knots", default=None, type=float, help="subdaily, knots, how many per day")
    parser.add_argument("-subdaily_subdir", default=None, type=str, help="subdaily, output directory")
    parser.add_argument("-subdaily_spline_outlier1", default=None, type=float, help="subdaily, outlier value (m), part1")
    parser.add_argument("-subdaily_spline_outlier2", default=None, type=float, help="subdaily, outlier value (m), part2")

    args = parser.parse_args().__dict__

    g.print_version_to_screen()

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['allfreq', 'l1', 'l2c', 'xyz', 'refraction','subdaily_alt_sigma']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def make_gnssir_input(station: str, lat: float=0, lon: float=0, height: float=0, e1: float = 5.0, e2: float = 25.0,
       h1: float = 0.5, h2: float = 8.0, nr1: float = None, nr2: float = None, peak2noise: float = 2.8, 
       ampl: float = 5.0, allfreq: bool = False, l1: bool = False, l2c: bool = False, 
       xyz: bool = False, refraction: bool = True, extension: str = '', ediff: float=2.0, 
       delTmax: float=75.0, frlist: list=[], azlist2: list=[0,360], ellist : list=[], refr_model : str="1", 
                      apriori_rh: float=None, Hortho : float = None, pele: list=[5,30], daily_avg_reqtracks: int=None, 
                      daily_avg_medfilter: float =None, subdaily_alt_sigma : bool=None, 
                      subdaily_ampl : float=None, subdaily_delta_out : float=None, 
                      subdaily_knots : int=None, subdaily_sigma: float=None, subdaily_subdir: str=None, 
                      subdaily_spline_outlier1: float=None, subdaily_spline_outlier2: float=None):

    """
    This new script sets the Lomb Scargle analysis strategy you will use in gnssir. It saves your inputs 
    to a json file which by default is saved in REFL_CODE/<station>.json. This code replaces make_json_input.

    This version no longer requires you to have azimuth regions of 90-100 degrees. You can set a single set of 
    azimuths in the command line variable azlist2, i.e. -azlist2 0 270 would accommodate all rising and setting arcs 
    between 0 and 270 degrees. If you have multiple distinct regions, that is also acceptable, i.e. -azlist2 0 150 180 360  
    would use all azimuths between 0 and 360 except for 150 to 180

    Your first azimuth constraint can be negative, i.e. -azlist2 -90 90, is allowed.

    Note: you can keep using your old json files - you just need to add this new -azlist2 setting manually.

    Latitude, longitude, and height are assumed to be stored in either the UNR database we provide with
    gnssrefl or in your local coordinate file. See the instructions in the file formats section of gnssrefl for 
    information about the format, name, and location of that local coordinate file.  

    Originally we had refraction as a boolean, i.e. on or off. This was stored in the gnssir 
    analysis description json. The code however, uses a 1 for a simple non-time-varying 
    Bennett correction and 0 for no correction.

    From version 1.8.4 we begin to implement more refraction models.  Model 1 (Bennett) will continue to be 
    the default.  The model number is written (as an integer) to the LSP results file so that people can 
    keep track easily of whether they are inadvertently mixing files with different strategies. And that 
    is why it is an integer, because all results in the LSP results files are numbers.  Going forward, 
    we are adding a time-varying capability.

        Model 1: Bennett, non-time-varying

        Model 2: Bennett, time-varying

        Model 3: Ulich, non-time-varying

        Model 4: Ulich, time-varying

        Model 5: NITE, Feng et al. 2023 DOI: 10.1109/TGRS.2023.3332422, time-varying

        Model 6: MPF, Williams and Nievinski, 2017,  DOI: 10.1002/2016JB013612, time-varying


    We allow users to input the model names NITE and MPF (nite and mpf also allowed).  The other models do not allow that.
    If you want model 2, you have to ask for model 2. We thank Peng Feng for providing python code to be used for some of these models.

    If you want to test the effect of different refraction models, you are encouraged to create
    two json files using the extension option. You can then run gnssir using those two extensions.
    In general I think the refraction default is fine for soil moisture and snow accumulation.
    If you are going to look at tall sites, you most definitely need the refraction correction. If you
    plan to look at very tall sites, you should pick the best one.

    Examples
    --------
    gnssir_input p041 
        uses only GPS frequencies and all azimuths and the coordinates in the UNR database

    gnssir_input p041   -azlist2 0 180 -fr 1 101
        uses UNR coordinates, GPS L1 and Glonass L1 frequencies, and azimuths between 0 and 180.

    gnssir_input p041 -lat 39.9494 -lon -105.19426 -height 1728.85  -l2c T -e1 5 -e2 15
        uses only L2C GPS data between elevation angles of 5 and 15 degrees.
        user input lat/long/height. The lat/long/height can also be entered into a local
        coordinate file.  See documentation in the file formats section.

    gnssir_input p041  -h1 0.5 -h2 10 -e1 5 -e2 25
        uses UNR database, only GPS data between elevation angles of 5-25 degrees and reflector heights of 0.5-10 meters

    gnssir_input p041 -ediff 1
        uses UNR database, only GPS data, default station coordinates, enforces elevation angles to be 
        within 1 degrees of default elevation angle limits (5-25)

    gnssir_input sc02 -ellist 5 10 7 12
        let's say you want to compute smaller arcs than just a single set of elevation angles.
        you can use this to set this up, so instead of 5 and 12, you could set it up to 
        do two arcs, one for 5-10 degrees and the other for 7-12.
        WARNING: you need to pay attention to QC metrics (amplitude and peak2noise).  You likely need to lower them since 
        your periodogram for fewer data will be less robust than with the longer elevation angle region.

    Parameters
    ----------
    station : str
        4 character station ID.

    lat : float, optional
        latitude in degrees.

    lon : float, optional
        longitude in degrees.

    height : float, optional
        ellipsoidal height in meters.

    e1 : float, optional
        elevation angle lower limit in degrees. default is 5.

    e2 : float, optional
        elevation angle upper limit in degrees. default is 25.

    h1 : float, optional
        reflector height lower limit in meters. default is 0.5.

    h2 : float, optional
        reflector height upper limit in meters. default is 8.

    nr1 : float, optional
        noise region lower limit for QC in meters. default is None.

    nr2 : float, optional
        noise region upper limit for QC in meters. default is None.

    peak2noise : float, optional
        peak to noise ratio used for QC.
        default is 2.7 (just a starting point for water - should be 3 or 3.5 for snow or soil...)

    ampl : float, optional
        spectral peak amplitude for QC. default is 6.0
        this is receiver and elevation angle region dependent - so you need to change it based on your site 

    allfreq : bool, optional
        True requests all GNSS frequencies.
        default is False (defaults to use GPS frequencies).

    l1 : bool, optional
        set to True to use only GPS L1 frequency. default is False.

    l2c : bool, optional
        set to use only GPS L2C frequency. default is False.

    xyz : bool, optional
        set to True if using Cartesian coordinates instead of Lat/Long/Ht.
        default is False.

    refraction : bool, optional
        set to False to turn off refraction correction.
        default is True.

    extension : str, optional
        provide extension name so you can try different strategies. 
        Results will then go into $REFL_CODE/YYYY/results/ssss/extension
        Default is '' 

    ediff : float, optional
        quality control parameter (Degrees)
        Allowed min/max elevation angle diff from requested min/max elev angle
        default is 2

    delTmax : float, optional
        maximum allowed arc length (minutes)
        default is 75, which can be a bit long for tides

    frlist : list of integers
        avoids all the booleans - if you know the frequencies, enter them.
        e.g. 1 2 or 1 20 5 or 1 20 101 102

    azlist2 : list of floats
        Default is 0 to 360. list of azimuth limits as subquadrants are no longer required.

    ellist: list of floats
        min and max elevation angles to be used with the azimuth regions you listed, i.e.
        [5 10 6 11 7 12 8 13] would allow overlapping regions - all five degrees long 
        Default is empty list. 

    refr_model : str
        refraction model. While defined as a string (so that people can specify names of models)
        we convert this to an integer for book-keeping. 1 is the default refraction model 
        (it corrects elevation angles using standard bending models).  0 is no refraction correction.  
        The other models are defined in the summary section of this code.

    apriori_rh : float
        apriori reflector height (meters). only used in NITE model 

    Hortho : float
        station orthometric height, in meters. Currently only used in subdaily.  If not provided on the command line, 
        it will use ellipsoidal height and EGM96 to compute.

    pele : float
        min and max elevation angles in direct signal removal, i.e. 3 40. Default is 5 30. 

    daily_avg_reqtracks : int, optional
        number of tracks required for daily_avg code

    daily_avg_medfilter : float, optional
        median filter value required for daily_avg code (meters)

    subdaily_alt_sigma : bool, optional
        use Nievinski sigma definition

    subdaily_ampl : float, optional
        override the required LSP amplitude  

    subdaily_delta_out : int, optional
        spacing for final subdaily spline output

    subdaily_knots : int, optional
        number of knots per day for subdaily spline fits

    subdaily_sigma : float, optional
        how many standard deviations for outliers in subdaily code setting

    subdaily_subdir : str, optional
        non-standard location for subdaily outputs

    subdaily_spline_outlier1 : float, optional
        alternate setting for outlier detection in part1

    subdaily_spline_outlier2 : float, optional
        alternate setting for outlier detection in part2

    """

    # make sure environment variables exist
    g.check_environ_variables()

    ns = len(station)
    if ns != 4:
        print('station name must be four characters long. Exiting.')
        sys.exit()


# location of the site - does not have to be very good.  within 100 meters is fine
    query_unr = False
# if you input lat and long as zero ...
    if lat + lon == 0:
        print('Assume you want to use our database for a priori receiver coordinates.')
        query_unr = True

    if xyz:
        xyz = [lat, lon, height]
        print(xyz)
        lat, lon, height = g.xyz2llhd(xyz)
        print(lat,lon,height)

    if query_unr:
        # try to find the coordinates  at UNR
        lat, lon, height = g.queryUNR_modern(station)
        if lat == 0:
            print('Tried to find coordinates in station database. None found so exiting')
            sys.exit()

    # calculate Hortho using EGM96 if none provided
    if Hortho is None:
        geoidC = g.geoidCorrection(lat,lon)
        Hortho = height - geoidC

    if apriori_rh is None:
        apriori_rh = 5 # completely made up, meters

# start the lsp dictionary
    reqA = ampl

    lsp = {}
    lsp['station'] = station.lower()
    lsp['lat'] = lat
    lsp['lon'] = lon
    lsp['ht'] = height
    lsp['Hortho'] = round(Hortho,4) # no point having it be so many decimal points
    lsp['apriori_rh'] = apriori_rh
    

    if h1 > h2:
        print(f'h1 cannot be greater than h2. You have set h1 to {h1} and h2 to {h2}. Exiting.')
        sys.exit()

    if ( (h2-h1)  < 5):
        print(f'h2-h1 must be at least 5 meters apart. You have set h1 to {h1} and h2 to {h2}. Exiting.')
        sys.exit()

    lsp['minH'] = h1 ; lsp['maxH'] = h2 ; lsp['e1'] = e1 ; lsp['e2'] = e2

# the default noise region will the same as the RH exclusion area for now
    if nr1 is None:
        nr1 = h1
    if nr2 is None:
        nr2 = h2

    lsp['NReg'] = [nr1, nr2]
    lsp['PkNoise'] = peak2noise

    # where the instructions will be written
    xdir = os.environ['REFL_CODE']
    outputdir = xdir + '/input'
    if not os.path.isdir(outputdir):
        subprocess.call(['mkdir', outputdir])

    if len(extension) == 0:
        outputfile = outputdir + '/' + station + '.json'
    else:
        outputfile = outputdir + '/' + station + '.' + extension + '.json'

    lsp['polyV'] = 4 # polynomial order for DC removal
    # change this so the min elevation angle for polynomial removal is the same as the 
    # requested analysis region. previously it was hardwired to 5-30

    lsp['pele'] = pele # elevation angles used for DC removal

    default_pele1 = 5; default_pele2 = 30
    if (pele[0] == default_pele1) & (pele[1] == default_pele2):
        print('Using default DC removal elevation angle limits,', default_pele1, default_pele2)
        print('Checking that they are sensible')
        usethis1 = default_pele1; usethis2 = default_pele2 
        if (lsp['e1']) < default_pele1:
            usethis1 = lsp['e1']
        if (lsp['e2']) > default_pele2:
            usethis2 = lsp['e2']
        lsp['pele'] = [usethis1, usethis2] # modified elevation angles 
    else:
        print('You manually set the DC removal elevation angle limits ', pele)
        print('We will respect your wishes. For future reference, ')
        print('they do not need to be the same as the requested elevation ')
        print('angle range - but they cannot be outside of them. For example,')
        print('pele min cannot be greater than e1 and pele max cannot be less than e2.')

    #if ((lsp['e1'] < 5 or lsp['e2'] > 30) and (lsp['pele'][0] >= 5 and lsp['pele'][1] <= 30)):
    ## Check if the elevation angle limits for DC removal are outside the default range
    #    print('Change the pele (elevation angle limits) for DC removal')
    #    sys.exit()
    #else:
    #    lsp['pele'] = pele # elevation angles used for DC removal

    lsp['ediff'] = ediff # degrees
    lsp['desiredP'] = 0.005 # precision of RH in meters
    # azimuth regions in degrees (in pairs)
    # you can of course have more subdivisions here
    #if (az_list[0]) == 0 & (az_list[-1] == 360):

    N2 = len(azlist2)
    if (N2 % 2) == 0:
        lsp['azval2'] = azlist2
    else:
        print('Illegal azimuth inputs. Must be an even number of azimuth pairs.')
        sys.exit()

    # default frequencies to use - and their required amplitudes. The amplitudes are not set in stone
    # this is the case for only GPS, but the good L2 
    lsp['freqs'] = [1, 20, 5]
    if allfreq is True:
        # 307 was making it crash.  did not check as to why
        # includes glonass, galileo, and beidou
        lsp['freqs'] = [1, 20, 5, 101, 102, 201, 205, 206, 207, 208, 302, 306]

    if l1 is True:
        lsp['freqs'] = [1]

    if l2c is True:
        lsp['freqs'] = [20]

    if len(frlist) == 0:
        print('Using standard frequency choices.')
    else:
        print('Implementing user-provided frequency list.')
        lsp['freqs'] = frlist

    # create a list with all values equal to reqA
    # but the length of the list depends on the length of the list of frequencies
    lsp['reqAmp'] = [reqA]*len(lsp['freqs'])

    # this is true or false.  I think
    lsp['refraction'] = refraction

    # write new RH results  each time you run the code
    lsp['overwriteResults'] = True

    # if snr file does not exist, try to make one
    # i don't think this option exists anymore
    lsp['seekRinex'] = False

    # compress snr files after analysis - saves disk space
    lsp['wantCompression'] = False

    # periodogram plots come to the screen
    lsp['plt_screen'] = False

    # command line req to only do a single satellite - default is do all satellites
    lsp['onesat'] = None

    # default will now be False ....
    # send some information on periodogram RH retrievals to the screen
    lsp['screenstats'] = False

    # save the output plots
    lsp['pltname'] = station + '_lsp.png'

    # how long can the arc be, in minutes
    lsp['delTmax'] = delTmax  
 
    # gzip SNR files after running the code
    # this really should be set to True.  the code is obviously ignoring it
    lsp['gzip'] = False   

    lsp['ellist'] = ellist

    if refr_model[0] == '-':
         print('You selected a negative refraction model. Exiting')
         sys.exit()

    if refr_model.isnumeric():
        # number has been input
        refr_model = int(refr_model)
        if (refr_model > 6) :
            print('We only have six refraction models and you selected ', refr_model, ' Exiting')
            sys.exit()
    else:
        if refr_model.upper() == 'NITE':
            refr_model = 5
        elif refr_model.upper() == 'MPF':
            refr_model = 6
        else:
            print('Your refraction model ', refr_model, ' is not recognized by the code. Exiting')

    lsp['refr_model'] = refr_model
    print('refraction model ', refr_model)

    # added for people that want to save their daily average and subdaily strategies.
    # if not set, then they are saved as None.
    lsp['daily_avg_reqtracks'] = daily_avg_reqtracks
    lsp['daily_avg_medfilter'] = daily_avg_medfilter

    lsp['subdaily_alt_sigma'] = subdaily_alt_sigma
    lsp['subdaily_ampl'] = subdaily_ampl
    lsp['subdaily_delta_out'] = subdaily_delta_out
    lsp['subdaily_knots'] = subdaily_knots
    lsp['subdaily_sigma'] = subdaily_sigma
    lsp['subdaily_spline_outlier1'] = subdaily_spline_outlier1
    lsp['subdaily_spline_outlier2'] = subdaily_spline_outlier2
    lsp['subdaily_subdir'] = subdaily_subdir

    print('writing out to:', outputfile)
    print(lsp)
    with open(outputfile, 'w+') as outfile:
        json.dump(lsp, outfile, indent=4)


def main():
    args = parse_arguments()
    make_gnssir_input(**args)


if __name__ == "__main__":
    main()
