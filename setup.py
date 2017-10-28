#!/usr/bin/env python
from setuptools import setup, find_packages
import os

setuppath = os.path.dirname(os.path.abspath(__file__))

# retrieve the version
try:
    versionfile = os.path.join(setuppath, 'mpcpy', '__version__.py')
    f = open(versionfile, 'r')
    content = f.readline()
    splitcontent = content.split('\'')
    version = splitcontent[1]
    f.close()
except:
    raise Exception('Could not determine the version from mpcpy/__version__.py')


# run the setup command
setup(
    name='mpcpy',
    version=version,
    license='GPLv3',
    description='A package to run MPC, moving horizon simulations in Python.',
    long_description=open(os.path.join(setuppath, 'README.rst')).read(),
    url='https://github.com/BrechtBa/mpcpy',
    author='Brecht Baeten',
    author_email='brecht.baeten@gmail.com',
    packages=find_packages(),
    install_requires=['numpy'],
    extras_require={
        'dev': [
            'pyomo',
            'matplotlib'
        ]
    },
    classifiers=['Programming Language :: Python :: 2.7'],
)