### Summit Camp, Greenland

Station smm3 is operated by UNAVCO. The data are archived at UNAVCO. 

[You should use my web app to get a sense of what the site looks like. Please note that the app 
will be analyzing data in real-time, so please wait for the answers to "pop" up in the 
left hand side of the page. It takes about 5 seconds](https://gnss-reflections.org/fancy6?example=smm3)
You are provided with a photograph, coordinates (make a note of them), and a google 
Earth map. Save the periodogram so you can look at it more closely.

**Coordinates:**
You can try the [Nevada Reno site](http://geodesy.unr.edu/NGLStationPages/stations/SMM3.sta).
Or use the ones on my web app. They are the same.

**This site has been optimally set up for positions and reflectometry.** This means it tracks modern
GPS signals (L2C and L5) as well as Glonass and Galileo. Unlike some of the earlier reflectometry demonstrations, 
the L1 data from this receiver are great. How can you tell what signals are tracked at this receiver?
Unfortunately I do not know how to find this information at the 
archive of record. 

Start out by trying to reproduce the web app results. The year and day of year are in the 
title of the periodogram plot. As are the elevation angle limits.

* First make the SNR file  

* Use quickLook

Why does this not look like the periodogram results from my web app?? Look closely.

If you previously used the defaults, remake the SNR file using gnss rather than gps orbits.
Make sure that your reflector height limits include the answer. Rerun **quickLook**. 



For running **gnssir**:

Use **make_json_input** but set -allfreq True and -peak2noise 3.5

you need to do some hand-editing to the json file. For example, set the allowed azimuths:

* 70-180
* 180-270

These are the "quiet" areas. To keep the reflection zones quite large - I only use data from 5-15 degree
elevation angles. This will make the amplitudes larger  - also because the surface is
relatively smooth, so I would set the required amplitude to 15, though in all honestly it 
could be set even higher. [Sample json](smm3.json)


