### Use Case for Lake Taupo, New Zealand

**Station Name:** tgho 

**Location:** Lake Taupo, New Zealand

**Archive:** [Geonet](https://www.geonet.org.nz/)

**DOI:**  	N/A

**Ellipsoidal Coordinates:**

- Latitude: -38.813

- Longitude: 175.996

- Height: -38.813 m

[Station Page at Geonet](https://www.geonet.org.nz/data/network/mark/TGHO)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/TGHO.sta)

[Google Map Link](https://goo.gl/maps/1zmgi6rRHPVPDAfV8)

<img src="https://gnss-reflections.org/static/images/TGHO.jpg" width="600">

## Data Summary

Station tgho is operated by Geonet (GNS) in New Zealand.  It is located 
on a platform in Lake Taupo and currently records GPS (L1 and L2 only) and Glonass.



## Take a Quick Look at the Data

Begin by making an SNR file. Use both GPS and Glonass and set the archive to Geonet:

<code>rinex2snr tgho 2020 300 -orb gnss -archive nz</code>


<code>quickLook tgho 2020 300 -e1 5 -e2 15</code>

<img src="tgho-default.png" width="500">


<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8</code>

<img src="tgho-better.png" width="500">

Now try looking at the periodogram for L2:

<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 2</code>

<img src="tgho-l2.png" width="500"/>

These results are not very compelling, and GPS L2 data will not 
be used in subsequent analysis here.  Next, try the two Glonass frequencies:

<CODE>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 101</code>

<code>quickLook tgho 2020 300 -e1 5 -e2 15 -h1 2 -h2 8 -fr 102</code>

<img src="tgho-glonass-l1.png" width="500"/>

<img src="tgho-glonass-l2.png" width="500"/>



## Analyze the Data

Begin by **make_json_input** to create a json file to set up analysis parameters. 
Set the elevation and reflector heights as in **quickLook**.  An azimuth mask will be used in this analysis, 
but will have to be manually edited in the json file.  The peak noise will also be set in this example.

<code>make_json_input tgho -38.8130   175.9960  385.990 -h1 2 -h2 8 -e1 5 -e2 15 -peak2noise 3.2</code>


Then run **rnx2snr** for six months:

<code>rinex2snr tgho 2020 130 -archive nz -doy_end 319 -orb gnss</code>

The output SNR files are stored in $REFL_CODE/2020/snr/tgho.

Now run **gnssir** for these same dates:

<code>gnssir tgho 2020 130 -doy_end 319 </code>

To look at daily averages, use **daily_avg**. The median filter is set to allow values within 0.25 meters of the 
median, and the minimum number of tracks required to calculate the average is set to 50 tracks.  

<CODE>daily_avg tgho .25 50 </code>

<img src="tgho-numvals.png" width="600">

<img src="tgho-all.png" width="600">

<img src="tgho-rhavg.png" width="600">

Although Taupo is in a volcanic caldera, lake levels are determined by seasonal processes such 
as evaporation, precipitation, input from local drainages, and outflow. The Waikoto 
River is sole river draining the lake, and river flow is regulated by a series of hydroelectric dams.
