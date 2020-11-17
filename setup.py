from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["numpy","wget","scipy","matplotlib","requests"]

setup(
    name="gnssrefl",
    version="0.0.33",
    author="Kristine Larson",
    author_email="kristine.larson@colorado.edu",
    description="A GNSS reflectometry software package ",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/kristinemlarson/gnssrefl/",
    packages=find_packages(),
    include_package_data=True,
    entry_points ={ 
        'console_scripts': [ 
            'gnssir = gnssrefl.gnssir_cl:main',
            'rinex2snr = gnssrefl.rinex2snr_cl:main',
            'daily_avg = gnssrefl.daily_avg:main',
            'quickLook= gnssrefl.quickLook_cl:main',
            'download_rinex = gnssrefl.download_rinex:main',
            'download_orbits = gnssrefl.download_orbits:main',
            'make_json_input = gnssrefl.make_json_input:main',
            'ymd = gnssrefl.ymd:main',
            'ydoy = gnssrefl.ydoy:main',
            'xyz2llh = gnssrefl.xyz2llh:main',
            'llh2xyz = gnssrefl.llh2xyz:main',
            ], 
        },
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
    ],
)
