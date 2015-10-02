#!/usr/bin/python
######################################################################################
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
######################################################################################

import sys
import numpy as np

class Emulator:
	def __init__(self,dymola,inputs,initializationtime = 1):
		"""
		Initialize a dympy object for use as an MPC emulation
		
		Arguments:
		dymola: a dympy object with an opened and compiled dymola model
		inputs: a list of strings of the variable names of the inputs
		"""
		
		self.inputs = inputs
		self.initializationtime = initializationtime
		
		self.dymola = dymola
		self.initial_conditions = {}
		self.parameters = {}
		self.res = {}
		
	def initialize(self):
		self.dymola.set_parameters(self.initial_conditions)
		self.dymola.set_parameters(self.parameters)
		
		# clear the result dict
		self.res = {}
		
		# simulate the model for a very short time to get the initial states in the res dict
		self.dymola.simulate(StartTime=0,StopTime=self.initializationtime)
		res = self.dymola.get_result()
		for key in res.keys():
			self.res[key] = np.array([res[key][0]])
				
	def set_initial_conditions(self,ini):
		"""
		Arguments:
		ini    dictionary with initial conditions
		"""
		self.initial_conditions = ini;
		
	def set_parameters(self,par):
		"""
		Arguments:
		par    dictionary with parameters
		"""
		self.parameters = par
		
	def __call__(self,input):
		"""
		Calculate values of the system variables for the length of the inputs
		Uses the value of _state as starting point and sets the value at the end of the simulation
		
		Arguments:
		inputs: dictionary with values for the inputs of the model, time must be a part of it
		
		Example:
		em = Emulator()
		t = np.arange(0.,3600.1,600.)
		u1 = 5.*np.ones_like(t)
		em(t,['u1':u1])
		"""
		
		# simulation
		self.dymola.write_dsu(input)
		try:
			self.dymola.dsfinal2dsin()
		except:
			pass
			
		self.dymola.simulate(StartTime=input['time'][0],StopTime=input['time'][-1],Tolerance=0.0001)
		res = self.dymola.get_result()
		
		
		# adding the inputs to the result
		for key in input.keys():
			# make sure not to do double adding
			if not key in res.keys():
				if key in self.res:
					# append the result
					if len(input[key]) == 1:
						self.res[key] = input[key]
					else:
						self.res[key] = np.append(self.res[key][:-1],np.interp(input['time'],input['time'],input[key]))
				else:
					self.res[key] = np.interp(input['time'],input['time'],input[key])
		
		# interpolate results to the input points in time	
		for key in res.keys():
			if key in self.res:
				# append the result
				if len(res[key]) == 1:
					self.res[key] = res[key]
				else:
					self.res[key] = np.append(self.res[key][:-1],np.interp(input['time'],res['time'],res[key]))
			else:
				self.res[key] = np.interp(input['time'],res['time'],res[key])