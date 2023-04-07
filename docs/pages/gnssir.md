# **gnssir**

<code>gnssir</code> is the main driver for the GNSS-IR code. 

## make_json_input 

You need a set of instructions which are made using <code>make_json_input</code>. 
The required inputs are: 

* station name 
* latitude (degrees)  
* longitude (degrees) 
* ellipsoidal height (meters). 

The station location *does not* have to be cm-level for the reflections code. Within a few hundred meters is 
sufficient. For example: 

<CODE>make_json_input p101 41.692 -111.236 2016.1</CODE>

If you happen to have the Cartesian coordinates (in meters), you can 
set <code>-xyz True</code> and input those instead of lat, long, and height.

If you are using a site that is in the UNR database, the a priori values can be set to zeros:

<CODE>make_json_input p101 0 0 0 </CODE>

[A full listing of the possible inputs and examples can be found here.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.make_json_input.html)

The json file of instructions will be put in $REFL_CODE/input/p101.json. 

Warning: Azimuth regions should not be larger than ~100 degrees. If for example you want to use the region from 0 to 
270 degrees, you should not set a region from 0 - 270, but instead a region from 0-90, 90-180, and the last
from 180-270. I know this is a bit offputting for people, but having these smaller regions makes the code
easier to maintain (i.e. you are less likely to have more than one rising and setting arc for a single satellite).

Example:

<CODE>make_json_input p101 41.692 -111.236 2016.1 -e1 5 -e2 10  -ampl 10 -peak2noise 3 -azlist 0 90 90 180 180 270</CODE>

The default is to allow four regions, each of 90 degrees.  


## running gnssir

Simple examples for my favorite GPS site [p041](https://spotlight.unavco.org/station-pages/p042/eo/scientistPhoto.jpg)

<CODE>make_json_input p041 39.949 -105.194 1728.856</CODE> (use defaults and write out a json instruction file)

<CODE>rinex2snr p041 2020 150</CODE> (pick up and translate RINEX file for day of year 150 and year 2020 from unavco )

<CODE>gnssir p041 2020 150</CODE> (calculate the reflector heights) 

<CODE>gnssir p041 2020 150 -fr 5 -plt True</CODE> (override defaults, only look at L5 SNR data, and periodogram plots come to the screen)

Where would the code store the files for this example?

- json instructions are stored in $REFL_CODE/input/p041.json
- SNR files are stored in $REFL_CODE/2020/snr/p041
- Reflector Height (RH) results are stored in $REFL_CODE/2020/results/p041

This is a snippet of what the result file would look like

<img src="../_static/results-snippet.png" width="600">

- *Amp* is the amplitude of the most significant peak in the periodogram (i.e. the amplitude for the RH you estimated).  
- *DelT* is how long a given rising or setting satellite arc was, in minutes. 
- *emin0* and *emax0* are the min and max observed elevation angles in the arc.
- *rise/set* tells you whether the satellite arc was rising (1) or setting (-1)
- *Azim* is the average azimuth angle of the satellite arc
- *sat* and *freq* are as defined in this document
- MJD is modified julian date
- PkNoise is the peak to noise ratio of the periodogram values
- last column is currently set to tell you whether the refraction correction has been applied 
- EdotF is used in the RHdot correction needed for dynamic sea level sites. The units are hours/rad.
When multiplied by RHdot (meters/hour), you will get a correction in units of meters. For further
information, see <code>subdaily</code>.

If you want a multi-GNSS solution, you need to:

- make sure your json file is set appropriately
- use a RINEX file with multi-GNSS data in it (i.e. use multi-GNSS orbits and in some cases rerun rinex2snr).

In 2020 p041 had a multi-GNSS receiver operating, so we can look at some of the non-GPS signals.
In this case, we will look at Galileo L1.  

<CODE>make_json_input p041 39.949 -105.194 1728.856 -allfreq True</CODE>

<CODE>rinex2snr p041 2020 151 -orb gnss -overwrite True</CODE>

<CODE>gnssir p041 2020 151 -fr 201 -plt True</CODE> 

Note that a failed satellite arc is shown as gray in the periodogram plots. And once you know what you are doing (have picked
the azimuth and elevation angle mask), you won't be looking at plots anymore.

**New:**

Before you start interpreting the results (using <code>daily_avg</code>, <code>subdaily</code>, <code>vwc</code>), and you just
want to "see" the reflector height results, I have added a new utility: <code>rh_plot</code>
It allows you to visualize results for up to a single year. It concantenates the RH results in case you 
want  to use another program (e.g. Matlab) to do more assessment. It creates a single txt file and a plot 
where the RH results are plotted with respect to time, color coded by signal frequency, azimuth, and periodogram amplitude.
The azimuth plots in particular might help you see that you should change your azimuth mask.

The required inputs are station name and year. Beyond that you can request:
<PRE>
  -doy1    initial day of year
  -doy2    end day of year
  -ampl    new amplitude constraint
  -azim1   new min azimuth (deg)
  -azim2   new max azimuth (deg)
  -h1 H1   min RH (m)
  -h2 H2   max RH (m)
  -peak2noise new peak2noise constraint 
</pre>
