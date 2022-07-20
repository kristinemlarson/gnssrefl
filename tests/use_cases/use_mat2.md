**Lake Mathews**

Station name: MAT2

Data archive is [UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/MAT2)

[Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/MCHN.sta)
<P>
<a href=http://gnss-reflections.org/rzones?station=mat2&lat=0.0&lon=0.0&height=0.0&msl=off&RH=20&freq=1&nyquist=0&srate=30&eang=4&azim1=140&azim2=220&system=gps target="_blank">Reflection zone</a>

<P>
<img src=south_mat2.jpg width=500>
<P>

Photograph from UNAVCO.


This site has a lot of history. It is 1-Hz and multi-GNSS since ~2016. 
You do not need 1-Hz for this site - I have chosen to decimate it to 5 seconds,
as in:

<code>rinex2snr mat2 2022 193 -doy_end 199 -orb gnss -rate high -dec 5 -archive unavco</code>

Note that you can use the rapid GFZ orbits after mid 2021. And before 2016, there are no multi-GNSS 
observations, so you can use the default (gps-only) option.


Only the low elevation data can be used (look at the reflection zone link above and note the RH). 
Here I use <code>quickLook</code> with elevation angles 4-8 degrees and RH 8-35 meters:

<code>quickLook mat2 2022 175 -e1 4 -e2 8 -h1 7 -h2 35</code>


<img src=try1_mat2.png>

I know from the google map image that the lake is to the south. And there are retreievals there,
but they are being set to bad because the amplitude of the reflection is so small.  You can override that:

<code>quickLook mat2 2022 175 -e1 4 -e2 8 -h1 7 -h2 35 -ampl 0

<img src=try2_mat2.png>

I have manually added a red box to show the good azimuths. If I further edit the correct azimuths, 
you see good strong returns:

<code>quickLook mat2 2022 175 -e1 4 -e2 8 -h1 7 -h2 35 -ampl 0 -azim1 220 -azim2 275</code>:

<img src=lsp-mat2.png>

Once you have the eleation and azimuth angles set (along with details like the required amplitude,
which we are not using here), you really just turn the crank. Run <code>make_json_input</code> using 
the information I discussed here. Then:

<code>gnssir mat2 2017 1 -year_end 2021 -doy_end 365</code> 

would analyze all the data from 2017-2021.

<img src=mat2-avg.png>

Because there were only useful GPS L1 data in the earlier dataset, I only used it for the entire time series.
For lake monitoring using the current receiver I would use all GPS, Galileo, and Glonass signals.

In situ data:

[Monthly Data from the California Department of Water Resources](https://cdec.water.ca.gov/dynamicapp/QueryWY?Stations=MHW&SensorNums=15&End=2022-05-20&span=20+years)

[CSV file](LAKE_MATHEWS_MHW.csv)

