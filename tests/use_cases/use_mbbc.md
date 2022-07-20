**Mbamba Bay on Lake Malawi**

Station name: MBBC

Data archive is [UNAVCO](https://www.unavco.org/data/gps-gnss/data-access-methods/dai1/ps.php?sid=6429&filter_data_availability=&from_date=1980-01-06&to_date=2022-07-20&parent_link=Permanent&pview=original)

[Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/MBBC.sta)
<P>

<P align=center>
<img src=https://www.unavco.org/data/gps-gnss/lib/images/station_images/MBBC.jpg width=500>
<BR>
Photo credit: UNAVCO.
<P>

**Use the Reflection Zone webapp
<a href=http://gnss-reflections.org/rzones?station=mbbc&lat=0.0&lon=0.0&height=0.0&msl=off&RH=20&freq=1&nyquist=0&srate=30&eang=1&azim1=0&azim2=360&system=gps target="_blank">Reflection zones</a>

I have initially input a RH of 20 meters and default elevation angles (5-15) to get you started.  
Do the reflection zones hit the surface of the lake? Iterate on both of these until 
your ellipses overlap the lake. Then put in azimuth restrictions.

Please keep in mind, this would not work at all with 30 sec data sampling. This only works because UNAVCO 
was using a 15 second data rate at MBBC. If you want to check out the Nyquist, please click the 
aprpropriate button on the reflection zone page.

**Pick Up Some Data**

<code>rinex2snr mbcc 2020 1 -archive unavco</code>

Note that we do not have to select multi-GNSS as this site is only collecting GPS data.

**Evaluate the Reflection Data**

Based on the reflection app, what kind of RH, azimuth, and elevation angle limits are 
appropriate?


<code>quickLook mmbc 2021 1 -e1 4 -e2 10 -h1 0 -h2 70</code>



<img src=try1_mat2.png>

*How did I know to use a RH region of 7 to 35 meters?* I did not know this initially. I first tried a limit of 20 meters, 
analyzed multiple years of data and realized that during the drought of 2015 the lake retrievals disappeared (i.e. 
the RH was greater than 20 meters). I re-analyzed the data using the larger limit. 
Once you have *translated* the files, it really doesn't take much cpu time to re-analyze the data.

*What does this image tell us?* I know from google maps that the lake is to the south. And there 
are retrievals to the south, but they are being set to bad because the amplitude of the 
reflection is so small. You can override that:

<code>quickLook mat2 2022 175 -e1 4 -e2 8 -h1 7 -h2 35 -ampl 0</code>

<img src=try2_mat2.png>

If the amplitude limit is set to zero, the code will rely on the peak of the Lomb Scargle 
retrieval relative to the noise (peak2noise) for quality control.

I have manually added a red box to show the good azimuths. If I further edit the correct azimuths, 
you see good strong returns in the peridograms:

<code>quickLook mat2 2022 175 -e1 4 -e2 8 -h1 7 -h2 35 -ampl 0 -azim1 220 -azim2 275</code>:

<img src=lsp-mat2.png>

**Analyze a Fuller Dataset**

Once you have the elevation and azimuth angles set (along with details like the required amplitude,
which we are not using here), you really just need to turn the crank. Run <code>make_json_input</code> using 
the information I discussed earlier (i.e. set azimuth and elevation angles limits, RH limits. Set the NReg to be
the same as the RH limits). 

Make SNR files using <code>rinex2snr</code>. Then compute reflector heights:

<code>gnssir mbbc 2019 1 -year_end 2021 -doy_end 365</code> 

This command would analyze all the data from 2017-2021. Use <code>daily_avg</code> to create a daily average.
Play with the inputs (median filter value, number of required RH to compute a reliable average) to make sure 
that you have a high quality results. My plot goes back to 2008 because I downloaded more RINEX data:

<img src=mbbc-avg.png>

Because there were only useful GPS L1 data in the earlier dataset, I only used it for the entire time series.
In general you should use all the good frequenices that are available to you.

[Simon Williams and the Permanent Service for Mean Sea Level has analyzed this full dataset](https://www.psmsl.org/data/gnssir/site.php?id=10318)

