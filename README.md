# gnssrefl v3.6.7

gnssrefl is an open source software package for GNSS Interferometric Reflectometry (GNSS-IR). 
When citing gnssrefl, please use:

Larson, K.M., gnssrefl: an open source python software package for environmental 
GNSS interferometric reflectometry applications, *GPS Solutions*, Vol. 28(165), 10.1007/s10291-024-01694-8, 2024.

Documentation: [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

- [online](https://gnssrefl.readthedocs.io/en/latest/)

- [pdf](https://gnssrefl.readthedocs.io/_/downloads/en/latest/pdf/)

Questions/Concerns and bug reports, **must** be submitted via the **Issues** button at 
the [github repository](https://github.com/kristinemlarson/gnssrefl/issues).

gnssrefl also has a DOI from zenodo.

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601494.svg)](http://dx.doi.org/10.5281/zenodo.5601494) 

The latest pypi version can be found here [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) 

**Some new features:**

You can now store coordinates for your local GNSS-IR sites. 
See [file formats](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html) for more information.
(A bug in this option was fixed in version 3.6.7. The previous version failed when you only had a single station in your file.)

![](docs/myAnimation.gif)

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

Kristine M. Larson

March 19, 2024


