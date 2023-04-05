# Utilities 

## refl_zones

This module creates "stand-alone" Fresnel Zones maps for 
google Earth. At a minimum it requires a four station character name as input.

<code>refl_zones sc02</code>

The defaults are that it does all azimuths, elevation angles of 5-10-15, GPS L1,
sea level reflections, and creates an output file called sc02.kml; 
this is stored in $REFL_CODE/Files/kml. 

It uses the station name to query your station location database.  If your station
is not in that database, you should use the optional lat,lon,el_height inputs.

If you want to specify the reflector height instead of using sea level, set -RH.
If you are making a file for an interior lake or river, you will need to use this option.
Similarly, for a soil moisture or snow reflection zone map, where height above sea level is not
important, you will want to set the RH value accordingly.

The optional inputs (at this time):

- azim1 min azimuth (degrees) can be negative.

- azim2 min azimuth (degrees)

- el_list 5 10 15 20 25 (for example)

- azlist can be used for azimuth regions that are more complicated than a single pair of values.
example:  90 180 270 would be northeast and southwest. Azimuths cannot be negative, greater than 360,
and they must be pairs of numbers that increase, i.e. you cannot say 90 50, you have to say 50 90.

- lat latitude in degrees

- lon longitude in degrees

- el_height ellipsoidal height in meters

- fr frequency (1,2,5 allowed)

- RH reflector height in meters

- system constellation (gps,glonass,galileo, beidou)

- output filename for the kml file (if you do not like the default)

The code relies on orbits stored on github. These will be downloaded and stored the 
first time you run the code. It also needs the EGM96 file 
for calculating geoid corrections. It is downloaded and stored the first time you run the code.
While ordinarily you do not need to have internet connection to run this module, you do need
it the first time you run the code to get these files.

<HR>

## download_rinex
<code>download_rinex</code> can be useful if you want to 
download RINEX v2.11 or 3 files (using the version flag) without using 
the reflection-specific codes. As with <code>rinex2snr</code>, the default archive is 
to check unavco, sopac, and sonel in that order. For other archives, you must specify their name.
For a listing of supported archives, please see the [rinex2snr documentation](rinex2snr.md).

Sample calls:

- <CODE>download_rinex p041 2020 6 1</CODE> downloads the RINEX 2.11 data from June 1, 2020

- <CODE>download_rinex p041 2020 150 0</CODE> downloads the data from day of year 150 in 2020

- <CODE>download_rinex p041 2020 150 0 -archive sopac</CODE> downloads the data from sopac archive on day of year 150 in 2020

- <CODE>download_rinex onsa00swe 2020 150 0 -archive cddis</CODE> downloads the RINEX 3 data 
from the cddis archive on day of year 150 in 2020

## Miscellaneous

<code>download_orbits</code> downloads orbit files and stores them in $ORBITS. The list of orbits 
we support changes regularly. Please see the [rinex2snr documentation](rinex2snr.md).

<code>ymd</code> translates year,month,day to day of year

<code>ydoy</code> translates year,day of year to month and day

<code>llh2xyz</code> translates latitude (deg), longitude (deg), and ellipsoidal ht (m) to X, Y, Z (m)

<code>xyz2llh</code> translates Cartesian coordinates (meters) to latitude (deg), longitude (deg), ellipsoidal height (m)

<code>gpsweek</code> translates year, month, day into GPS week, day of week (0-6) 
   
<code>download_unr</code> downloads ENV time series for GPS sites from the Nevada Reno website (IGS14), so ITRF 2014. Input is 
four character station name. Lowercase.

<code>download_tides</code> downloads up to a month of NOAA tide 
gauge data given a station number (7 characters), and begin/end dates, e.g. 
20150601 would be June 1, 2015. The NOAA API works perfectly well for this,
but this utility writes out a file with only columns of 
numbers (or csv if you prefer). To implement the latter, use csv as the ending 
of your output filename.
This can also be called as <code>download_noaa</code>; there is an optional plot produced with -plt T.

<code>download_psmsl</code> downloads sealevel files from the 
[Permanent Service for Mean Sea Level](https://www.psmsl.org/data/gnssir/map.php). 
Input is the station name. Ouput can be plain txt of csv. To implement the 
latter, use csv as the ending of your output filename. Optional plot to the screen if -plt is set to T.

<code>download_ioc</code> downloads up to a month of tide gauge records from the 
[IOC website](http://www.ioc-sealevelmonitoring.org/). Requires beginning and 
ending date (yyyymmdd format) and is limited by the IOC to 30 days. Optional output filename allowed. 
If the output file ends in csv, it writes a csv file instead of plain text.
You can pick the sensor type or you will get all of them. 
There is an optional plot produced with -plt T.

<code>query_unr</code> returns latitude, longitude, and ellipsoidal height and Cartesian position 
for stations that were in the Nevada Reno database as of October 2021. Coordinates are now more precise 
than they were originally (UNR used to provide four decimal points in lat/long). 

<code>check_rinex</code> returns simple information from the file header, such as receiver
and antenna type, receiver coordinates, and whether SNR data are in the file. RINEX 2.11 only

<code>prn2gps</code> will try to tell you which PRN numbers are associated with which SVN (or GPS) numbers 
for a given day, as in <code>prn2gps 2021-01-01</code>. 
It uses the public [JPL](https://sideshow.jpl.nasa.gov/pub/gipsy_products/gipsy_params/PRN_GPS.gz) translation file, so if that file
is no good, the translation will also be no good.  

<HR>
