## Steenbras Dam, Lower

Station Name: sbas

Latitude: -34.18704704

Longitude: 18.84986166

Ellipsoidal Height(m): 403.342

Network: TRIGNET

Archive: UNAVCO (use the special option)

<img src=https://gnss-reflections.org/static/images/SBAS.jpg width=500>

I am pretty sure that this site is now tracking Glonass, but the files currently available 
from UNAVCO are GPS only. So for now that is the use case we will discuss.

### Reflection Zones 

Use the reflection zone web app to think about which azimuths and elevation angles ot use.
Note the photograph!  **You are not 6 meters from the water.**

### Evaluate the Data

The defaults will only show reflector heights up to 6 meters. We need to be much bigger than that.
And since we know that you can only see water reflections in the northeast quadrant, I am going
to select those azimuths specifically. I will start with elevation angle limits of 5-12 degrees and 
the superior L2C frequency.

<code>quickLook sbas 2020 1 -e1 5 -e2 12 -h1 20 -h2 35 -azim1 0 -azim2 90 </code>

<img src=sbas-quicklook2.png width=600 />

You can see that last azimuth looks a bit lower than the others. If I run it again with 
screenstats set to True, I will get a little more information that will help me figure out how 
far we can go:

<PRE>
SUCCESS for Azimu   8.5 Satellite  1 UTC  5.96 RH  27.490
SUCCESS for Azimu  37.9 Satellite  3 UTC  8.60 RH  27.380
SUCCESS for Azimu  78.4 Satellite  5 UTC 19.64 RH  26.790
SUCCESS for Azimu  66.1 Satellite  6 UTC 16.63 RH  27.360
SUCCESS for Azimu  63.0 Satellite  9 UTC 12.10 RH  27.418
SUCCESS for Azimu  11.1 Satellite 10 UTC  1.25 RH  27.478
SUCCESS for Azimu  52.1 Satellite 12 UTC 20.56 RH  27.530
SUCCESS for Azimu  40.6 Satellite 17 UTC 14.82 RH  27.410
SUCCESS for Azimu   6.4 Satellite 24 UTC 17.65 RH  27.530
SUCCESS for Azimu  24.4 Satellite 25 UTC 21.04 RH  27.400
SUCCESS for Azimu   3.4 Satellite 27 UTC  2.28 RH  27.410
SUCCESS for Azimu  72.7 Satellite 29 UTC  0.40 RH  27.250
SUCCESS for Azimu  63.8 Satellite 31 UTC  4.96 RH  27.320

</PRE>

Looks like satellite 5 at an azimuth of 78.4 degrees is the onproblem, so we 
will further restrict our analysis to 78 degrees in the next section.

### Estimate Lake Level

Make the SNR files:

<code>rinex2snr sbas 2020 1 -doy_end 366 -archive special</code>

Save your analysis strategy:

<code>make_json_input sbas 0 0 0 -e1 5 -e2 12 -h1 15 -h2 35 -peak2noise 3</code>

I am going to edit the json file to restrict azimuths to 0-78 degrees.

Estimate reflector height :

First do a single day:

<code>gnssir sbas 2021 1 -plt T</code>

<img src=sbas-l1.png width=600/>	

<code>gnssir sbas 2021 1 -plt T -fr 20 </code>

<img src=sbas-l2.png width=600 />

Then go ahead and do them all:

<code>gnssir sbas 2021 1 -doy_end 366</code>

Compute a daily average:

<code>daily_avg sbas 0.25 10</code>

Number of available values per day:

<img src=sbas_4.png width=600 />

<img src=sbas_2.png width=600 />

Compare with in situ data:

sbas_use.md




https://www.dws.gov.za/Hydrology/Weekly/ProvinceWeek.aspx?region=WC


https://www.dws.gov.za/Hydrology/Verified/HyData.aspx?Station=G4R001100.00&DataType=Point&StartDT=2020-01-01&EndDT=2020-12-31&SiteType=RES
