# Vlissingen

## vlsi

**Unfortunately I had to turn off the web app in late 2023. When I get a chance I will update this document.**

**Updated June 4, 2023 to use gnssir_input**

<p align="center">
<img src=../_static/vlis.jpg width=600</img>
</P>

**Station Name:** vlis  or VLIS00NLD

**Location:** Vlissingen, the Netherlands

**Archives:** BKG, BEV

[Station Page at NGL](http://geodesy.unr.edu/NGLStationPages/stations/VLIS.sta)

### Take a Quick Look at the Site Reflection Zones

The [EUREF Page](https://epncb.oma.be/_networkdata/siteinfo4onestation.php?station=VLIS00NLD) page has a lot of information about the GNSS site here. It is currently tracking multiple GNSS constellations.  
If you are going to try and measure water levels, it is important to look at the reflection zones 
around the site. This will allow you to set a good mask.
[Type VLIS into the station name and first use the defaults at this web site.](http://gnss-reflections.org/rzones)
Try different azimuth constraints. I recommend only using 5-15 degree elevation angles.
Note that the height of the antenna above sea level is provided by the web app and returned on the right hand side.

Another thing you should try to do is get an idea of what the tidal range will be. At VLIS, there is a 
colocated [tide gauge](http://www.ioc-sealevelmonitoring.org/station.php?code=vlis). There are other ways
you can get the tidal range without a colocated tide gauge sensor - e.g. there are various web sites that will at least give you high and low tide predictions.

GNSS-IR has a Nyquist.  While I won't discuss it here (see [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8) for details), it is an issue at VLIS. The easiest VLIS data to find are the 30 second data
deposited by geodesists at various global archives. This sample rate would be fine for 
an antenna 6 meters above the water e.g. But at VLIS - with the known tidal range - we are really too close to the L1 Nyquist to use 30 second data. You can use the 30 second data for L2/L5, but
you are basically throwing away half your data if ignore L1. 

So what *can* you do? The good news is that this site reliably reports high-rate GNSS data. 
The bad news is that the sample rate is 1 second. And you do not need 1 second data for this site; 15 
second data is fine. If you retain the 1 second data, all the <code>gnssrefl</code> programs will be pretty slow.

To get you started so that you don't have to download and manipulate 1 sec GNSS files (which come 
in 96 separate files!), I have made some smaller 15 second RINEX files for you. They are 
available in this [tar file.](https://morefunwithgps.com/public_html/vlis_2022.tar)
After downloading, <code>tar -xvf vlis_tar.2022</code>. There should be 14 gzipped files in RINEX 2.11 format.
Instead of using <code>gnssrefl</code> I am going to show you how to use the web app. Open a browser and 
type in <code>gnss-reflections.org</code>. You will be using the RINEX upload option which is in the center.
Load one of the RINEX files and press the submit button.  Depending on your internet connection, your
answer should pop up in about 10 seconds. The writing in magenta are comments I have added to 
point out various things.

<p align=center>
<img src=../_static/vlis-default.jpg width=800/>
</p>

So what's going on here? (If you have never used this site before, I recommend you give a 
look to the [frequently asked questions page](http://gnss-reflections.org/overview).)
First, the most dominant reflections (which are colored) are coming
from the west. But this is where we should expect them. There is a large slab of concrete there and it 
looks like it is about 6.5 meters below the antenna. The area pointing to the ocean is showing up in gray in 
the periodograms (and also gray in the azimuth plot below) as unsuccesful.
That is because the defaults we used in our analysis 
strategy (RH ranging from 0.5 to 8 meters) **does not include the right answer**.
And that is why we can't see the tides. 

Second attempt. Make the following changes:

- the RH range (5 to 18 meters) to include the 
right answer (10 meters) and the tidal range (plus/minus two meters). 
- Use elevation angles of 5 to 15 because those looked best when we ran the reflection zone app.
- Change the minimum amplitude to 2. 
- Use the L1L2CL5 frequency option. (default was L1 only)
- set the azimuth range to 70 to 180 

Make sure your RINEX file is loaded and hit submit.

<p align=center>
<img src=../_static/vlis-better-choices.jpg width=800/>
</p>

Now you can see a broad swath of "successful" retrievals in the azimuth range you chose. The RH 
changes in the top plot (azimuth on the x-axis) are the tides. The reflector height 
answers are written out to a text file. Use the link called **Numerical Results**.
You will see L1, L2C, and L5 retrievals all together. The most retrievals are generally from
L1 - because every GPS satellite has L1. The second most are L2C (at least 24 satellites) and 
the fewest are L5 (I am not sure how many L5 transmitting satellites there are, but it is fewer than L2C).

I also have [a bash script](https://github.com/kristinemlarson/gnssIR_api) that will allow you to 
more automatically query the API. 

If you are using the github or pypi install of <code>gnssrefl</code> and 
have Python 3.9 or the [docker image](../pages/docker_cl_instructions.md) installed, you can 
do this on your local machine. The advantage of doing it on a local machine is mostly that you can use multi-GNSS 
signals. The web app is GPS only. For applications with a daily average, such as snow accumulation, 
GPS can be enough. But for tides you generally want as many measurements as 
possible, and that means multi-GNSS. The other
advantage of the using the <code>gnssrefl</code> package is that you can more easily use higher-rate data.
The web app strictly controls the maximum RH you can estimate and it also limits how large your RINEX 
file can be. <code>gnssrefl</code> also provides links to many more data archives.

### Make SNR files

To make your own 15 second multi-GNSS VLIS files with <code>rinex2snr</code> you need to :

- station vlis00nld (the longer station name will tell the code to find RINEX 3 instead of RINEX 2.11)
- rate high
- dec 15
- archive bkg
- orb gnss

### Take a Quick Look at the Data

Begin by making SNR files:

<code>rinex2snr vlis00nld 2020 171 -doy_end 184 -rate high -dec 15 -orb gnss -archive bkg-euref</code>

Then use <code>quickLook</code> to make sure your strategy is a good one, where you should try 
using different frequencies and the RH, elevation angle, and azimuth settings.

<code>quickLook vlis 2020 171</code>

This is the strategy I used:

<code>gnssir_input vlis -h1 5 -h2 15 -e1 5 -e2 20 -peak2noise 3 -ampl 1 -frlist 1 20 5 101 102 201 205 207 -azlist2 70 180 </code>

Now run <code>gnssir</code> for these same dates. This computes RH for each rising and setting satellite arc:

<code>gnssir vlis 2022 171 -doy_end 184 </code>

To put those results all together:

<code>subdaily vlis 2022</code>

Reports how many satellites were used in each constellation:

<img src=../_static/vlis_3.png width=600>

How the water levels look as a function of azimuth, constellation, and amplitude:

<img src=../_static/vlis_2.png width=800>

Time series with large outliers removed.

<img src=../_static/vlis-1.png width=600>
 
In the next section, it will compute and try to remove the RHdot correction:

<img src=../_static/vlis_rhdot3.png width=600>

This compares with and without RHdot correction:

<img src=../_static/vlis_rhdot2.png width=600>

**If you wish to access these new RH values, do not use column 3! The corrected values have 
been written as a new column.**

Then we remove an inter-frequency bias and refit a spline:

<img src=../_static/vlis_rhdot4.png width=600>

The RMS with respect to the spline fit starts over 0.325 m, improves to 0.276 m with RHdot,
and finally 0.253 m with an IF bias removed. **If you wish to access these new 
RH values, do not use column 3! The corrected values have been written as a new column.**

The precisions calculated from the spline fit for this site are *very poor* - particularly for L1. 
But this is not really precision - it is how well your RH agree with a spline. To really assess
this site you shold compare with a traditional tide gauge. You can try using our 
utility <code>download_tides</code>. The tide gauge network is ioc and the 
name of the tide gauge is ... vlis! If you say <code>-plt T</code> it makes a crude
plot for you.

