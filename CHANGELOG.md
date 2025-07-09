# Changelog

All notable changes to this project will be documented in this file.
The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## 3.15.2

Changed rinex3_snr to write out logs properly.

## 3.15.1

The nooverwrite option in gnssir was not properly working ... because I had moved the 
compress snr code 

## 3.15.0

Added new directory structure for GFZ rapid and ultra-rapid orbits. old directories were failing.
YOU STILL NEED TO USE orb option gnss to get Beidou. The rapid product does not have it.

I have not changed the final orbits that live in Potsdam - I typically pick up the final GFZ
orbits from CDDIS, which continues to be linked to the orb of gnss.

This impacted rinex2snr, nmea2snr, and rinex3_snr.  If you find places with problems, please post an issue.
I still do not fully understand how/when GFZ made these changes.  It could be that the what I wrote was
correct at the time, but they have migrated to new sites over the years. Since nothing broke, I did not 
notice it. Thanks to Leila Cruz for alerting me to this problem.


## 3.14.0

added "midnite crossing" capability.  -midnite T in gnssir.  Not 100 percent sure i did it the best
way, but it is a start.  All it does is check to see if you have an arc that starts at midnite - 
and if so, it then uses data from the last two hours of the previous day to allow you to get a better
RH. 

found a bug in nicerTime in gps.py that was used to write out UTC time in logs (HH:MM). Mostly it did not
like negative times, which is fine, because why are you using HH:MM anyway?  You should use MJD.  
But the bug was also killing file creation for people that asked for time tags in month, day, 
hours, minutes. So I guess not so many people were using that option!  
(this was because I was writing out the LSP file results - and np.write did not like that that column was a string - it wanted all floats.)

access to standard (default) rapid GFZ orbits is failing as of year 2025, doy 169.  
am changing default from that time stance to orb option gnss.

Pinned earthscope_sdk to an old version as their new version does not include the code we use.
Problem has been reported to earthscope.

## 3.13.0
Fixing a bug in the docker for Windows user.  Used slash twice in a filename???  for EGM96 file.
This doesn't cause a problem on a mac or maybe other machines. But it was found
by someone using Windows and the Docker. And there is no reason to have double slashes.
Also went ahead and installed it for the Docker. Hopefully.

## 3.12.1

I added new plot to subbaily - after large outlier removal (first section), it now makes a 
plot without the outliers. This is written to disk - not displayed to screen. Location 
and name of file is written to the screen.

## 3.12.0

Added new Beidou frequencies. See [issues](https://github.com/kristinemlarson/gnssrefl/issues/342) for more information.

## 3.11.0

Changing unavco URL addresses to earthscope.
The archive option will continue to be unavco.
Per email from Earthscope, this change is strongly encouraged (and for some 
access tools required) as of July 2, 2025.

Allow frequency 307 into quickLook (already allowed in gnssir)

## 3.10.10

Individual subdaily year plots (part 1 of the code) are still created but they are not opened on the screen
anymore. the names of the plots are output to the screen.  The final multi-year plots will continue to be shown on the screen
Why? matplotlib was complaining about having too many figures open.

small bug fixed in subdaily when it could not compute the orthometric height - Hortho. This is a rare occurrence, but
might as well fix it. This is triggered by using a station name for which there is no json (and thus
no lat,lon,ellipsoidal ht).

## 3.10.9

Changed some inconsistencies in subdaily for multi-year processing. rhdot3 plot
was not being created, but now is. And the filenames for the outputs are now consistent
with how they are named for the one year runs. The "last" png file is also named more 
consistently (i.e. year or year_year_end is in the filename).

Fixed vwc_input input for the extension parameter. Code was not finding the file inputs because
the file directory was not properly defined. Not sure about how is owrking downstream (i.e. modules phase
and vwc do not appear to allow the extension parameter). Thank you George Townsend.

Changed behavior for inputs to vwc.py  Command line takes precedence over stored values.

Allow extension input to vwc. If it does not find that extension json it reverts to the non-extension
version. It does not, however, stores results in the extension directory in $REFL_CODE/Files.
That is currently controlled by subdir - but to be consistent, subdir should probably be removed
and extension used instead (for the outputs).

## 3.10.8

While it works locally, I have been having problems making the docker using github actions.
I have recently changed the docker to use python 3.10 instead of 3.9.  To do so I had to 
update the EGM96 code that is used to go from ellipsoidal height to orthometric height.
The EGM96 code used interp2d which is no longer supported by scipy in v 3.10. 

Checked the latest GPS launch, which is documented in gps.py. It is PRN 1 - which 
is already in the l2c and l5 list, so we are good.

## 3.10.7

Fixed bug in check_rinex_file

Added nz archive to Rinex3 30 second list in download_rinex

Made better error messages for nmea2snr, added debug option so you aren't behind
a try.  And parallel processing is segregated.

## 3.10.6
December 3, 2024

I added date1 and date2 as optional inputs to subdaily. These can be used instead of the doy1, doy2,
and year_end inputs. for now both kinds are allowed though I will likely change that at some point.

I added date1 and date2 to daily_avg. You can narrow your use of data.  It set to correct values (i.e. it 
is truly a date in yyyymmdd format), it will override any -year1 and -year2 values.

## 3.10.5


added polyV to gnssir_input (polynomial used in direct signal removal)

added kadaster archive for 1-hz RINEX, Dutch site (kadaster.nl)

## 3.10.4
I somehow managed to delete the samplerate input to rinex2snr.  My Apologies.
It is back in now.

## 3.10.3
The parallel processing code (management of the spawned processes) was 
causing the code to crash when calling
rinex2snr or gnssir within a python function. I don't know enough to fix it - 
but I did segregate it so that people that don't want parallel processing
can still directly access the code within rinex2snr_cl and gnssir_cl.
I did not fix nmea2snr_cl, so I think that has to be fixed if people want
to run nmea2snr_cl within a python function.

## 3.10.2

I fixed a bug in rinex2snr inputs read from the json. It was ignoring
command line requests (such as samplerate, orb, archive).

## 3.10.1

added archive and orb to the gnssir_input json. These are to be used in rinex2snr - mostly
useful for people (like me) that forget what command line options I want to use.
Other things you can save are mostly for RINEX 3 (e.g. stream parameter, samplerate). snr and dec values can also be 
set if you are doing something non-standard (i.e. not using snr file 66 and not decimating).  

Default for rinex3 files is now explicitly set to cddis. This is different than for RINEX 2.11 files where
the default is all, which now cycles thru unavco and sopac. It used to use sonel, but I don't think
many people use sonel. And if they want to use sonel, of course they can do so by specifying sonel.

Trying to make a log file for rinex2snr so that you are not overwhelmed with messages
to the screen.  rinex3_rinex2 had to be changed to allow log input.  and file needed to be 
created in run_rinex2snr.

I added a debug option to rinex2snr so you could see what is going wrong without using
the task queues.



## 3.10.0

Making new pypi version with python 3.9 just to be sure we are all on the same page.

## 3.9.0

**Python 3.9 is now required.**

## 3.8.1

screenstats is always True now - but output goes to a file.
The file location is printed to the screen.
If this causes funny print statements please let me know.


Added RINEX 3 files for the nz archive. Minimal testing.

## 3.8.0

Changed our build to meson. This will now accommodate python >= 3.11.
It also eliminates the setup tool deprecation. 

Why we did this: https://numpy.org/doc/stable/reference/distutils_status_migration.html

Remove package stored version of station_pos.db. This has been replaced by station_pos_2024.db
And it will no longer download this file if you use unr_database function.  

## 3.7.0
I have been trying to make a way to save frequently used settings in rinex2snr and gnssir,
especially the snr ending, and to a lesser extent, the samplerate. 
I do not want to make a brand new file, so I have added them to them gnssir json
(created by gnssir_input). So if you are going to be downloading and translating RINEX 3 
files regularly, you should consider this. The relevant settings are in the gnssir_input documentation
(samplerate, stream, dec, and snr). I would not set snr unless you are using the non-default
values (88 or 50 are the most common). 

When you analyze data from a lot of different sites, you might have set up scripts that
save all this information. I no longer do this - so I do like to save the information so 
I don't have to remember if it is R or S (for streaming), or samplerate, or whether a site
should be decimated. It does not save the archive name or the nine character station name, which
are also useful bits of information when running rinex2snr. Someone else feel 
free to add these to gnssir_input.py and rinex2snr.

If you are going to do this it does mean the json needs to be created before using rinex2snr.
And that is a bit illogical. But if you are a frequent user, you will alreayd have a json and 
it will save you time. And it should not complain if it cannot find the json.

## 3.6.8

Added snr input to gnssir_input.  If you have non-default SNR files (i.e. not 66), then
you can set that and not have to type it in the command line.

Added a few info messages in quickLook explaining why station coordinates are not needed
(though they are helpful). Also check that azim1 is < azim2.

Fixed a very stupid bug in conv2snr that was looking for RINEX files even though
they already existed (as nolook option was set and the file was found). Optional
filename now sent to conv2snr to make sure this choice is not made.

## 3.6.7

added savearcs_format option - allows pickle format which has more information 
than plain txt version. See gnssir for more information.

removed bug in reading local coordinate file.  it failed when there was only a 
single station in the file. it should now work though you can't disobey the format.
you have to have four entries per line: station, lat, lon, ht. Comment lines must
have a % at the beginning.

## 3.6.6

added debug option to remove the try in gnssir_cl.py - because that 
makes it really hard to know why your run is crashing. If you set debug to
T, you will  have more information.

optional savearcs option to gnssir: writeout plain text files of 
elevation angle and detrended snr 
using savearcs option. This is bare bones ... not really ready for prime time

fixed bug in daily_avg for people that try to analyze sites with no results. it now  
politely exits for this case.

added peak 2 noise to subdaily summary plot

added gnssir output that tells you to use the (new) debug option in error situations.

exits when people try to use illegal refraction models in gnssir_input

added warning for people that don't input legal elevation angle lists to gnssir_input

added documentation for quickplt so people can look at raw SNR data.

added subdaily option to allow different required amplitude values for different frequencies.
It uses frequency list in the json to set the order of those amplitudes.  


## 3.6.5

July 29, 2024

Various minor changes.

Updated nmea2snr ultra orbit choices : first tries GFZ and then Wuhan (wum2)

Felipe Nievinski improved how the NMEA files are accessed in nmea2snr.
Uses a temporary file location which is deleted after use.

## 3.6.4

July 22, 2024

I added a final plot to subdaily. Doesn't have the spline in it.  Uses a line instead 
of a symbol. But otherwise it isn't new information.

I added a simple file for a priori lat lon and ellipsoidal height values. 
It should be located in $REFL_CODE/llh_local.txt. and the values should simply
be 4 ch station name lat lon height. NO COMMAS between then,  simply spaces.
comment lines are allowed if preceded by percent sign. I would prefer station names to be 
lowercase, but it allows and checks uppercase.
This kind of file would be particularly useful for NMEA people as it allows you to 
store your a priori receiver coordinates and don't have to worry about it being 
overwritten if you change your analysis strategy.

## 3.6.3
July 19, 2024

added option in rinex3_snr to correct illegal filenames that Earthscope is distributing
to the world. it assumes they used rinex 2.11 filename but filled it with Rinex 3 data.
and used upper case instead of lower case.

Am trying to add version number to print out to all major codes in gnssrefl.

## 3.6.2

July 17, 2024

There was a bug in the RINEX3 to RINEX2 conversion code.
This should be fixed - and the code is less silly now.  I think.
Thanks to Drew Lindow for finding this bug.

deleted gnssrefl/data/gpt_1wA.pickle. I do not think it is used.

## 3.6.1 

Versions 3.6.0 and 3.6.1 are about the same.  I had some issues with the version tags.

July 15, 2024

Daily Lomb Scargle results are sorted in time instead of frequency.

Fixed bug in rinex3_snr (inputs changed)

You can access 1-sec RINEX3 GNET archive data if you have 
an account and the utility lftp installed.

Allow snr choice to be stored in the gnssir_input json. For now you have 
to add it to the json by
hand, but I am happy to accept a PR that adds it explicitly. If 
you do that, you want to make sure that the downstream code (gnssir) can 
still change the snr choice on the command line. Right now it assumes
if it finds a snr value in the json, it should use it.

## 3.5.10

added new Wuhan (wum2) near real time orbits. Triggered from year 2024 and doy 187

added hourly NGS - useful for near real time users. 

I think both rinex2snr and download_rinex now make the sensible decision that
samplerate of 1 should mean rate=high whether you have selected it or not.
rate=high has to do with the folder name, and that varies by archive. 

I attempted to fix issues in subdaily having to do with gaps at beginning/end of series,
and also splinefits for data all on one year and multi-year.  In adding the latter, I had
treated the two cases separately, as the spilne was done on time units of day of year.
Now both cases are done with MJD, which is far easier and consistent.

## 3.5.9

July 5, 2024

You can input a frequency list for gnssir that overrides the json values stored via gnssir_input.
However, you can only have one request for minimum spectral amplitude on the command line.  if you want more
control, you need to use the  extension option. 

The gnssrefl version number if printed out when you run gnssir, rinex2snr, quickLook.
if you want to add it to other functions, submit a PR.

logfile of the gnssir screen stats is written to a file. The File location is written to screen. 
Default goes to $REFL_CODE/logs/ssss/yyyy 

## 3.5.8
At request for Felipe Nevinski, I am having the ultra orbit option in nmea2snr check for three different files.
I am skeptical ... but I could be wrong.

## 3.5.7

small issue with bkg high rate downloads. now fixed.

## 3.5.6

June 28, 2024

Changed default high-rate BKG behavior to wget.download as using requests
seems to be unhappy with many of the downloads - at least using my internet connection.
Adding a timeout did not alleviate the problem. 

Final spline output in subdaily was correct, but did not start at a sensible
value (i.e. it put out values at seconds 29 and 59 instead of 0 and 30). This
also depended on whether you did one year or two years of analysis.  I believe
this has been fixed.

## 3.5.5

Oops - introduced a bug for ultra orbit use in rinex2snr.  This should be 
fixed now. If you would like to select an ultrarapid orbit file at hours other than zero,
please submit a PR.

Added clearer error messages for people that try to use RINEX files without
SNR data in them. Hopefully

## 3.5.4

nmea2snr ultra/wum2 orb option tries to use the expected ultra rapid file and if it fails
to find it, tries to download the previous day at hour noon.

## 3.5.3

2024 Jun 17

Added more options for nmea2snr in terms of orbit choices. If you specify ultra or 
wum2, you can also use a specific hour for the ultrarapid orbit. GFZ (ultra) only
has hour solutions every three hours.  it appears that wum2 is every hour. If you say

If no orbit is selected, it will use the previous behavior, which tries a variety of different choices.
download_orbits also updated to be consistent.

## 3.5.2

2024 Jun 16

Fixed bug in nmea2snr that used old directories for (rapid?) gfz orbits.
Updated the wuhan orbit source so that it correctly translates a multi-day SP3 file.
Previously it was set to only allow one day sp3 file, depending on sampling rate. 
The same problem was most likely impacting the GFZ orbits as well. Not sure.


It no longer looks for final GFZ GNSS files after doy 153/year 2024 as that 
would require my writing a new function to access GFZ final orbit directories.  
This is unlikely to be a huge problem for chipsets - and the Wuhan orbits are 
perfectly good for this purpose and include all four systems. The GFZ rapids 
have historically not had Beidou in them.

## 3.5.1

... Had to change the source of the ultra rapid orbits from GFZ ... 
Also, had to change it so it uses the ultras from day before ... since it is a 
two day product ... 

This was added to download_orbits, rinex2snr and nmea2snr (and the library in gps.py).

## 3.5.0

Tried to implement parallel processing for NMEA files.  Let me know if it doesn't seem
to work.

## 3.4.0

June 5, 2024 

fixed pretty major problem with default (rapid) orbits.  updated to new file names and 
locations for GFZ analysis center.  I do not know when the old naming conventions will fail for ultra.

also added Wuhan ultra rapid orbit downloads from Wuhan to download_orbits.
It was previously added to rinex2snr 

Changed spline output file in subdaily so that you can print out 999 at the gap values
(times during large gaps were previously not written out at all).  per request, I also
told people the time tags are in UTC in the file header. this is currently on the command line
as gap_flag = T for putting in the gap flag.

## 3.3.1
rinex2snr: Added BKG access to high-rate files that are more than 6 months old.
This will allow parallel processing, though CDDIS does not (this is a restriction
at CDDIS, not because of gnssrefl).

Fixed bug in rinex3_snr (inputs had changed in run_rinex2snr)

Fixed download_rinex for highrate files from BKG and CDDIS so that it allows
both old and current datastreams

subdaily fails at the final spline that it writes out at even samples in cases where
there are no points at the end of hte final day (?), i.e. the record ends at hour 20
but it is trying to extrapolate to hour 24. To make my life easier I am simply using
the bandaid approach of using a try/except.  

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

May 8, 2024 

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




