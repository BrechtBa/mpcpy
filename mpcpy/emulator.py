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

import sys
import numpy as np

class Emulator(object):
	def __init__(self,dymola,inputs,initializationtime=1,**kwargs):
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
		
		# check for additional dymola arguments
		self.simulation_args = {}
		for key in kwargs:
			if key in ['OutputInterval','NumberOfIntervals','Tolerance','FixedStepSize','Algorithm']:
				self.simulation_args[key] = kwargs[key]
				
		
	def initialize(self):
		self.dymola.set_parameters(self.initial_conditions)
		self.dymola.set_parameters(self.parameters)
	
		# clear the result dict
		self.res = {}
		
		# simulate the model for a very short time to get the initial states in the res dict
		self.dymola.simulate(StartTime=0,StopTime=self.initializationtime)
		res = self.dymola.get_result()
		
		# remove the initial conditions and parameters which are not in the results file
		redosim = False
		keystoremove = []
		for key in self.initial_conditions:
			if not key in res:
				keystoremove.append(key)
				redosim = True
				
		for key in keystoremove:
			del self.initial_conditions[key]
				
		keystoremove = []		
		for key in self.parameters:
			if not key in res:
				keystoremove.append(key)
				redosim = True
				
		for key in keystoremove:
			del self.parameters[key]
		
		# redo the simulation if required
		if redosim:
			self.dymola.set_parameters(self.initial_conditions)
			
			self.dymola.set_parameters(self.parameters)
			self.dymola.simulate(StartTime=0,StopTime=self.initializationtime)
			res = self.dymola.get_result()
			
		
		for key in res:
			self.res[key] = np.array([res[key][0]])
				
				
	def set_initial_conditions(self,ini):
		"""
		Arguments:
		ini    dictionary with initial conditions
		"""
		# set only the last value for each key
		for key in ini:
			try:
				self.initial_conditions[key] = ini[key][-1];
			except:
				self.initial_conditions[key] = ini[key];
		
	def set_parameters(self,par):
		"""
		Arguments:
		par    dictionary with parameters
		"""
		self.parameters = par
		
	def __call__(self,time,input):
		"""
		Calculate values of the system variables for the length of the inputs
		Uses the value of _state as starting point and sets the value at the end of the simulation
		
		Arguments:
		time: numpy array, times at which the results are requested
		inputs: dict, dictionary with values for the inputs of the model, time must be a part of it
		
		Example:
		em = Emulator()
		t  = np.arange(0.,3600.1,600.)
		u1 = 5.*np.ones_like(t)
		em(t,['time':t,'u1':u1])
		"""
		
		# simulation
		self.dymola.write_dsu(input)
		try:
			self.dymola.dsfinal2dsin()
		except:
			pass
		
		try:
			self.dymola.simulate(StartTime=time[0],StopTime=time[-1],**self.simulation_args)
		except:
			print('Ignoring error during simulation at time {}'.format(input['time'][0]));
			
		try:
			res = self.dymola.get_result()
		except:
			print('Ignoring error while loading dymola res file at time {}'.format(input['time'][0]));
		
		
		# adding the inputs to the result
		for key in input.keys():
			# make sure not to do double adding
			if not key in res.keys():
				if key in self.res:
					# append the result
					if len(input[key]) == 1:
						self.res[key] = input[key]
					else:
						self.res[key] = np.append(self.res[key][:-1],np.interp(time,input['time'],input[key]))
				else:
					self.res[key] = np.interp(time,input['time'],input[key])
		
		# interpolate results to the input points in time
		for key in res.keys():
			if key in self.res:
				# append the result
				if len(res[key]) == 1:
					self.res[key] = res[key]
				else:
					if key == 'time':
						self.res[key] = np.append(self.res[key][:-1],time)
					else:
						self.res[key] = np.append(self.res[key][:-1],np.interp(time,res['time'],res[key]))
						
			else:
				if len(res[key]) == 1:
					self.res[key] = res[key]
				else:
					self.res[key] = np.interp(time,res['time'],res[key])
			
			
def interp_averaged(t,tp,yp):
	y = np.zeros_like(t)
	for i in range(len(t)-1):
		y[i] = np.mean(yp[np.where( (tp>=t[i]) & (tp<t[i+1]) )])
		
	y[-1] = np.interp(t[-1],tp,yp)
	
	return y

class Nodymola():
	"""
	A class with the required methods to test things when Dymola is not available
	"""
	def __init__(self):
		pass
	def openModel(self,filename):
		pass
	def clear(self):
		pass
	def compile(self,modelname,parameters=None):
		pass
	def simulate(self,StartTime=0,StopTime=1,OutputInterval=0,NumberOfIntervals=500,Tolerance=1e-4,FixedStepSize=0,Algorithm='dassl'):
		pass
	def set_parameters(self,pardict):
		pass
	def get_result(self):
		return {}
	def write_dsu(self,inputdict):
		pass
	def get_res(self,par):
		return []
	def dsfinal2dsin(self):
		pass
	def run_cmd(self,cmd):
		pass