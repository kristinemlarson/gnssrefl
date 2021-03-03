# preliminary water analysis to apply RHdot correction
import argparse
import datetime
import json
import matplotlib.pyplot as Plt
import numpy as np
import os
import sys

from datetime import date

# my code
import gnssrefl.gps as g
import gnssrefl.tide_library as t


import scipy.interpolate as interpolate
from scipy.interpolate import interp1d
import math


def main():
#   make surer environment variables are set 
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE'] 

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
# optional inputs: filename to output daily RH results 
    parser.add_argument("-year", default='None', type=str, help="restrict to years beginning with")
    parser.add_argument("-txtfile", default='None', type=str, help="output (plain text)") 
    parser.add_argument("-csvfile", default='None', type=str, help="output (csv)")
    parser.add_argument("-jsonfile", default='None', type=str, help="output (json)")
    parser.add_argument("-plt", default='None', type=str, help="set to False to suppress plots")

    args = parser.parse_args()
#   these are required
    station = args.station

    txtdir = xdir + '/Files'
    if not os.path.exists(txtdir):
        subprocess.call(['mkdir',txdir])
 
#   these are optional output options
    txtfile = args.txtfile
    csvfile = args.csvfile
    jsonfile = args.jsonfile
    writetxt,writecsv,writejson,outfile = t.output_names(txtdir, txtfile,csvfile,jsonfile)

    if args.year == 'None':
        year = 2020
    else:
        year=int(args.year)

    plt = True
    if args.plt == 'False':
        plt= False

    # read in the data and make a plot
    ntv = t.readin_and_plot(xdir, station, year,1,366)
    N,M = np.shape(ntv)

    # use function instead of writing it here
    t.write_subdaily(outfile,station,nvt,N,writecsv,writetxt)
    # for now exit
    if (writejson):
        print(outfile, station)
        t.writejson(ntv,station, outfile)
    sys.exit()
    # this should also be in a function
    if (writejson):
        print('you picked the json output')
        o = {}
        N= len(ntv)
        column_names = ['timestamp','rh','sat','freq','ampl','azim','edotf','mjd']

        # this worked - but didn't have names, so not useful
        #o['station'] = station
        #o['data'] =  ntv[:,[0,1,2,4,15,3]].tolist()
        # give my numpy variables names
        # to make a string
        # x=datetime.datetime(2018,9,15)
        # print(x.strftime("%b %d %Y %H:%M:%S"))
        year  =  ntv[:,0].tolist()
        year =[str(int(year[i])) for i in range(N)]; 

        doy =  ntv[:,1].tolist()
        doy=[str(int(doy[i])) for i in range(N)]; 

        UTChour = ntv[:,4].tolist()
        UTChour = [str(UTChour[i]) for i in range(N)]; 

        timestamp = [quickTr(ntv[i,0], ntv[i,1], ntv[i,4]) for i in range(N)]

        rh = ntv[:,2].tolist()
        rh=[str(rh[i]) for i in range(N)]; 

        sat  = ntv[:,3].tolist()
        sat =[int(sat[i]) for i in range(N)]; 

        freq  = ntv[:,10].tolist()
        freq =[int(freq[i]) for i in range(N)]; 

        ampl  = ntv[:,6].tolist()
        ampl =[str(ampl[i]) for i in range(N)]; 

        azim  = ntv[:,5].tolist()
        azim =[str(azim[i]) for i in range(N)]; 

        edotf  = ntv[:,12].tolist()
        edotf =[str(edotf[i]) for i in range(N)]; 

        mjd = ntv[:,15].tolist()
        mjd=[str(mjd[i]) for i in range(N)]; 

        # now attempt to zip them
        l = zip(timestamp,rh,sat,freq,ampl,azim,edotf,mjd)
        dzip = [dict(zip(column_names, next(l))) for i in range(N)]
        # make a dictionary with metadata and data
        o={}
        lat = "0"; lon = "0"; 
        firstline = {'name': station, 'latitude': lat, 'longitude': lon}
        o['metadata'] = firstline
        o['data'] = dzip

        outf = outfile
        print(outfile)
        with open(outf,'w+') as outf:
            json.dump(o,outf,indent=4)
        #close(outf)

    sys.exit()
    if (writecsv) or (writetxt):
        print('Results are being written to : ', outfile)
        fout = open(outfile, 'w+')
        write_out_header(fout,station)
        for i in np.arange(0,N,1):
            year = int(ntv[i,0]); doy = int(ntv[i,1])
            year, month, day, cyyyy,cdoy, YMD = g.ydoy2useful(year,doy)
            rh = ntv[i,2]; UTCtime = ntv[i,4]; mjd = ntv[i,15]
            ctime = g.nicerTime(UTCtime); ctime2 = ctime[0:2] + ' ' + ctime[3:5]
            if writecsv:
                fout.write(" {0:4.0f},{1:3.0f},{2:7.3f},{3:3.0f},{4:7.3f},{5:8.2f},{6:7.2f},{7:5.2f},   {8:3.0f},{9:8.5f}, {10:2.0f}, {11:2.0f},{12:2s},{13:2s},{14:15.6f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,13],ntv[i,10],ntv[i,12],month,day,ctime[0:2],ctime[3:5] ,mjd ))
            else:
                fout.write(" {0:4.0f} {1:3.0f} {2:7.3f} {3:3.0f} {4:7.3f} {5:8.2f} {6:7.2f} {7:5.2f}    {8:3.0f} {9:8.5f}  {10:2.0f}  {11:2.0f} {12:5s} {13:15.6f} \n".format(year, doy, rh,ntv[i,3],UTCtime,ntv[i,5],ntv[i,6],ntv[i,13],ntv[i,10],ntv[i,12],month,day,ctime2,mjd ))
        fout.close()

if __name__ == "__main__":
    main()
