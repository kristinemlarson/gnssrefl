from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["numpy","wget","scipy","matplotlib","requests"]

setup(
    name="gnssrefl",
    version="0.0.15",
    author="Kristine Larson",
    author_email="kristine.larson@colorado.edu",
    description="A GNSS reflectometry software package ",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/kristinemlarson/gnssrefl/",
    packages=find_packages(),
    entry_points ={ 
        'console_scripts': [ 
            'gnssir = gnssrefl.gnssir_cl:main',
            'rinex2snr = gnssrefl.rinex2snr_cl:main',
            'quickLook= gnssrefl.quickLook_cl:main',
            'download_rinex = gnssrefl.download_rinex:main',
            'make_json_input = gnssrefl.make_json_input:main',
            ], 
        },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
