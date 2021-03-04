### Ross Ice Shelf, Antarctica

**Station Name:**  lorg

**Location:**  Ross Ice Shelf, Antarctica

**Archive:**  [UNAVCO](http://www.unavco.org), [SOPAC](http://sopac-csrc.ucsd.edu/index.php/sopac/)

**DOI:**  [https://doi.org/10.7283/ACF6-YT23](https://doi.org/10.7283/ACF6-YT23)

**Ellipsoidal Coordinates:**

- Latitude:  -78.18365
- Longitude: 170.03361
- Height:  	-7.778 m

[Station Page at UNAVCO](https://www.unavco.org/instrumentation/networks/status/nota/overview/lorg)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/LORG.sta)

[Google Maps Link](https://goo.gl/maps/bSAuLXLLMmzWqPdW9) 

<img src="https://gnss-reflections.org/static/images/LORG.jpg" width="500">

## Data Summary

Station lorg is on the Ross Ice Shelf, Antarctica.
The site is a largely featureless ice plain with no obstructions (see photo above). 
The site was installed on November 27, 2018 and decommissioned and removed on November 15, 2019. 
It recorded only GPS frequencies during its operation. 

LORG is an example station on the [GNSS-IR web app.](https://gnss-reflections.org/fancy6?example=lorg) 
Please note that the app will be analyzing data in real-time, so it will take 5-10 seconds.

There are no significant topographic features near the station, so it is recommended to use default values 
for the elevation mask. An azimuth mask is not required.

## Reproduce the Web App

**Make SNR File**

Start by downloading the RINEX file and extracting the GPS SNR data:

*rinex2snr lorg 2019 205*

**Take a Look at the Data**

Use **quickLook** to produce a periodogram similar to the one in the web app. quickLook is set to use the L1 frequency by default:

*quickLook lorg 2019 205*

<img src="lorg-ql-l1.png" width="500">
 
Compare the periodograms for frequencies 1, 20 (L2C) and 5. They should be similar to the L1 periodogram, except that there 
will be fewer satellite traces because only GPS satellites launched after 2005 broadcast L2C and only satellites after 2010 broadcast L5.
The northwest qudarant is the noisiest and one could certainly try to improve the results by restricting some azimuths there.

*quickLook lorg 2019 205 -fr 20*

<img src="lorg-ql-l2c.png" width="500">

*quickLook lorg 2019 205 -fr 5*

<img src="lorg-ql-l5.png" width="500">

## Analyze the Data

Now prepare to analyze the data using **gnssir**.  First you need to create a set of analysis instructions. 
The default settings only need the station name, latitude, longitude, and ellipsoidal height. You make 
this file using **make_json_input**: 

*make_json_input -e1 5 -e2 25 lorg -78.18365 170.03361 -7.778*

The json output will be stored in $REFL_CODE/input/lorg.json. 
[Here is a sample json file.](lorg.json)

Next make some snr files for a time span of about eight months. Restrict the search to the UNAVCO archive to make the 
code run faster (otherwise it will check three other archives as well). The resulting SNR files will be stored in $REFL_CODE/2019/snr/lorg. 

*rinex2snr lorg 2019 1 -doy_end 233 -archive unavco*

Run **gnssir** for all the SNR files from **rinex2snr**.

*gnssir lorg 2019 1 -doy_end 233*

The default does not send any plots to the screen. If you do want to see them, set -plt:

*gnssir lorg 2019 1 -screenstats False -plt True* 

<img src="lorg-g-panels.png" width="800"/>

The results for a single day are stored in a folder for that year, i.e. 
$REFL_CODE/2019/results/lorg. [Here is a sample for day of year 102.](102.txt)

The **daily_avg** command will calculate the daily average reflector height from the daily output files. 
To minimize outliers in these daily averages, a median filter is set to allow 
values within a given value of the median. The user is also asked to set a required minimum number of daily satellite 
tracks. Here we use 0.25 meters and 50 tracks. We have also set a specific output filename:

*daily_avg lorg 0.25 50 -txtfile lorg-dailyavg.txt*


<img src="lorg_1.png" width="500"/>


<img src="lorg-dailyavg.png" width="500"/>

[A daily average Reflector height file is provided here.](lorg-dailyavg.txt). 
