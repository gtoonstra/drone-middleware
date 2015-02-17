import os
from setuptools import setup

# Utility function to read the README file.
# Used for the long_description.  It's nice, because now 1) we have a top level
# README file and 2) it's easier to type in the README file than to put a raw
# string in below ...
def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "dmw",
    version = "0.1",
    zip_safe=True,
    author = "Gerard Toonstra",
    author_email = "gtoonstra",
    description = ("Support library for python dmw"),
    license = "ISC",
    keywords = "drone middleware",
    url = "http://packages.python.org/dmw",
    packages=['dmw', 'tests'],
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Scientific/Engineering",
        "License :: OSI Approved :: ISC License",
        "Programming Language :: Python :: 2.7",
    ],
    install_requires=['pybonjour', 'pymavlink>=1.1.2']
)

