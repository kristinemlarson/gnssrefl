from setuptools import setup, find_packages

with open("README.md", "r") as readme_file:
    readme = readme_file.read()

requirements = ["numpy","wget","scipy","matplotlib"]

setup(
    name="gnssrefl",
    version="0.0.1",
    author="Kristine M. Larson",
    author_email="kristinem.larson@gmail.com",
    description="A GNSS reflections package",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/kristinemlarson/gnssrefl/",
    packages=find_packages(),
    install_requires=requirements,
    classifiers=[
        "Programming Language :: Python :: 3.7",
    ],
)
