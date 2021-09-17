
## Homework 1

**Due date:** This homework is to be completed **before** the short course given on October 21. You need to make
sure the software has been properly installed and you have successfully completed the "homework 0" assignment.

**Purpose:** Learn how to set your azimuth and elevation angle mask  

The purpose of this homework is to get you to better understand how to properly run gnssir. 
Each station is different and will have a unique set of parameters because of its location, height near the 
surface being measured, possible objects nearby, etc...
The <a href=https://gnss-reflections.org target="_blank">gnss-reflections.org</a> webapp has 
some tools to help you determine these parameters.
Let su start with the station **at01** in St. Michael, Alaska. Use the geoid tab and enter the station name.
You can see the general location of the antenna with respect to the coast. You 
will also note that it is at ~12 meters above sea level. Make a note of the latitude, longitude, and ellipsoidal height.

Now we can use the ReflZones tab of the webapp to try out different masks. Change azimuth and elevation 
For this site you can use the sea level option. 

Now make an SNR file for at01 using <code>rinex2snr</code>. Use year 2020 and day of year 109 and the unavco archive.
We can use the <code>quicklook</code> function to test the site mask you chose.





Looking at the plots we just generated, what went wrong? Nearly every single retrieval is set as bad (i.e. it is gray rather than blue).

It's important to remember that when we run quicklook like did above, that we didn't change any 
of the defaults. Lets take a look and see what the defaults are:

Remember that the site is about 12 meters above sea level and the default, as we can see, 
restricts the reflector height region to < 6 meters (h1=0.5 and h2=6). Try again using a reflector 
height region that includes the water surface and also use better elevation angles (e1 and e2).


Now you see strong retrievals in the Lomb Scargle periodograms with the reflector height of about 12 meters, as expected.
You also see good retrievals at azimuths sweeping from true north to about 220 degrees. Was this close to your orginial best azimuth range estimate? 



