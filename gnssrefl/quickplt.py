# -*- coding: utf-8 -*-
import argparse
from astropy.time import Time
import datetime
import matplotlib.pyplot as myplt
import numpy as np
import os
import subprocess
import sys


import gnssrefl.quicklib as q
import gnssrefl.gps as g

from gnssrefl.utils import validate_input_datatypes, str2bool

def parse_arguments():
    parser = argparse.ArgumentParser()

    parser.add_argument("filename", help="filename", type=str)
    parser.add_argument("xcol", help="x-axis column number", type=str)
    parser.add_argument("ycol",   help="y-axis column number", type=str)
    parser.add_argument("-errorcol",   help="column for errors for y-axis values", type=int,default=None)
    parser.add_argument("-mjd", help="True/T for when x-values are MJD ", type=str,default=None)
    parser.add_argument("-reverse", help="reverse the y-axis", type=str,default=None)
    parser.add_argument("-ymd", help="True/T for when columns 1-3 are year month day ", type=str,default=None)
    parser.add_argument("-ymdhm", help="True/T for when columns 1-5 are year month day hour minute", type=str,default=None)
    parser.add_argument("-xlabel", type=str, help="optional x-axis label", default=None)
    parser.add_argument("-ylabel", type=str, help="optional y-axis label", default=None)
    parser.add_argument("-symbol", help="plot symbol, e.g. o or -", type=str,default=None)
    parser.add_argument("-title", help="optional title", type=str,default=None)
    parser.add_argument("-outfile", help="optional filename for plot. Must end in png", type=str,default=None)
    parser.add_argument("-xlimits", nargs="*",type=str, help="optional x-axis limits, use yyyyMMdd", default=None)
    parser.add_argument("-ylimits", nargs="*",type=float, help="optional y-axis limits", default=None)
    parser.add_argument("-ydoy", help="True/T for when columns 1-2 are year and doy", type=str,default=None)
    parser.add_argument("-filename2", help="second filename", type=str, default=None)
    parser.add_argument("-freq", help="spec freq, column 11 in a LSP file ", type=int,default=None)
    parser.add_argument("-utc_offset", help="offset from UTC, hours  ", type=int,default=None)
    parser.add_argument("-yoffset", help="offset for y-axis values", type=float,default=None)
    parser.add_argument("-yoffset2", help="offset for y-axis values in file 2", type=float,default=None)
    parser.add_argument("-keepzeros", help="True/T if you want to keep zero y-values (default is to remove)", type=str,default=None)
    parser.add_argument("-sat", help="Only use this satellite (can also input gps, glonass, galileo, and beidou) SNR file", type=str,default=None)
    parser.add_argument("-scale", help="scale factor for first file", type=float,default=None)
    parser.add_argument("-scale2", help="scale factor for file 2", type=float,default=None)
    parser.add_argument("-elimits", nargs="*",type=float, help="optional elevation angle limits for SNR file", default=None)
    parser.add_argument("-azlimits", nargs="*",type=float, help="optional azimuth angle limits for SNR file", default=None)
    parser.add_argument("-plt", help="Set to False/F if you do not want the plot to come to the screen ", type=str,default=None)

    g.print_version_to_screen()

    args = parser.parse_args().__dict__

    # convert all expected boolean inputs from strings to booleans
    boolean_args = ['mjd', 'reverse', 'ymdhm', 'ydoy','ymd','keepzeros','plt']
    args = str2bool(args, boolean_args)

    # only return a dictionary of arguments that were added from the user - all other defaults will be set in code below
    return {key: value for key, value in args.items() if value is not None}


def run_quickplt (filename: str, xcol: str, ycol: str, errorcol: int=None, mjd: bool=False, xlabel: str=None, 
                  ylabel: str=None, symbol: str=None, reverse:bool=False,title:str=None,outfile: str=None,
                  xlimits: str=None, ylimits: float=[], ydoy:bool=False, ymd:bool=False, ymdhm:bool=False, 
                  filename2: str=None, freq:int=None, utc_offset: int=None, yoffset: float=None, 
                  keepzeros: bool=False, sat: str=None,yoffset2: float=None,scale: float=1.0, 
                  scale2: float=1.0, elimits: float=[0], azlimits:float=[0], plt:bool=True):

    """
    quick file plotting using matplotlib

    A png file is saved as temp.png or to your preferred
    filename if outfile is given. In either case, it goes to REFL_CODE/Files

    Allows you to set x and y-axis limits with a title and various axes labels, symbols etc.
    
    Someone could easily update this to include different filetypes (e.g. jpeg)

    I rewrote this recently to take advantage of our boolean argument translator.  Let me know 
    if things have broken or submit a PR.

    To make simple plots of observables in SNR files, the x-axis can be either time or elevation.
    The latter is short for elevation angle. To pick this option set -sat to a specific satellite
    nubmer or a constellation (gps, glonass, etc). You can also set elimits and azlimits for simple
    elevation angle and azimuth angle limits. Only for SNR files, you can send the name of the SNR file
    without the directory, i.e. sc021500.22.snr66 instead of /Users/Files/2022/snr/sc02/sc021500.22.snr66

    You may submit a filename that has been gzipped. The code will checked to see if the gzip version
    is there and gunzip it for you.


    Examples
    --------
    quickplt txtfile 1 16
        would plot column 1 on the x-axis and column 16 on the y-axis

    quickplt sc021500.22.snr66 time L1 -sat gps
        would plot all the GPS L1 SNR data for the given SNR file, with time on the 
        x-axis column 1 on the x-axis and SNR data on the y-axis
        You have to set -sat or it will not work. For a specific satellite number,
        provide that instead of gps. The other allowed x-axis option is elevation which
        is short for elevation angle.

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
    xcol : str
        column number in the file for the x-axis parameter
        for snrfiles, you can say time or elevation
    ycol : str
        column number in the file for the y-axis parameter
        for snrfiles, you can say L1, L2, or L5
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
    xlimits: list of str, 
        xaxis limits  
        if you selected any time options (ymd, mjd, ydoy,mjd), the code assumes
        a format of yyyyMMdd (year,month,day) 
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
        but I am not sure that it one hundred percent always works
    freq: int, optional
        use column 11 to find (and extract) a single frequency
    utc_offset: int, optional
        offset time axis by this number of hours (for local time)
        this only is used when the mjd option is used  
    yoffset : float
        add or subtract to the y-axis values
    keepzeros: bool, optional
        keep/remove zeros, default is to remove
    sat : str
        satellite number for SNR file plotting 
        for all gps satellites, say gps instead of a number
        similar for glonass, galileo, and beidou
    yoffset2 : float
        add or subtract to the y-axis values in filename2
    scale : float
        multiply all y-axis values in file 1 by this value
    scale2 : float
        multiply all y-axis values in file 2 by this value
    elimits : list of floats
        if SNR file is plotted, elevation angle limits are applied
    azlimits : list of floats
        if SNR file is plotted, azimuth angle limits are applied
    plt: bool
         whether you want the plot to be displayed on the screen.
         png file is always created.

    """
    if xlimits is None:
        xlimits = []

    snrfile = False
    if sat is not None:
        snrfile = True

        if xcol == 'elevation':
            xcol = 1 # python column
        elif xcol == 'time':
            xcol = 3 # python column
        else:
            xcol = int(xcol) - 1

        if (ycol.upper() == 'L1'):
            ycolT = 'L1'
            ycol = 6
        elif (ycol.upper() == 'L2'):
            ycolT = 'L2'
            ycol = 7
        elif (ycol.upper() == 'L5'):
            ycolT = 'L5'
            ycol = 8
        else:
            ycolT = ''
            ycol = int(ycol) - 1
    else:
        # change strings to integers and change to python column
        if (xcol == 'time'):
            print('You cannot chose time for the xcolumn unless you invoke -sat mode. xcol must be an integer. Exit')
            sys.exit()
        elif (xcol == 'elevation'):
            print('You cannot chose elevation for the xcolumn. Unless you invoke -sat mode. xcol must be an integer. Exit')
            sys.exit()
        else:
            xcol = int(xcol) - 1
            ycol = int(ycol) - 1


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
    if yoffset2 is None:
        yoffset2 = 0
    reverse_sign = reverse

    convert_mjd = mjd
    commentsign = '%'

    basename = os.path.basename(filename)
    station = basename[0:4]
    cyear = '20' + basename[9:11]  
    if snrfile:
        xdir = os.environ['REFL_CODE']
        longfile = xdir + '/' + cyear + '/snr/' + station + '/' + basename
        longfile_gz = longfile + '.gz'
        if not os.path.isfile(filename) and os.path.isfile(longfile):
            filename = longfile
            print('using ', longfile)
        elif not os.path.isfile(filename) and os.path.isfile(longfile_gz):
            subprocess.call(['gunzip', longfile_gz])
            filename = longfile
            print('now using ', longfile)

    if (not os.path.isfile(filename)) & os.path.isfile(filename + '.gz'):
        print('I will be nice and gunzip the file for you ...')
        subprocess.call(['gunzip', filename + '.gz'])

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
            if snrfile:
                if sat.lower() == 'gps':
                    print('Show all GPS satellites')
                    print('initial nmber of observations:', len(tvd))
                    ii = (tvd[:,0] < 33)
                    tvd = tvd[ii,:]
                    print('after editing:', len(tvd))
                elif sat.lower() == 'glonass':
                    print('Show all Glonass satellites')
                    print('initial nmber of observations:', len(tvd))
                    ii = (tvd[:,0] > 100) & (tvd[:,0] <= 199)
                    tvd = tvd[ii,:]
                    print('after editing:', len(tvd))
                elif sat.lower() == 'galileo':
                    print('Show all Galileo satellites')
                    print('initial nmber of observations:', len(tvd))
                    ii = (tvd[:,0] > 200) & (tvd[:,0] <= 299)
                    tvd = tvd[ii,:]
                    print('after editing:', len(tvd))
                elif sat.lower() == 'beidou':
                    print('Show all Beidou satellites')
                    print('initial nmber of observations:', len(tvd))
                    ii = (tvd[:,0] > 300) & (tvd[:,0] <= 399)
                    tvd = tvd[ii,:]
                    print('after editing:', len(tvd))
                else:
                    sat = int(sat)
                    print('Only show satellite ', sat)
                    ii = (tvd[:,0] == sat)
                    tvd = tvd[ii,:]
            if len(tvd) == 0:
                print('No data are left. Exiting')
                sys.exit()

            if snrfile:
                # this means it is a SNR file
                if len(elimits) == 2:
                    print('Apply elevation angle limits')
                    e1 = elimits[0]
                    e2 = elimits[1]
                    i= (tvd[:,1] >= e1) & (tvd[:,1] <= e2)
                    tvd=tvd[i,:]
                if len(azlimits) == 2:
                    print('Apply azimuth angle limits')
                    a1 = azlimits[0]
                    a2 = azlimits[1]
                    i= (tvd[:,2] >= a1) & (tvd[:,2] <= a2)
                    tvd=tvd[i,:]
                if len(tvd) == 0:
                    print('no data for this satellite and these editing choices.')
                    print('exiting '); sys.exit()

        tval = []
        yval = []
    else:
        print('input file does not exist')
        sys.exit()


    tvd2=[]
    secondFile = False
    if filename2 is not None:
        print('Warning: filename2 does not allow SNR file options')
        if os.path.isfile(filename2):
            tvd2 = np.loadtxt(filename2,comments=commentsign)
            if len(tvd2) == 0:
                print('empty input for filenumber 2')
                return
            else:
                secondFile = True
                if not keepzeros:
                    print('Remove zero values from second file')
                    ii = (tvd2[:,ycol] != 0)
                    tvd2 = tvd2[ii,:]
                if (sat is not None):
                    print('Only show satellite ', sat, ' for second file')
                    ii = (tvd2[:,0] == sat)
                    tvd2 = tvd2[ii,:]
        else:
            print('second filename does not exist')


    tval,yval = q.trans_time(tvd, ymd, ymdhm, convert_mjd, ydoy,xcol,ycol,utc_offset)

    yval = yval + yoffset

    if secondFile:
        tval2,yval2 = q.trans_time(tvd2, ymd, ymdhm, convert_mjd, ydoy,xcol,ycol,utc_offset)
        yval2 = yval2 + yoffset2
        yval2 = yval2*scale2


    # supercedes previous trans_time ... ??? 
    if ydoy:
        print('Making obstimes for ydoy x-axis')
        tval = g.ydoy2datetime(tvd[:,0], tvd[:,1])
    if ydoy & secondFile:
        print('Making obstimes for second ydoy x-axis')
        tval2 = g.ydoy2datetime(tvd2[:,0], tvd2[:,1])

    fig,ax=myplt.subplots()

    # i.e. using default
    if symbol is None:
        if yerrors:
            ax.errorbar(tval, yval, yerr=tvd[:,errorcol], fmt='.')
        else:
            ax.plot(tval, yval, 'b.')
    else:
        if yerrors:
            ax.errorbar(tval, yval, yerr=tvd[:,errorcol],fmt=symbol)
        else:
            ax.plot(tval, yval, symbol)

    # is second file currently supported???
    if secondFile:
        if symbol is None:
            ax.plot(tval2, yval2, 'r.')
        else:
            # ??
            ax.plot(tval2, yval2, symbol )

    myplt.grid()
    myplt.ylabel(ylabel)

    if xlabel is not None:
        myplt.xlabel(xlabel)
    else:
        if snrfile:
            if (xcol == 1): # python column name
                myplt.xlabel('elevation angle (degrees)')
            if (xcol == 3): # using python column name
                myplt.xlabel('seconds of the day')
            myplt.ylabel(ycolT + ' SNR, dBHz')


    if title is None:
        if snrfile:
            sname = os.path.basename(filename)
            ytitle = sname[0:4] + ' 20' + sname[9:11] + ' ' + sname[4:7]
            ax.set_title('sat ' + str(sat) + '/' + ytitle  )
        else:
            ax.set_title(os.path.basename(filename) )
    else:
        ax.set_title(title)



    if len(ylimits) == 2:
        print('found y-axis limits')
        myplt.ylim((ylimits))
    if len(xlimits) == 2:
        print('found x-axis limits')
        if (convert_mjd | ymd | ydoy | ymdhm):
            if (len(xlimits[0]) != 8):
                print('xlimit format is YYYYMMDD, but you said: ', xlimits[0], ' Exiting'); sys.exit()
            if (len(xlimits[1]) != 8):
                print('xlimit format is YYYYMMDD, but you said: ', xlimits[1], ' Exiting'); sys.exit()
        else:
            # make sure you change from string to numbers
            xlimits[0] = float(xlimits[0])
            xlimits[1] = float(xlimits[1])

        if convert_mjd:
            # need to just get MJD so you can use the local UTC offset
            year1, month1, day1, doy1, mjd1 = g.noaa2me(xlimits[0])
            year2, month2, day2, doy2, mjd2 = g.noaa2me(xlimits[1])

            t1 = Time(mjd1,format='mjd')
            t1_utc = t1.utc # change to UTC
            tvalues1 =  t1_utc.datetime # change to datetime
            t2 = Time(mjd2,format='mjd')
            t2_utc = t2.utc # change to UTC
            tvalues2 =  t2_utc.datetime # change to datetime
            myplt.xlim((tvalues1,tvalues2))
            if utc_offset is not None:
                cc = '{:02d}'.format(abs(utc_offset)) + ':00'
                if utc_offset < 0:
                    myplt.xlabel('UTC-' + cc)
                else:
                    myplt.xlabel('UTC+' + cc)
        else:
            if ymd | ydoy | ymdhm :
                t1 = g.noaatime_to_obstime(xlimits[0])
                t2 = g.noaatime_to_obstime(xlimits[1])
                myplt.xlim((t1,t2))
            else: 
                # this is for when you are plotting something that isn't time
                myplt.xlim((xlimits[0], xlimits[1]))

    if reverse_sign:
        ax.invert_yaxis()
    fig.autofmt_xdate() # obstimes

    q.save_plot(outfile)
    if plt:
        myplt.show()


def main():
    args = parse_arguments()
    run_quickplt(**args)

if __name__ == "__main__":
    main()
