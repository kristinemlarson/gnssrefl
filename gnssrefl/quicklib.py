import numpy as np
import datetime as datetime
from astropy.time import Time


def trans_time(tvd, ymd, convert_mjd, ydoy ,xcol,ycol):
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
        column number for x-axis

    ycol : int
        column number for y-axis

    Returns
    -------

    tval : list
         floats or datetime

    yval : list
         floats ?
        
    """

    tval = []
    yval = []

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
            t1 = Time(tvd[:,xcol],format='mjd')
            t1_utc = t1.utc # change to UTC
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
