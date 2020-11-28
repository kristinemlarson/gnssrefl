### St Lawrence River

**Background:** Station pmtl is operated by the Montreal Port Authority. The data are archived at NRCAN. 

L1, Glonass L1 and L2 can be used at this site. It would be great to get L2C, L5 and Galileo data
in the future.


Look at the [NRCAN Site Description for pmtl](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/station/report-rapport.php?id=M0722900)
Note that the GNSS antenna is on a very tall building. Also note that ellipsoidal height (and geoid corrected height),
[also provided at my geoid site](https://gnss-reflections.org/geoid)

**Picking a mask:** 
For reflections, you want to know the height above sea level - which means you need to apply
the geoid correction to the ellipsoidal height. [My web app will do that for you.](https://gnss-reflections.org/rzones)
I suggest you try different azimuth ranges and elevation angles.

**Exercise for the reader:** Download a 1-Hz RINEX file from NRCAN. Make sure to include GPS and Glonass.

- make a SNR file using the -orb gnss option

- run quickLook - but realize you are going to need to change the RH values

- 

<img src="mchn-default.png" width="500">


You need to use **make_json_input** to set up the analysis instructions.
[You will need to hand-edit it to remove L1 and to set the azimuth region.](pmtl.json)


Note: there is a tide gauge near this site. Please contact NRCAN for more information.
