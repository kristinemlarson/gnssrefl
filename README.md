
<p align=center>
<img src="https://morefunwithgps.com/public_html/gnssrefl-images-sm.jpg" width=600 />
</p>

# gnssrefl

**github version: 1.2.13** [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601495.svg)](http://dx.doi.org/10.5281/zenodo.5601495) [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

!!! Specific azimuth regions can now be added at the command line. Use -azlist in <code>make_json_input</code> !!!

New Google Earth utility for reflection zones: [refl_zones](docs/pages/utilities.md)

We are [developing readthedocs documentation](https://gnssrefl.readthedocs.io/en/latest/). We are also creating 
a new docker each time we upload the code to github. If you look to the right - see "Packages".

All access to UNAVCO data will end October 1, 2022 unless [you sign up for an account there](https://www.unavco.org/data/gps-gnss/file-server/file-server-access-examples.html)**

## Table of Contents

1. [Installation](docs/pages/README_install.md)
2. [Understanding the Code](docs/pages/understand.md)
    1. [rinex2snr: translating GNSS Data (RINEX, NMEA)](docs/pages/rinex2snr.md)
    2. [quickLook: assessing a GNSS site using SNR files](docs/pages/quickLook.md)
    3. [gnssir and rh_plot: estimating reflector heights from SNR data](docs/pages/gnssir.md)
3. Products:
    1. [daily_avg: daily average reflector heights](docs/pages/README_dailyavg.md)
    2. [subdaily: LSP quality control and RHdot for reflector height estimates](docs/pages/README_subdaily.md)
    3. [invsnr: SNR inversion for subdaily reflector height estimates](docs/pages/README_invsnr.md)
    4. [vwc: soil moisture module](docs/pages/README_vwc.md)
4. [Examples](docs/pages/first_drivethru.md)
5. [Utilities](docs/pages/utilities.md)
6. [Notes about File structure and Formats](docs/pages/file_structure.md)
7. [News/Bugs/Future Work](docs/pages/news.md)
8. [Publications](https://kristinelarson.net/publications)
9. [How can you help this project? How can you ask for help?](docs/pages/contributions_questions.md)

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was developed with support from NASA (80NSSC20K1731).

This documentation was updated on December 20, 2022
<HR>



