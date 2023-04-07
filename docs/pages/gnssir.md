# Estimating Reflector Heights 

## make_json_input 

Before you estimate reflector heights, you need a set 
of instructions. These are made using <code>make_json_input</code>. 
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

If you are using a site that is in the UNR station database, the *a priori* values can be set to zeros:

<CODE>make_json_input p101 0 0 0 </CODE>

[A full listing of the possible inputs and examples for make_json_input can be found here.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.make_json_input.html)

The json file of instructions will be put in $REFL_CODE/input/p101.json. 

Warning: Azimuth regions should not be larger than ~100 degrees. If for example you want to use the region from 0 to 
270 degrees, you should not set a region from 0 - 270, but instead a region from 0-90, 90-180, and the last
from 180-270. I know this is a bit offputting for people, but having these smaller regions makes the code
easier to maintain (i.e. you are less likely to have more than one rising and setting arc for a single satellite).

Example:

<CODE>make_json_input p101 0 0 0   -azlist 0 90 90 180 180 270</CODE>

The default is to allow four regions, each of 90 degrees.  


## gnssir

<code>gnssir</code> estimates reflector heights. It assumes you have made SNR files and defined an analysis strategy.
The minimum inputs are the station name, year, and doy

<CODE>gnssir p041 2020 150</CODE> 

[Additional inputs.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.gnssir_cl.html)

Where would the code store the files for this example?

- json instructions are stored in $REFL_CODE/input/p041.json
- SNR files are stored in $REFL_CODE/2020/snr/p041
- Reflector Height (RH) results are stored in $REFL_CODE/2020/results/p041/150.txt

For more information, set screenstats to True

For plots, set -plt to T or True. 

If you want to try different strategies, use multiple json files with the -extension input. Then use the same -extension command
in gnssir.

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
information, see the <code>subdaily</code> code.



