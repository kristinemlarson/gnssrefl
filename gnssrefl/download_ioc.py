# -*- coding: utf-8 -*-
"""
downloads IOC tide gauge files
kristine larson
"""
import argparse
import datetime
import requests
import sys
import gnssrefl.gps as g
import matplotlib.pyplot as plt

from gnssrefl.utils import validate_input_datatypes, str2bool


# beautiful soup
from bs4 import BeautifulSoup

def quickp(station,t,sealevel):
    """
    """
    plt.figure()
    plt.plot(t,sealevel)
    plt.grid()
    plt.title(station)
    plt.show()
    return


def parse_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("date1", help="end-date, 20150101", type=str)
    parser.add_argument("-output", default=None, help="Optional output filename", type=str)
    parser.add_argument("-plt", default=None, help="Optional plot to screen", type=str)
    args = parser.parse_args().__dict__


    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_ioc(station: str, date1: str, output: str = None, plt: bool = False):
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

    csv = False

    if output is None:
    # use the default
        outfile = station + '_' + 'ioc.txt'
    else:
        outfile = output
        if output[-3:] == 'csv':
            csv = True

    url1 = 'https://ioc-sealevelmonitoring.org/bgraph.php?code=' 
    url2 = '&period=30&endtime=2022-04-30'
    url = url1 + station + url2

    print(url)
    data = requests.get(url).text
    soup = BeautifulSoup(data, 'html.parser')

    t = []
    sealevel = []
    fout = open(outfile,'w+')
    print('Writing data to ', outfile)
    if csv:
        fout.write("# YYYY,MM,DD,HH,MM, Water(m),DOY, MJD \n")
    else:
        fout.write("%YYYY MM DD HH MM  Water(m) DOY  MJD \n")
    i = 1
    if soup.findAll('table') == []:
        print('There does not appear to be any data at this site.')
        sys.exit()

    for row in soup.findAll('table')[0].findAll('tr'):
    # Find all data for each column
        columns = row.find_all('td')
        if (i == 1):
            NCOL = len( columns )
        i+=1
        if (columns != []) :
            if NCOL == 3:
                sl = columns[2].text.strip()
            else:
                sl = columns[1].text.strip()
            time = columns[0].text.strip()
            if ('rad' in sl) or  ('Time' in time):
                print('skip this line')
            else:
                time = columns[0].text.strip()
                y = int(time[0:4]); m = int(time[5:7]); d=int(time[8:10])
                hh = int(time[11:13]); mm = int(time[14:16]); ss=int(time[17:19])
                modd,fr = g.mjd(y,m,d,hh,mm,ss)
                modjulian = modd+fr
            # calculate day of year
                today = datetime.datetime(y, m, d)
                doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
                if (len(sl) != 0):
                    t.append(modjulian)
                    sealevel.append(float(sl))
                    if csv:
                        fout.write(" {0:4.0f},{1:2.0f},{2:2.0f},{3:2.0f},{4:2.0f},{5:7.3f},{6:3.0f},{7:15.6f} \n".format(y, m, d, hh, mm, float(sl), doy, modjulian))
                    else:
                        fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} {7:15.6f} \n".format(y, m, d, hh, mm, float(sl), doy, modjulian))

                else:
                    print('No data ',time)
    fout.close()

    if plt:
        quickp(station,t,sealevel)


def main():
    args = parse_arguments()
    download_ioc(**args)


if __name__ == "__main__":
    main()
