# -*- coding: utf-8 -*-
import argparse
import datetime
import os
import requests
import subprocess
import sys
import gnssrefl.gps as g

from gnssrefl.utils import validate_input_datatypes, str2bool


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name, e.g. 5970026", type=str)
    parser.add_argument("-plt", default=None, help="Optional plot to screen", type=str)
    parser.add_argument("-output", default=None, help="Optional filename", type=str)
    args = parser.parse_args().__dict__


    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_wsv(station: str, plt: bool = True, output: str = None):
    """
    Downloads and saves WSV (Germany) tide gauge files

    Parameters
    ----------
    station : str
        IOC station name 
    plt: bool, optional
        plot comes to the screen
        default is None
    output: str, optional
        output filename
        if not set, it uses station.txt

    """
    g.check_environ_variables()
    # set up the address for the API call

    newurl = 'https://www.pegelonline.wsv.de/webservices/rest-api/v2/stations/' + station + '/W/measurements.json?start=P15D'

    data = requests.get(newurl).json()

    N= len(data)
    thetime = []; sealevel = [] ; obstimes = [] ; pt = 0
    if output is None:
        outfile = station + '.txt'

    else:
        outfile = args.output

    # open the file
    fout = open(outfile,'w+')


    for i in range(0, N):
        sl = float(data[i]['value'])/100 # change to meters
        t = data[i]['timestamp']
        o=datetime.datetime.fromisoformat(t)
        ts = datetime.datetime.utctimetuple(o)
        #    print(ts.tm_year, ts.tm_mon, ts.tm_mday, ts.tm_hour, ts.tm_min, ts.tm_sec, ts.tm_yday)
        year = ts.tm_year ; mm  = ts.tm_mon ; dd =  ts.tm_mday
        hh = ts.tm_hour ; minutes = ts.tm_min ; sec = ts.tm_sec
        doy = ts.tm_yday
        # calcualte MJD
        m, f = g.mjd(year, mm, dd, hh, minutes, sec)
        mjd = m + f;
        thetime.append(mjd); sealevel.append(sl)
            #print(year,mm,dd,hh,minutes,sec)
        bigT = datetime.datetime(year=year, month=mm, day=dd, hour=hh, minute=minutes, second=sec)
        obstimes.append(bigT)

        fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} {7:15.6f} {8:3.0f}\n".format(year, 
                mm, dd, hh, minutes, sl, doy, mjd,sec))
    # close the file
    fout.close()

    if plt:
        g.quickp(station,obstimes,sealevel)


def quickp(station,t,sealevel):
    """
    makes a quick plot of sea level for input station 
    prints to the screen - does not save it.

    Parameters
    -----------
    station : str
        station name

    t : numpy array in datetime format 
        time of the sea level observations UTC

    sealevel : list,  float 
        meters (unknown datum)
    
    """
    fs = 10
    if (len(t) > 0):
        fig,ax=plt.subplots()
        ax.plot(t, sealevel, 'b.')
        plt.title('Tides at WSV: ' + station)
        plt.xticks(rotation =45,fontsize=fs);
        plt.ylabel('meters')
        plt.grid()
        fig.autofmt_xdate()
        plt.show()
    else:
        print('no data found - so no plot')
    return

def main():
    args = parse_arguments()
    download_wsv(**args)


if __name__ == "__main__":
    main()
