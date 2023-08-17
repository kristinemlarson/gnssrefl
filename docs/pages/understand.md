# Understanding


## Overview

**gnssrefl** is an open source/python version of my GNSS interferometric reflectometry (GNSS-IR) code. 

*If you would like to try out reflectometry without installing the code*

I recommend you use [the GNSS-IR web app](https://gnss-reflections.org/api). It 
can show you representative results in less than 10 seconds. There are also some 
[examples](https://gnss-reflections.org/overview).

## Goals

The goal of the gnssrefl python repository is to help you compute (and evaluate) GNSS-based
reflectometry parameters using geodetic data. This method is often
called GNSS-IR, or GNSS Interferometric Reflectometry. There are three main modules:

* [**rinex2snr**](rinex2snr.md) translates RINEX files into SNR files needed for analysis.


* [**quickLook**](quickLook.md) gives you a quick (visual) assessment of aSNR  file without dealing
with the details associated with **gnssir**. It is not meant to be used for routine analysis.
It also helps you pick an appropriate azimuth mask and quality control settings.

* [**gnssir**](gnssir.md) computes reflector heights (RH) from SNR files.

There are also various [utilities](quick_recall.md) you might find to be useful.
If you are unsure about why various restrictions are being applied, it is really useful 
to read [Roesler and Larson (2018)](https://link.springer.com/article/10.1007/s10291-018-0744-8) 
or similar. You can also watch some background videos 
on GNSS-IR at [youtube](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

## Philosophy

In geodesy, you don't really need to know much about what you are doing to 
calculate a reasonably precise position from GPS data. That's just the way it is.
(Note: that is also thanks to the hard work of the geodesists that wrote the 
computer codes). For GPS/GNSS reflections, you need to know a little bit more - like what are you
trying to do? Are you trying to measure water levels? Then you need to know where the water
is! (with respect to your antenna, i.e. which azimuths are good and which are bad). 
Another application of this code is to measure snow accumulation. If you 
have a bunch of obstructions near your antenna, 
you are responsible for knowing not to use that region. If your antenna is 10 meters 
above the reflection area, and the software default only computes answers up to 6 meters,
the code will not tell you anything useful. It is up to you to know what is best for the site and 
modify the inputs accordingly. 
I encourage you to get to know your site. If it belongs to you, look at 
photographs. If you can't find photographs, use Google Earth.  You can also try using
my [google maps web app interface](https://gnss-reflections.org/geoid?station=smm3).

## Reflected Signal Geometry

To summarize, direct (blue) and reflected (red) GNSS signals interfere and create
an interference pattern that can be observed in GNSS Signal to Noise Ratio (SNR) data as a satellite rises or sets. 
The frequency of this interference pattern is directly related to the height of the GNSS antenna phase
center above the reflecting surface, or reflector height RH (purple). *The primary goal of this software 
is to measure RH.* This parameter is directly related to changes in snow height and water levels below
a GNSS antenna. This is why GNSS-IR can be used as a snow sensor and tide gauge. GNSS-IR can also be 
used to measure soil moisture, but the code to estimate soil moisture is not as strongly related to RH as
snow and water. We will be posting the code you need to measure soil moisture later in the year.

![](https://gnss-reflections.org/static/images/overview.png)

This code is meant to be used with Signal to Noise Ratio (SNR) data. This is a SNR sample for a site in the 
the northern hemisphere (Colorado) and a single GPS satellite. The SNR data 
are plotted with respect to time - however,
we have also highlighted in red the data where elevation angles are less than 25 degrees. These are the data used in 
GNSS Interferometric Reflectometry GNSS-IR. You can also see that there is an overall smooth polynomial signature
in the SNR data. This represents the dual effects of the satellite power transmission level and the antenna 
gain pattern. We aren't interested in that so we will be removing it with a low order polynomial (and 
we will convert to linear units on y-axis). 
After the direct signal polynomial is removed, we will concentrate on the *rising* 
and *setting* satellite arcs. These are shown in red.


<img src="../_static/p041-snr.png" width="600">

For a more dynamic example, look at these SNR data from [Kachemak Bay](../_static/pbay-snr.png)


Once the direct signal is removed (and units changed), you will have a dataset as shown below.
The x-axis is now in sine(elevation angle) instead of time, as this is the easiest way to 
analyze the spectral characteristics of the data. Below the SNR data is the periodogram associated 
with it. This periodogram is what allows us to estimate the reflector height of the antenna.

<img src="../_static/for_the_web.png" width="600">


In a nutshell, that is what this code does - it tries to find the rising and setting arcs 
for all GNSS satellites in a datafile, computes periodograms to find the dominant frequencies 
which can be related to reflector heights, and ultimately defines environmental characteristics from them.


There are three big issues :

1. You need to make sure that dominant frequency is meaningful (**Quality Control**).  

2. You need to make sure that the reflected signals are actually coming 
from where you want them (**Reflection Zones**)

3. Your receiver must be collecting data at sufficient rate so that your GNSS-IR results 
are not violating the Nyquist frequency (**Nyquist**).



## Quality Control 

It is easy to compute a periodogram and pick the maximum value so as to find the reflector height. It is 
more difficult to determine whether it is one you should trust.

* is the peak larger than a user-defined value  (amplitude of the dominant peak in your periodogram)

* is the peak divided by a "noise" metric larger than a user-defined value. (peak2noise).

* is the data arc sufficiently "long"

The amplitude and peak2noise ratio are influenced by choices you make, i.e. the elevation angle limits 
and the noise region used to compute peak2 noise.  And they are also 
influenced by the kind of experiment you do and receiver you use.  
Some examples follow:


Here we show a SNR series - outlining two different elevation angle regions in colors.

<img src="../_static/qc1.png" width="600">

We should expect that the periodograms will look different for these two regions and they are.
The peak amplitudes are larger when you only use the lower elevation angle data.  But the periodograms
are wider (why?).

<img src="../_static/qc2.png" width="600">


Peak2noise depends on the noise region. In <code>quickLook</code> it uses the same RH limits for noise as for computing
the periodogram. You can eaisly see that if you said you wanted all H values below 20 meters, the noise region
is much much larger, which means the peak value dividied by the noise values will be much much bigger.


<img src="../_static/qc3.png" width="600">

This is an example where two different stations with different surfaces are shown. The peak amplitudes of the 
periodograms are different.  This simply means that the ice has 
a different dielectric constant than soil.  You can verify this using the Nievinski simulator.

<img src="../_static/qc4.png" width="600">

Here is an example where the same station is used in both periodograms - but the surface itself changed. 

<img src="../_static/qc6.png" width="600">


In addition to amplitude and peak2noise, the code uses a quality control 
parameter called **ediff.** to test whether the data arc is sufficiently "long"
in an elevation angle sense. ediff has units of degrees.
If you set your desired elevation angle limits to 5 and 20 degrees, and ediff was 2, which is 
the default, then the code will require all arcs to track from at least 7 degrees and go up to 18 degrees. If you had a 
very short elevation angle range, i.e. 5-10 degrees, you might want to make that a little stricter,
minimum of 6 and at least go up to 9 degrees, so an ediff of 1. If you don't want to enforce this, just set it to something big.
But you can't turn off all quality control.  Since the amplitude can be influenced by the kind of 
receiver you are using, if you aren't sure what a good value would be, you can set that to zero.
And you can use quickLook to get an idea of what it should be.  

One more warning: if you tell the code that you want to use elevation angles of 5 to 25 degrees and it 
turns out that your receiver was using an elevation mask of 10 degrees, you will almost certainly
end up with no useful results. Why?  Because the best you will do is have a min elevation angle of 10 degrees,
and the code will expect them to start at 7 degrees (i.e. 5 + 2). Some cryosphere community members use
7 degree masks on their receivers for no reason that I can understand - so that situation would
also end up with a lot of arcs thrown out.

Another way of thinking about how long an arc is measured in time units.  The parameter 
is called delTmax in the code and is defined in minutes. The default is very long - 75 minutes - 
as this code is meant to be useable for soil moisture, snow, and tides. This will get you into
trouble if you are measuring tides and the tide rates of change are large. In those cases, you might
wish to reduce delTmax. 
See [Grauerort](https://gnssrefl.readthedocs.io/en/latest/use_cases/use_tggo.html) for an example of this problem. 


Even though we analyze the data as a function of sine of elevation angle, each satellite arc
is associated with a specific time period. The code keeps track of that and reports it in the final answers.
Each track is associated with an azimuth. In the initial versions of the code this was the average azimuth
for all the data in your track.  From version 1.4.5 and on, it is the azimuth of the lowest elevation angle
in your arc.


## Reflection Zones

What do these satellite reflection zones look like? Below are 
photographs and [reflection zone maps](https://gnss-reflections.org/rzones) for two standard GNSS-IR sites, 
one in the northern hemisphere and one in the southern hemisphere.

**Mitchell, Queensland, Australia**

<img src=https://gnss-reflections.org/static/images/MCHL.jpg width=300>

<img src="../_static/mchl_google.jpg" width=300>

**Portales, New Mexico, USA**

<img src=https://gnss-reflections.org/static/images/P038.jpg width="300">

<img src="../_static/p038_google.jpg" width=300>

Each one of the yellow/blue/red/green/cyan clusters represents the reflection zone
for a single rising or setting GPS satellite arc. The colors represent different elevation angles - 
so yellow is lowest (5 degrees), blue (10 degrees) and so on. The missing satellite signals in the north
(for Portales New Mexico) and south (for Mitchell, Australia) are the result of the GPS satellite 
inclination angle and the station latitudes. The length of the ellipses depends on the height of the 
antenna above the surface - so a height of 2 meters gives an ellipse that is smaller than one 
that is 10 meters. In this case we used 2 meters for both sites - and these are pretty 
simple GNSS-IR sites. The surfaces below the GPS antennas are fairly smooth soil and that 
will generate coherent reflections. In general, you can use all azimuths at these sites.  

Now let's look at a more complex case, station <code>ross</code> on Lake Superior. Here the goal 
is to measure water level. The map image (panel A) makes it clear
that unlike Mitchell and Portales, we cannot use all azimuths to measure the lake. To understand our reflection 
zones, we need to know the approximate lake level. That is a bit tricky to know, but the 
photograph (panel B) suggests it is more than the 2 meters we used at Portales - 
but not too tall. We will try 4 meters and then check later to make sure that was a good assumption.  

<img src="../_static/ross-google.jpg" width=300> 

A. Google Map of station ROSS 

<img src=https://gnss-reflections.org/static/images/ROSS.jpg width=300> 

B. Photograph of station ROSS

<img src="../_static/ross-first.jpg" width=300>

C. Reflection zones for GPS satellites at elevation 
angles of 5-25 degrees for a reflector height of 4 meters.

<img src="../_static/ross-second.jpg" width=300> 

D. Reflection zones for GPS satellites at 
elevation angles of 5-15 degrees for a reflector height of 4 meters.  

Again using the reflection zone web app, we can plot up the appropriate reflection zones for various options.
Since <code>ross</code> has been around a long time, [http://gnss-reflections.org](https://gnss-reflections.org) has its coordinates in a 
database. You can just plug in <code>ross</code> for the station name and leave 
latitude/longitude/height blank. You *do* need to plug in a 
RH of 4 since mean sea level would not be an appropriate 
reflector height value for this 
case. 

Start out with an azimuth range of 90 to 180 degrees.
Using 5-25 degree elevation angles (panel C) looks like it won't 
quite work - and going all the way to 180 degrees
in azimuth also looks it will be problematic. Panel D shows a 
smaller elevation angle range (5-15) and cuts 
off azimuths at 160. These choices appear to be better than those from Panel C.  
It is also worth noting that the GPS antenna has been attached to a pier - 
and *boats dock at piers*. You might very well see outliers at this site when a boat is docked at the pier.

Note: we now have a [refl_zones tool](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.refl_zones_cl.html) 
in the gnssrefl package. 

Once you have the code set up, it is important that 
you check the quality of data. This will also 
allow you to check on your assumptions, such as the 
appropriate azimuth and elevation angle 
mask and reflector height range. This is the main reason 
<code>quickLook</code> was developed. 

## Nyquist

Please see the [Roesler and Larson paper](https://link.springer.com/article/10.1007/s10291-018-0744-8) for a 
discussion of Nyquist. I have ported the Matlab code provided in that paper 
to [gnssrefl](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.nyquist_cl.html) 

