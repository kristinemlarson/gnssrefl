# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 1.4.7

August 7, 2023

I am trying a new build with Tim Dittmann's changes to the docker build.
This should allow us to define versions with tag numbers that are aligned
with the verion.


## 1.4.6
pushed Tim Dittmann's changes to make_meta. 
Still some issues that need to be fixed.

Changed input on refl_zones for ellipsoidal height to be consistent with gnssir_input
Commandl line variable shoud be height, not el_height.

## 1.4.5
Fixed unset variable in the data windowing function so it always has a value (iAzim).

## 1.4.4
I updated gnssir and quickLook so that it now reports the azimuth of the lowest
elevation angle in the arc. Previously it used the average azimuth over the 
entire rising or setting arc.

## 1.4.3

Changed gnss back to its original setting, which is getting the multi-GNSS final 
GFZ orbits from CDDIS.  I had sent those queries to rapid, not remembering that rapid
GFZ does not have beidou. 

gnss-gfz directly downloads multi-GNSS orbits from GFZ.  this is equivalent to gnss3 option.

for all four constellations, use gnss-gfz or gnss options.

Added script to download tide gauge data from Queensland ... download_qld.py

quickplt allows xaxis limits in MJD (i.e. it will use datetimes to make a nicer x-axis)

## 1.4.2

Fixed bug in query_modern in gps.py that did not check to see if Files subdirectory existed before
downloading station_pos.db. 

I do not know WHY the docker does not provide the necessary file, as it should.

## 1.4.1

I incorrectly implemented the refraction correction when I wrote the newarcs
option of gnssir.  This has been fixed with this version. I will be removing all
pypi versions that have the bug in it.  Effectively, the refraction correction
was not being implemented at all.  this will cause a bias between series computed before
and after.  It has no impact on the SNR data files. Only on gnssir output (and the programs
that use those outputs, like subdaily, snowdepth, phase, and vwc).


changed WSV water level to 30 day downloads instead of 15

gnssir_input incorrectly defined e1 and e2 as integers ... fixed.

quickLook also incorrectly defined e1 and e2 as integers ... fixed

added more columns to subdaily outlier file...

## 1.3.26

fixed major bug in gnssir for old arc selection


## 1.3.25

nyquist plots to the screen

Allow multiple elev ranges  - see gnssir_input for information about setting it up.
required changeds to gnssir as well - let me know if something seems not
to work anymore.

## 1.3.24

try to reduce print statements by using screenstats in rinex2snr and download_rinex

added azimuth limits to quickLook (they were missing from when I updated it)

newarcs is now the default for gnssir

removed make_json_input, command line version is no longer generated.

updated software_tests and use cases for these changes

## 1.3.23

added gnss3 orbit option for testing. eventually will use this for gnss.
it downloads multi-GNSS sp3files directly from GFZ instead of from CDDIS.

gnss now points to rapid when appropriate. hopefully.

added risky option to nmea2snr for people that do not read the screen output warning
them they are doing a bad thing.


## 1.3.22
allows gzip RINEX 2.11 files in local directory

went back to original CDDIS access. apparently there was something wrong with their sftp access
?  in any case, we now have two ways to access CDDIS, and eventually we will likely need 
the other one.

## 1.3.21

new version number to synch pypi and github versions

## 1.3.20
changed bkg archive to bkg-igs or bkg-euref

## 1.3.19

Time sorted daily_avg output
Added x-axis limits to quickplt
Snowdepth can be limited to a single frequency (useful for earlier datasets that only 
had useful L2C)

Added community pubication page to docs/pages/community.md

## 1.3.18 
Problems making the readthedocs - So many problems.... downgraded sphinx version
in the build. fixed it.

added hires_figs to subdaily - makes eps file instead of png.

nmea2snr uses sp3 file as default now. Low quality azel records in the NMEA files 
for some sensors.


## 1.3.17

New version of quickLook.  Uses a better algorithm for extracting rising and setting arcs.
Should be transparent to the user - but let me know.

## 1.3.16

delTmax allowed as input to quickLook

added azlist2 to gnssir - in testing phase - seems to work so far.  use gnssir -newarcs T

made gnssir_input - this will be the new make_json_input. coordinates no longer required
meaning UNR database is the default.

fixed bug in gnssir that didn't allow plots for newarcs -T

## 1.3.15
added smoosh_snr for decimating snr files

added some missing stations to the UNR database function

print out lat/lon/ht and XYZ for query_unr

added azlist2 to make_json_input to get ready for new way of identifying arcs



## 1.3.14
Default rinex2snr orbit is GPS only before doy 137, 2021 and multi-GNSS from GFZ after that.

tried smoke test for NMEA using wget

Check whether someone tries to download CDDIS highrate data that are too old.

## 1.3.13
Major changes to nmea2snr. Allows azimuth, elevation angle inputs from SP3 files.
And decimation. LLH can be input on the command line or it can be read from the 
$REFL_CODE/input/station.json file

Updated the readthedocs

## 1.3.12
Added nyquist utility code (was previously living at https://gnss-reflections.org)

## 1.3.11
Fixed bug in refl_zones - caused it to crash

Allowed bfg to have zip as well as gz files

## 1.3.10
Changed inputs to invsnr_input. They are now optional - you don't have to memorize
the order of RH, elevation angles and azimuth angles as it was before.  Am using
my variable for azimuth, i.e. azim1, azim2.

## 1.3.9
New version of nmea2snr - doesn't crash on bad files

Updated short course materials in sc_media.md

Fixed a bug in daily_avg that was unhappy when no results were found. Now it more politely exits.

renamed vwc.py to vwc_cl.py

## 1.3.8
hopefully check multiple directories at CDDIS because of inconsistencies
in how they name/store files

## 1.3.7
Fixed bug in phase code. Caused by my inability to type the word "plt."
Updated a lot of documentation and use cases.

## 1.3.6

fixed bug in soil moisture code.  code was crashing. have tried to improve how
it detects and removes bad tracks.

## 1.3.5

fixed bare soil bug in azimuth snow model.
added optional input for bare soil to snowdepth_cl.py

added check_rinex_file to the utilities section.  looks for L2C and returns other
header information to the screen

## 1.3.4

testing documentation

## 1.3.3

Improved rinex3_rinex2 and rinex3_snr (added more options, allow gzipped files, streamlined)

Individual tide gauge download scripts turned into functions - now called by download_tides

## 1.3.2

Fixed links in the online docs to eventually allow a pdf user guide.

## 1.3.1

removed download_tides - now download_noaa explicitly. Will ultimately combine
all the tide download scripts to be one

## 1.2.29
Fixed longstanding bug in where the refraction pickle file is stored.
was working in the docker.  was working for github clone.  not working for pypi
because it did not check for the input subdirectory existence.

## 1.2.28

changed az_sectors to azlist in refl_zones to be consistent with other codes

changed snr 88 for rinex2snr fortran codes.

tried to fix the software_tests so we can have smoke tests again. for now, I removed unavco
tests.

changed online doc for rinex2snr and nmea2snr for snr type 88.  

for rinex2snr (and download_rinex), the default behavior will now search sopac before unavco
for rinex2.11 files

Added nrcan and gfz to RINEX 3 archive list

Fixed bugs related to bkg inputs for IGS/EUREF folders

Updated various documentation.

## 1.2.27

add quick_recall documentation

bkg option in rinex2snr specifically for highrate files, since BKG has two 
directories(IGS and EUREF). For 30 sec files we will be kind and search both
directories for users.

Changed output format for download_noaa, ioc, and wsv

Added tmin and tmax soil moisture properties inputs to vwc. Modified
documentation.


## 1.2.26
Added new tide gauge download (for WSV).  Added documentation for all of them (new page)

subdaily now has a working spline_outlier input. This allows you to use an outlier
criterion in meters instead of the default 3 sigma. The latter can be too restrictive.
spline_outlier1 is for the first phase (RHdot) and spline_outlier2 is for the second 
one, after Rhdot and interfrequency biases are removed. Units are meters.

## 1.2.25
I have made good faith effort to institute the requirement for earthscope logins.
I had to change rinex 2.11, rinex 3, and highrate rinex 2.11 file downloads in both
rinex2snr and download_rinex. We will know on March 31 if I was successful.

I fixed a bug in gnssir triggered by unphysical elevation angles in NMEA messages
They peg at the same value - which makes LSP think that they have a window length
of zero. A warning is sent to the screen (if screenstats is set to True) and the satellite is skipped. 

README.md now directs users to readthedocs. 

## 1.2.24
added unavco2 option to test new unavco download protocols
requires earthscope-sdk import
currently works - I believe - for RINEX 2.11
users will need an account with Earthscope. [For more information on this](warning.md)

Made minor changes to subdaily. outlier file is created on the second go-thru, e.g.

Added alaska CORS sites if using the jeff archive.

added a few option to quickplt (mostly label axes)

## 1.2.23
Made a new option for snowdepth. Azimuth dependent bare soil correction is now
the default.  

Changed RHdot calculation in subdaily to default behavior.

## 1.2.22

Added rt_rinex3_snr to allow real-time rinex3 generated files

Fixed various documentation pages.

## 1.2.21

Docker is refusing to build with these libraries.
Adding test version of refl_zones that looks for blocking signal azimuths.
Requires adding geopandas, xarray, and rioxarray. This module is current undocumented.

Fixed minor bug in refl_zones that did not properly act on information from UNR
database query.

## 1.2.20

Accommodated CDDIS file structure change for MGEX orbits.

## 1.2.19
Changed how the periodograms in quickLook are displayed. Initially tried to 
set to the maximum used by matplotlib.  This can be dominated by bad tracks, so 
now pick by maximum good track (times 1.1).  If there are not any good tracks at all 
this can be tricky.  Now using a min value of 2 for that. 

Restricting RH region to be at least 5.5 meters (consistent with gnssir). This is needed
to stop people using RH region to remove outliers.  The RH region also determines whether
the periodogram is valid.

Fixing the refl_zones restriction of 25 degrees elevation angle.  Increasing to 30 degrees
and providing error message.

refl_zones now writes out satellite number and elevation angle in the kml file.
Makes it easier for people to take out specific Fresnel zones if they wish.

## 1.2.18

Changed default RH max in quickLook to 8 meters.

Multiple azimuth regions allowed in refl_zones. Documentation updated.

## 1.2.17

Require RH constraints (set in make_json_input or by hand) and then invoked 
by gnssir **must** be at least 5 meters apart. These are used for the periodogram 
and for quality control. Sometimes people think this setting is only for outliers.  Outliers can still be 
removed in **subdaily** with RH constraints.  For now I am going to continue allowing this kind of 
constraint in **quickLook**, but eventually I may remove it there too.  

Changed make_json_input default max RH to 8 meters.  Slight change to peak2noise default.
The first change will make peak2noise stats higher in general.

## 1.2.16

Added reflector height plot in subdaily that shows the results with respect to 
azimuth. Should hopefully make it easier to track down azimuth issues for a mask.

Upon request, subdaily writes out evenly sampled RH values for the last spline fit.

## 1.2.15

Add newest L2C transmitting GPS satellite, PRN 28. Transmitting since January 31, 2023.
I do not believe it is healthy.

y-axis limits are now the same in quickLook periodograms.

Add L1C (I think) to rinex3 reading code - but it is a backup signal to default L1 C/A (S1C).  
But I would really need to see more receivers to see what is going on here.  They all seem to 
use different settings. 

Fixed persistent bugs that occur when trying to use gnssir to isolate problems with one satellite.
Now checks that the requested satellite is available on the requested frequency.
If not, it exits gracefully instead of crashing. This is when using -sat option, which is not
relevant for routine processing.

## 1.2.14

Allow capital letter station names in quickLook and gnssir (mac does not distinguish
between these two cases, but other machines do).

Explicitly check that people are not using illegal frequencies when they run gnssir

Fix bugs in nmea2snr related to how directories were created and discontinued numpy libraries

Updated snowdepth to have user-friendler bare soil definitions.

## 1.2.13

Added initial snowdepth utility.

removed np.float and np.int from gps.py library (no longer defined in newer numpy versions)

## 1.2.12
Slight changes to the behavior of refl_zones - it make a station icon and the output goes
to a subdirectory now to decrease the clutter in $REFL_CODE/Files.

Added more optional inputs to quickplt

## 1.2.11

Added Glonass to <code>nmea2snr</code>. Thank you to Daniel Nowacki for helping on this one.

## 1.2.10
Added a new utility - <code>rh_plot</code> - which is basically a way to look at RH results before you start making 
products (snow, sea level, etc). It uses libraries developed for subdaily and daily_avg


## 1.2.9

Fixed bug for multi-freq json analysis instructions when there are no Beidou data.
Even if there were no Beidou data in the RINEX file, gnssir will fail.

## 1.2.8

New pypi with a successful automated build

## 1.2.7

New pypi build, working on automating build.

## 1.2.6

Uploaded this version to pypi on December 26, 2022

Bugs:

Fixed bug in -dec option in gnssir. Previously failed if the data were not multi-GNSS.

## 1.2.5

New Feature:

New command line tool - quickplt. It will plot plain text files, 
presumably time series on x-axis - will convert to datetime, reverse sign 
of the y-values etc.

## 1.2.4

Improvements:

* Subdaily writes out evenly sampled results if requested. This is from 
a spline fit - to the reflector height observations and thus is dependent 
on the assumption that the water level is smooth.

Bugfixes:

* Fixed a bug for delTmax in quickLook that had been changed to 45 minutes - 
returned it to 75 minutes to accommondate snow/soil moisture applications.
I had fixed it in make_json_input, but not in quickLook.

## 1.2.3 

Improvements:

* Added azlist to make_json_input command line.  This means you can control 
the azimuth regions without editing the json file. Thre regions are entered in
pairs, i.e. 0 90 180 270 would be the northeast and southwest regions.

* Added frlist to make_json_input command line. This allows simpler access to 
the multi-constellation frequencies, i.e. 1,2,101,102 would be the original 
GPS and Glonass frequencies.

## 1.2.2

* I had tried out making delTmax input for gnssir to 45 minutes, but that is way too short for soil moisture.
I put it back to 75 minutes. For sea level studies where you expect tidal ranges to be significant over
an arc, you should be careful with this parameter.

## 1.2.1

Bugfixes:

* Fixed output in subdaily. The file with the IF correction was wrong.


## 1.1.12 

Improvements:

* The Files directory was getting too cluttered. I now create and use 
a subdirectory for results. The subdirectory is the same as the 4 character
station name unless subdir is chosen on the command line. This has been 
linked for vwc, daily_avg, subdaily and the plots for quickLook

* added IF bias correction to subdaily 

Bugs:

* csv outputs are currently not working in subdaily.

## 1.1.11

??

## 1.1.10 

Improvements:

* Rewrote the spline fit used in subdaily. It no longer cuts off data at the
beginning and end of the data series.  

* Output files are written with the are interfrequency bias corrected relative to L1.
This output is written to a new column.

* Improved the document header for the RHdot correction

## 1.1.9 

Improvements:

* Added ediff as commandline input to quickLook. The default is 2 degrees and is meant as a 
quality control parameters. If you choose 5 and 20 degrees as your elevation angle limits, this 
would mean your arcs should be at least from 7 to 18 degrees.  If you want to 
allow shorter arcs than this, you can make ediff much larger. Within gnssir, it can be defined 
in the json file.


## 1.1.8 

New Features:

* refl_zones module added. Command line driven.

* EGM96 is now accessible from gps.py. This provides simple geoid corrections in meters 
as a function of latitude and longitude.

Improvements:

* updated download_ioc to allow multi month downloads.


## 1.1.7 

Bug fixes:

* fixed bug in invsnr that did not allow SNR files unless they were uncompressed.
Code now allows xz and gz compression

## 1.1.6 

New Features:

* Changed how CDDIS archive is used, from a wget subprocess call to using FTPS.
This required checking that downloaded file was not zero size.


## 1.1.5 

New Features:

* [Soil moisture module added](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/pages/README_vwc.md)
vwc_input and vwc are the main programs.




