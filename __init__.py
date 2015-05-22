#!/usr/bin/env python
# mpcPy
# Documentation


# import libraries
import sys
import numpy as np
import matplotlib.pyplot as plt
from pyfmi import load_fmu

###########################################################################
class Emulator:
	def __init__(self,filename,inputs,verbosity=50,rtol=1e-6,atol=1e-6,solver='CVode',initializationtime = 1):
		"""
		Initialise a fmu file for use as an MPC emulation
		Parameters:
		filename: path to fmu file relative to calling path
		inputs: a list of strings of the variable names of the inputs
		"""
		
		self.filename = filename
		self.model = load_fmu(self.filename)
		self.inputs = inputs
		
		self.simulate_options = self.model.simulate_options()
		
		self.simulate_options['initialize'] = False
		self.simulate_options['ncp'] = 60
		self.simulate_options['solver'] = solver
		self.simulate_options['CVode_options']['verbosity'] = verbosity
		self.simulate_options["CVode_options"]["rtol"] = rtol
		self.simulate_options["CVode_options"]["atol"] = atol
		#self.simulate_options["LSODAR_options"]["rtol"] = rtol
		#self.simulate_options["LSODAR_options"]["atol"] = atol
		self.model.initialize()
		self.res = {}
		
		
		self.initializationtime = initializationtime
		self.initialize()
		
	def initialize(self):
		# simulate the model for a very short time to get the initial states in the res dict
		res = self.model.simulate(start_time=0,final_time=self.initializationtime, options=self.simulate_options)
		for key in res.keys():
			self.res[key] = np.array([res[key][0]])
			
	def set_initial_conditions(self,ini):
		"""
		Inputs:
		ini    dictionary with initial conditions
		"""
		for key in ini:
			self.model.set(key,ini[key])
			self.res[key][-1] = ini[key]
	
		self.initialize()
		
	def set_parameters(self,par):
		"""
		Inputs:
		par    dictionary with parameters
		"""
		for key in par:
			self.model.set(key,par[key])
		
		self.initialize()
		
	def __call__(self,time,input):
		"""
		Calculate values of the system variables for the length of the inputs
		Uses the value of _state as starting point and sets the value at the end of the simulation
		Parameters:
		time: numpy array of time points where the solution should be returned
		inputs: dictionary with values for the inputs of the model
		
		Example:
		em = Emulator()
		t = np.arange(0.,3600.1,600.)
		u1 = 5.*np.ones_like(t)
		em(t,['u1':u1])
		"""
		
		# simulation
		input_tuple = self._create_input_tuple(time,input)
		res = self.model.simulate(start_time = time[0],final_time=time[-1],input=input_tuple, options=self.simulate_options)
		
		# interpolate results to the points in time
		if self.res != {}:
			for key in self.res.keys():
				self.res[key] = np.append(self.res[key][:-1],np.interp(time,res['time'],res[key]))
		else:
			for key in res.keys():
				self.res[key] = np.interp(time,res['time'],res[key])
			

	def _create_input_tuple(self,time,input):
		"""
		creates an input tuple to use in pyfmi simulate from a dictionary and a time vector
		"""
		
		values = time
		for key in input:
			values = np.vstack((values,input[key]))
		values = np.transpose(values)
			
		return (input.keys(),values)
	
	
###########################################################################
class Boundaryconditions:
	def __init__(self,bcs,periodic=True):
		"""
		Parameters:
		bcs:     		a dict with the actual boundary conditions and a time vector
		"""
		
		self.boundaryconditions = {}
		
		if periodic:
			# the entire dataset is repeated 3 times, once before the actual data, the actual data and once after the actual data
			# this implies the control horizon must be shorter than the boundary conditions dataset
			self.boundaryconditions['time'] = np.concatenate((bcs['time'][:-1]-bcs['time'][-1],bcs['time'],bcs['time'][1:]+bcs['time'][-1]))
			for key in bcs:
				if key != 'time':
					self.boundaryconditions[key] =  np.concatenate((bcs[key][:-1],bcs[key],bcs[key][1:]))
		else:
			# 1st and last value are repeated before and after the actual data
			self.boundaryconditions['time'] = np.concatenate((bcs['time'][:-1]-bcs['time'][-1],bcs['time'],bcs['time'][1:]+bcs['time'][-1]))
			for key in bcs:
				if key != 'time':
					self.boundaryconditions[key] =  np.concatenate((bcs[key][0]*np.ones(len(bcs['time'][:-1])),bcs[key],bcs[key][-1]*np.ones(len(bcs['time'][1:]))))
			
		
	def __call__(self,time):
		"""
		Return the interpolated boundary conditions
		Parameters
		time:   true value for time
		"""
		
		bcs_int = {}
		for key in self.boundaryconditions:
			bcs_int[key] = np.interp(time,self.boundaryconditions['time'],self.boundaryconditions[key])
		
		return bcs_int
		
		
###########################################################################
class Stateestimation:
	"""
	Base class for defining the state estimation for an mpc
	the "stateestimation" method must be redefined in a child class
	"""
	def __init__(self,emulator):
		"""
		Parameters:
		emulator:		an mpcpy.Emulator object
		"""
		
		self.emulator = emulator
	
	def stateestimation(self,time):
		"""
		"""
		return None

	def __call__(self,time):
		return self.stateestimation(time)

		
###########################################################################
class Prediction:
	"""
	Base class for defining the predictions for an mpc
	the "prediction" method must be redefined in a child class
	"""
	def __init__(self,boundaryconditions):
		"""
		Parameters:
		boundaryconditions:		an mpcpy.Boundaryconditions object
		"""
		
		self.boundaryconditions = boundaryconditions
		
	def prediction(self,time):
		"""
		Defines perfect predictions, returns the exact boundary conditions dict
		Can be redefined in a child class to contain an actual prediction algorithm
		"""
		return self.boundaryconditions(time)
		
	def __call__(self,time):
		return self.prediction(time)
		
	
###########################################################################
class Control:
	"""
	Base class for defining the control for an mpc
	the "formulation" method must be redefined in a child class
	"""
	def __init__(self,stateestimation,prediction,control_parameters=None,horizon=3*24*3600,timestep=3600,receding=3600):
		"""
		Parameters:
		stateestimation :	an mpcpy.Stateestimation object
		prediction:			an mpcpy.Prediction object
		"""
		
		self.stateestimation = stateestimation
		self.prediction = prediction
		self.horizon = horizon
		self.timestep = timestep
		self.receding = receding
		self.control_parameters = control_parameters
		self.solution = self.formulation()
		
	def time(self,starttime):
		"""
		starttime:       real start time of the control horizon
		"""
		return np.arange(starttime,starttime+self.horizon+0.01*self.timestep,self.timestep,dtype=np.float)

	def formulation(self):
		"""
		function that returns a callable function which solves the optimal control problem
		the returned function has the current state and the predictions as inputs and returns a dict with "the plan"
		Should be redefined in a child class to contain the actual control algorithm
		"""
		
		control_parameters = self.control_parameters
		time = self.time()
		
		def solution(state,prediction):
			sol = {}
			sol['time'] = time()
	
		return solution
	
	def __call__(self,starttime):
		"""
		Calculate the value of the control signal for the next timestep
		Parameters:
		starttime:       real start time of the control horizon
		"""
		
		state = self.stateestimation(starttime)
		prediction = self.prediction(self.time(starttime))
		solution = self.solution(state,prediction)
		
		return solution

		
###########################################################################
class MPC:

	def __init__(self,emulator,control,boundaryconditions,emulationtime=7*24*3600,resulttimestep=600,plotfunction=None):

		self.emulator = emulator
		self.control = control
		self.boundaryconditions = boundaryconditions

		self.emulationtime = emulationtime
		self.resulttimestep = resulttimestep
		self.plotfunction = plotfunction
		
	def __call__(self):
		"""
		Runs the mpc simulation
		"""
		print('Run MPC')
		
		if self.plotfunction:
			(fig,ax,pl) = self.plotfunction()
		
		if self.emulator.res:
			starttime = self.emulator.res['time'][-1]
		else:
			starttime = 0
			
			
		# prepare a progress bar
		bar_width = 50
		sys.stdout.write("[%s]" % (" " * bar_width))
		sys.stdout.flush()
		sys.stdout.write("\b" * (bar_width+1))
		barvalue = 0	
			
		while starttime < self.emulationtime:
			# create time vector
			time = np.arange(starttime,starttime+self.control.receding+0.01*self.resulttimestep,self.resulttimestep)
			
			boundaryconditions = self.boundaryconditions(time)
			control = self.control(starttime)
			
			# create input
			input = {}
			for key in self.emulator.inputs:
				if key in boundaryconditions:
					input[key] = np.interp(time,boundaryconditions['time'],boundaryconditions[key])
				elif key in control:
					input[key] = np.interp(time,control['time'],control[key])
			

			# prepare and run the simulation
			self.emulator(time,input)

			# plot results
			if self.plotfunction:
				self.plotfunction(pl=pl,res=self.emulator.res)
			
			# update starting time
			starttime = self.emulator.res['time'][-1]
			
			# update the progress bar
			if starttime/self.emulationtime*bar_width >= barvalue:
				addvalue = int(round(starttime/self.emulationtime*bar_width-barvalue))
				sys.stdout.write(addvalue*'-')
				sys.stdout.flush()
				barvalue += addvalue
		
			
		
		sys.stdout.write("\n")			
		print('done')
		
