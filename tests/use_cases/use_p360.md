### Use Case for Island Park, Idaho
  
**Station Name:**  p360

**Location:**  Island Park, Idaho

**Archive:**  [UNAVCO](http://www.unavco.org), [SOPAC](http://sopac-csrc.ucsd.edu/index.php/sopac/)

**DOI:**  [https://doi.org/10.7283/T5DB7ZR3](https://doi.org/10.7283/T5DB7ZR3)

**Ellipsoidal Coordinates:**

- Latitude:  44.31785

- Longitude: -111.45068

- Height:       1857.861 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/P360)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/P360.sta)

[Station Page at PBO H2O](http://cires1.colorado.edu/portal/index.php?product=snow&station=p360)

[Google Map Link](https://goo.gl/maps/EcTkbHjaSaWp4d8H9)

<img src="p360-photo.png" width="500">


## Data Summary

Station p360 is located to the west of Yellowstone National Park, near the town of Island Park 
in Idaho.  At an elevation of ~1858 m, winter snowfall can be frequent and heavy.

The site is operated by UNAVCO and has been recording multi-GNSS data since March 2020.

The station is in a flat, grassy plain with no obstacles or changes in topography, so elevation and azimuth 
masks are not particularly required.  

The [Reflection Zone Mapping tool](https://gnss-reflections.org/rzones?station=p360&msl=off&RH=2&eang=1&azim1=0&azim2=360) where reflection zones for selected elevation angles are plotted. 

P360 was part of [PBO H2O](http://cires1.colorado.edu/portal/)

## Reproduce the Web App

**Make SNR File**

Make an SNR file using only the default L1 GPS signal:

*rinex2snr p360 2019 100*

**Take a Quick Look at the Data**

**quickLook** analyzes the [spectral characteristics](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl/-/blob/christine-dev/docs/quickLook_desc.md) of the SNR data.

*quickLook p360 2019 100*

<img src="p360-ql-l1.png" width="500">

## Analyze the Data

Set the analysis paramaters using **make_json_input**.  The parameters are stored in a json file in $REFL_CODE/input/p360.json.  This analysis will use the L2C frequency.  

*make_json_input -e1 5 -e2 25 p360 44.31785 -111.45068 1857.861* 

The flags on this command set the elevation angles for SNR to a minimum of 5 degrees and a maximum of 25 degrees.  Edit the json file so that the list to remove the L1 and L5 frequencies from the list "freqs".  Change the code for L2 (2) to L2C (20), and then edit the list "reqAmp" so that it has the same number of elements as "freqs" (i.e., the list will contain 1 item, set to the default value of 6). Then change the peak-to-noise ratio ("PkNoise") from 2.7 to 3.2.  [Here is a sample json file](p360.json).

Run **rinex2snr** to get the SNR data for the winter of 
2017-2018 (set the dates from September 1 to June 30, though actual snowfall dates may vary).  
Because this analysis start in one year and finishes the next,  **rinex2snr** will have to be run twice, once for each calendar year. P360 records only L2 for standard RINEX files from UNAVCO, so this analysis will use custom RINEX files stored in a separate part of the UNAVCO ftp area.

*rinex2snr p360 2017 274 -doy_end 365 -archive special*

*rinex2snr p360 2018 1 -doy_end 121 -archive special*

Output SNR values are stored in $REFL_CODE/$year/snr/p360, where $year = 2017 or 2018.

Then run **gnssir** to calculate the reflector heights for each day, using only the L2C frequency:

*gnssir p360 2017 244 -doy_end 365 -fr 20*

*gnssir p360 2018 1 -doy_end 181*

The output files are stored in $REFL_CODE/$year/results/p360.  [Here is an example daily output file](334.txt).

The **gnssir** code does have an option to plot the daily spectrograms for each day, but it is not recommended to plot anything when running multiple days.  Instead, check one day and print some statistics to the screen:

*gnssir p360 2017 334 -screenstats True -plt True*

<img src="p360-gnssir-l2c.png" width="500">

Once the daily results are calculated, the daily averages of the reflector heights are calculated with **daily_avg**.  This code takes as arguments the median filter (all reflector heights must be within the given distance in meters from the median) and the minimum number of daily satellite tracks.  Because the data analysis was done using only the L2C frequency code, this number will be low.  The number of reflector heights for L2C only can range from 0 to 45 in this case, so set the minumum number to 12 (experimentation is encouraged to see what happens).  An output file is specified with the -txtfile flag, and will be placed in $REFL_CODE/Files. [Here is an example](p360-dailyavg.txt).

*daily_avg p360 0.25 12 -txtfile p360-dailyavg.txt*

The first plot shows the number of reflector heights each day.  This plot can be used to fine-tune the minimum number of reflector heights for the **daily_avg** command.

<img src="p360-dailynums.png" width="500">

The second plot shows the range of reflector heights for each day of available data.  

<img src="p360-dailyrange.png" width="500">

The third plot shows the average reflector height each day.  The changes in reflector height are consistent with snow accumulation (and subsequent compaction and spring melt) between November and June.

<img src="p360-dailyavg.png" width="500">
