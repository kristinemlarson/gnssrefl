# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 3.3.0

Problem with how some RINEX 2.11 files on Windows were being read when
I checked for whether the file was compliant.  numpy loadtxt assumes certain kinds of 
strings and it will fail if it is not (the file that led to this change was Latin-1).  
This is not apparently an issue in linux or on macos.  Or when files are picked up from
an archive.  Anyway, I put the check for compliance behind a try/except command.  So effectively
it own't check whether the file is RINEX 2.11, but it is better than crashing.

## 3.2.2

Fixed some bugs in quickplt. Timing limits along the x-axis are now
more consistent. If are you using time, the limits are YYYYMMDD format.
This can be prompted by using mjd, ydoy, ymdhms optional flags, e.g.

Changed issue report request so that users are directed to 
provide needed information about version number.

## 3.2.1

gnssrefl now allows 1-hz files from CDDIS that are more than 6 months old.
I would still like someone 'other than me' to make a similar change for BKG.
The download is clearly much faster (download 1 file instead of 96) but 
merging still slow. Has anyone tested new versions of gfzrnx to see if they
are faster? They might be.

## 3.2.0
Added NITE model.  In gnssrefl this is refl_model 5.

For details see Peng (2023), DOI: 10.1109/TGRS.2023.3332422
While the NITE publication advocates using estimated zenith troposphere delays,
we provide no such access here, and use Saastamoinen model corrections using
standard met outputs created by Generic Mapping functions.  If someone wants
to use estimated zenith delays, they are welcome to do so.

An a priori RH  is needed for this model. It should be input and saved when
using the optional apriori_rh. The NITE model should be much more accurate
than the default refraction model (1). It is not clear how much more precise
it is.  I would expect it to be more precise for tall sites. 

Added MPF model - name may change.  In gnssrefl this is refr_model 6.

## 3.1.5

quickplt has been significantly updated to allow plotting of SNR files.
This mode is triggered by setting the optional parameter -sat.  See 
the quickplt documentation for details.

remove_wget is a new function in gps.py. This is my attempt to get away from
using wet.download. It uses requests instead. That route doesn't work for ftp
address, so will need to do something else for those sites.

I removed fortran as optional boolean input to rinex2snr.  this hsould be accommodated by setting
translator to 'fortran' instead.

rinex2snr logs will now be written to $REFL_CODE/logs. Previously the logs directory
was created wherever you were running the code, which was confusing to people using
dockers.

## 3.1.4 

Added a gazillion options to gnssir_input to accommodate daily_avg and subdaily 
users that want to store strategies there. See the gnssir_input code for more details,
i.e. the parameter names.

## 3.1.3

Allow users to store required input parameters to daily_avg in the json used
by gnssir. The names of these parameters are:
"daily_avg_reqtracks" and  "daily_avg_medfilter".  For those making a new json,
the parameters will be set to None if you don't choose a value on the command line. 
You can also hand edit or add it. This would be helpful in not 
having to rerun gnssir_input and risk losing some of your other specialized selections.

## 3.1.2

Fixed bugs in highrate RINEX 3 downloads/translations that conflicted with parallel processing
(GA and BKG archives). This was mostly related to how I stored interim Rinex 2 files.

Restored csv outputs to subdaily module. 

## 3.1.1
nmea2snr checks rapid, final, and ultra GNSS orbits from GFZ.

Changed it so that last spline written out by subdaily only includes time
periods with data. Before it was starting at the beginning of first day and ending
at the end of the last day. This didn't cause huge problems when full days were 
analyzed but is definitely wrong otherwise.

## 3.1.0

hourly downloads from NGS allowed (download_rinex using ngs-hourly archive)
At some point the NGS merges the files - but this allows you to follow real time activities

fixed the ultra orbits option to look both day of and day before, as that is how it works
for GFZ

rewrote nmea2snr to use standard python packaging tools

rewrote rinex2snr to use standard python packaging tools. now set up for multi-processor
use.


## 3.0.0

parallel processing for gnssir, makes it much much faster. still testing how
it should be used with the docker.

fixed some places in gnssir where files were being downloaded/created - this has been
moved to gnssir_cl.py so that multiple spawned processes won't overwrite.

## 2.6.0

beta version of multi-processing for gnssir. It is called gnssir2 for now. I will
merge with gnssir after more testing.

## 2.5.4

started experimenting with parallel processing. NOT official yet.

added some features to quickplt , relevant for SNR data. allow specific satellite 
to be shown (if standard SNR file).  removes zeros to make it all more useful.

quickLook will use a very simple refraction correction in quickLook, but only
if the coordinates are in the UNR database. This can be updated by someone to use
the coordinates in the gnssir_input created file - as in nmea2snr - but I am
not going to do that. This is important for VERY tall sites - but mostly irrelevant
otherwise as quickLook is not an operational piece of software - it is for looking!

download_tides puts the request command behind a try so that there is a polite 
error message when it crashes for any reason.

New documentation, various.

## 2.5.3

added RINEX 3 pickups from $REFL_CODE/YYYY/rinex for gzipped crx and rnx files

Store peak2noise in invsnr_input

removed gazillion print statements from invsnr

Changed inputs pktnlim to peak2noise, tempres to dec and snr_ending to snr in invsnr to be consistent with
other codes.  I kept the interior variable names that David Purnell had used.


## 2.5.2

Mostly updating use cases

## 2.5.1

Added important verbiage about not allow python 3.11 for people with
local python installations

Warnings for Rinex 3 conversions using no look

Checked that pypi and docker install works

## 2.5.0

Did some changes to how files (EGM96, station position database) were loaded so that they could be 
more easily installed with the docker. Currently they were being
downloaded from github when they were already available locally in the source code area.
They were not being installed as I thought from the Dockerfile.  

Makan Karegar changed the elevation angle limits in refl_zones

## 2.4.0
Made quickplt faster with large datasets.  I was using numpy append when
i should have used a list and converted at the end.

Fixed a place where I was checking snr existence (twice) in rinex2snr when
I really should not have been.

quickplot allows y-offsets.

added station_pos_2024.db - includes more station coordinates from
nevada reno group.  

## 2.3.0
Fixed bug for SNR files that used non-compliant filenames that
are allowed by nmea2snr.  routine that picks up the SNR file failed
to check for gzipped files for these cases and it should have.
For historical reasons it is called define_and_xz_snr, though now
I am only using gz, not xz.

## 2.2.1

Added wuhan rapid orbit downloads from wuhan (community PR).
Updated gnsssnrbigger.f to allow three days with five minute orbits
This is activated from the wum2 orb flag

checked wum, which was pointing to ULA not ULT, i.e. 

WUM0MGXULT_20240050000_01D_05M_ORB.SP3

not sure if they changed the name or if it was always wrong.  


## 2.2.0

Had problems with docker because I was not using proper version names

## 2.1
Changed sigma on snowdepth to better reflect true errors. Previous 
value was gross overestimate


## 2.0.2

Changed how the Hatanaka code was installed in the docker
Need to follow up with how we use this code in install_exe

New optional DC polynomial elevation angle limits allowed 
for gnssir_input. 

Added some warnings in gnssir for pele and e1/e2 mismatches

## 2.0.1

trying to fix readthedocs formatting

## 2.0.0
January 4, 2024

Added multiyear option to subdaily

Various changes to vwc

Updated quickplt to use proper boolean argument inputs
Added errorbar option

## 1.9.9
December 8, 2023

A fair number of changes in vwc that are related to a new advanced option vwc. But you should not invoke
this advanced option because it does not currently produce vwc.

I now have rinex2snr check to see if you have a compliant file, i.e. you say it is Rinex 2.11 
(because you input a 4 character station name), but inside the code, it is Rinex 3 file. And vice versa,
you say it is Rinex 3, but it is really Rinex 2.11. It now exits.

## 1.9.8
November 26, 2023

utc time offset (in hours) for quickplt.  first version had a mistake (did not set
default for utc_offset to zero as I should have )

minor updates to various plots in subdaily

tried to fix the phase plots in vwc.  

added vwc inputs (soil texture min/max and min number of values per day) 
to the gnssir json file.  see documentation for vwc. added satellite legend information

adding advanced option - in progress.  cannot be used operationally.

## 1.9.7

November 22, 2023

New version of subdaily, datetime on most x-axis plots, removes gaps in the txt file.

## 1.9.6
November 18, 2023

Added highrate (1-sec) GNSS archive from Spain, IGN ES.  RINEX 3 only. 
For this archive, use ignes and make sure to say -rate high -samplerate 1 . 
And -orb gnss because there are very likely to be good multi-GNSS data.

quickplt will let you pick out a particular frequency if you give it is standard LSP
output file where frequency is being written in column 11.

Updated sc02 usecase and notebook install instructions.

Provided more feedback to people using nolook option in rinex2snr. Changed "local directory"
printed to the screen to the actual directory.

Substantially changed plots in subdaily to use datetime instead of day of year.  Ultimately 
all of subdaily should be changed to MJD so as to allow datasets crossing year boundaries.
It also removes gaps from the last spline output plot, but it has not been implemented in the output
txt file as yet (nor in the second to last plot)



## 1.9.5
November 13, 2023

fixed bug(s) in rh_plots, which is not meant for general use. Thank you to Felipe Nievinski for finding this.

cleaned up subdaily, i.e. made sd_libs.py and tried to limit subdaily.py to 
the major pieces of code.  sd_libs.py has the plotting and some of the writing routines.  Eventually
I will try to move the rest of the file writing codes as well.

## 1.9.4
November 9, 2023

Updated Juptyer Notebook information using PR 210

Added Hortho -RH column to the spline fit file created by subdaily.
Will likely rewrite this to be consistent with the output of the in situ tide gauge files
For now it uses the past column definition convention.  This is not useful until someone writes
documentation about what Hortho means in terms of comparing with tide gauges.



## 1.9.3
November 7, 2023

readthedocs appears to be alive again. We are now hardwiring python 3.11 in readthedocs creation 
via the file docs/environment.yml.

Added Hortho to gnssir_input. This is station orthometric height (altitude) in meters. If not provided 
on the command line it is calculated from the given station coordinates (either online
or via the Nevada Reno database) and EGM96.

Hortho is also added to subdaily, and the final spline fit is now plotted using it.

## 1.9.2
November 5, 2023

Trying to chase down a data issue in invsnr. Added more screenstats output.

Made MJD output from ymd an option rather than required in response to user issue.

## 1.9.1
October 29, 2023

SNR files gzipped after use by invsnr. 

SNR files are now gzip compressed after use by nmea2snr.
If you don't want that to happen, there is a flag to turn it off.
A previous version of the code had a flag called compress, and that 
was removed. This was done to make nmea2snr consistent with gnssir
and rinex2snr.

Help added to Docker use for PCs

Version number now written in the LSP results file (see v 1.8.9)


## 1.9.0
October 28,2023

Fixed bug in default peak to nosie ratio limit assumed for invsnr.  Was 4, but when
the calculation of peak to noise was changed, the default limit was left the same.
It is now 2.5, which is better than 4, but one is warned that this is not done the same
as gnssir.  The RH limits mean something different to invsnr than they do to gnssir.


## 1.8.9
October 26, 2023

Tried and failed to add version number to gnssir output (files stored in results directory)
docker would not allow import of importlib. 



## 1.8.8
October 25, 2023

decimation does not seem to be properly working in gnssir.  I have fixed it.

fixed so that the minimum of the polynomial values to remove DC 
is not higher than e1 selected by user in the json analysis instructions


## 1.8.7

Default now is to gzip SNR files upon creation

## 1.8.6

2023 October 9
fixed bug when refraction set to zero (I think?). gnssir would crash

## 1.8.5

2023 October 9

Added a small utility - rinex_coords - that will grep out the a priori coordinates in RINEX file
and print those and the Lat/Lon/Ht to the screen.  

removed p475 as suggested use case for soil moisture


## 1.8.4

Added refraction model number (refr_model) to gnssir_input and thus station analysis json.
on the way to implementing more than one refraction model. Default will remain refr_model = 1.
0 is no model.  All information about the refraction models are in the code for gnssir_input

Double-checked that vwc code is creating a txt output file.  

## 1.8.3
2023 September 26

Remove zero points from SNR traces in window_new.py in gnssir_v2.py

## 1.8.2
2023 September 25
added nmea2snr changes from naoyakadota.  Invalid lines no longer crash the code.

multiple frequencies allowed

https://github.com/kristinemlarson/gnssrefl/pull/194

## 1.8.1
2023 September 20

Added plot changes to subdaily (e.g. allow fontsize choice from command line)

Fixed a weirdness where GNSS files with no SNR data would create a file with
all zeros data.  Which is technically correct, but not terribly friendly.  The 
GPS orbit option exited with a message. Now GNSS files also exit with a message.

changed nyquist to max_resolve_RH so it makes more sense to learners. i.e. this is the max
resolvable RH you can expect for a given station location.

## 1.8.0
2023 September 19

Allow Hatanaka and Hatanaka + unix compressed files (.Z) in the local directory
for the nolook option. Hatanaka files also allowed in $REFL_CODE/YYYY/rinex/ station directory

Write out error message when people inadvertently throw out all data because
they did not take into account that their receiver had an elevation mask and
used e1 that is too small.

## 1.7.3
2023 September 17

rinex2snr SNR file creation fails are written to the log file. And users are told this on the screen. 
This does not seem to be helping people. This version writes the log file's explicit name to the screen

Various docs were hopefully improved.

gzipping the SNR files is now the default when running gnssir. Should save space
and I don't think it will be a huge time sink.  If it is, users can set gzip to False
on the command line.

## 1.7.2 
2023 September 14

leap second file picked up from github repository for pypi and git clone users.  Tim will take care of shipping 
it in the docker

add documentation to nmea2snr


## 1.7.1
2023 September 13

moved leap second file location to REFL_CODE/Files to accommodate docker users

## 1.7.0
2023 September 13

Attempted to add leap second corrections to SNR files created by non-compliant nmea2snr
code.  Added small function to gps.py that installs a leap second file - and reads it.
Returns the hopefully proper offset, which is applied when writing out the timetag in nmea2snr.
Feedback appreciated.

## 1.6.8

added mjd utility

chagned nmea2snr so it allows signals other than L1. this required changing the fortran
code that does the orbits for you. It is a slow module - maybe it always was. something to keep an eye on.

fixed some documentation in download_rinex that misdescribed the stream input as boolean, which it is not.

added tall site use case, ac59

## 1.6.7

Accepted Kelly Enloe PR, mostly Jupyter notebooks stuff

https://github.com/kristinemlarson/gnssrefl/pull/185


## 1.6.6
2023 August 29

accepted two PR

https://github.com/kristinemlarson/gnssrefl/pull/184

https://github.com/kristinemlarson/gnssrefl/pull/183


## 1.6.5
2023 August 28

plots saved in gnssir for docker users

improved documentation

## 1.6.4
2023 August 28

pypi failed last time ... trying again

## 1.6.3
2023 August 28

Added Taylor Smith's changes to nmea2snr. Allows gzip after the translation. 

## 1.6.2
2023 August 25

added option to NOT apply RHdot correction in subdaily.
This would make the code easier to use for lakes and rivers.
It is NOT recommended to use this for tidal regions.

gnssir now requires "new" way of selecting arcs.  newarcs optional cl input has no meaning.

added GPS Tool Box testcase instructions in docs/use_cases

## 1.6.1

2023 August 25

minor changes to documentation

## 1.6.0

Added height above sea level to query_unr

Too many functions were assuming that REFL_CODE/Files existed.  
Too many functions were assuming that REFL_CODE/Files/station existed.


## 1.5.9

2023 August 21

testing why readthedocs versions 1.5.6 , 1.5.7, and 1.5.8 were not created
(thought the latter was in latest)

## 1.5.8

2023 August 20

allow highres_figs in other functions

code now expects earthscope token to be stored in $REFL_CODE


## 1.5.7

2023 August 19

Try try again

## 1.5.6

2023 August 19

Subdaily outputs are written to the extension subdirectory. This allows the user
to test out different strategies without worrying about renaming them, etc.

This build failed based on some advice on how to push the tags at the same time.

## 1.5.5

2023 August 18

fixed bug in gnssir_input when ediff is set.  it was incorrectly thinking it was a 
string, when it is a float.

## 1.5.4.

Added dittmann edits to "homeworks"

## 1.5.3

Updated understanding

## 1.5.2
August 14, 2023

Added IGN for Spain for rinex2snr, RINEX 3 and 30 second only
These data are likely already available from SONEL.
archive is called ignes

Save output from quickplt even if someone doesn't ask for it.

Improve discussion of QC in the understanding section of readthedocs.

## 1.5.1
August 10, 2023

New version

## 1.5.0
August 10, 2023

Updated daily_avg to have three sections.  raw arcs, arcs with QC, daily average with QC.
Updated the discussion page.

## 1.4.9
August 10, 2023

New option on daily_avg that plots the median value and the limits from that 
median value that are used to filter outliers before the daily average is computed.

More documentation about daily_avg has been added online.


## 1.4.8

Another version to get it on pypi
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




