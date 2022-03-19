### Burnie, Australia

**Station Name:** bur2

**Location:** Tasmania, Australia

**Archives:**  Multiple (Geoscience Australia, CDDIS)

[Station Page at Nevada Geodetic Laboratory](http://geodesy.unr.edu/NGLStationPages/stations/BUR2.sta)

**Photo:** Please feel to contribute one.  The official site manager page at GA does 
not have any (as of 2022-March-15).

<HR>

Welcome - would you like to write up the use case for Burnie?

I suggest you read previous papers that analyzed the Burnie data. Start with this one:

**Levelling co-located GNSS and tide gauge stations using GNSS reflectometry**

Alvaro Santamaría-Gómez · Christopher Watson · Médéric Gravelle · Matt King · Guy Wöppelmann
 J Geodesy, DOI 10.1007/s00190-014-0784-y

I recommend using RINEX 3 (station name bur200aus) 30-second data as these 
provide high-quality multi-frequency multi-GNSS SNR observations.
The current 1-sec RINEX 3 data stream provided by Geoscience Australia is 
missing important observations. I cannot recommend you use it. 

I have used the <code>invsnr</code> code with some success. I used azimuth limits of 50-170 degrees.

There is a tide gauge at Burnie. And it is a fairly simple google search to find a visual interface 
for it. If you can find the API description to download the data from the Burnie tide gauge,
I would be happy to add it here.




