# gnssrefl

This package is a new version of my GNSS interferometric reflectometry (GNSS_IR) code. 

The main difference bewteen this version and previous versions is that I am
attempting to use proper python packaging rules, LOL. I have separated out the main
parts of the code and the command line inputs so that you can use the gnssrefl libraries
yourself or do it all from the command line. This should also - hopefully - make
it easier for the production of Jupyter notebooks. The latter are to be developed
by UNAVCO with NASA funding.

# For those of you who don't like reading documentation

I recommend you use the web app [I developed](https://gnss-reflections.org). It 
can show you how the technique works without installing any code. It also picks up 
the data for you and provides results in less than 10 seconds. 


# Overview Comments

The goal of this python repository is to help you compute (and evaluate) GNSS-based
reflectometry parameters using geodetic data. This method is often
called GNSS-IR, or GNSS Interferometric Reflectometry. There are three main codes:


* **rinex2snr** translates RINEX files into SNR files needed for analysis.

* **gnssir** computes reflector heights (RH) from GNSS data.

* **quickLook** gives you a quick (visual) assessment of a file without dealing
with the details associated with **gnssir**.

There is also a RINEX download script **download_rinex**, but it is not required.

# Environment Variables 

You should define three environment variables:

* EXE = where various RINEX executables will live.

* ORBITS = where the GPS/GNSS orbits will be stored. They will be listed under directories by 
year and sp3 or nav depending on the orbit format.

* REFL_CODE = where the reflection code inputs (SNR files and instructions) and outputs (RH)
will be stored (see below). Both SNR files and results will be saved here in year subdirectories.

However, if you do not do this, the code will assume your local working directory (where you installed
the code) is where you want everything to be. The orbits, SNR files, and periodogram results are stored in 
directories in year, followed by type, i.e. snr, results, sp3, nav, and then by station name.

# Python

If you are using the version from gitHub:

* make a directory, cd into that directory, set up a virtual environment, a la python3 -m venv env, activate it
* git clone https://github.com/kristinemlarson/gnssrefl 
* pip install .

If you use the PyPi version:  

* make a directory, cd into that directory, set up a virtual environment, activate it
* pip install gnssrefl


# Non-Python Code 

All executables should be stored in the EXE directory.  If you do not define EXE, it will look for them in your 
local working directory.  The Fortran translators are much faster than using python. But if 
you don't want to use them,
they are optional, that's fine. FYI, the python version is slow 
not because of the RINEX - it is because you need to calculate
a crude model for satellite coordinates in this code. And that takes cpu time....

* **Required** translator for compressed RINEX files. CRX2RNX, http://terras.gsi.go.jp/ja/crx2rnx.html

* Optional Fortran RINEX Translator for GPS, the executable must be called gpsSNR.e, https://github.com/kristinemlarson/gpsonlySNR

* Optional Fortran RINEX translator for multi-GNSS, the executable must be called gnssSNR.e, https://github.com/kristinemlarson/gnssSNR

* Optional datatool, teqc, is highly recommended.  There is a list of static executables at the
bottom of [this page](http://www.unavco.org/software/data-processing/teqc/teqc.html)

* Optional datatool, gfzrnx is required if you plan to use the RINEX 3 option. Executables available from the GFZ,
http://dx.doi.org/10.5880/GFZ.1.1.2016.002


# rinex2snr - making SNR files from RINEX files

I run a lowercase shop. Please name RINEX files accordingly and use lowercase station names. It also means 
that the filename must be N characters long (ssssddd0.yyo), where ssss is station name, ddd is day of year, and yy is
two character year. If you have installed the CRX2RNX code, you can also provide a compressed RINEX format file, 
which means your file must be called ssssddd0.yyd.  I think my code allows gz or Z as compression types.

A RINEX file has extraneous information in it (the data used for positioning) - and does not provide some of the 
information needed (elevation and azimuth angles) for reflectometry. The first task you 
have is to translate a data file from RINEX into what I will call a SNR format - and to calculate those geometric angles.  
For the latter you will need an orbit file. If you tell it which kind of orbit file you want, the code will go get it for you.  
Secondly, you will need to decide how much of the data file you want to save. If you are new
to the systems, I would choose **option 99**, which is all data between elevation angles of 5 and 30 degrees.

The command line driver is **rinex2snr**. You need to tell the program the name of the station,
the year and doy of year, your orbit file preference, and your SNR format type.
A sample call for a station called p041, restricted to GPS satellites, on day of year 132 and year 2020 would be:

*rinex2snr p041 2020 132 99 nav*

If the RINEX file for p041 is in your local directory, it will translate it.  If not, 
it will check four archives (unavco, sopac, cddis, and sonel) to find it. 
I will also search ga (geoscience Australia), nz (New Zealand), ngs, and bkg if you invoke -archive,
e.g.

*rinex2snr tgho 2020 132 99 nav -archive nz*

What if you want to run the code for all the data for a given year?  

*rinex2snr tgho 2019 1 99 nav -archive nz -doy_end 365* 
 
If your station name has 9 characters, the code assumes you are looking for a 
RINEX 3 file. However, it will store the SNR data using the normal
4 character name. This requires you install the gfzrnx executable that translates RINEX 3 to 2.

The snr options are always two digit numbers.  Choices are:

- 99 is elevation angles of 5-30 degrees  (most applications)
- 88 is elevation angles of 5-90 degrees
- 66 is elevation angles less than 30 degrees
- 50 is elevation angles less than 10 degrees (good for tall, high-rate applications)

orbit file options:

- nav : GPS broadcast, perfectly adequate for reflectometry
- igs : IGS precise, GPS only
- igr : IGS rapid, GPS only
- jax : JAXA, GPS + Glonass, within a few days
- gbm : GFZ Potsdam, multi-GNSS, not rapid
- grg: French group, GPS, Galileo and Glonass, not rapid
- wum : Wuhan, multi-GNSS, not rapid

What if you do not want to install the fortran translators?  Use -fortran True on the command line.

# quickLook 

Before using the **gnssir** code, I recommend you try **quickLook**. This allows you
to quickly test various options (elevation angles, frequencies, azimuths).
The required inputs are station name, year, doy of year, and SNR Format (start with 99).

If the SNR file has not been previously stored, you can provide a properly named RINEX file
(lowercase only) in your working directory. If it doesn't find a file in either of these places, it
will try to pick up the RINEX data from various archives (unavco, sopac, sonel, and cddis) and translate it for
you into the correct SNR format. There are stored defaults for analyzing the
spectral characteristics of the SNR data.  If you want to override those, use *quickLook -h*

*quickLook p041 2020 150 99*  (this uses defaults)

*quickLook gls1 2011 271 99*  (this uses defaults)

*quickLook smm3 2018 271 99 -h1 8 -h2 20*  (smm3 is about 15 meters tall, so I am modifying from the defaults)

Many archives make it difficult for you to access modern GNSS signals. This is really unfortunate,
as the L2C and L5 GPS signals are great, as are the signals from Galileo, Glonass, and Beidou.

Many archives also make it difficult for you to use high-rate data. Especially for sea level studies, I recommend
going higher than typical geodetic sampling rates.

# gnssir

This is the main driver for the reflectometry code.  You need a set of instructions which can be made using **make_json_input**.  At a minimum **make_json_input** needs the station name (4 char), the latitude (degrees), longitude (degrees) and ellipsoidal height (meters). It will use defaults for other parameters if you do not provide them. Those defaults tell the code an azimuth and elevation angle mask (i.e. which directions you want to allow reflections from), and which frequencies you want to use, and various quality control metrics. 

Things that are helpful to know for the json and commandline inputs:

*Names for the GNSS frequencies*
- 1,2,5 are GPS L1, L2, L5
- 20 is GPS L2C 
- 101,102 Glonass L1 and L2
- 201, 205, 206, 207, 208: Galileo frequencies
- 302, 306, 307 : Beidou frequencies

*Reflection parameters:*
- e1 and e2 are the min and max elevation angle, in degrees
- minH and maxH are the min and max allowed reflector height, in meters
- desiredP, desired reflector height precision, in meters
- PkNoise is the periodogram peak divided by the periodogram noise ratio.  
- reqAmp is the required periodogram amplitude value, in volts/volts
- polyV is the polynomial order used for removing the direct signal
- freqs are selected frequencies for analysis
- delTmax is the maximum length of allowed satellite arc, in minutes
- azval are the azimuth regions for study, in pairs (i.e. 0 90 270 360 means you want to evaluate 0 to 90 and 270 to 360).

*Other json inputs:*
- wantCompression, boolean, compress SNR files
- screenstats, boolean, whether minimal periodogram results come to screen
- refraction, boolean, whether simple refraction model is applied.
- plt_screen: boolean, whether SNR data and periodogram are plotted to the screen
- seekRinex: boolean, whether code looks for RINEX at an archive


Simple example for my favorite GPS site [p041](https://spotlight.unavco.org/station-pages/p042/eo/scientistPhoto.jpg)

- *make_json_input p041 39.949 -105.194 1728.856* (use defaults and write out a json instruction file)
- *rinex2snr p041 2020 150 99 nav* (pick up and translate RINEX file from unavco)
- *gnssir p041 2020 150 99* (calculate the reflector heights) 
- *gnssir p041 2020 150 99 -fr 5 -plt True* (override defaults, only look at L5, SNR data and periodogram plots come to the screen)

Where are the files for this example?

- json is stored in REFL_CODE/input/p041.json
- SNR files are stored in REFL_CODE/2020/snr/p041
- Reflector Height (RH) results are stored in REFL_CODE/2020/results/p041
- I do not save RINEX files.  

If you want multi-GNSS, you need to use multi-GNSS orbits and edit the json file. And the RINEX you select 
must have multi-GNSS SNR observations in it. p041 currently has multi-GNSS data in the RINEX file:

- *rinex2snr p041 2020 151 99 gbm* (use GFZ orbits so you can use GPS, Glonass, and Galileo)
- *gnssir p041 2020 151 99 -fr 201 -plt True* (look at the lovely Galileo L1 data) 


# Publications

There are A LOT of publications about GPS and GNSS interferometric reflectometry.
If you want something with a how-to flavor, try this paper, 
which is [open option](https://link.springer.com/article/10.1007/s10291-018-0744-8)

Also look to the publications page on my [personal website](https://kristinelarson.net/publications)

# How can I import the libraries in this package?

I will be adding more documentation and examples here.
