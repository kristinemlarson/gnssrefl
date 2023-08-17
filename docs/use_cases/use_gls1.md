# Dye2, Greenland 

[Warning](warning.md)

**This site has been retired.**

<p align=center>
<img src="../_static/gls1.jpg" width="400"><br>
</p>

## metadata

**Station Name:** gls1

**Location:**  Dye2, Qeqqata Province, Greenland 

**Archive:**  [UNAVCO](http://www.unavco.org), [SOPAC](http://sopac-csrc.ucsd.edu/index.php/sopac/)

**DOI:**  [https://doi.org/10.7283/T5WS8RDB](https://doi.org/10.7283/T5WS8RDB)

**Ellipsoidal Coordinates:**

- Latitude: 66.47940

- Longitude:  -46.31015

- Height: 2150 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/gls1)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/GLS1.sta)

[Google Maps Link](https://goo.gl/maps/391a7h2HpacAa59u8) 


## Data Summary

Station gls1 was installed at [Dye2](http://greenlandtoday.com/dye-2-a-relic-from-a-not-so-distant-past/?lang=en) on the Greenland Ice Sheet in 2011. 
The antenna is mounted on a long pole; approximately 3.5-meter of the pole was above the ice at the time of installation. 
The receiver at the site only consistently tracks legacy GPS signals. A detailed discussion of the monument and 
data from the station can be found in [Larson, MacFerrin, and Nylen (2020)](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf). 
The latest position time series for gls1 can be retrieved 
from the [Nevada Geodetic Laboratory](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/GLS1.tenv3). 
We also have a utility you can use: **download_unr**

As gls1 is on an ice sheet and the ice surface is relatively smooth in all directions, it 
is unlikely that a complicated azimuth mask will be required.
gls1 was originally installed with an elevation mask of 7 degrees, which is suboptimal for reflections research.
Even though the mask was later removed, we will use 7 degrees as the minimum elevation angle for all our analysis.
Similarly, even though the site managers later changed to enable L2C tracking, to ensure that 
a consistent dataset is being used, we will only use L1 data. gls1 is an example case 
for the [GNSS-IR Web App.](https://gnss-reflections.org/api?example=gls1)

## quickLook 

Our ultimate goal in this use case is to analyze one year of data. We have chosen the year 
2012 because there was a large melt event on the ice sheet. In order to set the proper
quality control parameters, we will use **quickLook** for one day. First we need to translate 
one day of RINEX data:

<code>rinex2snr gls1 2012 100</code>

And then:

<code>quickLook gls1 2012 100</code>

This produces two plots. The first is a geographically oriented (northwest, northeast and so on) 
summary of the frequency content of the GPS data:

<img src=../_static/quicklook-gls1-lsp.png width=600>

The peaks in these periodograms tell us how high the GPS antenna is above the ice surface. The peaks are associated with a reflector height (RH) of ~2.5 meters. [(For more details on quickLook output)](../pages/quickLook.md)

The next plot shows results with respect to azimuth angle.  The top plot is RH and the other 
two are quality control measures: peak amplitude and peak to noise ratio.

<img src=../_static/quicklook-gls1-qc.png width=600>

In the top plot we see that the retrieved reflector heights are consistent at all azimuths.
Retrievals for azimuths between 340 degrees and 40 degrees are consistently marked as not having
met quality control settings.From the center plot we can see that a peak2noise QC metric of 3 is reasonable. 
Similarly, the amplitudes (bottom plot) are generally larger than 10, so 8 is an acceptable minimum value.


Compare that to its level when the site was installed in the year 2011:

<Code>rinex2snr gls1 2011 271 -archive unavco</code>

<CODE>quickLook gls1 2014 271</CODE>

<img src="../_static/gls1-2011.png">

## Measure Snow Accumulation in 2012

The first step is to make SNR files for the year 2012:

<code>rinex2snr gls1 2012 1 -doy_end 366</code>

We will next analyze a year of L1 GPS reflection data from this site. We will use the default minimum and maximum 
reflector height values (0.4 and 6 meters). But for the reasons previously stated, we will set a minimum elevation angle 
of 7 degrees. We also specify that we only want to use the L1 data and set peak2noise and a mimimum
amplitude for the periodograms.  We excluded the northernmost azimuths.

<code>gnssir_input gls1  -e1 7 -l1 True -peak2noise 3 -ampl 8 -azlist2 40 330</code>


Now that you have SNR files and json inputs, you can go ahead and estimate reflector heights for the year 2012:

<code>gnssir gls1 2012 1 -doy_end 366 </code>

We will use the **daily_avg** tool to compute a daily average RH. A median filter is set to 0.25 meters 
and 30 individual tracks are required in order to recover a daily average:

<code>daily_avg gls1 0.25 30</code>

Three plots are returned. The first is all tracks:

<img src="../_static/dailyavg-gls1-3.png" width="600"/>

The second shows the number of tracks used in the daily average:

<img src="../_static/dailyavg-gls1-1.png" width="600"/>

Finally, the average RH each day for the year 2012:

<img src="../_static/dailyavg-gls1-2.png" width="600"/>

This data shown in the last plot show you long-term accumulation as well as relatively small snow accumulation events. The overall 
plot is dominated by the large melt event in the summer.

[A sample daily average RH file.](gls1_dailyRH.txt)

**Things to think about:**

* Why do the number of useable tracks drop drastically at various times in the year?

* Why are the number of tracks retrieved in the summer days consistently higher in number than 
in other times of the year? What is different about the surface in the summer of 2012?

* How would you find out whether this year was anomalously large melt?  

* Try comparing the GNSS-IR results with the [validation data](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf)


The original [J. Glaciology paper](https://www.kristinelarson.net/wp-content/uploads/2015/10/LarsonWahrKuipers_2015.pdf ) discussing this site.
