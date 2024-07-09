import argparse
import json
import os
import sys


import gnssrefl.spline_functions as spline_functions
import gnssrefl.refraction as refr

from gnssrefl.utils import str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", default=None, type=str)
    parser.add_argument("year", default=None, type=int, help="year")
    parser.add_argument("doy", default=None, type=int, help="doy")
    parser.add_argument("signal", default=None, type=str, help="L1, L2, L5, L1+L2, L1+L2+L5, etc")

    parser.add_argument("-peak2noise", default=None, type=float, help="Peak2noise ratio for Quality Control, default now 2.5")
    parser.add_argument("-constel", default=None, type=str, help="Only a single constellation (G,E, or R)")
    parser.add_argument("-screenstats", default=None, type=str, help="screen stats, False is default")
    parser.add_argument("-dec", default=None, type=int, help="SNR file decimator (seconds)")
    parser.add_argument("-polydeg", default=None, type=int, help="polynomial degree for direct signal removal (default is 2)")
    parser.add_argument("-snrfit", default=None, type=str, help="Do invsnr fit? True is the default ")
    parser.add_argument("-plt", default=None, type=str, help="Plot to the screen?  default is True")
    parser.add_argument("-doy_end", default=None, type=str, help="day of year to end analysis")
    parser.add_argument("-lspfigs", default=None, type=str, help="Make LSP plots, default False.")
    parser.add_argument("-snrfigs", default=None, type=str, help="Make SNR plots, default False.")
    parser.add_argument("-knot_space", default=None, type=int, help="knot spacing in hours (default is 3)")
    parser.add_argument("-rough_in", default=None, type=str, help="Roughness (default is 0.1)")
    parser.add_argument("-risky", default=None, type=str, help="Risky taker related to gaps/knot spacing, False is default.")
    parser.add_argument("-snr", default=None, type=int, help="SNR file ending. Default is 66")
    parser.add_argument("-outfile_type", default=None, type=str, help="Output file type (txt or csv)")
    parser.add_argument("-outfile_name", default=None, type=str, help="Output file name")
    parser.add_argument("-outlier_limit", default=None, type=str, help="outliers limit (m)")
    parser.add_argument("-no_dots", default=None, type=str, help="bool, no lomb scargle  results plotted")
    parser.add_argument("-delta_out", default=None, type=str, help="Output increment, in seconds (default is 300)")
    parser.add_argument("-refraction", default=None, type=str, help="bool, Set to False to turn off")
    parser.add_argument("-json_override", default=None, type=str, help="bool, Override json file name")
    parser.add_argument("-lastday_seconds", default=None, type=int, help="if last doy incomplete, provides last timepoint, this option currently does not work")

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['screenstats', 'snrfit', 'plt', 'lspfigs', 'snrfigs', 'risky', 'no_dots','refraction', 'json_override',]
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def invsnr(station: str, year: int, doy: int, signal: str, peak2noise: float = 2.5, constel: str = None, 
        screenstats: bool = False, dec: int = 1, polydeg: int = 2, snrfit: bool = True, plt: bool = True,
        doy_end: int = None, lspfigs: bool = False, snrfigs: bool = False, knot_space: int = 3, 
        rough_in: float = 0.1, risky: bool = False, snr: int = 66, outfile_type: str = 'txt', 
        outfile_name: str = '', outlier_limit: float = 0.5, no_dots: bool = False, delta_out: int = 300, 
           refraction: bool = True, json_override: bool = False, lastday_seconds: int=0):
    """
    You must have run invsnr_input before using this code. This is the wrapper code that does the 
    invsnr modelling. Note: outfile_name and outfile_type are unnecessary. Consolidate them.

    In an earlier version of the code the pk2nlim was set to 4.  Later the definition of the metric was changed,
    and this made the default setting far too stringent. In short, no arcs were being found.  As of 2023/10/28 it
    is set to 2.5.  This may not be optimal, but it is not as bad as 4.  Please set it yourself as you prefer.
    Note: it will not the same as gnssir as this code was written separately and for a different purpose.

    pktnlim is now known externally as peak2noise
    
    Examples
    --------
    invsnr sc02 2023 15 L1+L2+L5 
        would analyze day of year 15 and the L1, L2, and L5 signals
    invsnr sc02 2023 15 ALL
        would analyze day of year 15 and all signals
    invsnr sc02 2023 15 L1+L2
        would analyze day of year 15 and just L1 and L2
    invsnr sc02 2023 15 L1+L2 -pk2nlim 2
        would analyze day of year 15 and just L1 and L2, lower peak to noise limit ratio
    invsnr sc02 2023 15 L1+L2  -doy_end 18
        would analyze day of years 15 through 18 and L1 and L2 signals

    Parameters
    ----------
    station : str
        four character ID 
    year : int
        Year
    doy : int
        Day of year
    signal : str
        signal to use, L1  L2 L5 L6 L7 L1+L2 L1+L2+L5 L1+L5 ALL
    peak2noise: float, optional
        Peak2noise ratio limit for Quality Control.
        Default is 2.5
    constel: str, optional
        Only a single constellation.
        Default is gps, glonass, and galileo.
        value options:

            G : GPS

            E : Galileo

            R : Glonass

            C : Beidou

            withBeidou : adds Beidou to the default.

    screenstats: bool, optional
        Whether to print out stats to the screen.
        Default is False
    dec : int, optional
        SNR file decimator (seconds)
        Default is 1 (everything)
    polydeg : integer, optional
        polynomial degree for direct signal removal
        Default is 2
    snrfit : bool, optional
        Whether to do the inversion or not
        Default is True
    plt : bool, optional
        Whether to plot to the screen or not
        Default is True
    doy_end : int, optional
        day of year to end analysis.
        Default is None.
    lspfigs : bool, optional
        Whether or not to make LSP plots
        Note: Don't turn these on unless you really need plots because it is 
        slow to make one per satellite arc.
        Default is False
    snrfigs : boolean, optional
        Whether or not to make SNR plots
        Don't turn these on unless you really need plots because it is 
        slow to make one per satellite arc.
        Default is False
    knot_space : float, optional
        Knot spacing in hours
        Default is 3
    rough_in : float, optional
        Roughness
        Default is 0.1
    risky : bool, optional
        Risky taker related to gaps/knot spacing
        Default is False
    snr : int, optional
        SNR file ending. Default is 66
    outfile_type : string, optional
        output file type, txt or csv
        Default is txt
    outfile_name : string, optional
        output file name.
        Default is ??
    outlier_limit : float, optional
        Outliers plotted. (meters)
        Default is 0.5
    no_dots : bool, optional
        To plot lombscargle or not.
        Default is False
    delta_out : int, optional
        Output increment, in seconds.
        Default is 300
    refraction : bool, optional
        Default is True
    json_override : bool, optional
        Override json file name
        Default is False
    lastday_seconds : int, optional
        last time point (seconds of the day)
        should really be read from the file - 
        if you don't provide this the fit blows up

    """

    if len(station) != 4:
        print('Stations must be four characters long. Exiting.')
        sys.exit()

    if signal.upper() not in ['L1', 'L2', 'L5', 'L6', 'L7', 'L1+L2', 'L1+L2+L5', 'L1+L5', 'ALL']:

        print('Currently only allow L1,L2,L5,L6,L7 and various combinations')
        print('Illegal signal:', signal)
        sys.exit()

    if signal.upper() == 'ALL':
        print('Using all signals')
        signal = 'L1+L2+L5+L6+L7'
    print(signal)

    # build a dictionary with the analysis inputs
    # environment variable for the file inputs
    xdir = os.environ['REFL_CODE']

    # location of the analysis inputs, if it exists
    jsondir  = xdir + '/input/'
    instructions2 =  jsondir + station + '.inv.json'

    if json_override is False:
        if os.path.isfile(instructions2):
            #print('using:', instructions2)
            with open(instructions2) as f:
                lsp = json.load(f)
        else:
            print('Instruction file does not exist.', instructions2, ' Exiting.')
            sys.exit()
    else:
        instructions2 = json_override
        if os.path.isfile(instructions2):
            #print('using:', instructions2)
            with open(instructions2) as f:
                lsp = json.load(f)
        else:
            print('Instruction file does not exist.', instructions2, ' Exiting.')
            sys.exit()


# save json inputs to variables
# this is ridiculous - I should just send the dictionary!
    precision = lsp['precision']
    azilims = lsp['azilims']
    elvlims = lsp['elvlims']
    rhlims = lsp['rhlims']
    l2c_only = lsp['l2c_only']
    if 'pktnlim' in lsp:
        print('use peak2noise from json')
        peak2noise = lsp['pktnlim']


# multi doy listing
    if doy_end is None:
        doy_end = doy
    else:
        doy_end = int(doy_end)
    
    if (doy_end < doy):
        print('doy_end cannot be less than doy')
        sys.exit()

# set constellation.
    if constel is None:
        # added beidou 22feb09
        #satconsts=['E','G','R','C'] # the default is gps,glonass, and galileo
        satconsts=['E', 'G', 'R'] # the default is gps, glonass, and galileo
    else: 
        satconsts=[constel]
        # save people from themselves
        if (constel == 'R') and (signal == 'L5'):
            print('illegal constellation/frequency choice', constel, '/', 'signal')
            sys.exit()
        if (constel == 'E') and (signal == 'L2'):
            print('illegal constellation/frequency choice', constel, '/', signal)
            sys.exit()
        if (constel == 'C') and (signal == 'L1' or signal == 'L5'):
            print('illegal constellation/frequency choice', constel, '/', signal)
            sys.exit()

    if (constel == 'withBeidou'):
        satconsts=['E', 'G', 'R', 'C'] # the default is gps, glonass, and galileo
    if (constel == 'GPS+Gal'):
        satconsts=['E', 'G'] # 

    print('Roughness:', rough_in)

    print('Knot spacing (hours):', knot_space)

    kdt = knot_space * 60 * 60  # change knot spacing to seconds

    # trying to add refraction to an existing dictionary. this is how it is done in the main lsp code
    lsp['refraction'] = False

    if refraction:
        lsp['refraction'] = True

    spline_functions.snr2spline(station, year, doy, azilims, elvlims, rhlims, precision, kdt, signal=signal,
                                lspfigs=lspfigs, snrfigs=snrfigs, snrfit=snrfit, doplot=plt, pktnlim=peak2noise,
                                satconsts=satconsts, screenstats=screenstats, tempres=dec, doy_end=doy_end,
                                l2c_only=l2c_only, rough_in=rough_in, risky=risky, snr_ending=snr,
                                outfile_type=outfile_type, delta_out=delta_out, lsp=lsp, outfile_name=outfile_name,
                                outlier_limit=outlier_limit, no_dots=no_dots,lastday_seconds=lastday_seconds)


def main():
    args = parse_arguments()
    invsnr(**args)


if __name__ == "__main__":
    main()


