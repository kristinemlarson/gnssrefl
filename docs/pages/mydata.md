# How do I analyze my own GNSS data?

To analyze your own GNSS data you must 

- comply with the software expectations for how the files should be named. 

- make sure the files have the expected information in them (e.g. SNR data, RINEX files must 
have a priori coordinates in the header)

- files are stored in the expected directories.

The naming conventions for GNSS observation files are given in the 
[files page](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html).

For questions about expected folders, see 
the [rinex2snr documentation](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.rinex2snr_cl.html)

If you have questions about converting NMEA files, the best I can offer is that you read
the description in the [files page](https://gnssrefl.readthedocs.io/en/latest/pages/file_structure.html) and 
possibly the [nmea2snr documentation](https://gnssrefl.readthedocs.io/en/latest/api/gnssrefl.nmea2snr_cl.html)

For docker users, there is some additional information in the [install page](https://gnssrefl.readthedocs.io/en/latest/pages/docker_cl_instructions.html).

For notebook users, you must contact Kelly Enloe at Earthscope if you have questions about how to analyze your own data.


