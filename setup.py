#!/usr/bin/env python
from setuptools import setup

setup(
    name='mpcpy',
    version='0.1.0',
    license='GNU GENERAL PUBLIC LICENSE',
	description='A package to run mpc simulations in Python with Dymola or other simulation packages',
	url='https://github.com/BrechtBa/mpcpy',
	author='Brecht Baeten',
	author_email='brecht.baeten@gmail.com',
	packages=['mpcpy'],
	install_requires=['numpy'],
	classifiers = ['Programming Language :: Python :: 2.7'],
)