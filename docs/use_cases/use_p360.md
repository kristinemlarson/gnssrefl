# Island Park, Idaho

[Warning](warning.md)

**Use Case Updated on June 4, 2023 for gnssir_input**

<HR>
  
<p align=center>
<img src="https://gnss-reflections.org/static/images/P360.jpg" width="500">
</p>

## metadata

**Station Name:**  p360

**Location:**  Island Park, Idaho

**Archive:**  unavco

**DOI:**  [https://doi.org/10.7283/T5DB7ZR3](https://doi.org/10.7283/T5DB7ZR3)

**Ellipsoidal Coordinates:**

- Latitude:  44.31785

- Longitude: -111.45068

- Height: 1857.861 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/P360)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/P360.sta)

[Station Page at PBO H2O](http://cires1.colorado.edu/portal/index.php?product=snow&station=p360)

[Google Map Link](https://goo.gl/maps/EcTkbHjaSaWp4d8H9)



## Data Summary

Station p360 is located to the west of Yellowstone National 
Park. At an elevation of ~1858 m, 
winter snowfall can be frequent and heavy. 
The site has been recording multi-GNSS data since March 2020. Before that time, only 
the L2C GPS data are of reliable quality for snow accumulation studies. 
p360 was part of [PBO H2O](http://cires1.colorado.edu/portal/)

The station is in a flat, grassy plain with minimal obstacles or 
changes in topography. Complicated elevation and azimuth angle masks are not required.  


## Take a Quick Look at the Data

First you need to make an SNR file. Ordinarily one can only access L2C data at 
this site using the 1-sec data. To support <code>gnssrefl</code> users, UNAVCO 
has created special RINEX files with L2C SNR data in them at a friendlier sample
rate, 15 sec. Use the *special* archive:

<CODE>rinex2snr p360 2017 290 -archive special</code>

Then run <code>quickLook</code>:

<code>quickLook p360 2017 290</code>

The default return is for L1. This plot confirms our concerns about the quality of the L1 data.
It also suggests the southern quadrants are preferred to other quadrants.

<img src="../_static/p360-qc1.png" width="600">

Now check L2C:

<code>quickLook p360 2017 290 -fr 20</code>

<img src="../_static/qc-p360-l2c.png" width="600">

These reflector height retrievals are far superior to the L1 
data. The southern quadrants give more consistent retrievals than for the 
north. This is confirmed in the QC plot show here:

<img src="../_static/p360-qc-l2c.png" width="600">

## Analyze the Data

First we will set the analysis paramaters. This analysis will use the L2C frequency and 
will use QC metrics derived from the previous plot (for peak to noise ratio and amplitude).  
We don't want to use the northeast quadrant, so will use -azlist2 definition:

<code>gnssir_input p360 -l2c True -peak2noise 3.2 -ampl 8 -azlist2 90 360</code>

We then make SNR files to encompass approximately one water year:

<code>rinex2snr p360 2017 245 -doy_end 365 -archive special</code>

<code>rinex2snr p360 2018 1 -doy_end 145 -archive special</code>

SNR files are stored in $REFL_CODE/$year/snr/p360, where $year = 2017 or 2018.

Then we run <code>gnssir</code> to calculate the reflector heights for 2017/2018. Because the code
only creates results if the SNR file exists, we can use the year_end and doy_end settings.

<code>gnssir p360 2017 1 -year_end 2018 -doy_end 366 </code>

## Derive Snow Accumulation from Reflector Heights

Use the <code>daily_avg</code> utility with a relatively low number of required satellite tracks (12) 
and 0.25 meter median filter to remove large outliers:

<code>daily_avg p360 0.25 12 </code>

Here all RH retrievals are shown:

<img src="../_static/p360-all.png" width="600">

This plot makes it clear that there are data outages at p360, particular in the winter months.
This is due to the way the site was built. Power was provided by solar panels and batteries. When
snow covered the solar panels (see the photograph above), the site would soon lose power when 
the batteries ran down. When the snow on the panels melted, the site would track again.

This next plot shows the number of reflector heights each day. While they are consistent 
in the fall and later spring, there is significant variation in December, January, and February.

<img src="../_static/p360-dailynums.png" width="600">

The variation in retrievals in the winter is due to poor data retrieval in those winter months. 
This next plot shows the number of total observations in the RINEX file each day. You can see the 
correlation between the number of tracks available for the daily average and the number of 
observations in the file. For sites with more reliable power, there will not be 
data outages during the winter.

<img src="../_static/p360-raw.png" width="600">

Finally, the daily average RH for the water year: 

<img src="../_static/p360-dailyavg.png" width="600">

[Sample daily average RH output](p360_dailyRH.txt)

<HR>

As of January 28, 2023, there is a [new snowdepth utility](../pages/README_snowdepth.md).
It requires two inputs, the station name and the (northern hemisphere)
water year:

<code>snowdepth p360 2018</code>

and produces a plain text snowdepth file (the name of the file is sent to the screen) and a png file:

<img src="../_static/p360_snowdepth.png" width="600">


