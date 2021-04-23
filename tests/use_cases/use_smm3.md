### Summit Camp, Greenland


**Station Name:** smm3

**Location:** Dye2 

**Archive:** UNAVCO 

**Ellipsoidal Coordinates:**

Latitude: 72.573 degrees

Longitude: -38.470 degrees

Height: 3252.453 meters

## Data Summary

You can use my webapp to get a sense of what the results for this site looks like. Please note that the app 
will be analyzing data in real-time, so please wait for the answers to "pop" up in the 
left hand side of the page. It takes about 10 seconds](https://gnss-reflections.org/api?example=smm3).
It also has a google map and photograph.

Position time series for smm3 can easily be retrieved from [Nevada Reno](http://geodesy.unr.edu/gps_timeseries/tenv3/IGS14/SMM3.tenv3).
Note that there is an antenna height blunder in the very early data for the site. It is straight forward to find and remove.

This site has been optimally set up for positions and reflectometry. This means there is no elevation 
mask applied at the receiver and that it tracks modern GPS signals (L2C and L5) as 
well as Glonass. 

<img src="https://gnss-reflections.org/static/files/SMM3.jpg" width=400>

## A Quick Look at the Data

First make a multi-GNSS SNR file:

<code>rinex2snr smm3 2020 106 -orb gnss </code>


Then run **quickLook**:

<code>quickLook smm3 2020 106</code>

<img src="smm3-default.png" width="600" />

Why does this not look like the periodogram results from my web app? Look closely.
On the web app smm3 is ~14 meters above the ice sheet - and this far exceeds the 
defaults of 6 meters used in quickLook. You need to reset the allowed reflector heights. 
Modify your call to **quickLook**, using RH mask of 8-20 meters. Also change the elevation angle mask to 5-15.

<code>quickLook smm3 2020 106 -h1 8 -h2 20 -e1 5 -e2 15</code>

<img src="smm3-sensible.png" width="600" />

Notice that instead of strong peaks center at a single RH value, 
there is quite a bit of spread in the northwest and northeast quadrants. That is because the reflection 
area is more complex (and maybe also reflecting off things that are not snow). 

### Steps for Longer Analysis: 

Use **make_json_input** to set your analysis inputs. Instead of the defaults, set the special height and 
elevation angles, allfreq to True, peak to noise ratio to 3.5, and minimum amplitude to 15:

<code>make_json_input smm3 72.573 -38.470  3252.453 -peak2noise 3.5 -allfreq True  -ampl 15 -e1 5 -e2 15 -h1 8 -h2 20</code>

The azimuth mask had to be hand-edited. These azimuths are the "quiet" areas for making scientific 
measurements at Summit Camp. To keep the reflection 
zones quite large - I only opted to only use data from 5-15 degree elevation angles. This will make the amplitudes of the peaks 
in the periodogram larger. I also removed the Galileo signals from the json since they are not 
in the RINEX files I am using. [Sample json](smm3.json)

Then make SNR files:

<code>rinex2snr smm3 2018 180 -orb gnss -doy_end 365</code>

Run **gnssir**:

<code>gnssir smm3 2018 180 -doy_end 365 </code>

Compute daily average of these results:

<code>daily_avg smm3 0.25 50 </code>

<img src="smm3_RH.png" width="600" />

Notice that the [daily average RH file](smm3_RH.txt) shows well over 150 measurements per day are being 
used in the average. So you could rerun the code to use a bigger value than 50. Here the observations are so
robust it won't make a difference.

If you are interested in interpreting the results for this site, you should 
read [this paper](https://tc.copernicus.org/articles/14/1985/2020/tc-14-1985-2020.pdf), which was published open option.
smm3 was one of the sites highlighted in this paper.
