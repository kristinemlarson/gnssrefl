
## Homework 1

**Due date:** This homework is to be completed **before** the short course given on October 21. You need to make
sure the software has been properly installed and you have successfully completed the "homework 0" assignment.

**Purpose:** Learn how to set your azimuth and elevation angle mask  

The purpose of this homework is to get you to better understand how to properly run gnssir. 
Each station is different and will have a unique set of parameters because of its location, height near the 
surface being measured, possible objects nearby, etc...
The <code>gnssir</code> code has some tools to help you determine these parameters.
Lets first start with looking at the station **at01** in St. Michael, Alaska.

<img src="../../data/geoid-at01.png" width="400">

Run the cell below to view the geoid functionality in the gnss-reflections webapp. Using this, we will get an idea of its surroundings. You can enter the station coordinates by hand if you know them, but since at01 is part of a public archive known to geodesists, coordinates have been stored in the webapp. Just type in at01 for the station name.


```python
%%html
<iframe src="https://gnss-reflections.org/geoid" width="1000" height="600"></iframe>
```

You can see the general location of the antenna with respect to the coast. You 
will also note that it is at ~12 meters above sea level.

Now we can use the reflection zone functionality of the gnss-reflections webapp to set 
a possible mask. First, type in at01 and don't change any of the values.
For this site we would want to be measuring water levels. We can 
see very clearly that 0 to 360 degress would capture part of the land for the station. Go 
back and change the angles until we are only covering area that contains water. What azimuth angles did you choose?


Now make an SNR file for at01 using <code>rinex2snr</code>. Use year 2020 and day of year 109 and the unavco archive.
Now we can use the <code>quicklook</code> function to give you a visual assessment of the 
reflection characteristics of your GNSS site. 


* the top plot is the color coded RH retrieval color: blue for good and gray for bad. What you 
are looking for are RH that are consistent with your site. In this case the antenna is about 12 meters above sea level.

* the middle plot is the "peak to noise ratio" which is defined as peak spectral amplitude divided by the average 
spectral value over a defined noise region. In quickLook this will be the same region you used 
for your RH estimate. This value is surface dependent. If you happen to check the peak 
to noise ratio on a day at peak vegetation growth, you might be fooled into thinking the site did 
not work. Similarly, a windy day on a lake will produce lower peak to noise ratios than a day without 
wind. I generally use 3.5 for snow, 3.2 for lakes, and 2.7 for tides.

* the bottom plot is the spectral amplitude for the RH peak. This will depend -again - on the surface type. 
Different surfaces (water, ice, snow, bare soil) reflect signals differently. It also reflects how smooth 
the surface is and which elevation angle limits were used.

Looking at the plots we just generated, what went wrong? Nearly every single retrieval is set as bad (i.e. it is gray rather than blue).

It's important to remember that when we run quicklook like did above, that we didn't change any 
of the defaults. Lets take a look and see what the defaults are:

Remember that the site is about 12 meters above sea level and the default, as we can see, 
restricts the reflector height region to < 6 meters (h1=0.5 and h2=6). Try again using a reflector 
height region that includes the water surface and also use better elevation angles (e1 and e2).


Now you see strong retrievals in the Lomb Scargle periodograms with the reflector height of about 12 meters, as expected.
You also see good retrievals at azimuths sweeping from true north to about 220 degrees. Was this close to your orginial best azimuth range estimate? 



