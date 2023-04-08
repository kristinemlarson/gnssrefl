# Community 

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
- Sree Ram Radha Krishnan ported the rzones web app code.
- Dan Nowacki added Glonass to the NMEA reader

Authors and maintainers: [Kristine M. Larson](https://kristinelarson.net), Kelly Enloe, and Tim Dittmann


## How you can help improve this code

- Archives frequently change their file transfer protocols. If you find one in <code>gnssrefl</code> that doesn't work anymore,
please fix it and let us know. Please test that it works for both older and newer data.

- If you would like to add an archive, please do so. Use the existing code in gps.py as a starting point. 

- Check the [issues section](https://github.com/kristinemlarson/gnssrefl/issues) of the repository and look for "help wanted."

- Write up a new [use case](https://github.com/kristinemlarson/gnssrefl/blob/master/tests/first_drivethru.md).

- Investigate surface related biases.

## How to get help with your gnssrefl questions

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

Would you like to join our <code>gnssrefl</code> users email list?
This is currently operated by earthscope.org.  To join, please send Kristine an email.

Updated April 7, 2023  by Kristine M. Larson

[Old news section from before we moved to readthedocs](docs/pages/old_news.md)

