## Homework 2

**Prerequisite:** You need to make
sure the software has been properly installed and you have successfully completed the "homework 0" assignment.

**Purpose:** Learn how to measure snow surface variations with GNSS-IR

**Station:** gls1

gls1 was installed at [Dye2](http://greenlandtoday.com/dye-2-a-relic-from-a-not-so-distant-past/?lang=en) on the Greenland Ice Sheet in 2011. 
The antenna is mounted on a long pole; approximately 3.5-meter of the pole was above the ice at the time of installation. 
A detailed discussion of the monument and 
data from the station can be found in [Larson, MacFerrin, and Nylen (2020)](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf). 
The latest position time series for gls1 can be retrieved 
from the [Nevada Geodetic Laboratory](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/GLS1.tenv3). 

As gls1 is on an ice sheet and the ice surface is relatively smooth in all directions, it 
is unlikely that a complicated azimuth mask will be required.

gls1 was originally installed with an elevation mask of 7 degrees, which is suboptimal for reflections research.
Even though the mask was later removed, we will use 7 degrees as the minimum elevation angle for all our analysis.
Similarly, even though the site managers later changed to enable L2C tracking, this was not the case in 2012, so here we will only use L1 data.

Use the geoid tab at the [gnss-reflections webapp](https://gnss-reflections.org) to gather more i
nformation about the site. 
You can enter the station coordinates by hand if 
you know them, but since gls1 is part of a public archive provided by UNR, coordinates have been stored in the 
webapp. Just type in gls1 for the station name. 

**Using gnssrefl**

Our ultimate goal in this use case is to analyze one year of data. We have chosen the year 2012 
because there was a large melt event on the ice sheet. In order to set the proper quality control parameters, we will use 
<code>quickLook</code> for one day. 

First you need to translate one day of RINEX data.  Use the year 2012 and day of year 100.

Now run <code>quickLook</code>.

[If you don't remember how to run these modules](https://gnssrefl.readthedocs.io/en/latest/pages/quick_recall.html).

Looking at the QC metrics plots created by <code>quickLook</code>, do you have some ideas on how to change the azimuth mask angles?

Now make SNR files for gls1 for the all of 2012. Use the <code>-weekly True</code> setting to save time.

We will next analyze a year of L1 GPS reflection data from gls1. We will use the default minimum and maximum 
reflector height values. But for the reasons previously stated, you will want to 
set a minimum elevation angle of 7 degrees. We also specify that we only want to use the L1 data.
Use the utility <code>gnssir_input</code> to set and store the analysis settings.  
(Hint: we recommend the argument `-azlist2 40 330`.)
    
Now that you have SNR files and analysis inputs, you can go ahead and estimate reflector 
heights for the year 2012 using <code>gnssir</code>.
Note that it is normal to see 'Could not read the first SNR file:' because we only created SNR files once a week.

Now you can use the <code>daily_avg</code> tool to compute a daily average reflector height for gls1. 
Try setting the median filter to 0.25 meters and individual tracks to 30. These numbers are used 
by <code>daily_avg</code> to set QC in order to recover a trustworthy daily average [(there is more information here on these parameters)](https://gnssrefl.readthedocs.io/en/latest/pages/README_dailyavg.html). A plain txt file 
with the RH outputs are created as well as several plots. 
The data in the main RH plot show you long-term accumulation as well as relatively small snow 
accumulation events. The overall plot is dominated by the large melt event in the summer of 2012.
Note that RH is plotted on the y-axis with RH decreasing rather than increasing. Why do you think we 
did that?

