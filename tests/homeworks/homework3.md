### Homework 3  

*Dates:* This homework is to be completed **before** the short course given on October 21. You need to make
sure the software has been properly installed and you have passed the "homework 0" assignment. You should 
also read the [gnssrefl documentation].

*Purpose:* Learn how to measure water level with gnssrefl using data from GNSS station ross

**ross** is operated by NRCAN. This [map](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/cacs-scca.php?locale=en)
gives you an overview of GNSS stations operated by NRCAN. Use the plus sign on the map to look more closely at Lake Superior.
Find ROSS and click on it (station M023004). If you scroll down, you will see a photo of the monument. 


Next, let's get an idea of what this site looks like from a reflections 
viewpoint. Use the geoid tab on the [webapp](https://gnss-reflections.org/geoid) to
get an idea of its surroundings. You can enter the station coordinates by hand if you want, but since ROSS is part of a 
NRCAN, coordinates from the sites are available on the site. Just type in **ross** for the station name. 
Make a note of the station latitude, longitude, and ellipsoidal height.
Although the elevation above sea level of the site is ~186 meters, from the photo you looked at this is not the value 
we will want to use for our reflections study. We will start with our common sense, look at the data, and iterate if necessary.

Use the [reflection zone section of the web app](https://gnss-reflections.org/rzones). Set a 
Reflector Height (RH) value and see what comes back. You don't want your reflection zones to cross 
a dock or the nearby boats, so rerun it with azimuth limits.  

Make a note of:

<UL>
<LI>RH
<LI>elevation mask 
<LI>azimuth mask
<LI>the DECIMAL latitude, longitude, and height (from the geoid webapp).
</UL>

Now let's look at the data. Type <code>rinex2snr -h</code> if you want to see the options for translating SNR data.
We will throw caution to the winds and see if the defaults will work. 

* Make a SNR file for station **ross** in year 2020 and day of year 150. 

* Run **quickLook** for the same date. You will see two graphical representations of the data. The first is 
periodograms for the four quadrants (northwest, northeast, and so on). You are looking for nice clean (and 
colorful) peaks. Color means they have passed Quality Control (QC). The second plot summarizes the RH retrievals
and how the QC metrics look compared to the defaults.  

From these plots, how does the correct *RH* value compare with the one you assumed earlier?  How about the 
azimuths?  Go back to the reflection zone webapp and make sure you are happy with the azimuth and elevation angle
zones.

* We need to save our analysis strategy using **make_json_input**.

<code>make_json_input ross LAT  LONG  HEIGHT </code> 

are the minimum required inputs. Make sure you read the <code>gnssrefl</code> documentation
(or <code>make_json_input -h</code>) to see how to set the elevation angles and RH 
restrictions (you might as well restrict RH above 2 meters 
because those lower RH values are clutter and not related to the water).
Since NRCAN is operating a verry ery old piece of equipment at this site, only very 

You will need to hand edit the azimuths in the json file created by <code>make_json_input</code>

*Run **gnssir** for the same date. This module is meant for *routine analysis.* So nothing pops up to the screen.




