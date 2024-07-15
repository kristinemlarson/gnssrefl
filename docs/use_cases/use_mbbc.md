# Lake Malawi

## metadata

**Station name:** MBBC

Updated December 10, 2022

<P align=center>
<img src=../_static/mbbc-three.jpg>
<P>

**Latitude:** -11.2736 degrees

**Longitude:** 34.8002 degrees

**Ellipsoidal Ht:** 522 meters

**Data archive:** [UNAVCO](https://www.unavco.org/data/gps-gnss/data-access-methods/dai1/ps.php?sid=6429&filter_data_availability=&from_date=1980-01-06&to_date=2022-07-20&parent_link=Permanent&pview=original)

[**Nevada Reno**](http://geodesy.unr.edu/NGLStationPages/stations/MBBC.sta)
<P>

**Getting Started**

The first thing you need to do is find out if it is at all possible that you will be able to measure
reflections from Lake Malawi. The place to start is the reflection zone web app. 
[I initially input a RH value of 20 meters and default elevation angles to get started.](http://gnss-reflections.org/rzones?station=mbbc&lat=0.0&lon=0.0&height=0.0&msl=off&RH=20&freq=1&nyquist=0&srate=30&eang=1&azim1=0&azim2=360&system=gps). 
Do the reflection zones hit the surface of the lake using those inputs? Iterate on 
both of the RH and elevation angles until your ellipses overlap the lake. Then try different azimuth restrictions.
Please keep in mind, this would not work at all with 30 sec data sampling. This only works because the PIs 
were using a 15 second data rate at MBBC. If you want to check out the Nyquist for this site (i.e. what sampling 
rate is required to see Lake Malawi), please click the appropriate button on the reflection zone page.

**Testing the data from Lake Malawi**

First download and translate RINEX data:

<code>rinex2snr mbcc 2021 1 -archive unavco</code>

Note that we do not have to select multi-GNSS orbits as this site is only collecting GPS data.

Based on the reflection app, what kind of RH, azimuth, and elevation angle limits are appropriate? 

<code>quickLook mbbc 2021 1 -e1 4 -e2 10 -h1 50 -h2 70 </code>

<img src=../_static/mbbc-50-70.png>

I have manually added a red box to show the good azimuths. Can you use the L2 data at this site? Let's see:

<code> quickLook mbbc 2021 1 -e1 4 -e2 10 -h1 50 -h2 70 -azim1 220 -azim2 275 -fr 2</code>

<img src=../_static/mbbc-l2.png>
 
So you can see there are good RH results at the same azimuths as with L1, but they 
are marked as bad (gray circles) because the amplitudes are so small. So you need to more or 
less turn off the amplitude restriction for L2. You are allowed to have different amplitude constraints 
on L1 and L2. Note: the L2 amplitudes are smaller because the receiver lacks access to the P code.

**Analyze a Multi-year Dataset**

Step 1: Run <code>gnssir_input</code> using the information I discussed earlier 

- azimuth angle limits  **Try out -azlist2 220  275**

- elevation angle limits  **Use -e1 and -e2**

- RH limits. 

- amplitude limits to be small for L2 

- allow L1 and L2 **Try out -frlist 1 2**

Note: I usually tell people to use L2C instead of L2. This information is 
not available in this dataset - either because the PIs did not track L2C or because the data are not 
provided by UNAVCO in the standard RINEX files.

Step 2: Make SNR files using <code>rinex2snr</code>. 

Step 3: Compute reflector heights

<code>gnssir mbbc 2018 1 -year_end 2021 -doy_end 100</code> 

Step 4: Use <code>daily_avg</code> to create a daily average RH. Play with 
the inputs (median filter value, number of required RH to compute a reliable average) to make sure 
that you have a high quality results. 

<p align=center>
<img src=../_static/mbbc-rh.png>
<p>

[Simon Williams and the Permanent Service for Mean Sea Level have analyzed this full dataset](https://www.psmsl.org/data/gnssir/site.php?id=10318)

