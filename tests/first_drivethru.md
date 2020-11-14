# Getting Started with gnssrefl

This is a test case for GNSS interferometric reflectometry. 
It is not meant to explain everything about the technique, the code, or 
the site we are using. You really should read Roesler and Larson (2018) first.

# Install the code

Read the gnssrefl documentation.

Install either the github or the pypi version. 

Make requested environment variables.

Put CRXRNX in the EXE are area. Make sure it is executable


# Set up the code to run for a single site 

Start with p041.  



Now use lorg.  The data are archived at UNAVCO.  Get some coordinates for the site, either lat,long,ht
or XYZ. The coordinates do not have to be super precise (within 100 meters is fine).

**Exercise for the reader:** get a photograph of lorg from UNAVCO. If you cannot find it at their site,
email them and ask them to provide it.

You can try out lorg here, though Google Maps does not have imagery. https://gnss-reflections.org/rzones



Just in general, what do you think the azimuth mask should be?  Based on your reading, Elevation angle mask?

Make SNR files for station lorg, year 2019, doy 1 through 233

Do a quickLook for one file using the defaults. What frequency is displayed?  Compare frequencies 1,2 and 5.  Note the differences. Now run frequency 20.  How is that different than frequency 2?
Make a json input for station lorg. Use defaults. (Why is that reasonable?)
Run gnssir for all the SNR data.
Try out daily_avg using median filter of 0.25 meters and ReqTrack of 50. It should let you use different frequencies.  Try that out.  
Figure out how to save the output of daily_avg - both to a text file and to a plot.  


