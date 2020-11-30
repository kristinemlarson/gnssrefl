### Summit Camp, Greenland

Station smm3 is operated by UNAVCO. The data are archived at UNAVCO. 

If you are interested in interpreting the results for this site, you should 
read [this paper](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf), which was published open option.
smm3 was one of the sites highlighted in this paper.

[You can use my webapp to get a sense of what the results for this site looks like. Please note that the app 
will be analyzing data in real-time, so please wait for the answers to "pop" up in the 
left hand side of the page. It takes 5-10 seconds](https://gnss-reflections.org/fancy6?example=smm3).
It also has a google map and photograph.

**Coordinates:**
You can try the [Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/SMM3.sta).
Or use the ones on my web app. They are the same.

Position time series for smm3 can easily be retrieved from [Nevada Reno](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/SMM3.tenv3).
Note that there is an antenna height blunder in the very early data for the site. It is trivial to find and remove.

**This site has been optimally set up for positions and reflectometry.** This means there is no elevation 
angle applied at the receiver and that it tracks modern GPS signals (L2C and L5) as 
well as Glonass. I am not sure if it tracks Galileo - but you can inquire with Dave Mencin at UNAVCO. 
Unlike some of the earlier reflectometry demonstrations, the 
L1 data from this receiver are great. How can you tell what signals are tracked at this receiver?
Unfortunately I do not know how to find this information at the archive of record. Although 1 second
data are available at smm3, they are not needed for daily average reflectometry described here.

Start out by trying to reproduce the web app results. The year and day of year are in the 
title of the periodogram plot. As are the elevation angle limits.

- First make the SNR file *rinex2snr smm3 2020 106*

- Look at the results using default parameters: *quickLook smm3 2020 106*

<img src="smm3-default.png" width="500" />

Why does this not look like the periodogram results from my web app? Look closely.
smm3 is ~16 meters above the ice sheet - and this far exceeds the code default of 6 meters.
You need to reset the allowed reflector heights. Modify your call to 
**quickLook**, using RH mask of 8-20 meters.  Also change the elevation angle mask to 5-15.

- *quickLook smm3 2020 106 -h1 8 -h2 20 -e1 5 -e2 15*

<img src="smm3-sensible.png" width="500" />

Notice that instead of strong peaks center at a single RH value, 
there is quite a bit of spread in the northwest quadrant. That is because the reflection 
area is more complex (and maybe also reflecting off things that are not snow). 

### Steps for Longer Analysis: 

Use **make_json_input** but set -allfreq True and -peak2noise 3.5

I had to do some hand-editing to the json file. For example, I set the allowed azimuths:

- 70-180
- 180-270

These azimuths are the "quiet" areas for making scientific measurements Summit Camp. To keep the reflection 
zones quite large - I only opted to only use data from 5-15 degree elevation angles. This will make the amplitudes of the peaks 
in the periodogram larger, so I also set the required amplitude to 15. I also removed the Galileo signals from
the json since they are not in the RINEX files I am using. [Sample json](smm3.json)


Make daily SNR files:

- *rinex2snr smm3 2018 180 -orb gnss -doy_end 365*

Now analyze daily SNR files:

- *gnssir smm3 2018 180 -doy_end 365 -screenstats False*

Compute daily average of these results:

- *daily_avg smm3 0.25 50 -txtfile smm3_RH.txt*

<img src="smm3_RH.png" width="500" />

Notice that the [daily average RH file](smm3_RH.txt) shows well over 150 measurements per day are being 
used in the average.  So you could rerun the code to use a bigger value than 50.  Here the observations are so
robust it won't make a difference.

- *daily_avg smm3 0.25 100 -txtfile smm3_RH.txt*

