<div align="center">    
 
# IoTPy: Python + Streams

</div>

## Description

IoTPy is a Python package that helps you to build applications that operate on streams of data.

The two goals of IoTPy:

* Build non-terminating functions that operate on endless streams by reusing terminating functions, such as those in libraries like NumPy and SciPy.

* Build multithreaded, multicore, distributed applications by simply connecting streams.

Sensors, social media, news feeds, webcams and other sources generate streams of data. Many applications ingest and analyze data streams to control actuators, generate alerts, and feed continuous displays. IoTPy helps you to build such applications.

IoTPy is currently distributed under the 3-Clause BSD license.

## Installation

### Dependencies
* Python (>=3.5)
* NumPy (>=1.18.4)

For distributed applications, additional dependencies include the following 
* Pika (1.1.0)
Note that Pika may require other software to run.

### User Installation
The easiest way to install IoTPy is using ```pip``` as shows below.
```bash
pip install IoTPy
```
To install from source, please proceed as shown below:
```bash
git clone https://github.com/AssembleSoftware/IoTPy.git
cd IoTPy
python setup.py install
```
## Documentation

* Our project website is [AssembleSoftware](https://www.assemblesoftware.com/). We request anyone using IoTPy to visit the website to develop a better understading of IoTPy and its aims. 

* Documentation for the Code will be released soon. 

## Contributors

Several people have contributed to IoTPy. To view the list of contributors, please visit [this](https://www.assemblesoftware.com/people-k-mani-chandy) link on AssembleSoftware.

## Contributing

* We will soon create specific instructions for contributing to IoTPy.




