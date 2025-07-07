# Jupyter Notebook Installation Instructions

Notebooks are no longer supported by the Earthscope team that developed them. You are free to submit an Issue on github,
but as the README indicates, Earthscope expects the community to fix these issues themselves. 

Listed below are the original instructions that we posted for running jupyter notebooks with Docker (recommended) or on your local machine.

If you have run the notebooks in the past, the first thing you should do is update your docker. Look below to the **Update 
Docker Image**.

## Run Jupyter Notebooks with Docker (Recommended method)
### Install Docker
&ensp;&ensp; Pick your system and follow instructions on the Docker website. 
* [**Mac**](https://docs.docker.com/docker-for-mac/install/) 
* [**Windows**](https://docs.docker.com/docker-for-windows/install/)
* [**Ubuntu**](https://docs.docker.com/install/linux/docker-ce/ubuntu/) 

Once installed, type `docker run hello-world` in terminal to check if installed correctly.

More information on [getting started, testing your installation, and developing.](https://docs.docker.com/get-started/) 

[Docker Desktop](https://www.docker.com/products/docker-desktop) is a useful tool.

Note for **Windows** users: Please see these [Windows users install instructions](https://gnssrefl.readthedocs.io/en/latest/pages/docker_cl_instructions.html#for-windows-users).
Please note the volume mounting must have local paths consistent with windows paths. The examples given in this page work for linux/macos paths.


### Run gnssrefl jupyter Docker

Reminder: If you want to process EarthScope data, you will need to create [an EarthScope profile.](https://data.unavco.org/user/profile/info).

In a terminal, change directory into the local directory that you wish to keep your processed results and run

```bash
docker run -p 8888:8888 -it -v $(pwd):/etc/gnssrefl/refl_code -w /etc/gnssrefl/ --name gnssrefl_jupyter ghcr.io/kristinemlarson/gnssrefl:latest jupyter lab --allow-root --port=8888 --ip=0.0.0.0
```

Description of the commands used:  

`-it` calls interactive process

`-v` mounts external volumes to allow the user to keep persisted data such as their processing results, figures, or personal notebooks. $(pwd) is your local current directory, but you can set this to a local path (ex: local/path:/etc/gnssrefl/refl_code).

`-w` sets the working directory inside the container to `/etc/gnssrefl/`. This way jupyter lab has access to both refl_code and the notebook directories.

When this runs, you will see instructions come to the terminal which will look something like..
```
    To access the server, open this file in a browser:
        file:///root/.local/share/jupyter/runtime/jpserver-1-open.html
    Or copy and paste one of these URLs:
        http://7832eef81a9f:8888/lab?token=34644528573e4273c194b671337166c5ad59189b577dbf10
        http://127.0.0.1:8888/lab?token=34644528573e4273c194b671337166c5ad59189b577dbf10
```
Select the last url (` http://127.0.0.1:8888/lab?token=...`) and paste it into a browser of your choice. This will open Jupyter Lab. On the left hand side, navigate to the notebooks directory, and you can open a notebook of your choice in either the 'learn-the-code' directory or the 'use-case' directory and begin! 

If you desire to create your own notebook or want to persist the changes you've made to a notebook (if you delete/update your container), then, while in the notebook, select `File + Save Notebook As...` and save it to your mounted volume. If you ran the `docker run` command above, then your volume is located at /etc/gnssrefl/refl_code. The Jupyter lab working directory is already /etc/gnssrefl/, so to save your notebook to refl_code just enter 'refl_code/my_notebook.ipynb'.

### Update Docker Image to newest version <a name="Update Docker"></a>

`docker pull ghcr.io/kristinemlarson/gnssrefl:latest`

### Notes:

If you want to process RINEX files that are stored on your local machine, you can copy 
them into the local directory associated with your mounted volume, i.e.
`refl_code/yyyy/rinex/abcd`, where station is abcd and yyyy is the year. 
There is an alternate directory structure you can also try, but it requires the use of 
the makan option when running rinex2snr. I cannot promise that it works. Please note below that
instead of mounting the one volume, you are mounting two. 

```bash
docker run -p 8888:8888 -it -v $(pwd)/refl_code:/etc/gnssrefl/refl_code/ -v $(pwd)/refl_code/rinex/station/yyyy:/etc/gnssrefl/refl_code/rinex/station/yyyy/ --name gnssrefl_jupyter ghcr.io/kristinemlarson/gnssrefl:latest jupyter lab --allow-root --port=8888 --ip=0.0.0.0 
```
### Shutdown Docker <a name="Shutdown"></a>
To exit the container and stop the jupyter instance, press `ctrl+c`. This will shut down jupyter lab as well as stop the docker containter.

After exiting, to re-start this container, run `docker start -i gnssrefl_jupyter`. Then find the url to jupyter lab once again and open it in your browser. Note: gnssrefl_jupyter is what we named the container in the docker run command.

To shut down the docker container run `docker stop gnssrefl`

If you need to see the container(s) you have running you can use `docker ps`

If you need to see all container(s) you can use `docker container ls -a`

You can also see and run all of these commands within [Docker Desktop](https://www.docker.com/products/docker-desktop) as well.


## additional references:
* [gnssrefl base image dockerfile](https://gitlab.com/gnss_reflectometry/gnssrefl_docker_base_img/-/blob/master/Dockerfile)
* [gnssrefl docker file](https://github.com/kristinemlarson/gnssrefl/blob/master/Dockerfile)


## Run Jupyter Notebooks locally

### Install gnssrefl and Clone the gnssrefl github repo
 Please follow the instructions to [install gnssrefl locally](https://gnssrefl.readthedocs.io/en/latest/pages/README_install.html#local-python-install). 
 Do not worry about the environment variables - the notebooks will set these for you. You can follow either the git-clone instructions or the PyPI instructions.
 
  If you followed the **PyPI** instructions, then you will still need to git clone or zip the [github repository](https://github.com/kristinemlarson/gnssrefl) to you local machine, but all you will need to keep is the notebooks directory.

  If you ran the **git-clone** instructions, you will need to keep the entire gnssrefl source code.

 ### Run Jupyter Lab
 Once you have the notebooks directory ([this](https://github.com/kristinemlarson/gnssrefl/tree/master/notebooks)), navigate into it and run `jupyter lab`. When this runs, it should open a browser for you running Jupyter Lab. If it does not open a browser, then the terminal will list the url you can place into a browser to run it. From here, you can navigate to any of the notebooks and run them. 
