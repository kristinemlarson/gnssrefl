## when you make a new version

Use 1.5.1 as an sample version number

- change the version number in setup.py.  

- change the version in the README.md

- change the version number in CHANGELOG.md and provide 
a description of the main changes in this new version.

- push the code to github, git push origin master

- git tag 1.5.1 

- git push --tags

The latter will tell github to make a new pypi version.

git push origin master will make a new docker.


Install a new python:

- sudo apt install python3.9

Get a list of your outdated packages

- pip list --outdated

How to update them all? The horror, the horror


$EXE/gfzrnx -finp rinex3 -fout  rinex2 -vo 2 -ot G:S1C
