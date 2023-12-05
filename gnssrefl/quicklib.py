import datetime as datetime
import math
import matplotlib.pyplot as plt
import numpy as np
import os
import subprocess
import sys
from astropy.time import Time

import gnssrefl.gps as g

def trans_time(tvd, ymd, convert_mjd, ydoy ,xcol,ycol,utc_offset):
    """
    translates time for quickplt

    Parameters
    ----------
    tvd : str
        plain text file

    ymd : bool
        first three columns are year,month,day, hour,
        minute,second

    convert_mjd : bool
        convert from MJD (column 1 designation)
        time is datetime obj

    ydoy : bool
        first two columns are year and day of year
        time is datetime obj

    xcol : int
        column number for x-axis in python speak

    ycol : int
        column number for y-axis in python speak
    utc_offset : int
        offst in hours from UTC/GPS time.  None means do not use

    Returns
    -------

    tval : list
         floats or datetime

    yval : list
         floats ?
        
    """

    tval = []
    yval = []

    nr,nc = tvd.shape
    print('rows and columns ', nr,nc)
    if (ycol+1 > nc):
        print('You asked to plot column', ycol+1, ' and that column does not exist in the file')
        sys.exit()
    if (xcol+1 > nc):
        print('You asked to plot column', xcol+1, ' and that column does not exist in the file')
        sys.exit()

    if ymd == True:
        year = tvd[:,0]; month = tvd[:,1]; day = tvd[:,2];
        hour = tvd[:,3] ; minute = tvd[:,4]
        for i in range(0,len(tvd)):
            if (tvd[i, 4]) > 0:
                y = int(year[i]); m = int(month[i]); d = int(day[i])
                # i am sure there is a better way to do this
                today=datetime.datetime(y,m,d)
                doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
                h = int(hour[i])
                mi = int(minute[i])
                tval.append(y + (doy +  h/24 + mi/24/60)/365.25);
                yval.append( tvd[i,ycol]/1000)
    else:
        if convert_mjd:
            mm = tvd[:,xcol]
            if utc_offset is not None :
                if utc_offset != 0:
                    print('Apply local time offset')
                    mm = mm + utc_offset*3600/86400
            t1 = Time(mm,format='mjd')
            t1_utc = t1.utc # change to UTC
            #if utc_offset is not None:

            # probably can be done in one step!
            tval =  t1_utc.datetime # change to datetime
            yval = tvd[:,ycol] # save the y values
        elif ydoy:
            tval = tvd[:,0]  + tvd[:,1]/365.25
            yval = tvd[:,ycol]
            ii = np.argsort( tval)
            tval = tval[ii]; yval=yval[ii]
        else:
            tval = tvd[:,xcol] ; yval = tvd[:,ycol]
            x1 = min(tval) ; x2 = max(tval)


    return tval, yval 

def set_xlimits_ydoy(xlimits):
    """
    translate command line xlimits into datetime for nicer plots

    Parameters
    ----------
    xlimits : list of floats
         year (fractional, i.e. 2015.5)

    Returns 
    -------
    t1 : datetime
         beginning date for x-axis
    t2 : datetime
         end date for x-axis
    """
    year1 = math.floor(xlimits[0])
    doy1= math.floor(365.25*(xlimits[0]-year1))
    if doy1 == 0:
        doy1 = 1
    yy, mm, dd = g.ydoy2ymd(year1,doy1)
    t1 = datetime.datetime(year=yy, month=mm, day=dd)

    year2 = math.floor(xlimits[1])
    doy2= math.floor(365.25*(xlimits[1]-year2))
    if doy2 == 0:
        doy2 = 1

    yy, mm, dd  = g.ydoy2ymd(year2,doy2)
    t2 = datetime.datetime(year=yy, month=mm, day=dd)

    return t1, t2


def save_plot(out):
    """
    Makes a png plot and saves it in REFL_CODE/Files

    Parameters
    ----------
    out : str
        name of output file (or None)

    """
    # make sure output directory exists.
    xdir = os.environ['REFL_CODE']  + '/Files/' 
    if not os.path.exists(xdir) :
        subprocess.call(['mkdir', xdir])

    if out is None:
        out = 'temp.png'
        print('Plotfile saved to: ', xdir + out)
        plt.savefig(xdir + out ,dpi=300)
    else:
        if out[-3:] == 'png':
            print('Plotfile saved to: ', xdir  + out)
            plt.savefig(xdir + out,dpi=300)
        else:
            print('Output filename must end in png. No file is being written')
