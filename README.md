
<p align=center>
<img src="https://morefunwithgps.com/public_html/gnssrefl-images-sm.jpg" width=600 />
</p>

# gnssrefl

**github version: 1.1.6** [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601495.svg)](http://dx.doi.org/10.5281/zenodo.5601495)

**WARNING: All access to UNAVCO data will end October 1, 2022 unless [you sign up for an account there](https://www.unavco.org/data/gps-gnss/file-server/file-server-access-examples.html)**

**WARNING: CDDIS has changed their high-rate directory protocol for older files. This means some of our download codes now fail.
If someone wants to provide a pull request that addresses this issue, I would be happy to implement it.  I 
am not willing to write such code myself.**

## Table of Contents

1. [Installation](docs/pages/README_install.md)
2. Understanding the Code
    1. [rinex2snr: translating GNSS Data (RINEX, NMEA)](docs/pages/rinex2snr.md)
    2. [quickLook: assessing a GNSS site using SNR files](docs/pages/quickLook.md)
    3. [gnssir: estimating reflector heights from SNR data](docs/pages/gnssir.md)
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

## [gnssrefl Documentation]()

### [gnssrefl Understanding <a name="understanding"></a>](docs/pages/understand.md): project goals, philosophy and methods.

<HR>

### [gnssrefl Utilities <a name="helper"></a>](docs/pages/utilities.md): data retrieval and useful geodetic functions.

<HR>

### [GNSS-IR Community <a name="weneedhelp"></a>](docs/pages/contributions_questions.md): questions,  contributing and acknowledgements.


GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was developed with support from NASA (80NSSC20K1731).

This documentation was updated on October 4, 2022
<HR>



