# -*- coding: utf-8 -*-
import argparse
from astropy.time import Time
import datetime
import numpy as np
import matplotlib.pyplot as plt
import os
import sys


def main():
    """
    quick file plotting using matplotlib

    Parameters
    ----------
    filename : str
        name of file to be plotted 
    xcol : str
        column number in the file for the x-axis parameter
    ycol : str
        column number in the file for the y-axis parameter
    mjd : str
        T or True, code will convert MJD to datetime, optional
    xlabel : str
        label for x-axis, optional
    ylabel : str
        label for y-axis, optional
    symbol : str
        prescibe the marker used in the plot, optional
    reverse : str
        T or True, to reverse y-axis limits, optional
    title : str
        optional title for plot
    outfile : str
        name of png file to store plot
    ylimits: str
        pair of yaxis limits 

    """

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename", type=str)
    parser.add_argument("xcol", help="x-column", type=str)
    parser.add_argument("ycol",   help="y-column", type=str)
    parser.add_argument("-mjd", help="set to True/T if x-values are MJD (should add MM/SS?", type=str,default=None)
    parser.add_argument("-reverse", help="set to True/T to reverse the y-axis", type=str,default=None)
    parser.add_argument("-ymdh", help="if True/T, columns 1-4 are year mon day hour ", type=str,default=None)
    parser.add_argument("-xlabel", type=str, help="optional x-axis label", default=None)
    parser.add_argument("-ylabel", type=str, help="optional y-axis label", default=None)
    parser.add_argument("-symbol", help="plot symbol ", type=str,default=None)
    parser.add_argument("-title", help="optional title", type=str,default=None)
    parser.add_argument("-outfile", help="optional filename for plot", type=str,default=None)
    parser.add_argument("-ylimits", nargs="*",type=float, help="optional ylimits", default=None)

    args = parser.parse_args()

    filename = args.filename
    # change column numbers to pythonese
    xcol = int(args.xcol) - 1
    ycol = int(args.ycol) - 1


    if args.ylabel is None:
        ylabel = 'Unknown'
    else:
        ylabel = args.ylabel

    secondFile = False

    reverse_sign = False
    if (args.reverse == 'True') or (args.reverse == 'T'):
        reverse_sign = True

    ymd = False
    if (args.ymdh == 'True') or (args.ymdh == 'T'):
        ymd = True

    convert_mjd = False
    if (args.mjd== 'True') or (args.mjd == 'T'):
        convert_mjd = True

    commentsign = '%'

    if os.path.isfile(filename):
        tvd = np.loadtxt(filename,comments=commentsign)
        if len(tvd) == 0:
            print('empty input file number 1')
            return
        tval = []
        yval = []
    else:
        print('input file does not exist')
        sys.exit()

    if secondFile:
        tvd2 = np.loadtxt(filename2,comments=commentsign)
        if len(tvd2) == 0:
            print('empty input file number 2')
            return


    if ymd == True:
        year = tvd[:,0]; month = tvd[:,1]; day = tvd[:,2];
        hour = tvd[:,3]
        for i in range(0,len(tvd)):
            if (tvd[i, 4]) > 0:
                y = int(year[i]); m = int(month[i]); d = int(day[i])
                # i am sure there is a better way to do this
                today=datetime.datetime(y,m,d)
                doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
                h = int(hour[i])
                tval.append(y + (doy +  h/24)/365.25);
                yval.append( tvd[i,4]/1000)
    else:
        if convert_mjd:
            t1 = Time(tvd[:,xcol],format='mjd')
            t1_utc = t1.utc # change to UTC
            # probably can be done in one step!
            tval =  t1_utc.datetime # change to datetime
            yval = tvd[:,ycol] # save the y values
        else:
            tval = tvd[:,xcol] ; yval = tvd[:,ycol]
            x1 = min(tval) ; x2 = max(tval)
            if secondFile:
                tval2 = tvd2[:,xcol] ; yval2 = tvd2[:,ycol]

    fig,ax=plt.subplots()
    if args.symbol is None:
        ax.plot(tval, yval, 'b.')
    else:
        ax.plot(tval, yval, args.symbol)

    # second file is not currently supported
    if secondFile:
        ax.plot(tval2, yval2, 'r.')

    fig.autofmt_xdate()

    plt.ylabel(ylabel)

    if args.xlabel is not None:
        plt.xlabel(str(args.xlabel))

    if reverse_sign:
        ax.invert_yaxis()

    if args.title is None:
        ax.set_title(os.path.basename(filename) )
    else:
        ax.set_title(args.title )

    plt.grid()


    if args.ylimits is not None:
        print('found y-axis limits')
        ylimits = args.ylimits
        plt.ylim((ylimits))

    if args.outfile is not None:
        plt.savefig(args.outfile,dpi=300)

    plt.show()


if __name__ == "__main__":
    main()
