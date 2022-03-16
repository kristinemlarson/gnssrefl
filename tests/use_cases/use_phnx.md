### Phoenix, Antarctica

<P align=center>
<img src="https://gnss-reflections.org/static/images/PHNX.jpg" width="500">
</p>

**Station Name:**  phnx

**Location:**  Phoenix, Antarctica

**Archive:**  [UNAVCO](http://www.unavco.org)


[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/phnx)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/PHNX.sta)

[GNSS-IR reflections example](https://gnss-reflections.org/api?example=phnx&ftype=txt)


### Experiment

phnx was installed at the same time as a [dedicated snow measurement experiment](https://essd.copernicus.org/articles/13/5803/2021/) called
the Antarctic Precipitation System. That experiment is now over and their instruments were removed in December 2019.
We can see from their paper that the site was absoutely note set up to enhance the precise of the 
GNSS-IR experiment:

<img src=https://essd.copernicus.org/articles/13/5803/2021/essd-13-5803-2021-f02-web.png width="500">

However, we will take this opportunity to see if we can detect the impact of the clutter. The paper says 
all instruments were removed by 3 December 2019. 

### Take a Look at the Data

First make a SNR file.

<code>rinex2snr phnx 2021 1</code>

This will download the data from UNAVCO, translate into a SNR format. The command only uses GPS satellites.

Now use <code>quickLook</code> to produce a periodogram similar to the one in 
the web app [(For details on quickLook output)](../../docs/quickLook_desc.md). 
<code>quickLook</code> is set to use the L1 frequency by default:

<code>quickLook phnx 2021 1</code>

First, the lomb scargle periodograms for each quadrant which indicate that things are looking pretty good.
Remember that each color is a different satellite arc.

<img src="phnx_lsp_l1.png" width="600">

The summary plot shows consistent reflector height retrievals:


<img src="phnx_ql_l1.png" width="600">
 
Pretty sweet. It looks like all azimuths are pretty good. There could be something going on ~90 degrees, 
but not enough that I would waste time worrying about it.  *However*, these periodograms look a lot better than 
we saw on the automated gnss-reflections website:



<img src="phnx_2019_200.png" width="600">

I have circled in bright yellow some noise in the periodgrams that creates noise ~one meter reflector height.
If our theory is correct that this was created by the other sensors set out by the Antarctic Precipitation System, 
Let's run <code>quickLook</code> again after they removed their equipment:


<img src="phnx_2020_001.png" width="600">

You can see that noise source is gone.



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
going to increase it a bit to 3.2.

Next make some snr files. I am going to do most of 2020 and 2021, but if you prefer , you can set
the -weekly option to True and that will speed things up (it makes one file per week).
This will go from day 1 in 2020 to day 150 in the year 2021.

<code>rinex2snr phnx 2020 1 -doy_end 150 -year_end 2021

Then run the <code>gnssir</code> for all the SNR files:

<code>gnssir phnx 2020 1 -year_end 2021 -doy_end 150</code>

