import argparse
import datetime
import matplotlib.pyplot as plt
import os
import numpy as np
import sys

def main():
    """
    Quick Plotter for txt file 

    Parameters
    ----------
    filename : str
        filename to be plotted
    xcol : int
        column number to plot on the x-axis
    ycol : int
        column number to plot on the y-axis
    filename2 : str
        optional second filename to be plotted


    """

    parser = argparse.ArgumentParser()
    parser.add_argument("filename", help="filename", type=str)
    parser.add_argument("xcol", help="x-column", type=int)
    parser.add_argument("ycol",   help="y-column", type=int)
    parser.add_argument("-filename2", help="filename2", type=str,default=None)
    parser.add_argument("-hash", help="Comment delimiter in your file. Default is %", type=str, default=None)
    parser.add_argument("-mjd", help="set to True/T if x-values are MJD", type=str,default=None)
    parser.add_argument("-reverse", help="set to True/T to reverse the y-axis", type=str,default=None)
    parser.add_argument("-ymdh", help="if True/T, columns 1-4 are year mon day hour ", type=str,default=None)

    args = parser.parse_args()

    filename = args.filename;
    if args.filename2 == None:
        secondFile = False
    else:
        secondFile = True
        filename2 = args.filename2

    xcol = int(args.xcol) - 1
    ycol = int(args.ycol) - 1
    #print(filename,xcol,ycol)

    reverse_sign = False 
    if (args.reverse == 'True') or (args.reverse == 'T'):
        reverse_sign = True

    ymd = False
    if (args.ymdh == 'True') or (args.ymdh == 'T'):
        ymd = True

    if (args.hash== None):
        comment = '%'
    else:
        comment = '#'
        
    if os.path.isfile(filename):
        tvd = np.loadtxt(filename,comments=comment)
        if len(tvd) == 0:
            print('empty input file')
            return
        tval = []
        yval = []
    else:
        print('input file does not exist')
        sys.exit()

    if secondFile:
        tvd2 = np.loadtxt(filename2,comments=comment)
        if len(tvd2) == 0:
            print('empty input file')
            return
        tval2 = []
        yval2 = []
    else:
        print('second file does not exist')

    if ymd == True:
        year = tvd[:,0]; month = tvd[:,1]; day = tvd[:,2]; 
        hour = tvd[:,3] 
        for i in range(0,len(tvd)):
            if (tvd[i, 4]) > 0:
                y = int(year[i]); m = int(month[i]); d = int(day[i])
                today=datetime.datetime(y,m,d)
                doy = (today - datetime.datetime(today.year, 1, 1)).days + 1
                h = int(hour[i])
                tval.append(y + (doy +  h/24)/365.25);
                yval.append( tvd[i,4]/1000)
    else:
        if args.mjd == 'T':
            for i in range(0,len(tvd)):
                doy = int(tvd[i,1]) ; year = int(tvd[i,0])
                # get datetime
                d = datetime.datetime(year, 1, 1) + datetime.timedelta(days=(doy-1))
                # and 
                month = int(d.month) ; day = int(d.day)
                bigT = datetime.datetime(year=year, month=month, day=day, hour=12, minute=0, second=0)
                tval.append(bigT)
                yval.append(tvd[i,ycol])
        else:
            tval = tvd[:,xcol] ; yval = tvd[:,ycol]
            x1 = min(tval)
            x2 = max(tval)
            if secondFile:
                tval2 = tvd2[:,xcol] ; yval2 = tvd2[:,ycol]


    #fig,ax1 = plt.figure()
    fig,ax=plt.subplots()
    ax.plot(tval, yval, 'b.')
    if secondFile:
        ax.plot(tval2, yval2, 'r.')
    ax.set_title(os.path.basename(filename) )
    

    #plt.plot(tval,yval,'b.')
    plt.grid()
    #plt.xlim((x1,x2))
    if reverse_sign:
        ax.invert_yaxis()
    plt.show()

if __name__ == "__main__":
    main()


