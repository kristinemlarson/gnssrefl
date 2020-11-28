### St Lawrence River

Station pmtl is operated by the Montreal Port Authority. The data are archived at NRCAN. 

L1, Glonass L1 and L2 can be used at this site. It would be great to get L2C, L5 and Galileo data
in the future.


Look at the [NRCAN Site Description for pmtl](https://webapp.geod.nrcan.gc.ca/geod/data-donnees/station/report-rapport.php?id=M0722900)

<img src="https://webapp.geod.nrcan.gc.ca/cacs/PMTL_MONU.jpg" width="500" />

The GNSS antenna is on the roof of grain terminal. Also 
note that ellipsoidal height (and geoid corrected height),
[also provided at my geoid site](https://gnss-reflections.org/geoid)

**Picking a mask:** 

For reflections, you want to know the height above sea level - which means you need to apply
the geoid correction to the ellipsoidal height. [My web app will do that for you.](https://gnss-reflections.org/rzones)
I suggest you try different azimuth ranges and elevation angles.

<img src="pmtl_rzone.png" width="500" />

**Exercise for the reader:** Download a 1-Hz RINEX file from NRCAN. Make sure to include GPS and Glonass.

- make a SNR file using the -orb gnss option

- run quickLook - but given the height of pmtl, you are going to need to change the RH values


You need to use **make_json_input** to set up the analysis instructions.
The restricted elevation angles can be set at the command line, as can the heights. Use -allfreq True.
[You will need to hand-edit it to remove L2 and Galileo and to set the azimuth region.](pmtl.json)



There is a tide gauge near this site. Please contact NRCAN for more information.

<img src="montreal.png" width="500">
