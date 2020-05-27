from setuptools import find_packages, setup


with open("README.md", "r") as fh:
    long_description = fh.read()

with open("requirements.txt") as f:
    REQ = f.read().splitlines()


CLASSIFIERS = ['Intended Audience :: Science/Research',
               'Intended Audience :: Developers',
               'License :: OSI Approved',
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
    name="IoTPy", # Replace with your own username
    version="1.0.0",
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

