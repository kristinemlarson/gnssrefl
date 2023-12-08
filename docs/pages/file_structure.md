# Files, Formats, Frequencies

## Environment Variables

You need three environment variables to run 
this code: REFL_CODE, ORBITS, and EXE. If you are using 
the jupyter notebooks or the docker, they are defined for you. 

If you are working with pypi or github clone install, you must define them EVERY TIME YOU USE THE CODE.
This is most easily done by setting them in your setup script, which on my machine is called .bashrc.

If you are working with the docker, these should all be set up for you. But knowing that they 
exist can be helpful in looking for files, etc.

## How do I analyze my own data?

We do not have instructions within this software package for how you can operate your own receiver 
for GNSS-IR. Currently we need you to save your observation data as Rinex 2.11, Rinex 3, or 
NMEA formats (see below). At a minimum you **must** save the SNR data; we strongly urge you to track/save GPS L2C and L5.

The naming conventions for GNSS observation files that we expect are given below. If you are working with the 
docker, I have made some notes in the [docker install section](docker_cl_instructions.md) 
that might be helpful to you about where to store your files.

If you are working with git clone or pypi install, you should be able to have the RINEX files 
in the directory you are currently working in. Or you should put them in the rinex directory as defined 
below in the *Where Files are Stored* section. Examples are given 
in the [rinex2snr code](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html).
Documentation can always be improved, so if you would like to add more examples or find the 
current documentation confusing, please submit a pull request.

If you are using the notebooks, there is currently no notebook for this option.
Please contact Kelly.Enloe@earthscope.org for guidance.

If you have questions about converting NMEA files, the best I can offer is that you read
the next section on that specific format.

Many file conversion programs produce orbit files as well as observation files. These orbit files
are unnecessary in this software package. The code is set up to find the appropriate orbit files for you.


## GPS/GNSS Observation Data Formats

Please keep in mind that there are multiple issues here:

- Are your observation files stored in what gnssrefl considers to be a compliant format?

- Are your observation files properly named?  

- Are your observation files stored where the code expects to find them?

- Do your observation files include the data we need for GNSS-IR (the SNR observables)

- Did you compress you file in some way - and does gnssrefl recognize this kind of compression?
(Hatanaka, gzip, Z, etc etc)

Unfortunately all of these issues come into play, and it can be confusing 
to figure out where the problem is. We have tried as best we can to make screen
output that will help you with your problem.

Input observation formats: the code only 
recognizes [RINEX 2.11](https://www.ngs.noaa.gov/CORS/RINEX211.txt), 
[RINEX 3](https://files.igs.org/pub/data/format/rinex303.pdf) 
and [NMEA](https://www.gpsworld.com/what-exactly-is-gps-nmea-data/) input files.

**RINEX 2.11**

*We strongly prefer that you use lower case filenames.* I cannot promise you 
that the code will find files that are stored in uppercase. Lowercase filenames are the standard at global archives.
They must have SNR data in them (S1, S2, etc) and have the receiver coordinates in the header.
The files should follow these naming rules:

- all lowercase
- station name (4 characters) followed by day of year (3 characters) then 0.yyo where yy is the two character year.
- Example: algo0500.21o where station name is algo on day of year 50 from the year 2021

Example filename : onsa0500.22o

It is also standard to use the Hatanaka files. 

Example filename : onsa0500.22d

We also generally allow two kinds of compression, unix compression and gzip:

Unix compression example filename : onsa0500.22d.Z

gzip example filename : onsa0500.22o.gz

We do not make any effort to find files with the zip ending. If your files have this ending,
you must unzip them before running gnssrefl.


**RINEX 3**

While we support RINEX 3 files, we do not read the RINEX 3 
file itself - we rely on the <code>gfzrnx</code> 
utility developed by Thomas Nischan at GFZ to translate from RINEX 3+ to RINEX 2.11
If you have RINEX 3 files, they should be all upper case (except for the extension rnx or crx).

Example filename: ONSA00SWE_R_20213050000_01D_30S_MO.rnx

* station name (9 characters where the last 3 characters are the country), underscore
* capital R or capital S , with underscore on either side
* four character year
* three character day of year
* four zeroes, underscore,
* 01D, underscore
* ssS, underscore, M0.
* followed by rnx (crx if it is Hatanaka format). Note: these are lowercase

01D means it is one day. Some of the other parts of the very 
long station file name are no
doubt useful, but they are not recognized by this code. By 
convention, these files may be
gzipped but not unix compressed. If you want a 
generic translation program, you can try <code>rinex3_rinex2</code>.
It has the requirement that you input the input and output file names.

For a few archives, we allow 1 sample per second files. Following the protocol of the 
IGS, these files are unfortunately 15 minutes long, which means you have to download
96 of them. UNAVCO/Earthscope is much friendlier about providing 1 sample per second files,
and returns a single file, at least for RINEX 2.11.  

If you want the code to be able to find those highrate files, you must tell the code you 
want to use the -rate high files and provide -samplerate 1. Why two inputs?  Because the 
-rate high option tells the code to look in a particular folder. The samplerate is related
to the name of the file itself.  

Please see the rinex2snr documentation page for more examples.


**NMEA**

NMEA formats can be translated to SNR using <code>nmea2snr</code>.
Inputs are similar to <code>rinex2snr</code>: 4char station name, year, and day of year
NMEA files are assumed to be stored as:

$REFL_CODE + /nmea/ABCD/2021/ABCD0030.21.A

for station ABCD in year 2021 and day of year 3.

NMEA files may be gzipped.

Additional information about nmea2snr [is in the code.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.nmea2snr_cl.html)

**ORBITS**

We have tried our best to make the orbit files relatively invisible to users.
But for the sake of completeness, we are either using broadcast navigation files in the RINEX 2.11 format
or precise orbits in the sp3 format.   

**EXECUTABLES**

There are two key executables: CRX2RNX and gfzrnx. For notebook and docker users, these 
are installed for you.  pypi/github users must install them. The utility <code>installexe</code>
should take care of this. They are stored in the directory defined by the EXE environment variable.

## Where Files are Stored


File structure for station abcd in the year YYYY (last two characters YY), doy DDD:

- REFL_CODE/input/abcd.json - instructions for gnssir analysis, refraction files

- REFL_CODE/YYYY/snr/abcd/abcdDDD0.YY.snr66  - SNR files 

- REFL_CODE/YYYY/rinex/abcd/  - RINEX files can be stored here

- REFL_CODE/YYYY/results/abcd/DDD.txt  Lomb Scargle analysis goes here

- REFL_CODE/YYYY/phase/abcd/DDD.txt  phase analysis 

- REFL_CODE/Files/ - various output files and plots will be placed here

- ORBITS/YYYY/nav/autoDDD0.YYn - GPS broadcast orbit file 

- ORBITS/YYYY/sp3/ - sp3 files of orbits - these use names from the archives.

RINEX files downloaded from archives are not stored by this code. In fact, quite the opposite. If they are being translated, 
they are deleted. Do not keep your only copy of RINEX files in your default directory.

You do not need precise orbits to do GNSS-IR. We only use them as a convenience.
Generally we use multi-GNSS sp3 files. See the <code>rinex2snr</code> documentation for more details on 
the orbits you can use. 

Some of the utilities and environmental products code store files in REFL_CODE/Files
The locations of these files are always provided in the screen output.

The inputs to <code>gnssir</code> are generally stored in the REFL_CODE/input folder.
This primarily means the Lomb Scargle data analysis inputs, i.e. 
the "json" files, e.g. p041.json for station p041.
It also includes the refraction file (p041_refr.txt) that is 
created automatically. This calculation 
requires a set of parameters stored in a "pickle" format, gpt_1wA.pickle. 
This file should be automatically stored for you.

## The SNR data format

**Reminder:** UTC does not exist in our world. Everything should be GPS time, which is
UTC without leap seconds. 

The snr options are mostly based on the need to remove the "direct" signal. This is
not related to a specific site mask and that is why the most frequently used
options (99 and 66) have a maximum elevation angle of 30 degrees. The
azimuth-specific mask is decided later when you run **gnssir**.  The SNR choices are:

- 66 is elevation angles less than 30 degrees (**this is the default**)
- 99 is elevation angles of 5-30 degrees
- 88 is all data
- 50 is elevation angles less than 10 degrees (good for very tall sites, high-rate applications)

66,99, etc are not good names for files. And for this I apologize. It is too late to change them now.

The columns in the SNR data are defined as:

- Satellite number (remember 100 is added for Glonass, 200 for Galileo etc)
- Elevation angle, degrees
- Azimuth angle, degrees
- **Seconds of the day, GPS time**
- elevation angle rate of change, degrees/sec.
-  S6 SNR on L6
-  S1 SNR on L1
-  S2 SNR on L2
-  S5 SNR on L5
-  S7 SNR on L7
-  S8 SNR on L8

The unit for all SNR data is dB-Hz.

## GNSS frequencies

- 1,2,20, and 5 are GPS L1, L2, L2C, and L5 

- 101,102 are Glonass L1 and L2

- 201, 205, 206, 207, 208: Galileo frequencies, which are
set as 1575.420, 1176.450, 1278.70, 1207.140, 1191.795 MHz

- 302, 306, 307 : Beidou frequencies, defined as 1561.098, 1207.14, 1268.52 MHz


## Additional files

- EGM96geoidDATA.mat is stored in REFL_CODE/Files
- station_pos.db is stored in REFL_CODE/Files. This is a compilation of station coordinates from Nevada Reno.
- gpt_1wA.pickle is stored in REFL_CODE/input. This file is used in the refraction correction.

## Some comments about signals

### GPS L2C

Why do I like L2C? What's not to like? It is a modern **civilian** code without high chipping rate.
That civilian part matters because it means the receiver knows the code and thus
retrievals are far better than a receiver having to do extra processing to 
extract the signal. Here is an example of a receiver that is tracking **both** L2P and L2C.
Originally installed for the Plate Boundary Observatory, it is a Trimble. The archive 
(unavco) chose to provide only L2P in the 15 second default RINEX file.
However, it does have the L2C data in the 1 second files. So that is how I am able to make 
this comparison.  P038 is a very very very flat site.

Here are the L2P retrievals:

<img src="../_static/p038usingL2P.png" width="600">

Now look at the L2C retrievals.

<img src="../_static/p038usingL2c.png" width="600">

If you were trying to find a periodic signal, which one 
would you want to use?

To further confuse things, when the receiver was updated to a Septentrio, unavco began
providing L2C data in the default 15 second files. This is a good thing - but it is confusing
to people that won't know why the signal quality improved over night.

### GPS L5

Another great signal.  I love it. It does have a high chipping rate, which is 
relevant (i.e. bad) for reflectomtry from very tall sites.

### Aliasing

While it will show up in GPS results too - there seems to be a particularly
bad problem with Glonass L1.  I used an example from Thule. The RH is significant -
~20 meters. So you absolutely have to have at least 15 sec at the site or you violate
the Nyquist. Personally I prefer to use 5 sec - which means I have to download
1 sec and decimate. This is extremely annoying because of how long it takes to 
ftp those files to my local machine. Let's look at L1 solutions using a 5 second file - 
but where I invoke the -dec option for gnssir. That way I can see the impact of the sampling.
I also using the -plt T option. 

This is 5 second GPS L1.

<img src="../_static/thule_l1.png" width="600"/>

This is 15 second GPS L1. You see some funny stuff at 30 meters, and yes, the periodograms
are noisier. But nothing insane.

<img src="../_static/thule_l1_15sec.png" width="600"/>

Now do 5 second Glonass L1

<img src="../_static/not_aliased_101.png" width="600"/>


Contrast with the Glonass L1 results using 15 sec decimation!
So yeah, aliasing is a problem.

<img src="../_static/aliased_101.png" width="600"/>


### E5

Now about RINEX L8 ... also known as E5. This is one of 
the new Galileo signals. Despite the fact that it is near
the frequencies of the other L5 signals, it is **not** the 
same. You can see that 
it in the multipath envelope work of Simsky et al. shown below.

<img src="../_static/multipath-envelope.png" width="600"/>

Most of you will not be familiar with multipath envelopes - 
but for our purposes, we want those envelopes to be big - cause
more multipath, better GNSS-IR. First thing, multipath delay 
shown on the x-axis is NOT the reflector height (RH).  it is 
2*RH*sin(elevation angle). So even a pretty tall RH will not 
be obstructed by the new Galileo codes except for E5.


This is E5a

<img src="../_static/at01_358_205.png" width="600"/>

This is E5. Note that instead of nice clean peaks, it is 
spread out. You can also see that the E5 retrievals degrades as elevation angle increases,
which is exactly what you would expect with the multipath delay 
increasing with elevation angle. I would just recommend only using
this signal for RH < 5 meters. And even then, if you are tracking
L8, you probably also have L5, L6, and L7, so there is not a ton gained 
by also using L8.

<img src="../_static/at01_358_208.png" width="600"/>


###  What about L1C?

I would be happy to host some results from L1C - please submit a pull request 
with the needed figures and a description of what you are comparing. I imagine
this would require making two snr files - one with L1C and one with L1 C/A. 
And using only the small subset of satellites that transmit L1C.
From what I have seen, it is not much better than L1 C/A - which surprisees me.
But I have to imagine it is receiver dependent (some receivers have terrible C/A SNR).  

<HR>

The multipath envelope figure is taken from:

Title: Experimental Results for the Multipath Performance of Galileo 
Signals Transmitted by GIOVE-A Satellite

Authors: Andrew Simsky,David Mertens,Jean-Marie Sleewaegen,
Martin Hollreiser, and Massimo Crisci

International Journal of Navigation and Observation 
Volume 2008, DOI 10.1155/2008/416380

