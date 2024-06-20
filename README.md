# gnssrefl v3.5.5 

If you use this code in any presentation or publication, you are expected to cite either 
this github repository or the gnssrefl DOI, which is given just below.

[![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) 

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601494.svg)](http://dx.doi.org/10.5281/zenodo.5601494) 


gnssrefl is an open source software package for GNSS interferometric reflectometry (GNSS-IR). 

![](docs/myAnimation.gif)

I made this animation ages ago - so it is in Matlab.  I would be happy to host a link to 
a version in python.  The main code is [snr_simulation](docs/pages/snr_simulation.m) 
and the helper function is [setFrame.m](docs/pages/set_Frame.m). 

High-rate data from CDDIS that are more than six months old can now be downloaded.

Documentation:

- [online](https://gnssrefl.readthedocs.io/en/latest/)

- [pdf](https://gnssrefl.readthedocs.io/_/downloads/en/latest/pdf/)

- [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

See documentation for [gnssir_input](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.gnssir_input.html) for new refraction models.

How do you find out which version are you running? Type <code>pip list | grep gnssrefl</code>

If you want to sign up for the GNSS-IR email list, please contact Kristine Larson.

[Youtube videos for beginners](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

If you want to access CDDIS, including orbits, you should make [an account](https://urs.earthdata.nasa.gov/users/new).

If you want to access to any Earthscope data, [an account is required](https://data-idm.unavco.org/user/profile/login).

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was initially developed 
as a fun post-retirement project, followed by support from NASA (80NSSC20K1731).

The [CRC 1502 DETECT project](https://sfb1502.de/) supported this project from 2022-2024.

Kristine M. Larson

March 19, 2024


