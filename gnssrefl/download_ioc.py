# -*- coding: utf-8 -*-
"""
downloads IOC tide gauge files
kristine larson

originally used XML download. changing to json
"""
import argparse
import datetime
import requests
import sys
import gnssrefl.gps as g
import matplotlib.pyplot as plt

from gnssrefl.utils import validate_input_datatypes, str2bool

def quickp(station,t,sealevel):
    """
    """
    plt.figure()
    plt.plot(t,sealevel)
    plt.grid()
    plt.xlabel('MJD')
    plt.ylabel('meters')
    plt.title('Tides at ' + station + ' from IOC website')
    plt.show()
    return


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("date1", help="first-date, 20150101", type=str)
    parser.add_argument("date2", help="end-date, 20150101", type=str)
    parser.add_argument("-output", default=None, help="Optional output filename", type=str)
    parser.add_argument("-plt", default=None, help="Optional plot to screen", type=str)
    args = parser.parse_args().__dict__


    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_ioc(station: str, date1: str, date2: str, output: str = None, plt: bool = False):
    """
        Downloads IOC tide gauge files
        Downloads HTML (?????)  and converts it to plain txt with columns!

        Parameters:
        ___________
        station : string

        date1 : string
            end date in yyyymmdd.
            Example value: 20150101

        output : string, optional
            Optional output filename
            default is None

    """

    if len(date1) != 8:
        print('date1 must have 8 characters', date1); sys.exit()
    if len(date2) != 8:
        print('date2 must have 8 characters', date1); sys.exit()
    # should check for < 30 days

    csv = False
    if output is None:
    # use the default
        outfile = station + '_' + 'ioc.txt'
    else:
        outfile = output
        if output[-3:] == 'csv':
            csv = True

    
    url1 = 'http://www.ioc-sealevelmonitoring.org/service.php?query=data&code='
    url2 = '&format=json'
    newurl = url1 + station + '&timestart=' + date1 + '&timestop=' + date2 + url2
    print(newurl)
    data = requests.get(newurl).json()
    NV = len(data)
    print('number of records', NV)
    if (NV < 1):
        print('exiting')
        sys.exit()

    fout = open(outfile,'w+')
    print('Writing IOC data to ', outfile)
    if csv:
        fout.write("# YYYY,MM,DD,HH,MM, Water(m),DOY, MJD \n")
    else:
        fout.write("%YYYY MM DD HH MM  Water(m) DOY  MJD \n")
    i = 1

    thetime = []; sealevel = []
    for i in range(0, NV):
        slr = data[i]['slevel']
        t = data[i]['stime']
        sl = float(slr)
        year = int(t[0:4]); mm = int(t[5:7]); dd = int(t[8:10])
        hh = int(t[11:13]); minutes = int(t[14:16])
        #print(year, mm, dd, hh, minutes)
        today = datetime.datetime(year, mm, dd)
        doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
        m, f = g.mjd(year, mm, dd, hh, minutes, 0)
        mjd = m + f;
        thetime.append(mjd); sealevel.append(sl)
        if csv:
            fout.write(" {0:4.0f},{1:2.0f},{2:2.0f},{3:2.0f},{4:2.0f},{5:7.3f},{6:3.0f},{7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))
        else:
            fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} {7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))
    fout.close()

    if plt:
        quickp(station,thetime,sealevel)


def main():
    args = parse_arguments()
    download_ioc(**args)


if __name__ == "__main__":
    main()
