### Friday Harbor

**Station Name:** sc02

**Location:** Friday Harbor, Washington, USA 

**Archive:** [UNAVCO](http://www.unavco.org)

**Ellipsoidal Coordinates:**

- Latitude: 48.546

- Longitude: -123.008  

- Height: -15.049 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/SC02)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/SC02.sta)


<p align="center">
<img src="http://gnss-reflections.org/static/images/SC02.jpg" width="500"/>
</P>


### Data Summary

### Take a quick look at the SNR data

Translate the GPS data for January 1 in 2018. First you need to make the SNR file:

<code>rinex2snr sc02 2018 1</code>

Use our utility **quickLook** to look at these data [(For more details on quickLook output)](../../docs/quickLook_desc.md):

<code>quickLook sc02 2018 1 -e1 7</code>

<img src="sc02-day1-2018.png" width="600"/>

This is a bit of a mess really. If there are significant peaks, they are really 
close to the cutoff for the method (at 0.5 meters). Let's compare with about a week later.
First make a SNR file:


### Measure Tides 

Translate the GNSS data for the year of 2018:

<code>rinex2snr sc02 2018 1 -doy_end 365</code>

Then you need to make the list of analysis inputs (stored in json format):

<code>make_json_input sc02 -76.458  -107.782 1011.0 -e1 7 -e2 25 -peak2noise 3.2 -l1 True</code>

[Example json file](sc02.json). It is fine to hand edit the json file to remove the unreliable azimuths if 
you prefer.

Now analyze the data:

<code>gnssir sc02 2018 1 -doy_end 365 -screenstats False</code>

This produces reflector heights for every rising and setting satellite track that meets your 
quality control selections.  In order to estimate snow accumulation, you will want to calculate
the daily average. Using our **daily_avg** utility - and specifying 50 satellite tracks and median filter of 0.25 meters:

<code>daily_avg sc02 0.25 50</code>

<img src="sc02-req50.png" width="600"/>



[Sample daily average RH file for 2018](sc02_dailyRH.txt)
