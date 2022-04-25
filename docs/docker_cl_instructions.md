# Assistance on deploying gnssrefl docker image from dockerhub
(Feedback on these instructions is appreciated!)

[docker hub image](https://hub.docker.com/repository/docker/unavdocker/gnssrefl)

for jupyter notebook version, please see [gnssrefl_jupyter instructions](https://www.unavco.org/gitlab/gnss_reflectometry/gnssrefl_jupyter)
## Install Docker
&ensp;&ensp; Pick your system and follow instructions on the Docker website. 
* **Mac** - https://docs.docker.com/docker-for-mac/install/ 
* **Windows** - https://docs.docker.com/docker-for-windows/install/ 
* **Ubuntu** - https://docs.docker.com/install/linux/docker-ce/ubuntu/ 

*Once installed, type `docker run hello-world` in terminal to check if installed correctly.*

More information on [getting started, testing your installation, and developing.](https://docs.docker.com/get-started/) 

Useful tool to use is [Docker Desktop](https://www.docker.com/products/docker-desktop)

## gnssrefl Docker Run
* cd into the local directory that you wish to keep your processed results
* <code>docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/ -v $(pwd)/refl_code/Files:/etc/gnssrefl/refl_code/Files unavdocker/gnssrefl:latest /bin/bash</code>

(Description of the commands used:  <code>-it</code> calls interactive process (bin/bash shell); <code>-v</code> mounts external volumes to allow the user to keep their processing results and figures)

### notes:
* docker has vim for editing text files (ie .json station config file)
* if you want to process rinex files already on your local machine, you can copy them into /refl_code/ local directory that is mounted to the container.  If you have a lot of rinex and want to keep organized, you could copy into refl_code/rinex/station/cyyy/, where station is the 4char ID and cyyy is the 4char year, and then mount that directory in the docker run command as follows: <code> docker run -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/ -v $(pwd)/refl_code/Files:/etc/gnssrefl/refl_code/Files/ -v $(pwd)/refl_code/rinex/station/cyyy:/etc/gnssrefl/refl_code/rinex/station/cyyy/ unavdocker/gnssrefl:latest /bin/bash </code>

## For WINDOWS USERS (thank you Paul Wu at Univ of CO for this):
* install [Docker for Windows](https://desktop.docker.com/win/main/amd64/Docker%20Desktop%20Installer.exe)
	* Problem: <code>WSL2 Installation is incomplete</code>.  
		* Solution: Need to download and install [from step 4](https://docs.microsoft.com/en-us/windows/wsl/install-manual#step-4---download-the-linux-kernel-update-package)
	* Problem Docker stuck at initial stage
		* Solution: restart the computer after docker installation


* execute docker run command (see above) in terminal window
* Feeback from jupyter notebook user:
	* About folder permission: When I ran homework 0 for the environment test, the error prompted out that the program could not write to the file. Therefore, I used the command line to change the permissions of the folder and the problem was solved.

## additional references:
* [gnssrefl docker base image dockerfile](https://gitlab.com/gnss_reflectometry/gnssrefl_docker_base_img/-/blob/master/Dockerfile)
* [gnssrefl docker file](https://github.com/kristinemlarson/gnssrefl/blob/master/Dockerfile)


