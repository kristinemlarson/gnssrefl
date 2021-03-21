### Niwot Ridge, Colorado

Station nwot was originally installed/designed by Jim Normandeau (UNAVCO) to support research 
by Kristine Larson, Eric Small, Ethan Gutmann, and Felipe Nievinski at the University of Colorado. 
The site was hosted by the Niwot Ridge LTER. After the original receiver failed, a new receiver
was installed by Mark Raleigh (then at CIRES, now at the University Oregon). 
Though it may be tracking now, it has not been downloaded in some time and there is no telemetry.

Data are available from UNAVCO.

[UNAVCO station page](https://www.unavco.org/instrumentation/networks/status/nota/overview/NWOT)

Unfortunately, there is very little useful information at UNAVCO (i.e. no time series). Nor is it routinely
analyzed by the Nevada Reno group.

Latitude: 40.05539 

Longitude: -105.59053

Elevation(m): 3522.729 


Because it was installed to support testing GPS reflections, nwot has always tracked L2C.

Ethan Gutmann and Felipe Nievinski both wrote papers that highlighted data from this site:

[Gutmann, E., K. M. Larson, M. Williams, F.G. Nievinski, and V. Zavorotny, 
Snow measurement by GPS interferometric reflectometry: an evaluation at Niwot Ridge, Colorado, Hydrologic Processes, Vol. 26, 2951-2961, 2012](https://www.kristinelarson.net/wp-content/uploads/2015/10/GutmannEtAl_2012.pdf)


[Nievinski, F.G. and K.M. Larson, Inverse Modeling of GPS Multipath for Snow Depth Estimation, Part II: Application and Validation, IEEE TGRS, Vol. 52(10), 6564-6573, doi:10.1109/TGRS.2013.2297688, 2014](https://www.kristinelarson.net/wp-content/uploads/2015/10/felipe_inv2_revised.pdf)

nwot was also part of PBO H2O.

### Make a SNR File and run quickLook

Start slow. Make a SNR file for one day, specifying unavco archive (no point looking
elsewhere since it is only at UNAVCO). The best data are currently unavailable unless you download
the 1-sec data.  However, you do not need this sample rate for reflectometry, so we are going to 
decimate it to 15 seconds.

*rinex2snr nwot 2014 270 -archive unavco -rate high -dec 15*

Both L1 and L2C can be used at this site. Unfortunately there were not very many L2C satellites
at that time.  Nevertheless, it is more than enough to measure snow.

*quickLook nwot 2014 270* 

will produce

<img src="nwot_L1.png" width="500"/>

A bit ratty in the low RH area - which is just noise from this particular receiver.
Nice strong peaks in the south.  Try L2:

*quickLook nwot 2014 270 -fr 2*

<img src="nwot_L2.png" width="500"/>

This will have both L2C and non-L2C. But it is easy to see why I don't use non-L2C. They are
the failed tracks in the gray.



### Make multiple years of SNR files and and run gnssir 


Until UNAVCO makes lowrate data avilalbe for this site, we need to use the highrate data and decimate.
We are going to look at the data from installation (fall 2009) through spring 2015.

*rinex2snr nwot 2009 240 -doy_end 365 -archive unavco -rate high -dec 15*
*rinex2snr nwot 2010 1 -doy_end 366 -archive unavco -rate high -dec 15 -year_end 2014*
*rinex2snr nwot 2015 1 -doy_end 120 -archive unavco -rate high -dec 15*


[sample json file for gnssrefl](nwot.json)

Run **gnssir** for hte years 2009-2015:

*gnssir nwot 2009 1 -doy_end 366 -year_end 2015*


### Compute daily averages:

*daily_avg nwot 0.25 10 -year1 2009 -year2 2015*


produces this plot:

<img src="nwot_RH.png" width="400"/>

and this file:

[daily average file](nwot_dailyRH.txt)


We installed the GPS site at Niwot Ridge because there was a long-standing experiment 
for measuring snow depth (and snow water equivalent).  We therefore have a way to assess
accuracy. We download the in situ data:

[in situ data from the Niwot Ridge LTER](saddsnow.dw.data.csv)

If the daily average file created before is stored in the same directory, you can use 
[this python script](nwot_usecase.py) to visual compare them:

*python nwot_usecase.py*

produces:

<img src="nwot_usecase.png" width="400"/>


