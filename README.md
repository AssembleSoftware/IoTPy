<div align="center">    
 
# IoTPy: Python + Streams

</div>

## Description

IoTPy is a Python package that helps you to build applications that operate on streams of data.

The two goals of IoTPy:

* Build non-terminating functions that operate on endless streams by reusing terminating functions, such as those in libraries like NumPy and SciPy.

* Build multithreaded, multicore, distributed applications by simply connecting streams.

Sensors, social media, news feeds, webcams and other sources generate streams of data. Many applications ingest and analyze data streams to control actuators, generate alerts, and feed continuous displays. IoTPy helps you to build such applications.

IoTPy is distributed under the 3-Clause BSD license. Collaborations are welcome.

Look at AssembleSoftware.com for documentation and tutorials.

## Installation
Clone the GitHub repository.

### Dependencies
* Python (>=3.5)
* NumPy (>=1.18.4)

For distributed applications, additional dependencies include the following:
* Pika (1.1.0)
Note that Pika may require other software to run.

### User Installation
You can clone the GitHub repository.

Another easy way to install IoTPy is using ```pip3``` as shows below.
```bash
pip3 install IoTPy
```
To install from source, please proceed as shown below:
```bash
git clone https://github.com/AssembleSoftware/IoTPy.git
cd IoTPy
python3 setup.py install
```

## Examples

* Please see the [Jupyter Notebooks](https://github.com/AssembleSoftware/IoTPy/tree/master/examples) inside the Examples directory above. We have several examples demonstrating a variety of applications that have been developed using IoTPy.


## Documentation

A good way to understand the code is to read the examples in the
Jupyter notebooks, Stream.ipynb and ExampleOperators.ipynb, in GitHub.

* Our project website is [AssembleSoftware](https://www.assemblesoftware.com/). 

## Contributors

Several people have contributed to IoTPy. To view the list of contributors, please visit [this](https://www.assemblesoftware.com/people-k-mani-chandy) link on AssembleSoftware.




