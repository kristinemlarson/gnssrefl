# -*- coding: utf-8 -*-
import argparse
from astropy.time import Time
import datetime
import matplotlib.pyplot as plt
import numpy as np
import os
import sys


import gnssrefl.quicklib as q
import gnssrefl.gps as g

from gnssrefl.utils import validate_input_datatypes, str2bool

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("filename", help="filename", type=str)
    parser.add_argument("xcol", help="x-column", type=int)
    parser.add_argument("ycol",   help="y-column", type=int)
    parser.add_argument("-errorcol",   help="error bar for y-values", type=int,default=None)
    parser.add_argument("-mjd", help="if x-values are MJD ", type=str,default=None)
    parser.add_argument("-reverse", help="reverse the y-axis", type=str,default=None)
    parser.add_argument("-ymd", help="columns 1-3 are year mon day ", type=str,default=None)
    parser.add_argument("-ymdhm", help="columns 1-5 are year mon day hour minute", type=str,default=None)
    parser.add_argument("-xlabel", type=str, help="optional x-axis label", default=None)
    parser.add_argument("-ylabel", type=str, help="optional y-axis label", default=None)
    parser.add_argument("-symbol", help="plot symbol ", type=str,default=None)
    parser.add_argument("-title", help="optional title", type=str,default=None)
    parser.add_argument("-outfile", help="optional filename for plot. Must end in png", type=str,default=None)
    parser.add_argument("-xlimits", nargs="*",type=float, help="optional xlimits", default=None)
    parser.add_argument("-ylimits", nargs="*",type=float, help="optional ylimits", default=None)
    parser.add_argument("-ydoy", help="if True/T, columns 1-2 are year and doy", type=str,default=None)
    parser.add_argument("-filename2", help="second filename", type=str, default=None)
    parser.add_argument("-freq", help="spec freq, column 11 in a LSP file ", type=int,default=None)
    parser.add_argument("-utc_offset", help="offset from UTC, hours  ", type=int,default=None)
    parser.add_argument("-yoffset", help="offset for y-axis values", type=float,default=None)
    parser.add_argument("-keepzeros", help="keep zeros (default is to remove)", type=str,default=None)
    parser.add_argument("-sat", help="print only this satellite (only for SNR file)", type=int,default=None)


    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['mjd', 'reverse', 'ymdhm', 'ydoy','ymd','keepzeros']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def run_quickplt (filename: str, xcol: int, ycol: int, errorcol: int=None, mjd: bool=False, xlabel: str=None, 
                  ylabel: str=None, symbol: str=None, reverse:bool=False,title:str=None,outfile: str=None,
                  xlimits: float=[], ylimits: float=[], ydoy:bool=False, ymd:bool=False, ymdhm:bool=False, 
                  filename2: str=None, freq:int=None, utc_offset: int=None, yoffset: float=None, 
                  keepzeros: bool=False, sat: int=None):

    """
    quick file plotting using matplotlib

    A png file is saved as temp.png or to your preferred
    filename if outfile is given. In either case, it goes to REFL_CODE/Files

    Allows you to set x and y-axis limits with a title and various axes labels, symbols etc.
    
    Someone could easily update this to include different filetypes (e.g. jpeg)

    I rewrote this recently to take advantage of our boolean argument translator.  Let me know 
    if things have broken or submit a PR.

    Examples
    --------
    quickplt txtfile 1 16
        would plot column 1 on the x-axis and column 16 on the y-axis

    quickplt txtfile 1 16 -xlabel Time
        would plot column 1 on the x-axis and column 16 on the y-axis
        and add Time on the x-axis label

    quickplt txtfile 1 16 -xlabel "Time (sec)"
        would plot column 1 on the x-axis and column 16 on the y-axis
        and add Time (sec) on the x-axis label, but need quote marks since you 
        have spaces in the x-axis labe.

    quickplt txtfile 1 16 -reverse T
        would plot column 1 on the x-axis and column 16 on the y-axis
        it would reverse the y-axis parameter as you might want if 
        you are ploting RH but want it to have the same sense as a tide gauge.

    quickplt txtfile 1 3 -errorcol 4 
        would plot error bars from column 4 

    quickplt txtfile 1 3 -errorcol 4 -ydoy T
        would plot error bars from column 4  and assume columns 1 and 2 
        are year and day of year

    quickplt txtfile 1 4 -mjd T
        assume column 1 is modified julian day

    quickplt txtfile 1 16 -ylimits 0 2
        would restrict y-axis to be between 0 and 2

    quickplt txtfile 1 16 -outfile myfile.png
        would save png file to $REFL_CODE/Files/myfile.png

    quickplt snrfile 4 7 
        Assuming you submitted a standard SNR file, it would plot the 
        L1 data (column 7) vs time (seconds of the day in column 4). Zeroes would
        be removed, but you can toggle that to keep it.

    quickplt snrfile 2 7 
        Assuming you submitted a standard SNR file, it would plot the 
        L1 data (column 7) vs elevation angle (degrees in column 2). 

    quickplt snrfile 4 8 -sat 25
        Assuming you submitted a standard SNR file, it would plot the 
        data for satellite 25 for L2 data (column 8) vs time (seconds of the day in column 4). 

    quickplt snrfile 4 8 -sat 22
        Assuming you submitted a standard SNR file, it would plot the 
        data for Glonass satellite 22 for L2 data (column 8) vs time (seconds of the day in column 4). 

    Parameters
    ----------
    filename : str
        name of file to be plotted 
    xcol : int
        column number in the file for the x-axis parameter
    ycol : int
        column number in the file for the y-axis parameter
    errorcol : int, optional
        column number for the error bars
    mjd : bool, optional
        code will convert MJD to datetime (for xcol) 
    xlabel : str, optional
        label for x-axis 
    ylabel : str
        label for y-axis 
    symbol : str, optional
        prescribe the marker used in the plot . It can include the color, i.e.
        'b.' or 'b^'
    reverse : bool, optional
        to reverse y-axis limits
    title : str, optional
        title for plot 
    outfile : str, optional
        name of png file to store plot 
    xlimits: list of floats, optional
        xaxis limits  
    ylimits: list of floats, optional
        yaxis limits  
    ydoy : bool, optional
        if columns 1 and 2 are year and doy, the x-axis will be plotted in obstimes
        you should select column 1 to plot
    ymd : bool, optional
        if columns 1,2,3 are year, month, date. So meant for plots with daily measurements -
        not subdaily.
    ymdhm : bool, optional
        if columns 1-5 are Y,M,D,H,M then x-axis will be plotted in obstimes
    filename2 : str
        in principle this allows you to make plots from two files with identical formatting
        not sure that it works
    freq: int, optional
        use column 11 to find (and extract) a single frequency
    utc_offset: int, optional
        offset time axis by this number of hours (for local time)
        this only is used when the mjd option is used  
    yoffset : float
        add or subtract to the y-axis values
    keepzeros: bool, optional
        keep/remove zeros, default is to remove
    sat : int
        satellite number for SNR file plotting (i.e. column 1)

    """

    # change column numbers to pythonese
    xcol = xcol - 1
    ycol = ycol - 1
    if errorcol is None:
        yerrors = False
    else:
        yerrors = True
        errorcol = errorcol - 1

    if ylabel is None:
        ylabel = 'Unknown'

    secondFile = False

    if yoffset is None:
        yoffset = 0

    reverse_sign = reverse

    convert_mjd = mjd

    commentsign = '%'

    if os.path.isfile(filename):
        tvd = np.loadtxt(filename,comments=commentsign)
        if len(tvd) == 0:
            print('empty input file number 1')
            return
        else:

            if (freq is not None):
                print('restricting frequency',freq)
                ii = (tvd[:,10] == freq)
                if (len(tvd[ii,10]) == 0):
                    print('nothing for that frequency')
                    return
                else:
                    tvd = tvd[ii,:]
            if not keepzeros:
                print('Remove zero values')
                ii = (tvd[:,ycol] != 0)
                tvd = tvd[ii,:]
            if (sat is not None):
                print('Only show satellite ', sat)
                ii = (tvd[:,0] == sat)
                tvd = tvd[ii,:]
            if len(tvd) == 0:
                print('No data are left. Exiting')
                sys.exit()

        tval = []
        yval = []
    else:
        print('input file does not exist')
        sys.exit()


    tvd2=[]
    secondFile = False
    if filename2 is not None:
        if os.path.isfile(filename2):
            tvd2 = np.loadtxt(filename2,comments=commentsign)
            if len(tvd2) == 0:
                print('empty input for filenumber 2')
                return
            else:
                secondFile = True
        else:
            print('second filename does not exist')


    tval,yval = q.trans_time(tvd, ymd, ymdhm, convert_mjd, ydoy,xcol,ycol,utc_offset)

    yval = yval + yoffset

    if secondFile:
        tval2,yval2 = q.trans_time(tvd2, ymd, ymdhm, convert_mjd, ydoy,xcol,ycol,utc_offset)
        yval2 = yval2 + yoffset

    # supercedes previous trans_time ... ??? 
    if ydoy:
        print('Making obstimes for ydoy x-axis')
        tval = g.ydoy2datetime(tvd[:,0], tvd[:,1])
    if ydoy & secondFile:
        print('Making obstimes for second ydoy x-axis')
        tval2 = g.ydoy2datetime(tvd2[:,0], tvd2[:,1])

    fig,ax=plt.subplots()

    # i.e. using default
    if symbol is None:
        if yerrors:
            ax.errorbar(tval, yval, yerr=tvd[:,errorcol], fmt='.',color='blue')
        else:
            ax.plot(tval, yval, 'b.')
    else:
        if yerrors:
            ax.errorbar(tval, yval, yerr=tvd[:,errorcol],fmt=symbol)
        else:
            ax.plot(tval, yval, symbol)

    # is second file currently supported???
    if secondFile:
        ax.plot(tval2, yval2, 'r.')

    plt.grid()
    plt.ylabel(ylabel)

    if xlabel is not None:
        plt.xlabel(xlabel)

    if title is None:
        ax.set_title(os.path.basename(filename) )
    else:
        ax.set_title(title)



    if len(ylimits) == 2:
        print('found y-axis limits')
        plt.ylim((ylimits))
    if len(xlimits) == 2:
        print('found x-axis limits')
        if convert_mjd:
            t1 = Time(xlimits[0],format='mjd')
            t1_utc = t1.utc # change to UTC
            tval1 =  t1_utc.datetime # change to datetime
            t2 = Time(xlimits[1],format='mjd')
            t2_utc = t2.utc # change to UTC
            tval2 =  t2_utc.datetime # change to datetime
            plt.xlim((tval1,tval2))
            if utc_offset is not None:
                cc = '{:02d}'.format(abs(utc_offset)) + ':00'
                if utc_offset < 0:
                    plt.xlabel('UTC-' + cc)
                else:
                    plt.xlabel('UTC+' + cc)
        else:
            if ydoy:
                t1,t2 = q.set_xlimits_ydoy(xlimits)
                plt.xlim((t1,t2))
            else:
                plt.xlim((xlimits))

    if reverse_sign:
        ax.invert_yaxis()
    fig.autofmt_xdate() # obstimes

    q.save_plot(outfile)
    plt.show()


def main():
    args = parse_arguments()
    run_quickplt(**args)

if __name__ == "__main__":
    main()
