### Homework 3  

**Prerequisite:** You need to make sure the software has been properly installed and you have successfully completed the "homework 0" assignment. You should 
also read the [gnssrefl documentation.](gnssrefl.rtfd.io)

**Purpose:** Learn how to measure water level with <code>gnssrefl</code> using GNSS data 


**Station:**
We will be using station **ross**. It is operated by [NRCAN](https://www.nrcan.gc.ca). 
This [map](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/cacs-scca.php?locale=en)
gives you an overview of GNSS stations operated by NRCAN. Use the plus sign on the map 
to look more closely at Lake Superior. Find **ross** and click on it (station M023004). 
If you scroll down, you will see a photo of the monument. 

NRCAN is operating what I would call a "legacy" GNSS instrument. This means it only tracks 
the original GPS signals that were designed in the 1970s. This means none of the 
enhanced GPS signals (L2C and L5) available since 2005 are provided. 
Furthermore, there are no signals from Glonass, Galileo, or Beidou. 
The bottom line is that you will be using only the L1 GPS signal, which leaves you with ~15% of what 
would be available from a modern multi-GNSS unit. The sample rate - 30 seconds - limits what 
kind of reflectometry you can do. For the purposes of this homework, it restricts the RH to values less 
than ~10 meters.

**Azimuth/Elevation Mask**

Next, let's get an idea of what this site looks like from a reflections viewpoint. 
Use the geoid tab on the [gnss-reflections webapp](https://gnss-reflections.org/geoid) to
get an idea of its surroundings. You can enter the station coordinates by hand if you know them, 
but since **ross** is part of a public archive known to geodesists, coordinates have been stored in the webapp.
Just type in **ross** for the station name. Make a note of the station 
latitude, longitude, and ellipsoidal height that is returned by the 
webapp because you will need it later. Although the elevation above sea level of 
the site is ~186 meters, from the photo you know already this is not the value 
we will want to use for our reflections study. We will start with our common 
sense, look at the data, and iterate if necessary.

Use the [reflection zone section of the web app](https://gnss-reflections.org/rzones) to get an idea
of what reflection zones are possible for this site. We cannot use the default sea level reflection 
value, so you need to set a Reflector Height (RH) value. Based on the photograph, try values that
you think are reasonable. You don't want your reflection zones to cross 
a dock or the nearby boats, so you should also rerun it with different azimuth limits. Don't worry about it too much as we will get feedback from the actual GPS data.

Make a note of:

<UL>
<LI>RH
<LI>elevation angle values that give water coverage without interference from docks/boats
<LI>azimuth angle values that cover open water without interference
<LI>the DECIMAL latitude, longitude, and height (from the geoid webapp).
<LI>we can only use L1 GPS data at this site 
<LI>We can't estimate RH larger than 10 meters because of the sampling rate
</UL>

**Using gnssrefl**

Now let's look at the **ross** data. We need to pick up a RINEX file and strip out the 
SNR data.  We use the <code>rinex2snr</code> for this purpose.  Use -h if you want to 
see the options for this module. We will throw caution to the winds and see if the defaults will work. 
The only required inputs are the station name (ross), the year (2020) and day of year (150) 
(note: to convert from year and day of year to year, 
month, day and vice versa, try the modules <code>ydoy</code> and 
<code>ymd</code>). 

By default <code>rinex2snr</code> tries to find the RINEX data for you by looking at a few 
key archives.  However, if you know where the data are, it will be faster to specify it.
In this case they are available from both sopac and nrcan. Try the <code>-archive</code> option.

Once you have successfully created a SNR file, run <code>quickLook</code>. 
You will see two graphical representations of the data. The first is 
periodograms for the four geographic quadrants (northwest, northeast, and so on). 
You are looking for nice clean (and colorful) peaks. Color means they have 
passed Quality Control (QC). Gray lines are satellite tracks that failed QC. The second plot summarizes the 
RH retrievals and how the QC metrics look compared to 
the defaults. In this case the x-axis is azimuth in degrees.

From these plots, how does the correct *RH* value compare with the one you assumed earlier when you 
were trying out the webapp?  How about the azimuths?  Go back to the reflection zone webapp and 
make sure you are happy with your azimuth and elevation angle selections.

Next we need to save our <code>gnssrefl</code> analysis strategy using 
<code>gnssir_input</code>. Your analysis strategy can and should
be improved by setting some parameters on the command line.

*Hints:*

* Check the documentation to see how to set the elevation angles and RH limits on the command line

*  Since we can only use L1 data, you should use the <code>-l1 True</code> flag.

* You will need to estimate the azimuth mask using the `-azlist2` argument

Now run <code>gnssir</code> for the year 2020/doy 150. 
This module is meant for *routine analysis* and thus there are not a lot
of bells and whistles. However, it is good practice to see that something is actually 
created (the screen output will tell you where it is).

**Extra Credit:**

The <code>gnssir</code> output tells you the vertical distance between the GPS antenna and 
the lake for each successful satellite track. That is not 
super exciting; it is a little more interesting to see if it changes over time, which means 
you need to analyze a bit more data. 

* use <code>rinex2snr</code> to make SNR files for the same year, but now do doy 120 through 290. Remember to use <code>-doy_end</code> to
do that in a single command.  And use <code>-weekly True</code> to make fewer files (which will make
everything much faster).  Why did I pick those dates? Mostly to avoid snow (yeap, it snows up there!) 

* run <code>gnssir</code> for those dates.  You do not need the weekly option here - you can just
specify 120 through 290. It will look for every day, but if it doesn't find it, it just looks for the 
next day, etc.

* You can now use the <code>daily_avg</code> to make a daily average for the lake level on each day 
you analyzed.  

**Extra Extra Credit:**

Compare your results with the [lake gauge data.](https://www.isdm-gdsi.gc.ca/isdm-gdsi/twl-mne/inventory-inventaire/sd-ds-eng.asp?no=10220&user=isdm-gdsi&region=CA)
