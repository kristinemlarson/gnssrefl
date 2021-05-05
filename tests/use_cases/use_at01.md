### Use Case for Bering Sea 
  
**Station Name:**  at01

**Location:**  St Michael, Alaska

**Archive:**  [UNAVCO](http://www.unavco.org)

**Ellipsoidal Coordinates:**

- Latitude:  63.4840

- Longitude: -162.0064

- Height:       21.7 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/AT01)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/AT01.sta)

[Google Map Link](https://goo.gl/maps/uWyoNFf4DRjYLmfUA)

<center>
<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/AT01.jpg" width="500">
</center>

**at01 is the only tide gauge in this region of Alaska.**

### Data Summary

at01 was installed for reflectometry and thus has excellent tracking characteristics. It observes
all constellation signals and high-rate data are available. There is good visibility over a large 
azimuthal region. The monument is about a meter taller to improve visibility.

From the [geoid app](http://gnss-reflections.org/geoid?station=at01&lat=0.0&lon=0.0&height=0.0) you can 
see the general location of the antenna with respect to the coast. You will also note that it is at 
~12 meters above sea level.


Use the gnss-reflections.org webapp to set a [possible Mask](http://gnss-reflections.org/rzones?station=at01&lat=0.0&lon=0.0&height=0.0&msl=msl&RH=2&eang=3&azim1=0&azim2=240). In this example we used elevation angle 5-12 degrees. The goal is to have the ellipses on the water with no intersection of 
the land.

### Take a Quick Look at the Data

We will use **quickLook** to examine the spectral characteristics of the SNR data. 
[(For details on quickLook output.)](../../docs/quickLook_desc.md):

First we need to make a SNR file:

<code>rinex2snr at01 2020 109 -archive unavco</code>

This will generate a SNR file at a sampling rate of 15 seconds. One second data are available if you would 
like to use them (-rate high).

If you use the default settings with **quickLook** you will mistakenly think it is not a useful site. Nearly
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

This site has modern GPS signals, Galileo signal, and Glonass signals. 
Here are some sample results:

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 20</code>

<img src=at01_l2c.png width=600>

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 101</code>

<img src=at01_glonass.png width=600>

<code>quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15 -fr 205</code>

<img src=at01_galileo.png width=600>

### Analyze the Data

Next we analyze data for days 100-131 for the year 2020. First make the SNR files:

<code>rinex2snr at01 2020 100 -archive unavco -doy_end 130</code>

Now set up the analysis instructions:

<code>make_json_input make_json_input at01 63.484 -162.006 21.565 -h1 8 -h2 15 -e1 5 -e2 13 -allfreq True </code>

You will need to hand-edit the file to restrict the azimuths per our QC output. I also removed the Beidou signals (frequencies > 300) 
because they are not in the RINEX 2.11 file.  

Then estimate RH for the 31 day period:

<code>gnssir at01 2020 100 -doy_end 130</code>





