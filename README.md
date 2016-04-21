mpcpy
=====

A group of classes to run model predictive control (MPC) simulations using python and Dymola.

## Installation
requires:
* `numpy`

To install download the latest [release](https://github.com/BrechtBa/mpcpy/releases), unpack, cd to the unpacked folder and run:
```
python setup.py install
```

## Examples
In the examples folder some documented examples of how to work with mpcpy are available as IPython Notebooks.

This example should get you started with mpcpy
 - [Simple space heating mpc](https://github.com/BrechtBa/mpcpy/blob/master/examples/example.ipynb)


# Cplex in Python
IBM ILOG CPlex has it's own API for python. 

## Installation
The following instructions were adapted from [here](http://www-01.ibm.com/support/knowledgecenter/SSSA5P_12.6.2/ilog.odms.cplex.help/CPLEX/GettingStarted/topics/set_up/Python_setup.html?lang=en)
Go to the directory you installed CPlex in 'YOURCPLEXDIR', on windows this could be `C:\Program Files (x86)\IBM\ILOG\CPLEX_Studio1261\cplex`.
Now go to `YOURCPLEXDIR/python/VERSION/PLATFORM` where VERSION is your python version (2.7 or 3.4 most likely) and PLATFORM is your platform (for instance x86_win32 on a 32 bit windows computer). 

Now it is best to install the cplex package in your package directory ('YOURPYTHONPACKAGEDIR') as this is where python searches for packages.
On a windows system with python 2.7 this is probably `C:\Python27\Lib\site-packages`
This is done by running the following command in a terminal:
```
python setup.py install --home YOURPYTHONPACKAGEDIR/cplex
```

## Examples
 - [Cplex python API](https://github.com/BrechtBa/mpcpy/blob/master/examples/cplex_example.ipynb)


