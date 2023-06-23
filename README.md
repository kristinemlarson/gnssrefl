# gnssrefl

**github version: 1.3.20** [![PyPI Version](https://img.shields.io/pypi/v/gnssrefl.svg)](https://pypi.python.org/pypi/gnssrefl) [![DOI](https://zenodo.org/badge/doi/10.5281/zenodo.5601495.svg)](http://dx.doi.org/10.5281/zenodo.5601495) [![Documentation Status](https://readthedocs.org/projects/gnssrefl/badge/?version=latest)](https://gnssrefl.readthedocs.io/en/latest/?badge=latest)

**On or about July 1, the newarcs option will be the default for the <code>gnssir</code>.**

We have improved the way the code chooses rising and setting satellite arcs. 
Please use the <code>gnssir_input</code> instead of <code>make_json_input</code> when setting an analysis 
strategy, and <code>-newarcs T</code> when 
running <code>gnssir</code>. If you prefer to use the old way, it should continue to work.

Our documentation is now available [here.](https://gnssrefl.readthedocs.io/en/latest/)

If you want to sign up for the GNSS-IR email list, please contact Kristine Larson.

[Youtube videos for beginners](https://www.youtube.com/channel/UCC1NW5oS7liG7C8NBK148Bg).

New discussion page started about [modern GNSS signals](docs/pages/signal_issues.md).

<HR> 

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and 
NASA (NNX12AK21G and NNX13AF43G). <code>gnssrefl</code> was initially developed 
as a fun post-retirement project, followed by support from NASA (80NSSC20K1731).

Our funding ends August 31. Please help us in maintaining this code. 

Kristine M. Larson

June 21, 2023

<HR>



