## Vegetation Statistic

This is an unofficial part of the [gnssrefl package](README.md). 
The best way to learn about this technique is to read 
these two papers:

* [Larson and Small, 2014](https://www.kristinelarson.net/wp-content/uploads/2015/12/Larson_2014Small.pdf) 

* [Small, Larson, and Smith , 2014](https://www.kristinelarson.net/wp-content/uploads/2015/11/SmallLarsonSmith2014.pdf)

The first is a "how to" and the second is a validation using sites in Montana.
Matt Jones does a very nice job of showing how the GPS stats compare to vegetation optical depth
[(pdf)](https://www.kristinelarson.net/wp-content/uploads/2015/10/JonesMJ_etal_2013.pdf).

Mike Willis has been kind enough to provide a home for the [PBO H2O results](https://cires1.colorado.edu/portal). And finally, there was one paper led by Eric Small to use these data to 
study the [2012-2014 California drought.](https://www.kristinelarson.net/wp-content/uploads/2018/03/Small-Roesler-Larson2018-1.pdf) 


### Installing the Code

Install gnssrefl using git clone https://github.com/kristinemlarson/gnssrefl


Set up requested gnssrefl environment variables:

* EXE = where various RINEX executables will live.

* ORBITS = where the GPS/GNSS orbits will be stored. 

* REFL_CODE = where outputs of the code will be stored

If you prefer, the ORBITS and REFL_CODE environment variables can point to the same directory

Eventually you will need to install teqc and CRX2RNX in the EXE area. See the gnssrefl readme file for more details. 

*For the most part I live in a lowercase world.*

### Utilities

**download_teqc**

UNAVCO has a large stockpile of teqc logs that can be used to extract vegetation stats.
For PBO H2O we had a system for QC that worked pretty well to eliminate outliers caused 
by snow or rain. *We do not reproduce here.* We also provided context
for preciptation and thus provided NLDAS and NDVI data. We do not do that here. 
PBO took advantage of the fact that 1100 identical receivers that only tracked GPS signals (Trimble NETRS) were 
installed at the same time. By the mid2010s receivers did start to fail and were replaced
with newer units. We deliberately removed the data from these receivers because there were 
biases. This points to a problem that will be an issue going forward, as receivers WILL be 
updated.  And multi-GNSS is not the same as GPS.



To download teqc logs for station p048 (which is used in Larson and Small, 2014) in 2008:

*download_teqc p048 2008* 

If you want to look at more than one year for p048:

*download_teqc p048 2008 -year_end 2020* 

Go ahead and download teqc logs for p208, which is an awfully nice site:

*download_teqc p208 2008 -year_end 2020* 

**vegetation_multiyr**

This utility makes an output txt file (filename is sent to the screen) and displays a plot.
For p208: 

*veg_multiyr p208 2008 2020*

<img src="docs/p208.png">

p048 was highlighted in Larson and Small (2014):

*veg_multiyr p048 2008 2020*

<img src="docs/p048.png">

At this site a snow filter is required. We only have a simple one:

*veg_multiyr p048 2008 2020 -winter True*

<img src="docs/p048_winter.png">

the trend you see IS NOT VEGETATION. It is the long-term death of this receiver.
You can see we got lucky that our original paper only had eight years of data:

*veg_multiyr p048 2008 2015 -winter True*

<img src="docs/p048_edit.png">


p537 has a change from Trimble to Septentrio. This is relevant because 
we are going to use Septentrio. Even though there is a bias between the 
receivers, that is OK.  We are looking at variations - and the data have 
always been normalized against the receiver behavior when the vegetation is driest:

*veg_multiyr p537 2008 2020*

<img src="docs/p537.png">

### mp1mp2
So the sort of bad news is I am hesitant to trust the multi-GNSS teqc logs
that UNAVCO computes. In order to avoid any confusion, for NEW experiments, it is best
to run teqc yourself. To do this yourself, it only requires the station name, the year, and 
the day of year. In this example, you must have the RINEX file in your directory:

*mp1mp2 p537 2020 1*

If you RINEX file is stored at UNAVCO, just add the look option:

*mp1mp2 p537 2020 1 -look True*

It will pick up the RINEX file for you and the orbits and compute the teqc log making sure that
only GPS data are used.  



