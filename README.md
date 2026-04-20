# gnssrefl v4.1.3

gnssrefl is an open source software package for GNSS Interferometric Reflectometry (GNSS-IR). 

**News**

gnssrefl releases from v4.0.0+ are focused on modernizing the package code to improve maintainability, 
consistency, and performance (up to 5x faster).  Specifically, changes since v3.19.2 (17th Feb 2026) 

* The default Lomb-Scargle Periodogram backend has changed from SciPy to AstroPy, which is more efficient 
but introduces absolute difference in RH on the order of ~ 1mm. Use -lsp_method scipy to use the 
old method, which produces identical results to previous versions. 

* FORTRAN compilation/meson is no longer required to install the package

* gfzrnx binary is no longer required to process RINEX 3 files, which increases speed.

* A new arc extraction module (extract_arcs) allows efficient loading of raw dSNR 
data / processing results from a user-facing Python API

* gnssir and phase processing will now automatically load data from previous/next 
days to avoid arcs truncating at the midnight boundary (optional, previously disabled by default) - most days gain a few observations

* Improve track identification in phase processing- most stations will gain a few new tracks

* Add refraction correction to phase processing - dSNR data now aligned with gnssir

* If you make your own install, we require you use python versions >= 3.10. 

* Added the lsp_method parameter in the station json, gnssir_input, and gnssir. Options are 'fast' 
(default) or 'scipy'. With -lsp_method scipy the RH estimates are identical to previous versions.

Thanks to George Townsend for all his work on these changes.

**All questions must be posted as an [issue](https://github.com/kristinemlarson/gnssrefl/issues).**
This allows tracking of community usage and allows others to benefit if they have the same question. It also
provides a forum for other community members to provide their perspective as I am not able to answer every question 
that is posted.

When showing any results created using gnssrefl, I request that you use:

Larson, K.M., gnssrefl: an open source python software package for environmental 
GNSS interferometric reflectometry applications, *GPS Solutions*, Vol. 28(165), 10.1007/s10291-024-01694-8, 2024.

If you use the [online Fresnel mapping tool](https://gnss-reflections.org/rzones), 
you should similarly cite this paper as it uses the exact same code.

Documentation: [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

- [online](https://gnssrefl.readthedocs.io/en/latest/)

- [pdf](https://gnssrefl.readthedocs.io/_/downloads/en/latest/pdf/)

gnssrefl also has a DOI from zenodo.

[![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601494.svg)](http://dx.doi.org/10.5281/zenodo.5601494) 

[Time to upgrade to python 3.10](https://devguide.python.org/versions/)

The latest pypi version can be found here [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) 

Latest Features

- There is a more advanced vegetation model available for the soil moisture module.

- You can define your water level measurements with respect to more than one 
orthometric height. This value is read from the analysis json 
in both subdaily and daily_avg. Please see the documented inputs to gnssir_input for more information.

- You can set your own leveling time periods for soil moisture (see vwc.py).

- You can estimate LSP in SNR units of dB-Hz. Command line option dbhz.

- Soil moisture can be computed from L1 and L5 data, see e.g. [George Townsend PR](https://github.com/kristinemlarson/gnssrefl/pull/354)

- you can set beginning and end dates in <code>daily_avg</code> and <code>subdaily</code>. The parameters are 
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

**Some older new features:**

You can now store coordinates for your local GNSS-IR sites. 
See [file formats](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html) for more information.
(A bug in this option was fixed in version 3.6.7. The previous version failed when you only had a single station in your file.)

![](docs/myAnimation.gif)

A [notebook version](https://github.com/kristinemlarson/gnssrefl/blob/master/notebooks/use-cases/Soil_Moisture/GNSSRefGeometry-SNRSimulation.ipynb) of this animation is also available if you would like to try changing parameters.

See documentation for [gnssir_input](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.gnssir_input.html) for new refraction models.

How do you find out which version are you running? Any of the major pieces
of code (rinex2snr, gnssir, subdaily) should display this information on the first line of the screen output. 

If you would like to sign up for the GNSS-IR email list, please contact Melissa Weber at Melissa.weber@earthscope.org

[Youtube videos for beginners](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

If you want to access CDDIS, including orbits, you should make [an account](https://urs.earthdata.nasa.gov/users/new).

If you want to access to any Earthscope data, [an account is required](https://data-idm.unavco.org/user/profile/login).

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was initially developed 
as a fun post-retirement project, followed by support from NASA (80NSSC20K1731).
The [CRC 1502 DETECT project](https://sfb1502.de/) and the University of Bonn supported this project from 2022-2024.

I am not funded to give courses on using <code>gnssrefl</code>. If you are interested in 
hosting a GNSS-IR workshop or short course, please contact one of the chairs of 
the [IAG study group on GNSS-IR](https://geodesy.science/iccc/structure/jwg-c-5/)


Kristine M. Larson

Last updated

December 11, 2025


