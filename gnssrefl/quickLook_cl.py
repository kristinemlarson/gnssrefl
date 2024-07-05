# -*- coding: utf-8 -*-
"""
quickLook command line function 
"""
import argparse
import sys

# internal codes
import gnssrefl.gps as g
# old version
#import gnssrefl.quickLook_function as quick
import gnssrefl.quickLook_function2 as quick2

from gnssrefl.utils import validate_input_datatypes, str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("year", help="year", type=int)
    parser.add_argument("doy", help="day of year", type=int)
    parser.add_argument("-snr", default=None, type=int, help="snr ending - default is 66")
    parser.add_argument("-fr", default=None, type=int, help="e.g. -fr 1 for GPS L1  or -fr 101 for Glonass L1")
    parser.add_argument("-ampl", default=None, type=float, help="minimum spectral amplitude allowed")
    parser.add_argument("-e1",  default=None, type=float, help="lower limit elevation angle (default is 5 deg) ")
    parser.add_argument("-e2",  default=None, type=float, help="upper limit elevation angle (default is 25 deg)")
    parser.add_argument("-h1",  default=None, type=float, help="lower limit reflector height (default is 0.5m) ")
    parser.add_argument("-h2",  default=None, type=float, help="upper limit reflector height (default is 8 m)")
    parser.add_argument("-azim1",  default=None, type=float, help="lower limit azimuth (default is 0 deg)")
    parser.add_argument("-azim2",  default=None, type=float, help="upper limit azimuth (default is 360 deg)")
    parser.add_argument("-sat", default=None, type=int, help="satellite")
    parser.add_argument("-screenstats", default=None, type=str, help="if True, Success and Failure info printed to the screen")
    parser.add_argument("-peak2noise",  default=None, type=float, help="Quality Control ratio (default is 3)")
    parser.add_argument("-ediff",  default=None, type=float, help="ediff Quality Control parameter (default 2 deg)")
    parser.add_argument("-delTmax",  default=None, type=float, help="maximum arc length, in minutes, (default is 75 )")
    parser.add_argument("-plt", default=None, type=str, help="Set to false to turn off plots to the screen.")
    parser.add_argument("-hires_figs", default=None, type=str, help="Set to true to make eps instead of png.")

    g.print_version_to_screen()


    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['screenstats','plt','hires_figs']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def quicklook(station: str, year: int, doy: int,
              snr: int = 66, fr: int = 1, ampl: float = 7., e1: float = 5, e2: float = 25, h1: float = 0.5, 
              h2: float = 8., sat: int = None, peak2noise: float = 3., screenstats: bool = False, fortran: bool = None, 
              plt: bool = True, azim1: float = 0., azim2: float = 360., ediff: float = 2.0, delTmax : float=75.0, hires_figs : bool=False ):
    """

    quickLook assessment of GNSS-IR results using SNR data. It creates two plots: one with periodograms for
    four different quadrants (northwest, northeast, southeast, southwest) and the other with the RH
    results shown as a function of azimuth. This plot also summarizes why the RH retrievals were accepted
    or rejected in terms of the quality control parameters.  

    Examples
    --------
    quickLook p041 2023 1 
        analyzes station p041 on day of year 1 in the year 2023 with defaults (L1, e1=5, e2=25)

    quickLook p041 2023 1 -h1 1 -h2 10
        analyzes station p041 on day of year 1 in the year 2023.  
        The periodogram would be restricted to RH of 1-10 meters.  

    If your site name is in the GNSS-IR database (which is generated from the Nevada Reno geodesy group), 
    a standard refraction correction is applied. If not, it does not.  This is most relevant for very very
    tall sites, i.e. > 200 meters. Refraction models are always applied in the gnssir module.

    If users would like the refraction correction to be applied here for stations that are not in the standard database,
    they need to submit a pull request making that possible. One option is to read from an existing gnssir_input 
    json file. That is what is done in nmea2snr and invsnr_input.

    Parameters
    ----------
    station : str
        4 character ID of the station
    year : int
        Year
    doy : int
        Day of year
    snr : int, optional
        SNR format. This tells the code which SNR file to use.  66 is the default.
        Other options: 50, 88, and 99.

    f : int, optional. 
        GNSS frequency. Default is GPS L1
        value options:

            1,2,20,5 : GPS L1,L2,L2C,L5 (1 is default)

            101,102 : GLONASS L1 and L2

            201,205,206,207,208 : GALILEO E1 E5a E6,E5b,E5

            302,306,307 : BEIDOU B1, B3, B2

    reqAmp : int or array_like, optional
        Lomb-Scargle Periodogram (LSP) amplitude significance criterion in volts/volts.
        Default is 7 

    e1 : int, optional
        elevation angle lower limit in degrees for the LSP.
        default is 5.

    e2: int, optional
        elevation angle upper limit in degrees for the LSP.
        default is 25.

    h1 : float, optional
        The allowed LSP reflector height lower limit in meters.
        default is 0.5.

    h2 : float, optional
        The allowed LSP reflector height upper limit in meters.
        default is 6.

    sat : integer, optional
        specific satellite number, default is None.

    peak2noise : int, optional
        peak to noise ratio of the periodogram values (periodogram peak divided by the periodogram noise).
        For snow and ice, 3.5 or greater, tides can be tricky if the water is rough (and thus
        you might go below 3 a bit, say 2.7 
        default is 3.

    screenstats : boolean, optional
        Whether to print stats to the screen.
        default is False.

    plt : boolean, optional
        Whether to print plots to the screen.
        default is True. Regardless, png files are made

    azim1 : float, optional
        minimum azimuth angle (deg)
        default is 0.

    azim2 : float, optional
        maximum azimuth angle (deg)
        default is 360.

    ediff : float, optional
        elevation angle difference, quality control parameter 
        default is 2 degrees.

    delTmax: float, optional
        maximum allowed arc length, in minutes
        default is 75 minutes.

    hires_figs : bool, optional
        eps instead of png files
    """

    vers = 'gnssrefl version ' + str(g.version('gnssrefl'))
    #print('You are running ', vers)


#   make sure environment variables exist.  set to current directory if not
    g.check_environ_variables()

    # checks for output
    g.checkFiles(station, '')

    exitS = g.check_inputs(station, year, doy, snr)


    if exitS:
        sys.exit()

    # set some reasonable default values for LSP (Reflector Height calculation).
    # most of these can be overriden at the command line
    if fr is not type(list):
        fr = [fr]  # default is to do L1

    pele = [5, 30]  # polynomial fit limits
    if ampl is not type(list):
        ampl = [ampl]  # this is arbitrary  - but often true for L1 obs

    if e1 < 5:
        print('We have to change the polynomial limits because you went below 5 degrees.')
        print('This restriction is for quickLook only ')
        pele[0] = e1

    pltscreen = plt
    args = {'station': station.lower(), 'year': year, 'doy': doy, 'snr_type': snr, 'f': fr[0], 'reqAmp': ampl, 'e1': e1,
            'e2': e2, 'minH': h1, 'maxH': h2, 'PkNoise': peak2noise, 'satsel': sat, 'fortran': fortran, 'pele': pele,
            'pltscreen': pltscreen, 'screenstats': screenstats, 'azim1': azim1, 'azim2': azim2, 'ediff': ediff, 
            'delTmax': delTmax, 'hires_figs': hires_figs}

    deltaRH = h2-h1
    if (deltaRH <= 0):
        print('Your reflector height region is invalid (i.e. h1 is greater than h2). h1:', h1, ' h2: ',h2)
        print('Exiting')
        sys.exit()

    if (deltaRH < 5.5):
        print('The reflector height region must be at least 5.5 meters long. These values are used for computing ')
        print('a valid periodogram and for quality control.  Change h1 or h2 or both. Exiting')
        sys.exit()

    # returns two variables: data, datakey = quick.quicklook_function(**args)
    return quick2.quickLook_function(**args)


def main():
    args = parse_arguments()
    data, datakey = quicklook(**args)


if __name__ == "__main__":
    main()
