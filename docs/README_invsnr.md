### invsnr

This is a utility for analyzing time-varying smooth surfaces with GNSS interferometric reflectometry.
The method was first introduced by [Joakim Strandberg](https://github.com/Ydmir) and his colleagues. This implementation of the method was written by 
[David Purnell](https://purnelldj.github.io/). It reads the inputs from the <code>gnssrefl</code> package (SNR files). 
It analyzes L1, L2, and L5 signals and the GPS, Galileo, and Glonass constellations.

You might notice that the Lomb Scargle Periodogram (LSP) results from this software are different 
than <code>gnssir</code>. In some locations you might see relatively large outliers. *This is to be expected.* 
This code uses the LSP results as a starting place - the quality control applied 
is entirely different than what was used in <code>gnssir</code>. Since the point of this code is to estimate smoothly
varying sea level, I don't think we need to make the LSP portion of it a clone of <code>gnssir</code>. 

Note: 

- txt and csv output is now supported. 

- You can specify the temporal sampling of the output.

- a simple refraction correction (elevation angle bending) has been included

### Installation 

The module is part of <code>gnssrefl</code>. Please see the installation instructions for 
[the main package](https://github.com/kristinemlarson/gnssrefl#environment). It is currently only available on gitHub.
We will be making a docker and pypi version.

### Running the code

The <code>gnssrefl</code> **REFL_CODE** environment variable must be set. This variable is used for storage of 
the SNR files and the inputs to the analysis strategy.

I. Make SNR files as you would normally for the <code>gnssrefl</code> using <code>rinex2snr</code>. They will be stored in
$REFL_CODE/yyyy/snr/ssss where yyyy is the year and ssss is the station name.

II. Set up analysis instructions. These instructions are stored in $REFL_CODE/input.

The required inputs are the station name (four characters lowercase), the reflector height limits (in meters)
the elevation angle limits (in degrees). 

*Example:*

<code>invsnr_input p041 0.5 6 5 25 </code>

In this case the station coordinates for p041 will be retrieved from the UNR database. If you have a 
site that is not in the database, please use -lat, -lon, -height inputs.

You can add an azimuth restriction using -a1 and -a2:

<code>invsnr_input p041 0.5 6 5 25 -a1 180 -a2 270</code>

Because this software identifies rising and setting arcs in a different way than <code>gnssir</code>, you 
can set a single range of azimuth ranges.

III. Run invsnr

*Required inputs*

- station name (4 characters, lowercase)
- year
- day of year 
- frequency (e.g. L1, L2, L5, L6, L1+L2, L1+L2+L5). ALL means L1+L2+L5+L6+L7

The code will attempt GPS, Galileo, Beidou and Glonass unless you tell it otherwise

*Optional inputs*

- pktnlim peak2noise ratio for QC
- constel (G,E,R, or C which represent GPS, Galileo, Glonass, and Beidou)
- screenstats (True or False)
- tempres decimation value for the SNR file (seconds)
- polydeg polynomial degree for direct signal removal (default is 2)
- snrfit Do a invsnr fit? Default is True
- doplot Send a summary plot to the screen? Default is True
- doy_end day of year for multiday analysis
- lspfigs and -snrfigs make LSP and SNR plots, default False. 
- knot_space value used for smoothing, in hours 
- rough_in, roughness parameter as described in Strandberg et al (2016). Default is 0.1
- risky set to True means you will ignore the warrning telling you that you have a gap and should not do this.

Please see <code>invsnr -h</code> for more options. Some are related to outputs (i.e. you can tell
the code to write out smoothed RH values into a text or csv file.


*Output of the invsnr Code*

The code makes a first cut of LSP reflector height estimation. It also does
a cubic spline fit and then the spline fit estimation. 
I am currently printing out the smoothed results to a plain txt file every five minutes.
You can modify that temporal setting or change to a csv format at the command line.

Warning: No phase center corrections are currently applied to the reflector heights.
Nor are changes from material properties addressed (water, snow, ice). 

*Example for station AT01*

<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/AT01.jpg" width=500>

- Make SNR files <code>rinex2snr at01 2021 301 -doy_end 303 -orb gnss -archive unavco</code>

- Save analysis strategy <code>invsnr_input at01 9 14 5 13 -a1 20 -a2 220</code>

- Just one day of GPS on L1: <code>invsnr at01 2021 301 L1 -constel G</code> 

<img src="at01-ex1.png" width=500>

- Two days with L1 and all constellations: <code>invsnr at01 2021 301 L1 -doy_end 302</code> 

<img src="at01-ex2.png" width=500>

- Two days with L1+L2+L5 and all constellations: <code>invsnr at01 2021 301 L1+L2+L5 -doy_end 302</code> 

<img src="at01-ex3.png" width=500>

*Example for station TNPP*

<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/TNPP.jpg" width=500>

- Make SNR files using <code>rinex2snr</code>, using high-rate data, UNAVCO archive, and GNSS orbits options 

- Save analysis strategy <code>invsnr_input tnpp 58 67  5 12 -a1 180 -a2 270</code>

- Two days with L1+L2+L5, all constellations, decimate to speed up the code (1-sec data will be very slow)

<code>invsnr tnpp 2021 315 L1+L2+L5 -doy_end 316 -tempres 2</code>

<img src="tnpp-ex2.png" width=500>

*Example for station SC02*

<img src="https://www.unavco.org/data/gps-gnss/lib/images/station_images/SC02.jpg" width=500>

- Used default 15 second RINEX files from UNAVCO and -orb gnss option

- ranges: 3.5-8 meter RH, 5-13 elevation angle, 40-240 azimuth 

- Multi-day, multi constellation, L1+L2 <code>invsnr sc02 2021 30 L1+L2 -doy_end 33 </code>

<img src="sc02-ex1.png" width=500>

### Future Changes

- Currently assumes you are using full 24 hour SNR files.  This obviously is not very sensible 
if you have a large gap 
at the beginning or end of your analysis.  

### Further reading

J. Strandberg, T. Hobiger, and R. Haas (2016), Improving GNSS-R sea level determination through 
inverse modeling of SNR data, Radio Science, 51, 1286–1296
[pdf](https://publications.lib.chalmers.se/records/fulltext/241876/local_241876.pdf)

D. Purnell, N. Gomez,  et al. (2021) Precise water level measurements using low-cost GNSS antenna arrays, Earth Surf. Dynam., 9, 673–685 [pdf](https://esurf.copernicus.org/articles/9/673/2021/)
