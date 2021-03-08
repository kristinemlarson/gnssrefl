### Vegetation Statistic

This is an unofficial part of the [gnssrefl package](README.md). 
The best way to learn about this technique is to read 
these two papers:

* 1.[Larson and Small, 2014](https://www.kristinelarson.net/wp-content/uploads/2015/12/Larson_2014Small.pdf) 

* 2. [Small, Larson, and Smith , 2014](https://www.kristinelarson.net/wp-content/uploads/2015/11/SmallLarsonSmith2014.pdf)

The first is a "how to" and the second is a validation using sites in Montana.
Matt Jones does a very nice job of showing how the GPS stats compare to vegetation optical depth
[pdf](https://www.kristinelarson.net/wp-content/uploads/2015/10/JonesMJ_etal_2013.pdf)

Mike Willis has been kind enough to provide a home for the [PBO H2O results](https://cires1.colorado.edu/portal).  
And finally, there was one paper led by Eric Small to use these data to 
study the [2012-2014 California drought.](https://www.kristinelarson.net/wp-content/uploads/2018/03/Small-Roesler-Larson2018-1.pdf) 


##Utilities

Install gnssrefl using git clone https://github.com/kristinemlarson/gnssrefl


Set up requested gnssrefl environment variables:

* EXE = where various RINEX executables will live.

* ORBITS = where the GPS/GNSS orbits will be stored. They will be listed under directories by
year and sp3 or nav depending on the orbit format.

* REFL_CODE = where outputs of the code will be stored

You might need to install CRX2RNX in the EXE area. See gnssrefl readme file. 

UNAVCO has a large stockpile of teqc logs that are used to extra vegetation stats.
For PBO H2O we had a system for QC that we do not reproduce here. We also provided context
for preciptation and thus provided NLDAS and NDVI data. We do not do that here. 

To download teqc logs for station p048 (which is used in Larson and Small, 2014) in 2008:

*download_teqc p048 2008* 

If you want to get more than one year:

*download_teqc p048 2008 -year_end 2020* 










