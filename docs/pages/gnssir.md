# Estimating Reflector Heights 


## gnssir_input

[A full listing of the possible inputs and examples for gnssir_input can be found here.](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.gnssir_input.html)

Your first task is to define your analysis strategy. If the station location is in our database:

<CODE>gnssir_input p101</CODE>

If you have your own site, you should use -lat, -lon, -height as inputs.  
If you happen to have the Cartesian coordinates (in meters), you can 
set <code>-xyz True</code> and input those instead.


The json file of instructions will be stored in $REFL_CODE/input/p101.json. 

The default azimuth inputs are from 0 to 360 degrees.
You can set your preferred azimuth regions using -azlist2. Previously you were required to use multiple
azimuth regions, none of which could be larger than 100 degrees. That is no longer required. However, if 
you do need multiple distinct regions, that is allowed, e.g.

<CODE>gnssir_input p101  -azlist2 0 90 180 270</CODE>

If you wanted all southern quadrants, since these are contiguous, you just need to give the starting and ending 
azimuth.

<CODE>gnssir_input p101  -azlist2 90 270</CODE>

You should also set the prefrred reflector height region (h1 and h2) and elevation angle mask (e1 and e2).
Note: the reflector height region should not be too small, as it is also used to set the region for your periodogram.
If you use tiny RH constraints, your periodogram will not make any sense and your work will fail the quality control metrics.


## gnssir

<code>gnssir</code> estimates reflector heights. It assumes you have made SNR files and defined an analysis strategy.
The minimum inputs are the station name, year, and doy. 
 

<CODE>gnssir p041 2020 150 </CODE> 


[Additional inputs](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.gnssir_cl.html)

Where would the code store the files for this example?

- json instructions are stored in $REFL_CODE/input/p041.json
- SNR files are stored in $REFL_CODE/2020/snr/p041
- Reflector Height (RH) results are stored in $REFL_CODE/2020/results/p041/150.txt

For more information about the decisions made in <code>gnssir</code>, set **-screenstats T**

For plots, set -plt to T or True. 

If you want to try different strategies, use multiple json files with the -extension input. Then use the same -extension command
in <code>gnssir</code>.

This is a snippet of what the result file would look like

<img src="../_static/results-snippet.png" width="600">

Note that the names of the columns (and units) are provided:

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
- ediff QC metric

Warning: We try to enforce homogenous track lengths by using a quality control factor called *ediff*. Its 
default value is 2 degrees, which means your arc should be within 2 degrees of the requested elevation angle inputs.
So if you ask for 5 and 25 degrees, your arcs should at least be from 7 to 23 degrees.  To tell 
<code>gnssir</code> you want to allow smaller arcs, just set ediff to a much larger value.
