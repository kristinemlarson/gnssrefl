## Vegetation Statistic

This is an unofficial part of the [gnssrefl package](README.md). 
The best way to learn about this technique is to read 
these two papers:

* [Larson and Small, 2014](https://www.kristinelarson.net/wp-content/uploads/2015/12/Larson_2014Small.pdf)
Normalized Microwave Reflection Index: A Vegetation Measurement Derived from GPS Data 

* [Small, Larson, and Smith , 2014](https://www.kristinelarson.net/wp-content/uploads/2015/11/SmallLarsonSmith2014.pdf)
Normalized Microwave Reflection Index: Validation of Vegetation Water Content Estimates at Montana Grasslands

The first is a "how to" and the second is a validation using sites in Montana.
Matt Jones does a very nice job of showing how the GPS stats compare to vegetation optical depth
[(pdf)](https://www.kristinelarson.net/wp-content/uploads/2015/10/JonesMJ_etal_2013.pdf)
Comparing Land Surface Phenology Derived from Satellite and GPS Network Microwave Remote Sensing.

Mike Willis has been kind enough to provide a home for the [PBO H2O results](https://cires1.colorado.edu/portal). Some
of the sites are highlighted in this documentation (includes photos, ancillary data, terrain maps, google Earth link):

* [p048](http://cires1.colorado.edu/portal/index.php?product=vegetation&station=p048)

* [p208](http://cires1.colorado.edu/portal/index.php?product=vegetation&station=p208)

* [p537](http://cires1.colorado.edu/portal/index.php?product=vegetation&station=p537)

And finally, there was one paper led by Eric Small to use these data to 
study the [2012-2014 California drought.](https://www.kristinelarson.net/wp-content/uploads/2018/03/Small-Roesler-Larson2018-1.pdf) 
Vegetation Response to the 2012-2014 California Drought from GPS and Optical Measurements


### Installing the Code

Install gnssrefl using git clone https://github.com/kristinemlarson/gnssrefl

Set up requested gnssrefl environment variables:

* EXE = where various RINEX executables will live.

* ORBITS = where the GPS/GNSS orbits will be stored. 

* REFL_CODE = where outputs of the code will be stored

If you prefer, the ORBITS and REFL_CODE environment variables can point to the same directory. 
You have to make sure these values are set every time you work. So please put them in your 
.bashrc (or similar). Example from my setup: 

export ORBITS=/Users/kristine/Documents/Research/Orbits


Eventually you will need to install *teqc* and *CRX2RNX* in the EXE area. See the gnssrefl readme file for more details. 
I know encourage you to use <code>installexe</code>. It allows linux 
and mac installs. Type <code>installexe -h</code> for more information. Note: there is no *teqc* for the 
mac with the new chip - so you are out of luck there.

*For the most part I live in a lowercase world.*

### Utilities

**download_teqc**

UNAVCO has a large stockpile of teqc logs that can be used to extract vegetation stats.
For PBO H2O we had a system for QC that worked pretty well to eliminate outliers caused 
by snow or rain. *We do not reproduce that here.* We also provided context
for preciptation and thus provided NLDAS and NDVI data. We do not do that here. 
PBO took advantage of the fact that 1100 identical receivers that only tracked GPS signals (Trimble NETRS) were 
installed at the same time. By the mid-2010s the GPS receivers did start to fail and were replaced
with newer units. We deliberately removed the data from these receivers because there were 
biases. This points to a problem that will be an issue going forward, as receivers WILL be 
updated. And multi-GNSS is not the same as GPS. Generally, receivers today are multi-GNSS. PBO H2O was GPS only.


To download teqc logs for station p048 in the year 2008 (which is used in Larson and Small paper) :

*download_teqc p048 2008* 

If you want to look at more than one year for p048:

*download_teqc p048 2008 -year_end 2020* 

Go ahead and also download teqc logs for p208, which is an awfully nice site:

*download_teqc p208 2008 -year_end 2020* 

**vegetation_multiyr**

This utility makes an output txt file (filename is sent to the screen) and displays a plot.
For p208: 

*veg_multiyr p208 2008 2020*

<img src="docs/p208.png" width=450>

p048 was highlighted in Larson and Small (2014). You can get a feel for the processing steps:

<img src="docs/p048-frompaper.jpg" width=450>

Let's try to reproduce some of this with the new software:

*veg_multiyr p048 2008 2020*

<img src="docs/p048.png" width=450>

At this site a snow filter is required. We only have a simple one:

*veg_multiyr p048 2008 2020 -winter True*

<img src="docs/p048_winter.png" width=450>

the trend you see IS NOT VEGETATION. It is the long-term death of this receiver.
You can see we got lucky that our original paper only had six years of data:

*veg_multiyr p048 2008 2015 -winter True*

<img src="docs/p048_shorter.png" width=450>

Note: I should have downloaded the year 2007 as well.

p537 has a change from Trimble to Septentrio. This is relevant because 
we are going to use a multi-GNSS Septentrio unit. Even though there is a bias between the 
receivers, that is OK.  We are looking at variations - and the data have 
always been normalized against the receiver behavior when the vegetation is driest:

*veg_multiyr p537 2008 2020*

<img src="docs/p537.png" width=450>

### mp1mp2
So the sort of bad news is I am hesitant to trust the multi-GNSS teqc logs
that UNAVCO now computes. In order to avoid any confusion, for NEW experiments, I think it is best
to run <code>teqc</code> yourself. You need to have installed the teqc executable.  Otherwise, it 
only requires the station name, the year, and the day of year. In this example, 
you must have the RINEX file in your directory:

*mp1mp2 p537 2020 1*

If your RINEX file is stored at UNAVCO, just add the look option:

*mp1mp2 p537 2020 1 -look True*

It will pick up the RINEX file for you and the orbits and compute the teqc log making sure that
only GPS data are used.  

The utility recognizes that sometimes you will want to do multiple days of this, so you can do the whole year:

*mp1mp2 p537 2020 1 -look True -doy_end 366*


### Receiver/Antenna Information

If you have teqc logs for a site and you just want to check the receiver and antenna type:

*mp1mp2 p537 2020 50 -rcvant True*

It will print to the screen:

Receiver type           : SEPT POLARX5 (# = 3012343) (fw = 5

Antenna type            : TRM59800.00     SCIT (# = 52113544


### Download RINEX files from UNACVCO

For December 2, 2010 and station p537:

*download_rinex 537 2010 12 2* 

If you prefer to use day of year, leave the last input as zero.  So for year 2010 and day of year 2:

*download_rinex p537 2010 2 0* 


### Reflection Zone

The reflection zone depends on the height of the antenna over the reflecting surface. While
for snow and soil moisture we used the SNR data down to 5 degrees, the vegetation statistic only
uses pseudorange and carrier phase data down to 10 degrees (there are reasons for 
this). I made a webapp that produces reflection
zone maps over google earth. I have added a vegetation friendly option (elevation angles 10,15,20)
and you should use the tower height (~18 meters) not the default sea level option.  Here is the command
using 66.15696 and -147.5028:

[BONA](http://gnss-reflections.org/rzones?station=&lat=66.15696&lon=-147.5028&height=100&msl=off&RH=18&eang=5&azim1=0&azim2=360)

I used a fake height for BONA since the app only needs lat and long.

