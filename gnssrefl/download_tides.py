# -*- coding: utf-8 -*-
"""
downloads NOAA tide gauge files
kristine larson
"""
import argparse
import datetime
import matplotlib.pyplot as plt
import requests
import sys
import gnssrefl.gps as g

from gnssrefl.utils import validate_input_datatypes, str2bool


def quickp(station,t,sealevel):
    """
    """
    fs = 10
    fig,ax=plt.subplots()
    ax.plot(t, sealevel, '-')
    plt.title('Tides at ' + station)
    plt.xticks(rotation =45,fontsize=fs);
    plt.ylabel('meters')
    plt.grid()
    fig.autofmt_xdate()

    plt.show()
    return


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("date1", help="start-date, 20150101", type=str)
    parser.add_argument("date2", help="end-date, 20150110", type=str)
    parser.add_argument("-output", default=None, help="Optional output filename", type=str)
    parser.add_argument("-plt", default=None, help="quick plot to screen", type=str)
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_tides(station: str, date1: str, date2: str, output: str = None, plt: bool = False):
    """
        Downloads NOAA tide gauge files
        Downloads a json and converts it to plain txt with columns!

        Parameters:
        ___________
        station : string
            7 character ID of the station.

        date1 : string
            start date.
            Example value: 20150101

        date2 : string
            end date.
            Example value: 20150110

        output : string, optional
            Optional output filename
            default is None

        plt: boolean, optional
            plot comes to the screen
            default is None


    """

    # metadata records  {'id': '8764227', 'name': 'LAWMA, Amerada Pass', 'lat': '29.4496', 'lon': '-91.3381'}

    #station = '8764227' this was a test station
    if len(station) != 7:
        print('station must have 7 characters ', station); sys.exit()
    if len(date1) != 8:
        print('date1 must have 8 characters', date1); sys.exit()
    if len(date2) != 8:
        print('date2 must have 8 characters', date2); sys.exit()

    urlL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
    endL = "&product=water_level&datum=mllw&units=metric&time_zone=gmt&application=web_services&format=json"
    url = urlL + "begin_date=" + date1 + "&end_date=" + date2 + "&station=" + station + endL
    data = requests.get(url).json()
    if 'error' in data.keys():
        print(data['error'])
        sys.exit()
    else:
        print(data['metadata'])
    # number of records
    NV = len(data['data']) 
    if output is None:
        # use the default
        outfile = station + '_' + 'noaa.txt'
    else:
        outfile = output

    tt = []; slevel = []; obstimes = []
    fout = open(outfile, 'w+')
    fout.write("%YYYY MM DD HH MM  Water(m) DOY  MJD\n")
    for i in range(0, NV):
        t = data['data'][i]['t']
        slr = data['data'][i]['v']
        slf = data['data'][i]['f']
        #print(i,t, slr,slf)
        if slr == '':
            aa=1 
            #print('no data')
        else:
            sl = float(data['data'][i]['v'])
            year = int(t[0:4]); mm = int(t[5:7]); dd = int(t[8:10])
            hh = int(t[11:13]); minutes = int(t[14:16])
            today = datetime.datetime(year, mm, dd)
            doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
            m, f = g.mjd(year, mm, dd, hh, minutes, 0)
            mjd = m + f;
            tt.append(mjd)
            bigT = datetime.datetime(year=year, month=mm, day=dd, hour=hh, minute=minutes, second=0)
            obstimes.append(bigT)

            slevel.append(sl)
            fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} {7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))
    fout.close()
    print('NOAA tide gauge data written out to: ', outfile)

    if plt:
        quickp(station,obstimes,slevel)


def main():
    args = parse_arguments()
    download_tides(**args)


if __name__ == "__main__":
    main()
