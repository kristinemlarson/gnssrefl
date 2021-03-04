#!/bin/python3
#Plot tide gauge data and gps reflector heights.  This script assumes data files have been downloaded and are in the same directory
#as the script
from csv import reader
import re
from datetime import datetime
from datetime import timedelta
import math
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

def readfiles(file1, file2):
    tidedates=[]
    waterlevel=[]
    mchndates=[]
    reflht=[]
    regex1 = '(?P<date>^[\d|-]+),(?P<slev>[-|\d|.]*),'
    regex2 = '^ (?P<year>[ \d]+) +(?P<doy>[\d]+) +(?P<rh>[\d|-|.]+)'

#read tide data    
    with open(file1, 'r') as myfile1:
        data1 = myfile1.read()
        matches1 = re.finditer(regex1, data1, flags=re.MULTILINE)        
    for match1 in matches1:
        tidedates.append(datetime.strptime(match1.group('date'), '%Y-%m-%d'))
        waterlevel.append(float(match1.group('slev')))

#read daily average reflector heights
    with open(file2, 'r') as myfile2:
        data2 = myfile2.read()
        matches2 = re.finditer(regex2, data2, flags=re.MULTILINE)        
        for match2 in matches2:
            ydoy = f'{int(match2.group("year"))}-{int(match2.group("doy"))}'
            date = datetime.strptime(ydoy, '%Y-%j')
            mchndates.append(date)
            reflht.append(float(match2.group('rh')))    
    return tidedates, waterlevel, mchndates, reflht

#both tidegauge and gps data sets have gaps, so pad the missing days with nan (also generate date vector list for full year)
def addnans(ymdvec, datavec):
    yearvec=[]
    paddedvec=[]
    date1 = datetime.fromisoformat('2013-01-01')
    date2 = datetime.fromisoformat('2013-12-31')
    ct_day = date1    
    for day in range(0, 365):
        yearvec.append(ct_day)
        ct_day = ct_day + timedelta(days=1)    
    tmp = math.nan
    for i in range(0, len(yearvec)):
        for j in range(0, len(ymdvec)):
            if yearvec[i] == ymdvec[j]:
                tmp = datavec[j]
        paddedvec.append(tmp)
        tmp = math.nan    
    return yearvec, paddedvec

def getrms(residuals):
    val = np.sqrt((residuals**2).mean())
    return val

if __name__ == "__main__":    
    tidedates, waterlevel, mchndates, reflht = readfiles(file1='10750-01-JAN-2013_slev.csv', 
                                                                         file2='mchn-dailyavg.txt')    
#pad missing days with nan
    ymd, padded_rh = addnans(mchndates, reflht)
    ymd, padded_wl = addnans(tidedates, waterlevel)    

#create numpy array objects
    rh_array = np.array(padded_rh)
    wl_array = np.array(padded_wl)    

#get linear regression (use scipy but mask out nans)
    mask = ~np.isnan(rh_array) & ~np.isnan(wl_array)    
    slope, intercept, r_val, p_val, std_err = stats.linregress(rh_array[mask], wl_array[mask])
    checkfit = slope*rh_array[mask] + intercept    
    resids = [i - j for i, j in zip(wl_array[mask], checkfit)]
    resids_array = np.array(resids)
    rms_resids = getrms(resids_array)

#plot reflector height vs. water level (using masked values)    
    fig, ax = plt.subplots(figsize=(10,8))
    ax.plot(rh_array[mask], checkfit, '-', color='black')
    ax.scatter(rh_array[mask], wl_array[mask], color = 'tab:blue')    
    ax.set_xlabel("Reflector Height (m)", fontsize=16)
    ax.set_ylabel("Water Level (m)", fontsize=16)
    ax.set_title('MCHN Reflector Height vs. Tide Gauge Measurements', fontsize=18)
    ax.tick_params(labelsize=14)
    plt.grid()
    txtstr = '\n'.join((
        'Slope=%.2f' % (slope, ),
        'Intercept=%.2f m' % (intercept, ),
        'Correlation=%.3f' % (r_val, ),
        'P-value=%.2f' % (p_val, ),
        'RMS of Residuals=%.3f m' % (rms_resids, )))
    props = dict(boxstyle='round', facecolor='white', alpha=1)
    ax.text(.65, .95, txtstr, transform=ax.transAxes, fontsize=14, verticalalignment='top', bbox=props)

#plot time series for the water levels and reflector heights (with reversed axes)    
    fig, ax1 = plt.subplots(figsize=(10, 8))
    color = 'tab:blue'
    ax1.set_xlabel('Date', fontsize=16)
    ax1.set_ylabel('Tide Gauge Water Level (m)', color='black', fontsize=16)
    ax1.scatter(tidedates, waterlevel, label='Tide Gauge', color=color)
    ax1.tick_params(axis='y', labelcolor='black', labelsize=14)
    ax1.tick_params(axis='x', labelcolor='black', labelsize=14)
    plt.ylim(-.5,.3)    
#instantiate a second axes that shares the same x-axis    
    ax2 = ax1.twinx()  
    color = 'tab:orange'
    ax2.set_ylabel('GPS Reflector Height (m)', color='black', fontsize=16)  
#we already handled the x-label with ax1
    ax2.scatter(mchndates, reflht, label='GPS Reflector Height', color=color)
    ax2.tick_params(axis='y', labelcolor='black', labelsize=14)
    plt.ylim(6.75,7.55)
    plt.gca().invert_yaxis()
    fig.legend(loc='lower right', bbox_to_anchor=(0.925, 0.079), edgecolor='black')
    plt.title('MCHN Tide Gauge Measurements vs. Reflectometry', fontsize=18)    
    fig.tight_layout()
    plt.show()
