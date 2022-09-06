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
Note the photograph!  **You are not 6 meters from the water.** You will not be able to test
your reflector height value until you look at some real data. But you can get an idea of which
RH values put you over the water.

### Evaluate the Data

We know that the reservoir will only be in the northeast quadrant, so I am going 
to select those azimuths specifically. I will start with elevation angle limits of 5-12 degrees and 
the superior L2C frequency.

<code>quickLook sbas 2020 1 -e1 5 -e2 12 -h1 20 -h2 35 -azim1 0 -azim2 90 -fr 20</code>

<img src=sbas-quicklook2.png width=600 />

You can see that the last point looks a little bit lower than the others. If I run it again with 
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

Looks like satellite 5 at an azimuth of 78.4 degrees is the problem, so we 
will further restrict our analysis to 78 degrees in the next section.

### Estimate Lake Level

Make the SNR files:

<code>rinex2snr sbas 2020 1 -doy_end 366 -archive special</code>

Save your analysis strategy:

<code>make_json_input sbas 0 0 0 -e1 5 -e2 12 -h1 15 -h2 35 -peak2noise 3</code>

Hand edit the json file to restrict azimuths to 0-78 degrees.

The next step is to estimate reflector heights. First do a single day using the plt option.
I've added an arrow to show you what happens if you violate the Nyquist - double peaks!
Luckily this is not prevalent in this dataset thanks to the help of TRIGNET 
using a 15 second sample rate in the files.

<code>gnssir sbas 2021 1 -plt T</code>

<img src=sbas_gnssir_l1.png width=600/>	

Notice that the L2C frequency - which has a longer wavelength - does not have a double peak.
And that is what we should expect.

<code>gnssir sbas 2021 1 -plt T -fr 20 </code>

<img src=sbas_gnssir_l2c.png width=600 />

Go ahead and estimate reflector height for all days:

<code>gnssir sbas 2021 1 -doy_end 366</code>

Compute a daily average. Since we only have reflections in one geographic quadrant, and are 
only using GPS signals, we should not require as many points as we have done in other examples:

<code>daily_avg sbas 0.25 10</code>

Number of available values per day:

<img src=sbas_4.png width=600 />

Daily averaged reflector height results 

<img src=sbas_2.png width=600 />

Numerical values are saved in a file. The location of the file is printed to the screen.

### Compare with in situ data:

[Current state of the reservoir](https://www.dws.gov.za/Hydrology/Weekly/ProvinceWeek.aspx?region=WC)

Simon Williams found this web app that will [provide 2020 data for a comparison](https://www.dws.gov.za/Hydrology/Verified/HyData.aspx?Station=G4R001100.00&DataType=Point&StartDT=2020-01-01&EndDT=2020-12-31&SiteType=RES)
