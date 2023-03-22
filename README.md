
<p align=center>
<img src="https://morefunwithgps.com/public_html/gnssrefl-images-sm.jpg" width=600 />
</p>

# gnssrefl

**github version: 1.2.23** [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601495.svg)](http://dx.doi.org/10.5281/zenodo.5601495) [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

[New station guidelines](docs/pages/new_station.md)

The [shortcourse](docs/pages/shortcourse_2023_web.md) dates have been tentatively set for May 2-5 (two hours each day). 
The registration page is not available as yet - but hopefully soon.

If you want to sign up for the GNSS-IR email list, please contact Kristine Larson.

[Youtube videos for beginners](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

New [snowdepth utility](docs/pages/README_snowdepth.md).

New discussion page started about [modern GNSS signals](docs/pages/signal_issues.md).

We have developed [readthedocs style documentation](https://gnssrefl.readthedocs.io/en/latest/).

We create a new [docker](https://github.com/kristinemlarson/gnssrefl/blob/master/docs/pages/docker_cl_instructions.md) every time we update this repository.

We create a new [pypi version](https://pypi.python.org/pypi/gnssrefl) every time a new version is created.

All access to UNAVCO data will end (unknown date) unless [you sign up for an account there](https://www.unavco.org/data/gps-gnss/file-server/file-server-access-examples.html)

## Table of Contents

1. [Installation](docs/pages/README_install.md)
2. [Understanding the Code](docs/pages/understand.md)
    1. [rinex2snr: translating GNSS Data (RINEX, NMEA)](docs/pages/rinex2snr.md)
    2. [quickLook: assessing a GNSS site using SNR files](docs/pages/quickLook.md)
    3. [gnssir and rh_plot: estimating reflector heights from SNR data](docs/pages/gnssir.md)
3. Products:
    1. [daily_avg: daily average reflector heights](docs/pages/README_dailyavg.md)
    2. [subdaily: water level measurements](docs/pages/README_subdaily.md)
    3. [invsnr: SNR inversion for subdaily reflector height estimates](docs/pages/README_invsnr.md)
    4. [vwc: soil moisture module](docs/pages/README_vwc.md)
    5. [snowdepth: utility for snowdepth calculation](docs/pages/README_snowdepth.md)
4. [Examples](docs/pages/first_drivethru.md)
5. [The Simulator](docs/pages/simulator.md)
6. [Utilities](docs/pages/utilities.md)
7. [Notes about File structure and Formats](docs/pages/file_structure.md)
8. [News/Bugs/Future Work](docs/pages/news.md)
9. [Some Publications](https://kristinelarson.net/publications)
10. [How can you help this project? How can you ask for help?](docs/pages/contributions_questions.md)

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was initially developed 
as a fun post-retirement project, followed by support from NASA (80NSSC20K1731).

This documentation was updated on February 23, 2023

Kristine M. Larson

<HR>



