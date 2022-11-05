# Community and Questions

## Acknowledgements
- [Radon Rosborough](https://github.com/raxod502) helped with 
python/packaging questions and improved our docker distribution. 
- [Naoya Kadota](https://github.com/naoyakadota) added the GSI data archive. 
- Joakim Strandberg provided python RINEX translators. 
- Johannes Boehm provided source code for the refraction correction. 
- At UNAVCO, Kelly Enloe made Jupyter notebooks and Tim Dittmann made docker builds. 
- Makan Karegar added the NMEA capability.
- Dave Purnell provided his inversion code, which is now running in the <code>invsnr</code> capability.  
- Carolyn Roesler helped with the original Matlab codes.
- Felipe Nievinski and Simon Williams have provided significant advice for this project.
- Clara Chew and Eric Small developed the soil moisture algorithm; I ported it to python with Kelly's help.

GNSS-IR was developed with funding from NSF (ATM 0740515, EAR 0948957, AGS 0935725, EAR 1144221, AGS 1449554) and NASA (NNX12AK21G and NNX13AF43G).
The python package development, docker distributions and jupyter notebooks are supported under NASA 80NSSC20K1731.
For relevant citations, the code is citable via `doi <https://doi.org/10.5281/zenodo.5601495>`__, and the methods are covered in gnssrefl `publications <https://www.kristinelarson.net/publications>`__.

Authors and maintainers: Dr. Kristine M. Larson, Kelly Enloe and Tim Dittmann

[https://kristinelarson.net](https://kristinelarson.net)


## We need help to maintain and improve this code. How can you help?

- Archives are *constantly* changing their file transfer protocols. If you 
find one in <code>gnssrefl</code> that doesn't work anymore,
please fix it and let us know. Please test that it 
works for both older and newer data.

- If you would like to add an archive, please do so. Use the existing code in gps.py as a starting point. 

- We need better models for GNSS-IR far more than we need more journal articles finding that the 
method works. And we need these models to be in python. 

- I would like to add a significant wave height calculation to this code. If you have such code that 
works on fitting the spectrum computed with detrended SNR data, please consider contributing it.

- If you have a better refraction correction than we are using, please provide it to us as a function in python.

- Write up a new [use case](https://github.com/kristinemlarson/gnssrefl/blob/master/tests/first_drivethru.md).

- Investigate surface related biases for polar tide gauge calculations (ice vs water).

- I have ported NOCtide.m and will add it here when I get a chance.

## How to get help with your gnssrefl questions?

If you are new to the software, you should consider watching the 
[videos about GNSS-IR](https://www.youtube.com/playlist?list=PL9KIPkLxL-c_d-NlNsaoGgScWqSxxUB5n)

Before you ask for help - a few things to ask yourself:

Are you running the current software?

- gnssrefl command line  <code>git pull </code>

- gnssrefl docker command line  <code>docker pull unavdocker/gnssrefl</code>

- gnssrefl jupyter notebook  <code>git pull</code>

- gnssrefl jupyter notebook docker <code>docker pull unavdocker/gnssrefl_jupyter</code>

You are encouraged to submit your concerns as an issue to 
the [github repository](https://github.com/kristinemlarson/gnssrefl). If you are unfamiliar 
with github, you can also email Kelly (enloe@unavco.org ) about Jupyter 
NoteBooks or Tim (dittmann@unavco.org) for commandline/docker issues.

Please

- include the exact command or section of code you were running that prompted your question.

- Include details such as the error message or behavior you are getting. 
Please copy and paste (this is preferred over a screenshot) the error string. 
If the string is long - please post the error string in a thread response to your question.

- Please include the operating system of your computer.

## Would you like to join our <code>gnssrefl</code> users email list?
Send an email to community@unavco.org and put the words
*subscribe (or unsubscribe to leave) to gnss-ir* in your email subject.


<HR>