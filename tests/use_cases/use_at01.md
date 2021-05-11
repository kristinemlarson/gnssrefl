### Bering Sea 
  
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

<p align="center">
<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/AT01.jpg" width="500">
</p>


### Data Summary

**at01 is the only tide gauge in this region of Alaska.** 

at01 observes all constellation signals and high-rate data are available. There is good visibility over a large 
azimuthal region. The monument is about a meter taller to improve visibility of the sea surface.

From the [geoid app](http://gnss-reflections.org/geoid?station=at01&lat=0.0&lon=0.0&height=0.0) you can 
see the general location of the antenna with respect to the coast. You will also note that it is at 
~12 meters above sea level.


Use the gnss-reflections.org webapp to set a [possible mask.](http://gnss-reflections.org/rzones?station=at01&lat=0.0&lon=0.0&height=0.0&msl=msl&RH=2&eang=3&azim1=0&azim2=240) In this example we used the option for elevation angles between 5 and 12 degrees. The goal is to have the ellipses on the water and not the land.

### Take a Quick Look at the Data

First examine the spectral characteristics of the SNR data. [(For details on quickLook output.)](../../docs/quickLook_desc.md). Make a SNR file:

<code>rinex2snr at01 2020 109 -archive unavco</code>

This will generate a SNR file at a sampling rate of 15 seconds. One second data are available if you would like to use them (-rate high).

If you use the default settings with <code>quickLook</code> you will mistakenly think it is not a useful site. Nearly
every single retrieval is set as bad (i.e. it is gray rather than blue):

<img src=at01_default_qc.png width=600>		

Remember that the site is 12 meters above sea level and the default restricts the reflector height
region to < 6 meters. Try again using a reflector height region that includes the water 
surface (h1 = 8 and h2 = 15) and better elevation angles 5 and 13 degrees:

<code> quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15</code>

<img src=at01_day109.png width=600>		

Now you see good retrievals at azimuths sweeping from true north to about 220 degrees.  
You will also see strong retrievals in the Lomb Scargle periodograms:

<img src=at01_lsp_109.png width=600>

This site has modern GPS signals, Galileo signal, and Glonass signals. Here are some sample results for L2C:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 20</code>


<img src=at01_l2c.png width=600>

Glonass:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 101</code>

<img src=at01_glonass.png width=600>

and Galileo:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 205</code>

<img src=at01_galileo.png width=600>

### Analyze the Data

Next we analyze data for days 100-131 for the year 2020. First make the SNR files:

<code>rinex2snr at01 2020 100 -archive unavco -doy_end 130</code>

Now set up the analysis instructions:

<code>make_json_input at01 63.484 -162.006 21.565 -h1 8 -h2 15 -e1 5 -e2 13 -allfreq True </code>

You will need to hand-edit the file to restrict the azimuths per our QC output. I also removed the Beidou signals (frequencies > 300) 
because they are not in the RINEX 2.11 file. [Sample json file.](at01.json)

Then estimate reflector height (RH) for the one month period:

<code>gnssir at01 2020 100 -doy_end 130</code>

We have written some code to help you look at these subdaily files - it is not complete as yet,
but you can certainly give it a try. We have set an outlier criteria of ~3 sigma. At this site (without
removing biases between frequencies), this will be ~0.12 m, so 0.36 m.

<code>subdaily at01 2020 -doy1 100 -doy2 130 -outlier 0.36</code>

The code [concatenates the daily RH files](at01_subdaily_rh.txt.gz) for this period and also makes this plot:

<img src=at01_raw.png width=600>

It tries to do some simple outlier removal and will make an effort to compute the RH dot correction.
The default for outliers is 0.5 meters, but you can set that value at the command line.
*The RH dot correction computed here is using a test version of our code.* It uses a cubic 
spline to fit the RH data which allows a 
first order estimate for RH dot. That, along with geometrical information as to the 
elevation angle rate of change, is used to make the RH dot correction. This term
is **very important** for sites with large tidal ranges, but is of minimal importance at sites like at01.

<img src=at01_edits.png width=600>

The code will also print out a list of outliers (outliers.txt) so that you can assess whether you 
might want to change your azimuth mask.


