## snowdepth

In order to estimate snow depth, you should first run <code>daily_avg</code>.
We have a utility to will change this to snow depth using the procedures
used in PBO H2O. The assumptions are:

- you set the "no snow" or "bare soil" values using data from the fall (in the northern hemisphere)
- negative snow depth is not allowed!
- snow depth < 0.05 is set to zero as these small values are close to the resolution of the method.
- we do not estimate snow depth after June 30. This is purely a practical constraint as most 
of the GNSS sites where we tested the method did not have snow cover then. 

The current required inputs are :

- station name
- water year

Optional inputs allow you to set the y-axis limits for snow depth (minS, maxS), and 
the days of year used to set the "no snow" defintion (doy1, doy2). The 
defaults are September 1-September 30.
For Alaska and Canada September is likely not to work, so you should set those accordingly.  
Since the plots are made for the (northern hemisphere) water year, you might also set 
<code>-longer T</code> so you can see a longer time series. Otherwise you 
see October 1 through June 30 for all sites.

The default behavior sends a plot to the screen, but you can turn that off with -plt F.

The error bars are **over-estimates** and based on the standard deviation of the 
reflector heights used in the daily average. These include terrain errors as well 
as snow depth errors.

There is a SWE module that is currently written in matlab. If you are willing to port it to
python, we would be happy to add it to <code>gnssrefl</code>. 

PBO H2O snow depth products were based on L2C data. This utility allows multi-GNSS retrievals.
For further reading, [search for the word snow on this page](https://www.kristinelarson.net/publications/).
