from setuptools import find_packages, setup
import os

with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    REQ = f.read().splitlines()

# get __version__ from _version.py
ver_file = os.path.join('IoTPy', '_version.py')
with open(ver_file) as f:
    exec(f.read())

VER = __version__

CLASSIFIERS = ['Intended Audience :: Science/Research',
               'Intended Audience :: Developers',
               'License :: OSI Approved :: BSD License',
               'Programming Language :: Python',
               'Topic :: Software Development',
               'Topic :: Scientific/Engineering',
               'Operating System :: Microsoft :: Windows',
               'Operating System :: POSIX',
               'Operating System :: Unix',
               'Operating System :: MacOS',
               'Programming Language :: Python :: 3.5',
               'Programming Language :: Python :: 3.6',
               'Programming Language :: Python :: 3.7',
	       'Programming Language :: Python :: 3.8']

setup(
    name="IoTPy", 
    version=VER,
    author="Mani Chandy",
    author_email="",
    description="IoTPy - Python for Streams",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/AssembleSoftware/IoTPy",
    classifiers= CLASSIFIERS,
    packages = find_packages(),
    install_requires = REQ
)

