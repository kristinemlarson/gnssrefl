# St Michael Bay

[Warning](warning.md)

**at01 is the only tide gauge in this region of Alaska.** 
  
<p align="center">
<img src="https://gnss-reflections.org/static/images/AT01.jpg" width="500">
</p>

## metadata

**Station Name:**  at01

**Location:**  St Michael, Alaska

**Archive:**  [UNAVCO](http://www.unavco.org)

**Ellipsoidal Coordinates:**

- Latitude:  63.4840

- Longitude: -162.0064

- Height: 21.7 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/AT01)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/AT01.sta)

[Google Map Link](https://goo.gl/maps/uWyoNFf4DRjYLmfUA)

### Data Summary

at01 observes all constellation signals and high-rate data are available. There is good visibility over a large azimuthal 
region. The monument is about a meter taller than normal geodetic monuments to 
improve visibility of the sea surface.  From the [geoid app](http://gnss-reflections.org/geoid?station=at01&lat=0.0&lon=0.0&height=0.0) you can see 
the general location of the antenna with respect to the coast. You will also note that it is at ~12 meters above sea level.

<p align=center>
<img src=../_static/geoid-at01.jpg width=400>
</p>

Use the gnss-reflections.org webapp to set a [possible mask.](http://gnss-reflections.org/rzones?station=at01&lat=0.0&lon=0.0&height=0.0&msl=msl&RH=2&eang=3&azim1=0&azim2=240) In this example we used the option for elevation angles between 5 and 12 degrees. 

### Take a Quick Look at the Data

First examine the spectral characteristics of 
the SNR data. [(For details on quickLook output.)](../pages/quickLook.md). Make a SNR file:

<code>rinex2snr at01 2020 109 -archive unavco</code>

This will generate a SNR file at a sampling rate of 15 seconds. One second data are available if you would like to use them (-rate high).

If you use the default settings with <code>quickLook</code> you will mistakenly think it is not a useful site. Nearly
every single retrieval is set as bad (i.e. it is gray rather than blue):

<code>quickLook  at01 2020 109</code>

<img src=../_static/at01_default_qc.png width=600>		

Remember that the site is 12 meters above sea level and the default restricts the reflector height
region to < 8 meters. Try again using a reflector height region that includes the water 
surface (h1 = 8 and h2 = 15) and better elevation angles 5 and 13 degrees:

<code> quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15</code>

<img src=../_static/at01_day109.png width=600>		

Now you see good retrievals at azimuths sweeping from true north to about 220 degrees.  
You will also see strong retrievals in the Lomb Scargle periodograms:

<img src=../_static/at01_lsp_109.png width=600>

This site has modern GPS signals, Galileo signal, and Glonass signals. Here are 
some sample results for L2C:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 20</code>


<img src=../_static/at01_l2c.png width=600>

Glonass:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 101</code>

<img src=../_static/at01_glonass.png width=600>

and Galileo:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 205</code>

<img src=../_static/at01_galileo.png width=600>

### Analyze the Data

Next we analyze data for two months in the fall of 2020. First make the SNR files:

<code>rinex2snr at01 2020 230 -archive unavco -doy_end 290</code>

Now set up the analysis instructions (assume database receiver coordinates are correct)
using our new utility (extending h2 a bit):

<code>gnssir_input at01 -h1 8 -h2 17 -e1 5 -e2 13 -ampl 4 -frlist 1 20 5 101 102 201 205 206 207 -azlist2 20 220</code>

Next estimate reflector height (RH) for the two month time period 

<code>gnssir at01 2020 230 -doy_end 290 </code>

We have written some code to help you look at these subdaily files - it is a work in progress, but you can 
certainly give it a try. (**Note:** These figures were generated with an older version of the code and should be updated.)
Concatenates the RH files for this period:

<code>subdaily at01 2020 -doy1 230 -doy2 290 </code>

You can see that there are a very large number of RH retrievals per day:

<img src=../_static/at01_Subnvals.png  width=600>


This preliminary version of the code removes outliers and makes an effort 
to compute the RH dot correction if <code>rhdot</code> is set to true. It  uses a cubic 
spline to fit the RH data which allows a first order estimate for the 
surface rate of change. That, along with geometrical information as to the elevation angle rate 
of change, is used to make the RH dot 
correction [(for more information)](https://www.kristinelarson.net/wp-content/uploads/2015/10/LarsonIEEE_2013.pdf). 


<img src=../_static/at01_rhdot3.png width=600>

This term is **very important** for sites with 
large tidal ranges, but is of less importance at sites like at01. Nevertheless, 
you can see here that it does help a bit:

<img src=../_static/at01_rhdot2.png width=600>

<PRE>
RMS no RHdot correction (m)  0.084
RMS w/ RHdot correction (m)  0.071
</PRE>

**Please note: the corrected RH value is not written to column 3. Please look into the file.**

Finally, we attempt to remove the inter-frequency biases and fit a new spline, yielding a RMS agreement of about 5 cm with
respect to the spline:

<img src=../_static/at01_rhdot4.png width=600>

**Again: the corrected RH values are written to new columns in the output files, not to column 3. Please look into the file.**

I would like to include Simon Williams' RH retrieval/tidal estimation code 
in this package. Simon has been kind enough to make the Matlab 
code [open source.](https://git.noc.ac.uk/noc-tide-gauges/noc-tgqc/-/blob/bab322f9677bca47ecd8e1c7da099d5925c00b4d/NOCtidefit.m) 
If someone is willing to convert it to python, that would be fabulous.
 
