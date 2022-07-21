**Mbamba Bay on Lake Malawi**

Station name: MBBC

Data archive is [UNAVCO](https://www.unavco.org/data/gps-gnss/data-access-methods/dai1/ps.php?sid=6429&filter_data_availability=&from_date=1980-01-06&to_date=2022-07-20&parent_link=Permanent&pview=original)

[Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/MBBC.sta)
<P>

<P align=center>
<img src=https://www.unavco.org/data/gps-gnss/lib/images/station_images/MBBC.jpg width=500> <img src=mbbc-locale.png>
<P>

**Use the Reflection Zone webapp**

[First Try](http://gnss-reflections.org/rzones?station=mbbc&lat=0.0&lon=0.0&height=0.0&msl=off&RH=20&freq=1&nyquist=0&srate=30&eang=1&azim1=0&azim2=360&system=gps). I initially input a RH value of 20 meters and 
default elevation angles (5-15) to get you started.  
Do the reflection zones hit the surface of the lake? Iterate on both of these until 
your ellipses overlap the lake. Then put in azimuth restrictions.

Please keep in mind, this would not work at all with 30 sec data sampling. This only works because UNAVCO 
was using a 15 second data rate at MBBC. If you want to check out the Nyquist, please click the 
aprpropriate button on the reflection zone page.

**Pick Up Some Data**

<code>rinex2snr mbcc 2021 1 -archive unavco</code>

Note that we do not have to select multi-GNSS as this site is only collecting GPS data.

**Evaluate the Reflection Data**

Based on the reflection app, what kind of RH, azimuth, and elevation angle limits are 
appropriate? 

<code>quickLook mbbc 2021 1 -e1 4 -e2 10 -h1 50 -h2 70 </code>

<img src=mbbc-50-70.png>


I have manually added a red box to show the good azimuths. 
If I further edit the correct azimuths:

<code>quickLook mbbc 2021 1 -e1 4 -e2 10 -h1 50 -h2 70 -azim1 220 -azim2 275</code>

Can you use L2? Yes, but you need to more or less turn off the amplitude restriction. These
values are low because of how the legacy L2 signal is extracted. With this at a low value, the peak 
to noise ratio is used for quality control

<code> quickLook mbbc 2021 1 -e1 4 -e2 10 -h1 50 -h2 70 -azim1 220 -azim2 275 -fr 20  -ampl 1</code>

<img src=mbbc-l2.png>

**Analyze a Fuller Dataset**

Once you have the elevation and azimuth angles set (along with details like the required amplitude,
which we are not using here), you really just need to turn the crank. Run <code>make_json_input</code> using 
the information I discussed earlier 

- azimuth and elevation angle limits 
- RH limits. 
- the NReg to be the same as the RH limits 
- amplitude limits to be small for L2 
- allow L1 and L2 (L2C was either not tracked by these investigators or is not provided online by UNAVCO)

Make SNR files using <code>rinex2snr</code>. 

Compute reflector heights:

<code>gnssir mbbc 2018 1 -year_end 2021 -doy_end 100</code> 

Use <code>daily_avg</code> to create a daily average. Play with the 
inputs (median filter value, number of required RH to compute a reliable average) to make sure 
that you have a high quality results. 

<p align=center>
<img src=mbbc-rh.png>


[Simon Williams and the Permanent Service for Mean Sea Level has analyzed this full dataset](https://www.psmsl.org/data/gnssir/site.php?id=10318)

