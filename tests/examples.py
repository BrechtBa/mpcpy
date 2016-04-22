#!/usr/bin/env python
################################################################################
#    Copyright 2015 Brecht Baeten
#    This file is part of mpcpy.
#
#    mpcpy is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    mpcpy is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with mpcpy.  If not, see <http://www.gnu.org/licenses/>.
################################################################################

import unittest
import mpcpy
import numpy as np
import sys
import os
import subprocess

# current path
modulepath = os.path.dirname(sys.modules['mpcpy'].__file__)
examplespath =  os.path.join(modulepath,'..','examples')

# define null file
fnull = open(os.devnull, 'w')

class TestExamples(unittest.TestCase):
	
	def test_example(self):
	
		currentdir = os.getcwd()
		os.chdir(examplespath)
		
		p = subprocess.Popen(["runipy", "example.ipynb"], stdout=fnull, stderr=subprocess.PIPE)
		output,error = p.communicate()
		
		os.chdir(currentdir)
		
		self.assertEqual(p.returncode,0,error)

	def test_cplex_example(self):
		
		currentdir = os.getcwd()
		os.chdir(examplespath)
		
		p = subprocess.Popen(["runipy", "cplex_example.ipynb"], stdout=fnull, stderr=subprocess.PIPE)
		output,error = p.communicate()
		
		os.chdir(currentdir)
		
		self.assertEqual(p.returncode,0,error)

	
	
		
if __name__ == '__main__':
    unittest.main()