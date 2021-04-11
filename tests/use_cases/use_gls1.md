### Dye2, Greenland 

**Station Name:** gls1

**Location:**  Greenland Ice Sheet in Qeqqata Province 

**Archive:**  [UNAVCO](http://www.unavco.org), [SOPAC](http://sopac-csrc.ucsd.edu/index.php/sopac/)

**DOI:**  [https://doi.org/10.7283/T5WS8RDB](https://doi.org/10.7283/T5WS8RDB)

**Ellipsoidal Coordinates:**

- Latitude: 66.47940

- Longitude:  -46.31015

- Height: 2150 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/gls1)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/GLS1.sta)

[Google Maps Link](https://goo.gl/maps/391a7h2HpacAa59u8) 

<img src="gls1.jpg" width="400">
<BR>
gls1 at installation

## Data Summary

Station gls1 was installed on the Greenland Ice Sheet in 2011. 
The antenna is mounted on a long pole; approximately 3.5-meter of the pole was above the ice at the time of installation. 
The receiver at the site only consistently tracks legacy GPS signals. A detailed discussion of the monument and 
data from the station can be found in [Larson, MacFerrin, and Nylen (2020)](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf). 
Various position time series for gls1 can be retrieved 
from the [Nevada Geodetic Laboratory](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/GLS1.tenv3). We also have 
a utility you can use: *download_unr*

As gls1 is on an ice sheet and the ice surface is relatively smooth in all directions, it 
is unlikely that a complicated azimuth mask will be required.
gls1 was originally installed with an elevation mask of 7 degrees, which is suboptimal for reflections research.
Even though the mask was later removed, we will use 7 degrees as the minimum elevation angle for all our analysis.
Similarly, even though the site managers later changed to enable L2C tracking, to ensure that a consistent dataset is being 
used, we will only use L1 data. More information about 
gls1 can be found on the [GNSS-IR Web App.](https://gnss-reflections.org/fancy6?example=gls1)

## quickLook 

Our goal in this use case is to analyze one year of data. We have chosen 2012. In order to set the proper
quality control parameters, we will use quickLook for one day. First we need to translate 
one day of RINEX data using **rinex2snr**:

*rinex2snr gls1 2012 100*

We then use **quickLook**:

*quickLook gls1 2012 100*

This produces two plots:

<img src=quicklook-gls1-lsp.png width=500>

The peaks in all four qudarants are bunched at ~2.5 meters reflector height (RH).  
[(For more details on quickLook output)](../../docs/quickLook_desc.md)

The next plot puts the RH retrievals in the context of azimuth and two quality control measures:
peak amplitude and peak to noise ratio.

<img src=quicklook-gls1-qc.png width=500>

In the top plot we see that in the reflector heights are consistent at all azimuths.
The azimuths between 340 degrees and 40 degrees do not appear to provide reliable RH retrievals.
We also see that a peak2noise QC metric (middle plot) of 3 is reasonable. 
Similarly, the amplitudes (bottom plot) are generally larger than 10, so 8 is an acceptable minimum value.

## Measure Snow Accumulation in 2012

We will next analyze a year of data from this site. We will use the default minimum and maximum 
reflector height values. But for the reasons previously stated, we will set a minimum elevation angle 
of 7 degrees. We also specify that we only want to use the L1 data and set peak2noise and a mimimum
amplitude for the periodograms:

*make_json_input gls1 66.479 -46.310 2148.578 -e1 7 -e2 25 -l1 True -peak2noise 3 -ampl 8*

[Example json file.](gls1.json)

We have also excluded a bit of the northern tracks by handediting the json. This is not required as 
the software appears to be appropriately removing these unreliable azimuths. Note: the removal of these
azimuths is more related to the GPS satellite inclination than local conditions at gls1.

Now make SNR files for the year 2012:

*rinex2snr gls1 2012 1 -doy_end 366*

Then estimate reflector heights:

*gnssir gls1 2012 1 -doy_end 366*

We will use the **daily_avg** tool to compute a daily average. Here the median filter is set to 0.25 meters 
and 30 individual tracks are required:

*daily_avg gls1 0.25 30*

All tracks:

<img src="dailyavg-gls1-3.png" width="500"/>

Number of tracks used in the daily average:

<img src="dailyavg-gls1-1.png" width="500"/>

Average RH for the year 2012:

<img src="dailyavg-gls1-2.png" width="500"/>

Questions:

* Why do you think the number of useable tracks drops drastically at various times in the year?

* Why do you think the number of tracks retrieved in the summer days are consistently higher in number than 
in other times of the year?

[A sample daily average RH file.](gls1_dailyRH.txt)

Validation snow accumulation data for this site are provided in [Larson et al., 2020](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf).
