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

<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/AT01.jpg" width="500">

### Data Summary

at01 was installed for reflectometry and thus has excellent tracking characteristics. It observes
all constellation signals and high-rate data are available. There is good visibility over a large 
azimuthal region.

From the [geoid app](http://gnss-reflections.org/geoid?station=at01&lat=0.0&lon=0.0&height=0.0) you can 
see the general location of the antenna with respect to the coast. You will also note that it is at 
~12 meters above sea level.

### Take a Quick Look at the Data

First make a SNR file:

<code>rinex2snr at01 2020 109 -archive unavco</code>

This will generate a SNR file at a sampling rate of 15 seconds. One second data are available if you would 
like to use them (set -rate high).

If you use the default settings with **quickLook** you will mistakenly think it is not a useful site:

<img src=at01_default_qc.png width=600>		

Remember that the site is 12 meters above sea level and the default restricts the reflector height
region to < 6 meters.  Try again using elevation angles 5 and 13 degrees:

<code> quickLook at01 2020 109 -e1 5 -e2 13 -h1 8 -h2 15</code>

<img src=at01_day109.png width=600>		

You will also see strong retrievals in the Lomb Scargle periodograms:

<img src=at01_lsp_109.png width=600>


### Analyze the Data

We will look at 31 days from April 2020. First make the SNR files:

<code>rinex2snr at01 2020 100 -archive unavco -doy_end 130</code>

Now set up the analysis instructions:

<code>make_json_input</code>

Then estimate RH:

<code>gnssir at01 2020 100 -doy_end 130</code>





