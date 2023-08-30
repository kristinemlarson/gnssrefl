# GPS  Tool Box

## mnis00aus

This is a use case put together to allow the GPS Tool Box to test instllation
and operation of the code. It is not meant to be as detailed (wordy) as our other use cases.
Our preference is that you use the docker because that way we can be 
sure you are using a compatible version of python. If you are able to install
version 1.6.0 (using git clone or pip install), you should see the same answers.

**you must have internet access to run this test case**

Step one: install the docker software from docker.com

Step two: install gnssrefl version 1.6.0

Step three: analyze mnis00aus data

The RINEX 3 files for this site have been downloaded from geoscience australia.
They were then translated to RINEX 2.11 and stored at public website. We will 
use this dataset in order to be sure that you have access to the needed RINEX files.

wget https://morefunwithgps.com/public_html/mnis2023.tar

tar -xvf mnis2023.tar

rinex2snr mnis 2023 151 -doy_end 164 -nolook T -orb gnss

query_unr mnis

nyquist mnis -e1 5 -e2 15

refl_zones mnis -el_list 5 10 15


quickLook mnis 2023 151 -h2 12 -h1 4 -e2 15


gnssir_input mnis -h1 4 -h2 12 -e1 5 -e2 15 -allfreq T -azlist2 120 240 -ampl 5 -delTmax 45
 

gnssir mnis 2023 151 -doy_end 164
 

subdaily mnis 2023  


