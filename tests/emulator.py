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
import dympy

# define variables
val = 123

# current path
modulepath = os.path.dirname(sys.modules[__name__].__file__)

dymola = dympy.Dymola()
dymola.clear()
dymola.openModel(os.path.join(modulepath,'data','example.mo'))
dymola.compile('example')

inputlist = ['T_amb','Q_flow_sol','Q_flow_hp']
ini = {'C_em.T': 22+273.15, 'C_in.T': 21+273.15}
par = {'C_em.C': 10e6,
       'C_in.C': 5e6,
	   'UA_in_amb.G': 200,
	   'UA_em_in.G': 1600}
inp = {'time': [0., 3600., 7200.],
	   'T_amb': [273.15, 274.15, 275.15],
	   'Q_flow_sol': [500., 400., 300.],
	   'Q_flow_hp': [4000., 4000., 4000.]}

class TestEmulator(unittest.TestCase):
	
	def test_create(self):
		
		emulator = mpcpy.Emulator(dymola,inputlist)

	def test_create_initializationtime(self):
		
		emulator = mpcpy.Emulator(dymola,inputlist,initializationtime=0.1)

	def test_initialize(self):
	
		emulator = mpcpy.Emulator(dymola,inputlist)
		emulator.initialize()
	
	def test_set_initial_conditions(self):
	
		emulator = mpcpy.Emulator(dymola,inputlist)
		emulator.set_initial_conditions(ini)
		
	def test_set_parameters(self):
	
		emulator = mpcpy.Emulator(dymola,inputlist)
		emulator.set_parameters(par)	
		
	def test_call(self):
	
		emulator = mpcpy.Emulator(dymola,inputlist)
		emulator(inp['time'],inp)
		
	def test_call_after_initialization(self):
	
		emulator = mpcpy.Emulator(dymola,inputlist)
		emulator.initialize()
		emulator(inp['time'],inp)
		
if __name__ == '__main__':
    unittest.main()