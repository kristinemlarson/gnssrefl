# -*- coding: utf-8 -*-
"""
downloads IOC tide gauge files

originally used XML download. now uses json
"""
import argparse
import datetime
import numpy as np
import os
import requests
import sys
import gnssrefl.gps as g
import matplotlib.pyplot as plt

from gnssrefl.utils import validate_input_datatypes, str2bool

def quickp(station,t,sealevel):
    """
    makes a quick plot of sea level for station s

    Parameters

    station : string
        station name

    t : numpy array in datetime format 
        time of the sea level observations

    sealevel : numpy array, float 
        meters (relative - not defined in a datum)
    
    """
    fs = 10
    if (len(t) > 0):
        fig,ax=plt.subplots()
        ax.plot(t, sealevel, '-')
        plt.title('Tides at ' + station)
        plt.xticks(rotation =45,fontsize=fs);
        plt.ylabel('meters')
        plt.grid()
        fig.autofmt_xdate()
        plt.show()
    else:
        print('no data found - so no plot')
    return

def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("date1", help="first-date, 20150101", type=str)
    parser.add_argument("date2", help="end-date, 20150101", type=str)
    parser.add_argument("-output", default=None, help="Optional output filename", type=str)
    parser.add_argument("-plt", default=None, help="Optional plot to screen", type=str)
    parser.add_argument("-outliers", default=None, help="attempt to remove outliers", type=str)
    parser.add_argument("-sensor", default=None, help="flt, prs or rad, default is rad", type=str)
    args = parser.parse_args().__dict__


    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt','outliers']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_ioc(station: str, date1: str, date2: str, output: str = None, plt: bool = False, outliers: bool = False, sensor= None):
    """
        Downloads IOC tide gauge files

        Parameters:
        ___________
        station : string

        date1 : string
            begin date in yyyymmdd.
            Example value: 20150101

        date2 : string
            end date in yyyymmdd.
            Example value: 20150101

        output : string, optional
            Optional output filename
            default is None

        plt: boolean, optional
            plot comes to the screen
            default is None

        outliers: boolean, optional
            tried to remove outliers, but it doesn't work as yet
            default is No

        sensor: string, optional
            type of sensor, prs(for pressure), rad (for radar), flt (for float)
            default is None, which means it will print out what is there.
            if there is more than one sensor you should specifically ask for the one
            you want

    """

    if len(date1) != 8:
        print('date1 must have 8 characters', date1); sys.exit()
    if len(date2) != 8:
        print('date2 must have 8 characters', date1); sys.exit()
    # should check for < 30 days

    g.check_environ_variables()

    xdir = os.environ['REFL_CODE']
    if not os.path.exists(xdir):
        print('REFL_CODE environment variable must be set')
        sys.exit()
    outdir = xdir  + '/Files/'
    if not os.path.exists(outdir) :
        subprocess.call(['mkdir', outdir])

    csv = False
    if output is None:
    # use the default
        outfile = outdir + station + '_' + 'ioc.txt'
    else:
        outfile = outdir + output
        if output[-3:] == 'csv':
            csv = True

    # set up the address for the API call
    url1 = 'http://www.ioc-sealevelmonitoring.org/service.php?query=data&code='
    url2 = '&format=json'
    newurl = url1 + station + '&timestart=' + date1 + '&timestop=' + date2 + url2
    print(newurl)
    data = requests.get(newurl).json()
    NV = len(data)
    print('number of records', NV)
    if (NV < 2):
        print('exiting')
        sys.exit()

    fout = open(outfile,'w+')
    print('Writing IOC data to ', outfile)
    if csv:
        fout.write("# YYYY,MM,DD,HH,MM, Water(m),DOY, MJD \n")
    else:
        fout.write("%YYYY MM DD HH MM  Water(m) DOY  MJD \n")
    i = 1

#    All values X where abs(X – median) > tolerance are hidden.
#    With tolerance = 3*abs(percentile90 - median)
#    The statistics (median and percentile90) are calculated on the data being plotted (12h, 1d, 7d, 30d)
    s = []
    for i in range(0, NV):
        s.append(float(data[i]['slevel']))
    medv = np.median(s) 
    print('median',medv)
    sv = np.sort(np.abs(s-medv))
    percent90 = sv[int(NV*0.9)]  

    print('Your sensor choice:', sensor)
    if outliers:
        criteria = np.abs(percent90*3)
        print('outlier criteria:',round(criteria,2), ' meters')
    else:
        criteria = 100000000

    all_sensors = []
    thetime = []; sealevel = [] ; obstimes = [] ; pt = 0
    for i in range(0, NV):
        slr = data[i]['slevel']
        instrument = data[i]['sensor']
        if instrument not in all_sensors:
            all_sensors.append(instrument)
            print('Found this sensor', instrument)
        t = data[i]['stime']
        sl = float(slr)
        if ((np.abs(sl-medv)) < criteria) and ((sensor == None) or (instrument == sensor)):
            year = int(t[0:4]); mm = int(t[5:7]); dd = int(t[8:10])
            hh = int(t[11:13]); minutes = int(t[14:16])
            #print(year, mm, dd, hh, minutes)
            today = datetime.datetime(year, mm, dd)
            doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
            m, f = g.mjd(year, mm, dd, hh, minutes, 0)
            mjd = m + f;
            thetime.append(mjd); sealevel.append(sl)
            bigT = datetime.datetime(year=year, month=mm, day=dd, hour=hh, minute=minutes, second=0)
            obstimes.append(bigT)

            if csv:
                fout.write(" {0:4.0f},{1:2.0f},{2:2.0f},{3:2.0f},{4:2.0f},{5:7.3f},{6:3.0f},{7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))
            else:
                fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} {7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))
        else:
            pt = pt + 1
    fout.close()

    if plt:
        quickp(station,obstimes,sealevel)

    #for i in range(0,NV):
    #    print(s[i], sortedvalues[i])


def main():
    args = parse_arguments()
    download_ioc(**args)


if __name__ == "__main__":
    main()
