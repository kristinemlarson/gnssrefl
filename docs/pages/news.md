# News 

## 2023 News

<code>nmea2snr</code> has been updated to support multi-frequency-GNSS by community member Taylor Smith.


Specific azimuth regions can now be added at the command line. Use -azlist in <code>make_json_input</code>

There is a new Google Earth utility for reflection zones: [refl_zones](docs/pages/utilities.md)

December 1, 2022

Fixed a bug in the new subdaily output file, (IF).  If you are using subdaily and want
to use the interfrequency bias correction file created at the end, you need to download
this version.

November 8, 2022

I fixed a bug in the download_ioc and download_noaa scripts. I had somehow failed to import the subprocess
library - so output directories were not being made if needed.

**WARNING: CDDIS has changed their high-rate directory protocol for older files. This means some 
of our download codes now fail.
If someone wants to provide a pull request that addresses this issue, I 
would be happy to implement it.**

Please note: <code>rinex2snr</code> and <code>download_rinex</code> have been substantially changed. Please
let me know if I broke anything.

Command line inputs which previously required True also now work with T and true.

You can now gzip your snr files (in addition to xz compression).

Our docker (and thus jupyter notebooks) now works with the new Mac chip. I have also updated
installexe for the new chip - but I have not yet changed the pypi version.

**New utility for subdaily analysis:** [invsnr](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/README_invsnr.md). 
This is currently only available for the command line version on github.

A new UNR database has been created/updated - it can be used to provide precise lat/long/ht a priori coordinates 
in <code>make_json_input</code> if you have a station that is recognized by UNR.

If you are being blocked by CDDIS (currently used for downloading almost
all multi-GNSS orbit files), you can try the <code>-orb gnss2</code> option 
in either the <code>download_orbit</code> 
or <code>rinex2snr</code>. It retrieves multi-GNSS files for GFZ from IGN instead of CDDIS.

Access to ultrarapid multi-GNSS (and thus real-time) orbits is now available 
via the [GFZ](https://www.gfz-potsdam.de/en/section/space-geodetic-techniques/topics/gnss-services/). 
Please use the -ultra flag in [<code>rinex2snr</code>](#module1).

If you have orbit files you would like to use and they follow the naming conventions used 
by <code>gnssrefl</code>, you can use them. You need to store them in 
the proper place ($ORBITS/yyyy/nav for nav messages and $ORBITS/yyyy/sp3 for sp3 files).

Access to GSI RINEX data has been provided Naoya Kadota. [An account from GSI is required.](https://www.gsi.go.jp/ENGLISH/geonet_english.html)
In my experience GSI is very responsive to account requests.  

A bug was fixed in the old python translator option for S6/S7 data. Thank you to Andrea Gatti for this information.

Thanks to Makan Karegar the NMEA file format is now supported. See [<code>nmea2snr</code>](#module4).

As they are announced, I am trying to update dependencies for various archives, 
as the GNSS world moves from Z compression to gzip and anonymous ftp to https. 
I recently fixed ngs, bkg, unavco, and nz archives. Bug fixes have been moved to the Bug section.

I encourage you to read [Roesler and Larson, 2018](https://link.springer.com/article/10.1007/s10291-018-0744-8). 
Although this article was originally written to accompany Matlab scripts, 
the principles are the same. It explains to you what a reflection
zone means and what a Nyquist frequency is for GNSS reflections. 
My reflection zone webapp will [help you pick appropriate elevation and azimuth angles.](https://gnss-reflections.org/rzones)
If you click the box, the same web app will also compute the Nyquist for L1,L2, and L5.

If you are interested in measuring sea level, this 
webapp tells you [how high your site is above sea level.](https://gnss-reflections.org/geoid)  



## Bugs/Features <a name="bugs"></a>

Bug Diary

**October 26, 2021** Fixed bug in the rinex2snr code for the python translator. It was mixing up
S6 and S7 - or something like that. Subdaily now exits when there are data gaps.  

**fixed query_unr input files and -rate high archive choices.**

**September 15, 2021** There was a screen output about missing fortran translators that 
was a bug. The hybrid translator is the default and you should not be getting warnings 
about missing fortran translators.

**August 28, 2021** Fixed NGS archive accessibility. Also, switched UNAVCO, BKG, NZ Geonet to https.

**June 14,2021** Fixed bug in nolook option.  Fixed rinex2snr conversion for RINEX 3/nav orbits.

**June 1, 2021** Added esa orbits 

**April 17, 2021** New plot added to quickLook. This should provide feedback to the user on which QC 
metrics to use and which azimuths are valid. New plot also added to daily_avg.

**March 30, 2021** Hopefully bug fixed related to the refraction file (gpt_1wA.pickle). If it is missing from your build,
it is now downloaded for you. Apologies. 

**March 29, 2021** The L2C and L5 options now use (appropriate) time-dependent lists of satellites. 

**March 17, 2021** I have removed CDDIS from the default RINEX 2.11 archive search list. It is still useable if you use 
-archive cddis.

**March 14, 2021** Minor changes - filenames using the hybrid option are allowed to be 132 characters long.
This might address issue with people that want to have very very very long path names.
I also added the decimation feature so it works for both GPS and GNSS.

**February 24, 2021** We now have three translation options for RINEX files: fortran, hybrid, and python. The last of these
is ok for 30 sec data but really too slow otherwise. Hybrid binds the python to my (fast) fortran code.
This has now been implemented for both GPS and multi-GNSS.

CDDIS is an important GNSS data archive. Because of the way that CDDIS has 
implemented security restrictions, we have had to change our download access. 
For this reason we strongly urge that you install **wget** on your machine and that 
it live in your path. You will only have very limited analysis abilities without it.

I have added more defaults so you don't have to make so many decisions. The defaults are that  
you are using GPS receiver (not GNSS) and have a fairly standard geodetic 
site (i.e. not super tall, < 5 meters). If you have previously used this package, please
note these changes to **rinex2snr**, **quickLook**, and **gnssir**.
Optional commandline inputs are still allowed.

I have been using <code>teqc</code> to reduce the number of observables and to decimate. I have removed the former 
because it unfortunately- by default - removes Beidou observations in Rinex 2.11 files. If you request decimation 
and fortran is set to True, unfortunately this will still occur. I am working on removing my 
code's dependence on <code>teqc</code>.

No phase center offsets have been applied to reflector heights. While these values are relatively small for RH < 5 m,
we do plan to remove them in subsequent versions of the code. 

At least one agency (JAXA) writes out 9999 values for unhealthy satellites. I should remove these satellites 
at the <code>rinex2snr</code> level, but currently (I believe) the code simply removes the satellites because the elevation
angles are all very negative (-51). JAXA also has an incomplete number of GPS satellites in its sp3 files (removing 
the newer ones). It is unfortunate, but I cannot do anything about this.

