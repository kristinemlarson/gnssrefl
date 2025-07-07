# Community Information 

## E-mail list
Would you like to join our <code>gnssrefl</code> users email list?
This is currently maintained by earthscope.org. To join, please e-mail 
melissa.weber@earthscope.org or Kristine Larson.

## Citation for gnssrefl

- [Larson K.M., gnssrefl: an open source python software package for environmental GNSS interferometric reflectometry applications, GPS Solutions, Volume 28, article number 165, 2024](https://link.springer.com/article/10.1007/s10291-024-01694-8)

## Acknowledgements

- [Kristine M. Larson](https://kristinelarson.net) Overall 
- [Kelly Enloe](https://github.com/k-enloe) Jupyter Notebooks
- [Tim Dittmann](https://github.com/timdittmann) Access to Dockers
- [Radon Rosborough](https://github.com/raxod502) helped with python/packaging questions, improved our docker distribution, and 
set up smoke tests. 
- [Naoya Kadota](https://github.com/naoyakadota) added the GSI data archive and helped find a bug in nmea2snr. 
- [Joakim Strandberg](https://github.com/Ydmir) provided python RINEX translators and the EGM96 code. 
- Johannes Boehm provided source code for the refraction correction. 
- [Makan Karegar](https://github.com/MakanAKaregar) added the NMEA capability.
- [Dave Purnell](https://github.com/purnelldj) provided his SNR inversion code. 
- Carolyn Roesler helped with the original GNSS-IR Matlab codes.
- [Felipe Nievinski](https://github.com/fgnievinski) and Simon Williams have provided significant advice for this project.
- Clara Chew and Eric Small developed the soil moisture algorithm; I ported it to python with Kelly's help.
- [Sree Ram Radha Krishnan](https://github.com/sreeram-radhakrishnan) ported the rzones web app code.
- [Dan Nowacki](https://github.com/dnowacki-usgs) added 
Glonass to the NMEA reader
- [Taylor Smith](https://github.com/tasmi) has worked on the NMEA reader and the refl_zones utility.
- Surui Xie and Thomas Nylen were instrumental in finding a bug in the newarcs version
- Peng Feng, Rudiger Haas, and Gunnar Elgered have helped us improve refraction models.

## 2023 Short Course  on GNSS-IR
- [overview](https://gnssrefl.readthedocs.io/en/latest/pages/sc_index.html)
- [videos/lectures](https://gnssrefl.readthedocs.io/en/latest/pages/sc_media.html)

## 2024 Short Course on GNSS-IR for Water Level Measurements
- [index](https://gnssrefl.readthedocs.io/en/latest/pages/sc_index2024.html)
- videos are on Kristine's youtube page.

## How you can help improve this code

- Archives frequently change their file transfer protocols. If you find one 
in <code>gnssrefl</code> that doesn't work anymore,
please fix it and let us know. Please test that it works for both older and newer data.

- If you would like to add an archive, please do so. Use the existing code as a starting point. 

- Check the [issues section](https://github.com/kristinemlarson/gnssrefl/issues) of the 
repository and look for "help wanted."

- Write up a new [use case](https://gnssrefl.readthedocs.io/en/latest/pages/first_drivethru.html)

- Investigate surface related biases.

## How to get help with your gnssrefl questions

If you are new to the software, you should consider watching the 
[videos about GNSS-IR](https://www.youtube.com/playlist?list=PL9KIPkLxL-c_d-NlNsaoGgScWqSxxUB5n)

Before you ask for help - you should check to see if you are running the current software.
Please go to the install page for help on how to update your latest 
docker/jupyter installs. For github/pypi, we recommend doing a clean download and new install.

You are encouraged to submit your concerns as an **Issue** to 
the [github repository](https://github.com/kristinemlarson/gnssrefl). 

Please include

* the exact command or section of code you were running that prompted your question.

* details such as the error message or behavior you are getting. 
Please copy and paste (this is preferred over a screenshot) the error string. 
If the string is long - please post the error string in a thread response to your question.

* the operating system of your computer.

**We are not able to answer any questions about Jupyter Notebooks. These were developed 
by Earthscope and unfortunately they no longer help maintain them.**

[Old news section from before we moved to readthedocs](https://gnssrefl.readthedocs.io/en/latest/pages/old_news.html)

I have removed the publications section.

Kristine M. Larson


