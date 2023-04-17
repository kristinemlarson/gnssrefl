import argparse
import wget
import sys
import os
import gnssrefl.gps as g


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    args = parser.parse_args().__dict__

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_unr(station: str):
    """
    Command line interface for downloading time series from the 
    University of Nevada Reno website

    This code is not actively maintained.

    Examples
    --------
    download_unr p041

    download_unr sc02

    Parameters
    ----------
    station : str
        4 character ID of the station name

    """

    if len(station) != 4:
        print('illegal station name-must be 4 characters')
        sys.exit()
    station = station.upper()
    url= 'http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/'
    fname = station + '.tenv3'
    stationL = station.lower() # lower case
    url = url + fname
    # file will be stored in this directory
    xdir = os.environ['REFL_CODE']
    outdir = xdir  + '/Files/'
    if not os.path.exists(outdir) :
        subprocess.call(['mkdir', outdir])

    g.check_environ_variables()

    # store in Files subdirectory
    myfname = xdir + '/Files/' + stationL + '_igs14.tenv3'
    try:
        wget.download(url, out=myfname)
    except:
        print('\n download failed:', url)

    if os.path.exists(myfname):
        print('\n SUCCESS:', myfname)


def main():
    args = parse_arguments()
    download_unr(**args)


if __name__ == "__main__":
    main()
