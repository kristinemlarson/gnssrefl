### Burnie, Australia

<center>Welcome - would you like to write up the use case for Burnie?</center>

**Station Name:** bur2

**Location:** Tasmania, Australia

**Archive:** Geoscience Australia

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/BUR2.sta)

**Photo:** 

<HR>


I suggest you read previous papers that analyzed the Burnie data. Start with this one:

**Levelling co-located GNSS and tide gauge stations using GNSS reflectometry**, Alvaro Santamaría-Gómez,
Christopher Watson, Médéric Gravelle, Matt King,and Guy Wöppelmann, *J Geodesy*, DOI 10.1007/s00190-014-0784-y

I recommend using RINEX 3 (station name bur200aus) 30-second data as these 
provide high-quality multi-frequency multi-GNSS SNR observations.
The current 1-sec RINEX 3 data stream provided by Geoscience Australia is 
missing important observations. I cannot recommend you use it. 

I have used [<code>invsnr</code>](https://github.com/kristinemlarson/gnssrefl/blob/master/README_invsnr.md) with some success. I 
used azimuth limits of 50-240 degrees. However, please keep in mind that can vary some of the knobs on the code - changing
peak2noise, reflector height, and elevation angle limits etc.

There is a tide gauge at Burnie. It only takes pretty simple google search to find a visual interface 
for it. If you can find the API description to download the data from the Burnie tide gauge,
I would be happy to add it here.



