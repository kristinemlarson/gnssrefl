### Lake Superior

**Background:** Station mchn is operated by NRCAN. The data are archived at SOPAC. Don't tell Fox News, but 
this site is in Canada.

Unfortunately only L1 data should be used at this site. Encourage the station operators to 
track L2C, L5 (and Galileo, Glonass, and Beidou !)

[You should use my web app to get a sense of what the site looks like. Please note that the app 
will be analyzing data in real-time, so please wait for the answers to "pop" up in the 
left hand side of the page. It takes about 5 seconds](https://gnss-reflections.org/fancy6?example=mchn)
The webapp provides you with a photograph, coordinates (make a note of them), 
a google Earth map. Save the periodogram so you can look at it more closely.

**Coordinates:** You can try the [Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/MCHN.sta).
Or use the ones on my web app. They are the same.


**Picking a mask:**
From the periodogram and google Earth map you should be able to come up with a pretty good 
azimuth mask.  Elevation angle might be a bit trickier, but in this case, go ahead and 
use what I did, which is in the title of the periodogram plot.

Reproduce the web app results:

*rinex2snr mchn 2019 205 -archive scripps*

*quickLook mchn 2019 205*

<img src="mchn-default.png" width="500">

Why does this not look like the results from my web app?? Look closely. Make some changes
at the commandline for quickLook.


<img src="mchn-better.png" width="500">

Once you figure out what you need to do, go ahead and analyze the data from 2013.

*rinex2snr mchn 2013 1 -archive sopac -doy_end 365*

make a json file. You will need to hand-edit it to only use L1 and to set the azimuth region.
You will notice that I have a pretty restricted azimuth region.  Although you can get
good reflections beyond 180 degrees, tehre is clearly something funny in the water there
(from google Earth), and if you look at the photograph, it is apparent that there is something 
there that is not water. So I am going with the safer region.



