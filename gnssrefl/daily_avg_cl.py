# command line module that calls daily_avg.py
# Kristine Larson May 2019
import argparse
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import sys

from datetime import date

# my code
import gnssrefl.gps as g
# this was originally all one file - now moving the computations to a library
import gnssrefl.daily_avg as da
#
# changes to output requested by Kelly Enloe for JN
# two text files will now always made - but you can override the name of the average file via command line



def main():
#   make surer environment variables are set 
    g.check_environ_variables()
    xdir = os.environ['REFL_CODE'] 

# must input start and end year
    parser = argparse.ArgumentParser()
    parser.add_argument("station", help="station name", type=str)
    parser.add_argument("medfilter", help="Median filter for daily RH (m). Start with 0.25 ", type=float)
    parser.add_argument("ReqTracks", help="required number of tracks", type=int)
    parser.add_argument("-txtfile", default=None, type=str, help="Set your own output filename")
    parser.add_argument("-plt", default=None, type=str, help="plt to screen: True or False")
    parser.add_argument("-extension", default=None, type=str, help="extension for solution names")
    parser.add_argument("-year1", default=None, type=str, help="restrict to years starting with")
    parser.add_argument("-year2", default=None, type=str, help="restrict to years ending with")
    parser.add_argument("-fr", default=0, type=int, help="frequency, default is to use all")
    parser.add_argument("-csv", default=None, type=str, help="True if you want csv instead of plain text")
    args = parser.parse_args()
#   these inputs are required
    station = args.station
    medfilter= args.medfilter
    ReqTracks = args.ReqTracks

    # frequency is zero for all frequencies.  not typically used, but if you wanted only 
    # glonas L1 for some reason, you could get it by setting fr = 101
    fr = args.fr

    if args.csv == None:
        csvformat = False
    else:
        csvformat = True

#   default is to show the plot 
    if (args.plt == None) or (args.plt == 'True'):
        plt2screen = True 
    else:
        plt2screen = False

    if args.extension == None:
        extension = ''
    else:
        extension = args.extension

    if args.year1 == None:
        year1 = 2005
    else:
        year1=int(args.year1)

    if args.year2 == None:
        year2 = 2021
    else:
        year2=int(args.year2)

# where the summary files will be written to
    txtdir = xdir + '/Files' 

    if not os.path.exists(txtdir):
        print('make an output directory', txtdir)
        os.makedirs(txtdir)

    # set the name of the output format
    if csvformat:
        alldatafile = txtdir + '/' + station + '_allRH.csv' 
    else:
        alldatafile = txtdir + '/' + station + '_allRH.txt' 

    tv,obstimes = da.readin_plot_daily(station,extension,year1,year2,fr,alldatafile,csvformat,medfilter,ReqTracks)

    # default is to show the plots
    if plt2screen:
        plt.show()

    # now write out the result file:

    if args.txtfile == None:
        if csvformat:
            outfile = txtdir + '/' + station + '_dailyRH.csv' 
        else:
        # use default  filename for the average
            outfile = txtdir + '/' + station + '_dailyRH.txt' 
    else:
        txtfile = args.txtfile
        # use filename provided by the user
        outfile = txtdir + '/' + txtfile

    da.write_out_RH_file(obstimes,tv,outfile,csvformat)

if __name__ == "__main__":
    main()
