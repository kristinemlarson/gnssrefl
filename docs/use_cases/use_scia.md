# Airport near Victorville, CA


[Warning](warning.md)

<p align="center">
<img src=https://www.unavco.org/data/gps-gnss/lib/images/station_images/SCIA.jpg width="500"/>
</P>

## scia


**Location:** Victorville, California, USA 

**Archive:** [UNAVCO](http://www.unavco.org)

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/SCIA)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/SCIA.sta)


L2C data are available at UNAVCO in the standard RINEX files for this site starting in 2018.

## Translate the SNR data/Estimate RH

<code>rinex2snr scia 2018 1 -archive unavco -doy_end 366 -year_end 2020</code>

Take a quick look at the L2C data:

<code>quickLook scia 2018 1 -fr 20</code>

<img src=../_static/quicklook_scia.png width=600>

<img src=../_static/quicklook_scia2.png width=600>

**These are Lovely reflections!**

Set up (default) analysis stratgegy:

<code>gnssir_input scia -l2c T</code>

**Estimate reflector heights:**

<code>gnssir scia 2018 1 -doy_end 365 -year_end 2020 </code>

## Estimate Soil Moisture
[Please read the soil moisture user manual.](../pages/README_vwc.md) 
It is very short and has a lot of tips that will save you time.

We need a list of satellite tracks to use. We'll use 2019 for now as the 
year:

<code>vwc_input scia 2019</code>

Estimate the phase for each satellite track on each day:

<code>phase scia 2018 1 -doy_end 366 -year_end 2020</code>

Finally, convert the phase to volumetric water content. To make it easier to 
look at the plots, I'll just show the first two years:

<code>vwc scia 2018 -year_end 2019 </code>

Phase results plotted in geographic coordinates:

<img src="../_static/scia_1.png" width="600">

Daily average phase:

<img src="../_static/scia_2.png" width="600">

What is going on at the end of 2019? A little googling:

<img src="../_static/powerfulstorm.png" width="600">


If it is just rain, that's ok. If it is snow, that last very high point in 2019 is contaminated.
[This site says it was snow!](https://weatherspark.com/h/s/1975/2019/3/Historical-Weather-Winter-2019-in-Victorville-California-United-States#Figures-ObservedWeather)

Final plot:

<img src="../_static/scia_4.png" width="600">

VWC results are written to:

$REFL_CODE/Files/scia/scia_vwc.txt

Let's try to get rid of that snow outlier. I could look in the vwc file to see 
what day has a very large value. Or you can also try setting -snow_filter to True.
When I ran it, it did not create a snow outlier file - but it did tell me where it is stored
and what format it needed (year and day of year).  

<code>$REFL_CODE/Files/scia/snowmask_scia.txt</code>

So I went ahead and made that file with one line in it, 2019 361

Then I ran the vwc code again:

<code>vwc scia 2018 -year_end 2019 -snow_filter T</code>

Produces:

<img src="../_static/scia_2years.png" width=600>

Now let's look at three years:

<code>vwc scia 2018 -year_end 2020 -snow_filter T</code>

<img src="../_static/scia_3years.png" width=600>

There is what appears to be a big precipitation event followed by a drydown in April 2020.
[What does the weather station say?](https://weatherspark.com/h/s/1975/2020/0/Historical-Weather-Spring-2020-in-Victorville-California-United-States)
