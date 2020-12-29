# -*- coding: utf-8 -*-
"""
downloads NOAA tide gauge files
kristine larson
"""
import argparse
import datetime
import requests
import sys

def main():
    """
    command line interface for download_rinex
    it downloads a json and converts it to plain txt with columns! 

    author: kristine m. larson
    """

    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("date1", help="start-date, 20150101", type=str)
    parser.add_argument("date2", help="end-date, 20150110", type=str)

    args = parser.parse_args()

# metadata records  {'id': '8764227', 'name': 'LAWMA, Amerada Pass', 'lat': '29.4496', 'lon': '-91.3381'}

#   assign to normal variables
    station = args.station
    #station = '8764227' this was a test station
    date1 = args.date1
    date2 = args.date2
    if (len(station) != 7):
        print('station must have 7 characters ', station); sys.exit()
    if (len(date1) != 8):
        print('date1 must have 8 characters', date1); sys.exit()
    if (len(date2) != 8):
        print('date2 must have 8 characters', date2); sys.exit()

    urlL = "https://api.tidesandcurrents.noaa.gov/api/prod/datagetter?"
    endL = "&product=water_level&datum=mllw&units=metric&time_zone=gmt&application=web_services&format=json"
    url = urlL + "begin_date=" + date1 + "&end_date=" + date2 + "&station=" + station + endL
    data = requests.get(url).json()
    if ('error' in data.keys()):
        print(data['error'])
        sys.exit()
    else:
        print(data['metadata'])
    # number of records
    NV = len(data['data']) 
    outfile  = station + '_' + 'noaa.txt'
    fout = open(outfile, 'w+')
    fout.write("%YYYY MM DD HH MM  Water(m) DOY\n")
    for i in range(0,NV):
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
            today=datetime.datetime(year,mm,dd)
            doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
            fout.write(" {0:4.0f} {1:2.0f} {2:2.0f} {3:2.0f} {4:2.0f} {5:7.3f} {6:3.0f} \n".format(year,mm,dd,hh,minutes,sl,doy))
    fout.close()
    print('NOAA tide data written out to ', outfile)
if __name__ == "__main__":
    main()
