###  Utqiagvik, Alaska

**Station Name:** utqi00usa

**Location:** Utqiagvik (Barrow), Alaska, USA

**Archives:** BKG, CDDIS

**[Nevada Reno](http://geodesy.unr.edu/NGLStationPages/stations/UTQI.sta)** 

**[IGS station log](https://files.igs.org/pub/station/log/utqi_20211028.log)**

<p align=center>
<img src=http://gnss-reflections.org/static/images/UTQI.jpg width=500/>
</p>

UTQI was installed by and is supported by <a href=https://www.gfz-potsdam.de/en/section/space-geodetic-techniques/overview>GFZ</a>.
It is located at the <a href=https://gml.noaa.gov/obop/brw/>NOAA environmental facility</a>. It is also an <a href=https://igs.net>IGS site</a>.


Use the <a href=https://gnss-reflections.org/rzones target="_blank">web app to get an idea of the reflection zones at this site.</a>
Remember that the default is the elevation of the site above sea level. That might be ok - but it might not. Check 
with the real data. What azimuths should you use?

### Look at the data

First make a SNR file using the BKG archive:

<code>rinex2snr utqi00usa 2022 150 -orb rapid -archive bkg</code>

This will return a multi-GNSS SNR file, but only 30 second data. This restricts 
the possible reflector heights, but is good enough for a start.
From the photograph, it looks that it is very possible the GNSS antenna is more than 6 meters
above the reflecting surface (the default in <code>quickLook</code>). And I will further restrict elevation 
angles to 5-15 so as to avoid the building.  I will set the reflection zone on the command line:

<code>quickLook utqi 2022 150 -h1 2 -h2 12 -e1 5 -e2 15</code>


<img src=utqi-quicklook1.png width=600</>

I've outlined the "sweet spot" for reflections on the summary figure:

<img src=utqi-quicklook.png width=600</>

The main take home message: the *a priori* reflector height is a bit more than 6 meters. You
can use that value within the reflection zone app if you want to look at the reflection zones again.

### Make SNR files for multiple years

The RINEX files are available from both CDDIS and BKG. Here we selected CDDIS and multi-GNSS orbits.
Another orbit option is rapid (also from GFZ). These files only become available in 2021, and I want to 
start the time series in 2020, so I opted to use gnss as the orbit source.

<code>rinex2snr utqi00usa 2020 1 -orb gnss -archive cddis -year_end 2022 -doy_end 243 </code>

This won't take too long since the data files are relatively small.

### Estimate Reflector Height

Set your analysis strategy:

<code>make_json_input utqi 0 0 0 -h1 2 -h2 12 -e1 5 -e2 15 -allfreq T </code>

There don't appear to be Beidou data at this site, so you should hand-edit those frequencies out of the json file. 
You should also set the final azimuth region. This was my [starter json file](utqi.json)
In retrospect, I should have limited the azimuths a little more.

<code>gnssir utqi 2020 1 -year_end 2022 -doy_end 243</code>


###  Assess the results

Use the <code>daily_avg</code> to consolidate your results and estimate snow accumulation. I am using 
a median value of 50 cm and a minimum of 50 retrievals. You can certainly play with those parameters.

<code>daily_avg utqi 0.5 50</code>

This summary shows you how much each constellation is contributing to the daily average (GPS, Galileo, Glonass).

<img src=utqi_f4.png width=600/>

All the retrievals are shown here:

<img src=utqi-f1.png width=600/>

Finally, the daily average from 2020 to the present:

<img src=utqi-f2.png width=600/>

The values are written to a file - the location of the file is written to the screen.
How do you turn this into snow accumulation? Set the fall values (before the first snow) as your 
zero point and then simply subtract. Why are RH values changing during the summer? This is related to 
permafrost active layer changes. [Lin Liu](https://www.cuhk.edu.hk/sci/essc/people/liu.html)'s group at the 
University of Hong Kong has pioneered the use 
of GNSS-IR to study this effect. There are a few papers on [my website](https://kristinelarson.net/publications) from this early work; more papers
can be found on his website.

Note:

I found cases where the archived files are missing SNR data entirely. This will show up on the screen 
as failure to translate the RINEX 3 file into RINEX 2. 


Kristine M. Larson September 4, 2022




