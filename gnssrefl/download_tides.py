# -*- coding: utf-8 -*-
"""
downloads NOAA tide gauge files
kristine larson
"""
import argparse
import datetime
import matplotlib.pyplot as plt
import os
import requests
import sys
import gnssrefl.gps as g

from gnssrefl.utils import validate_input_datatypes, str2bool

def noaa_command(station,fout,year,month1,month2,datum,metadata,tt,obstimes,slevel,csv):
    """
    downloads/writes data within one year

    Parameters

    station : string

    year : integer

    month1 : integer

    month2 : integer

    datum : string

    metadata : boolean

    tt : numpy array 
        modified julian date for water measurements

    obstimes : numpy array

    slevel : numpy array

    csv : boolean
        True if csv output wanted
        default is False


    fout - fileID for writing the results
    year that you want to write out
    month1 and month2 are the starting and ending months
    metadata = boolean to decide whether to write the metadata to the screen
    tt - MJD

    """
    cyyyy = str(year)
    imeta = 0
    for m in range(month1,month2+1):
        cmm = '{:02d}'.format(m)
        d1 = cyyyy + cmm + '01'
        if m in [1,3,5,7,8,10,12]:
            d2 = cyyyy + cmm + '31'
        else:
            if m == 2:
                if (g.dec31(year) == 366): # leap year
                    d2 = cyyyy + cmm + '29'
                else:
                    d2 = cyyyy + cmm + '28'
            else:
                d2 = cyyyy + cmm + '30'

        print(d1,d2) # send whether imeta is equal to 0 ...  
        data, error = pickup_from_noaa(station,d1,d2,datum,imeta==0)
        if not error: # only write out if error not thrown. update the variables
            tt,obstimes,slevel = write_out_data(data,fout, tt,obstimes,slevel,csv)

        imeta = imeta + 1

    return tt,obstimes,slevel


def multimonthdownload(station,datum,fout,year1,year2,month1,month2,csv):
    """
    downloads NOAA measurements > one month


    Parameters:
    -----------
    station : string

    datum : string

    fout - fileID for writing results

    year1 : integer
        year when first measurements will be downloaded

    month1 : integer
        month when first measurements will be downloaded

    year2 : integer
        last yaer when measurements will be downloaded

    month2 : integer 
        last month when measurements will be downloaded

    csv : boolean 
        whether output file is csv format

    returns:
    --------------
    tt : list of times 
        modified julian day
    obstimes : list of datetime objects 

    slevel : list 
         water level in meters

    """
    # set variables for making the plot ... 
    tt = []; slevel = []; obstimes = []
    metadata = True  # set true for now

    imeta = 0
    if (year1 == year2):
        tt, obstimes, slevel = noaa_command(station,fout,year1,month1,month2,datum,metadata,tt,obstimes,slevel,csv)
    else:
        for y in range(year1,year2+1):
            if (y == year1):
                tt,obstimes,slevel = noaa_command(station,fout,y,month1,12,datum,metadata,tt,obstimes,slevel,csv)
            elif (y == year2):
                tt,obstimes,slevel = noaa_command(station,fout,y,1,month2,datum,metadata,tt,obstimes,slevel,csv)
            else:  # get whole year
                tt,obstimes,slevel = noaa_command(station,fout,y,1,12,datum,metadata,tt,obstimes,slevel,csv)

    return tt, obstimes, slevel

def noaa2me(date1):
    """
    parameters 
    --------
    date1 : string
        time in format YYYYMMDD for year month and day

    returns 
    -------
    year1 : integer

    month1 : integer

    day1 : integer

    doy : integer  
        day of year

    modjulday : float

    """
    year1 = int(date1[0:4]); 
    month1=int(date1[4:6]); 
    day1=int(date1[6:8])
    doy, cdoy, cyyyy, cyy =g.ymd2doy(year1, month1, day1)

    mj, fj = g.mjd(year1, month1, day1, 0, 0, 0)
    modjulday = mj + fj;

    return year1, month1, day1, doy, modjulday

def write_out_data(data,fout, tt,obstimes,slevel,csv):
    """
    input: data record from NOAA API
    tt - MJD 
    obstimes - datetime
    slevel - water level in meters
    csv - whether csv format or not (boolean)
    """
    NV = len(data['data'])

    for i in range(0, NV):
        t = data['data'][i]['t']
        slr = data['data'][i]['v']
        slf = data['data'][i]['f']
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
            if csv:
                fout.write(" {0:4.0f},{1:2.0f},{2:2.0f},{3:2.0f},{4:2.0f},{5:7.3f},{6:3.0f},{7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))
            else:
                fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} {7:15.6f} \n".format(year, mm, dd, hh, minutes, sl, doy, mjd))

    return tt,obstimes,slevel


def pickup_from_noaa(station,date1,date2,datum, printmeta):
    """
    station: str
    date1: str , beginning time, 20120101 is January 1, 2012
    date2: str, end time , same format
    datum: str
    """

    error = False
    urlL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
    # add the datum - i think
    endL = "&product=water_level&datum=" + datum + "&units=metric&time_zone=gmt&application=web_services&format=json"
    url = urlL + "begin_date=" + date1 + "&end_date=" + date2 + "&station=" + station + endL
    data = requests.get(url).json()
    if 'error' in data.keys():
        print(data['error'])
        error = True
    else:
        if printmeta:
            print(data['metadata'])

    return data, error

def quickp(station,t,sealevel):
    """
    """
    fs = 10
    fig,ax=plt.subplots()
    ax.plot(t, sealevel, '-')
    plt.title('Water Levels at ' + station)
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
    parser.add_argument("-datum", default=None, help="datum (lwd for lakes?)", type=str)
    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['plt']
    args = str2bool(args, boolean_args)


    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def download_tides(station: str, date1: str, date2: str, output: str = None, plt: bool = False, datum: str = 'mllw'):
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

        datum: string, optional
            set to lwd for lakes?
            default is mllw

        If you ask for 31 days of data or less, it will downlaod exactly what you ask for.
        But if you want a longer time series, this code needs to query the NOAA API every month.
        To make the code easier to write, I start with the first day of the first month you ask for and end with
        last day in the last month.

        Output is written to REFL_CODE/Files/

    """
    g.check_environ_variables()

    xdir = os.environ['REFL_CODE']
    outdir = xdir  + '/Files/'
    if not os.path.exists(outdir) :
        subprocess.call(['mkdir', outdir])



    if len(station) != 7:
        print('station must have 7 characters ', station); sys.exit()
    if len(date1) != 8:
        print('date1 must have 8 characters', date1); sys.exit()
    if len(date2) != 8:
        print('date2 must have 8 characters', date2); sys.exit()


    csv = False
    if output is None:
        # use the default
        outfile = outdir + station + '_' + 'noaa.txt'
    else:
        if output[-3:] == 'csv':
            csv = True
        outfile = outdir + output

    print('Writing contents to: ', outfile)
    fout = open(outfile, 'w+')
    if csv:
        fout.write("#YYYY,MM,DD,HH,MM, Water(m),DOY,   MJD\n")
    else:
        fout.write("%YYYY MM DD HH MM  Water(m) DOY    MJD\n")
        fout.write("% 1    2  3  4  5    6       7       8\n")


    year1, month1, day1, doy1,modjul1 = noaa2me(date1)
    year2, month2, day2, doy2,modjul2 = noaa2me(date2)
    deltad = int(modjul2-modjul1)
    if deltad < 1:
        print('second time is later than first time OR time is less than one day.')
        sys.exit()

    metadata = True
    if (deltad) > 31:
        tt,obstimes,slevel = multimonthdownload(station,datum,fout,year1,year2,month1,month2,csv)
    else:
        tt = []; slevel = []; obstimes = []
        # 'data' are stored in the dictionary data
        data,error = pickup_from_noaa(station,date1,date2,datum,True)
        if not error:
            tt,obstimes,slevel = write_out_data(data,fout, tt,obstimes,slevel,csv)

    fout.close()
    if plt:
        quickp(station,obstimes,slevel)

def main():
    args = parse_arguments()
    download_tides(**args)


if __name__ == "__main__":
    main()

    #urlL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
    # add the datum - i think 
    #endL = "&product=water_level&datum=" + datum + "&units=metric&time_zone=gmt&application=web_services&format=json"
    #url = urlL + "begin_date=" + date1 + "&end_date=" + date2 + "&station=" + station + endL
    #data = requests.get(url).json()
    #if 'error' in data.keys():
    #    print(data['error'])
    #    sys.exit()
    #else:
    #    print(data['metadata'])
    # number of records
#        imeta = 0
#        if (year1 != year2):
#            print('I do not download across years. Exiting')
#            sys.exit()
#        for m in range(month1,month2+1):
#            cmm = '{:02d}'.format(m)
#            d1 = cyyyy + cmm + '01' 
#            if m in [1,3,5,7,8,10,12]:
#                d2 = cyyyy + cmm + '31' 
#            else:
#                if m == 2:
#                    if (g.dec31(year1) == 366): # leap year
#                        d2 = cyyyy + cmm + '29' 
#                    else:
#                        d2 = cyyyy + cmm + '28' 
#                else:
#                    d2 = cyyyy + cmm + '30' 
#
#            print(d1,d2)
#            if imeta > 0:
#                metadata = False
#            data, error = pickup_from_noaa(station,d1,d2,datum,metadata)
#            if not error:
#                write_out_data(data,fout, tt,obstimes,slevel)
#            imeta = imeta + 1
