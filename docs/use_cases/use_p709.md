# Lake Yellowstone, USA

[Warning](warning.md)

**Use Case Updated December 10, 2022**

## metadata

**Station Name:** p709

<P align=center>
<img src=https://www.unavco.org/data/gps-gnss/lib/images/station_images/P709.jpg width=500>
<P>
Why does this photograph suggest that GNSS-IR should not work?
<p>

**Archive:** unavco

**Ellipsoidal Coordinates:**

- Latitude: 44.3917953 

- Longitude: -110.286006 

- Height: 2379.7 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/P709)

[Station Page at UNR](http://geodesy.unr.edu/NGLStationPages/stations/P709.sta)

**Examine the Site**

[Reflection Zone App](https://gnss-reflections.org/rzones?station=p709&lat=0.0&lon=0.0&height=0.0&msl=off&RH=30&freq=1&nyquist=0&srate=30&eang=6&azim1=0&azim2=90&system=gps)

Note that I have restricted azimuths here and used a reflector height of 30 meters.

**Background Information**

This site was installed for tectonic purposes. The view of the lake from P709 is severely obstructed and it is relatively
far from the shore. However, if you have access to the highrate (1-Hz) datastream **and** use low elevation data, you can easily
detect the daily average lake level. Make sure that you use the reflection zone information when you make your json file.

**Translate Data**

<code>rinex2snr p709 2022 1 -dec 5 -archive unavco -rate high -orb gnss</code>

**quickLook**

<code>quickLook p709 2022 1 -e1 5 -e2 10 -h1 20 -h2 40</code>

**Estimate Reflector Height**

Set your analysis strategy using the <code>gnssir_input</code>. 

<code>rinex2snr p709 2021 183 -dec 5 -archive unavco -rate high -orb gnss</code>

<code>gnssir p709 2021 1 -doy_end 180 </code>

Use <code>daily_avg </code> to calculate a daily reflector height. Various statistics also
come to the screen. Here is the RH series:

<img src=../_static/p709_RH.png width=500>

I am *only* showing the data for the new multi-GNSS receiver. If you look at earlier data, you 
are restricted to L1.

**In Situ Data**

<img src=../_static/p709-comparison-data.png width=500>

[USGS station page](https://waterdata.usgs.gov/nwis/uv?06186500)


[last year of data, USGS](https://waterdata.usgs.gov/monitoring-location/06186500/?agency_cd=USGS#parameterCode=00065&period=P365D)


Living in the US - you get to see feet instead of meters!

**Something to Think About**

Note that the amplitudes (of the RH periodograms) are also a bit interesting.

<img src=../_static/p709_RHamp.png>

Why do you think the amplitudes vary like this? What changes about Lake Yellowstone in the winter?



