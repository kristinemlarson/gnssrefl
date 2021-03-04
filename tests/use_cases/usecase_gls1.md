### Use Case for Greenland Ice Sheet, Greenland

**Station Name:**		gls1

**Location:**  Greenland Ice Sheet in Qeqqata Province, Greenland

**Archive:**  [UNAVCO](http://www.unavco.org), [SOPAC](http://sopac-csrc.ucsd.edu/index.php/sopac/)

**DOI:**  [https://doi.org/10.7283/T5WS8RDB](https://doi.org/10.7283/T5WS8RDB)

**Ellipsoidal Coordinates:**

- Latitude: 66.47940

- Longitude:  -46.31015

- Height:    2150 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/gls1)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/GLS1.sta)

[Google Maps Link](https://goo.gl/maps/391a7h2HpacAa59u8) 

<img src="gls1-photo.png" width="300">
Image source: IRIS/PASSCAL

## Data Summary

Station gls1 was installed on the Greenland Ice Sheet.
The antenna mounted on a ~3.5-meter pole.  The receiver at the site tracks only 
GPS signals, and the data are archived at UNAVCO and SOPAC.  A detailed discussion of 
data from the station can be found in this 
[open option paper](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf). 
Position time series for gls1 can be retrieved 
from the [Nevada Geodetic Laboratory](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/GLS1.tenv3).

## Web App

The [GNSS-IR Web App](https://gnss-reflections.org/fancy6?example=gls1) uses gls1 as an example. 
It takes 5-10 seconds to run.

**Setting Elevation and Azimuth Mask**

The site is on an ice sheet, flat in all directions, so no elevation or azimuth masks are required 
to run the reflectometry codes and defaults are sufficient.

## Reproduce the Web App

**Make SNR File**

First, make an SNR file by downloading the RINEX file and extracting the GPS SNR data:

*rinex2snr gls1 2019 200*

**Take a Quick Look at the Data**

Use **quickLook** to produce a periodogram similar to the one in the web app. The periodogram  is set to use the L1 frequency by default.

*quickLook gls1 2019 200*

<img src="gls1-L1.png" width="500">

The four subplots show different regions around the antenna (NW, NE, SW, SE). The x-axis gives the reflector height (RH) and the y-axis gives the spectral amplitude of the SNR data. The multiple colors are used to depict different satellites that rise or set over that section (quadrant) of the field at gls1. The goal of this exercise is to notice that the peaks of those periodograms are lining up around an x-value of ~1.3 meters. There are also some thin gray lines - and those are failed periodograms. This means that the SNR data for a satellite do not meet the quality standards in the code.

The SNR values for the L2 and L5 frequencies do not meet the quality standards for **quickLook** and are not plotted here.

## Analyze the Data

gls1 was originally installed with an elevation mask of 7 degrees. 
The mask was later changed, but for consistency the gnssir code will be set to use a 
minimum elevation angle of 7 degrees. This is done when setting up the json file containing the analysis paramters:

*make_json_input gls1 66.479 -46.310 2148.578 -h1 0.5 -h2 8 -e1 7 -e2 25*

The **make_json_input** defaults are to use all GPS frequencies (1,20,5). 

However, the L2 data are problematic at this site. L5 data do not exist.
Manually edit the json file to remove L2 and L5 from the list 
labeled "freqs". Then change the list "reqAmp" so that it has the same number 
of elements as the list "freqs" (by default, all elements in "reqAmp" will have a value of 6). 
[Example json file.](gls1.json)

To test the code, we will use the year 2012. First, make SNR files.

*rinex2snr gls1 2012 1 -doy_end 365*

Then estimate reflector heights:

*gnssir gls1 2012 1 -doy_end 365*

We will use the **daily_avg** tool to compute a daily average. Here the median filter is set to 0.25 meters 
and 30 individual tracks are required:

*daily_avg gls1 0.25 30*

All tracks:

<img src="gls1-1.png" width="500"/>

Daily averages:

<img src="gls1-2.png" width="500"/>


[An sample daily average RH file.](gls1-dailyavg.txt)



