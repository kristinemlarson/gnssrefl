### Phoenix, Antarctica

<P align=center>
<img src="https://gnss-reflections.org/static/images/PHNX.jpg" width="500">
</p>

**Station Name:**  phnx

**Location:**  Phoenix, Antarctica

**Archive:**  [UNAVCO](http://www.unavco.org)

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/phnx)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/PHNX.sta)

[Webapp example using this site](https://gnss-reflections.org/api?example=phnx&ftype=txt)

### Experiment

phnx was installed at the same time as a [dedicated snow measurement experiment](https://essd.copernicus.org/articles/13/5803/2021/) called
the Antarctic Precipitation System. That experiment is now over and their instruments were removed in December 2019.
We can see from this figure 
from [their paper](https://essd.copernicus.org/articles/13/5803/2021/) that the other instruments 
around (and above) the GPS antenna would obstruct GPS reflections in some sense:  

<P align=center>
<img src=https://essd.copernicus.org/articles/13/5803/2021/essd-13-5803-2021-f02-web.png width="500">
</P>

However, we will take this as an opportunity to see if we can see how the 
clutter impacts the GNSS-IR results. The paper says the Antarctic Precipitation System removed 
their instruments by 3 December 2019. The GPS receiver continues to 
[operate and produce good data as of March 14, 2022](http://gnss-reflections.org/api?station=phnx&year=2022&doy=73&freq=L1&amp=10&h1=0.4&h2=6.0&e1=5.0&e2=25.0&pk2noise=3.0&rinex=2.11&azim1=0&azim2=360&archive=all&ftype=txt)

### Let's Take a Look at the Data

First make a SNR file.

<code>rinex2snr phnx 2021 1</code>

This will download the data from UNAVCO, translate into a SNR format. The command only uses GPS satellites.
At my request, UNAVCO tracked good GPS signals (L2C and L5). We will use both of those and L1.

Now use <code>quickLook</code> to produce a periodogram similar to the one in 
the web app [(For details on quickLook output)](../../docs/quickLook_desc.md). 
<code>quickLook</code> is set to use the L1 frequency by default:

<code>quickLook phnx 2021 1</code>

First, the lomb scargle periodograms for each quadrant which indicate that things are looking pretty good.
Remember that each color is a different satellite arc.

<img src="phnx_lsp_l1.png" width="600">

The summary plot shows consistent reflector height retrievals:


<img src="phnx_ql_l1.png" width="600">
 
Pretty sweet. It looks like the azimuths are pretty good. There are some low amplitudes at 
certain azimuths. *However*, these periodograms look a lot better than 
we saw on the automated gnss-reflections website:

<img src="phnx_2019_200.png" width="600">

I have circled in bright yellow in the periodograms that are noise at a little less than one meter reflector height.
If our theory is correct that this was created by the other sensors set out by the Antarctic Precipitation System, 
Let's run <code>quickLook</code> again a few weeks after they removed their equipment:

<img src="phnx_2020_001.png" width="600">

You can see that that particular noise source is now gone.

### Analyze the Data

Now prepare to analyze the data using <code>gnssir</code>. 
First you need to create a set of analysis instructions. 
The default settings need the station name, latitude, longitude, and ellipsoidal height. 
Originally the software required you to input the coordinates. If you believe  
that the Nevada Reno group has the site in its database, you can 
avoid that step, as so:

<code>make_json_input phnx 0 0 0 -query_unr True</code>

The json output will be stored in $REFL_CODE/input/phnx.json. [Here is a sample json file.](phnx.json)
The default peak to noise ratio is 2.7 - which is better for water. Since these are ice/snow reflections, I'm
going to increase it a bit to 3.2 and require a larger amplitude.

<code>make_json_input phnx 0 0 0 -query_unr True -ampl 10 -peak2noise 3.2</code>

I also removed by hand the region from 320-360 degrees in the final json file I used.

Next we need to make some snr files. I am going to do most of 2019 thru 2021, but if you prefer, you can set
the -weekly option to True and that will speed things up (it makes one file per week).
This command will go from day 1 in 2019 to day 150 in the year 2021.

<code>rinex2snr phnx 2020 1 -doy_end 150 -year_end 2021</code>

Run the <code>gnssir</code>:

<code>gnssir phnx 2020 1 -year_end 2021 -doy_end 150</code>

It takes a couple seconds to run <code>gnssir</code> for one day of data - so you will have to wait 
five minutes or so for two and a half years of data to run. At that point you want to compute a daily 
average reflector height:

<code>daily_avg phnx 0.2 100 </code> will create a daily average reflector height using a 
median filter of 0.2 meters to remove outliers.  The 100 input says you require 100 arcs to have confidence
in the average. You can vary these parameters to better see what is going on.

<P align=center>
<img src=phnx_RH.png width=600>
</P>

A file with the reflector height results is created by <code>daily_avg</code>; that is what 
you use to measure snow accumulation using GNSS-IR.

A big thank you to Thomas Nylen for his efforts on installing and maintaining this site.
