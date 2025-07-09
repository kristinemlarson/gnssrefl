# gnssrefl v3.15.2

gnssrefl is an open source software package for GNSS Interferometric Reflectometry (GNSS-IR). 
When showing results created using gnssrefl, please use:

Larson, K.M., gnssrefl: an open source python software package for environmental 
GNSS interferometric reflectometry applications, *GPS Solutions*, Vol. 28(165), 10.1007/s10291-024-01694-8, 2024.

Documentation: [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

- [online](https://gnssrefl.readthedocs.io/en/latest/)

- [pdf](https://gnssrefl.readthedocs.io/_/downloads/en/latest/pdf/)

gnssrefl also has a DOI from zenodo.

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601494.svg)](http://dx.doi.org/10.5281/zenodo.5601494) 

The latest pypi version can be found here [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) 

Latest Feature - you can set beginning and end dates in <code>daily_avg</code> and <code>subdaily</code>. The parameters are 
called date1 and date2. See the descriptions of these modules in the usual place.

Questions and bug reports for gnssrefl (but not the notebooks) **must** be submitted via the **Issues** button at 
the [github repository](https://github.com/kristinemlarson/gnssrefl/issues). The notebooks were created by Earthscope 
with NASA funding. I formally asked Earthscope about maintenance of the notebooks and received the following response from them:

*In general, we place maintenance of notebooks (and many of our apps) that are not in active production on 
the Low Priority list and I think it would be really healthy for our community to be 
willing to apply their expertise to provide fixes and enhancements 
to the notebook collection that can be reviewed in a pull request and merged for deployment.*

**Questions?**

Try looking at old Issues on github. People might have asked your question before. If you found our documentation confusing or 
lacking, please submit a PR to improve it.

**Some new features:**

You can now store coordinates for your local GNSS-IR sites. 
See [file formats](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html) for more information.
(A bug in this option was fixed in version 3.6.7. The previous version failed when you only had a single station in your file.)

![](docs/myAnimation.gif)

A [notebook version](https://github.com/kristinemlarson/gnssrefl/blob/master/notebooks/use-cases/Soil_Moisture/GNSSRefGeometry-SNRSimulation.ipynb) of this animation is also available if you would like to try changing parameters.

See documentation for [gnssir_input](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.gnssir_input.html) for new refraction models.

How do you find out which version are you running? Any of the major pieces
of code should display this information on the first line. Try <code>rinex2snr</code>.

If you want to sign up for the GNSS-IR email list, please contact Kristine Larson.

[Youtube videos for beginners](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

If you want to access CDDIS, including orbits, you should make [an account](https://urs.earthdata.nasa.gov/users/new).

If you want to access to any Earthscope data, [an account is required](https://data-idm.unavco.org/user/profile/login).

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was initially developed 
as a fun post-retirement project, followed by support from NASA (80NSSC20K1731).
The [CRC 1502 DETECT project](https://sfb1502.de/) and the University of Bonn supported this project from 2022-2024.

I am not funded to give courses on using <code>gnssrefl</code>. If you are interested in 
hosting a GNSS-IR workshop, as was done by the Earth Observatory of Singapore in 
2022, please feel free to contact me.

Kristine M. Larson

January 19, 2025


