#!/usr/bin/env python
# mpcPy
# Documentation


# import libraries
import sys
import numpy as np
from pyfmi import load_fmu

###########################################################################
class Emulator:
	def __init__(self,filename,inputs):
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
		self.simulate_options['ncp'] = 100
		self.simulate_options['CVode_options']['verbosity'] = 50
		self.model.initialize()
		self.res = {}

		
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
		res = self.model.simulate(start_time = time[0],final_time=time[-1],input=self._create_input_tuple(time,input), options=self.simulate_options)
		
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
	def __init__(self,bcs):
		"""
		Parameters:
		bcs:     a dict with the actual boundary conditions and a time vector
		"""
		
		# periodicity is assumed
		self.boundaryconditions = {}
		self.boundaryconditions['time'] = np.concatenate((bcs['time'][:-1]-bcs['time'][-1],bcs['time'],bcs['time'][1:]+bcs['time'][-1]))
		for key in bcs:
			if key != 'time':
				self.boundaryconditions[key] =  np.concatenate((bcs[key][:-1],bcs[key],bcs[key][1:]))
		
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
	def __init__(self,emulator,estimation_function):
		self.emulator = emulator
		self.estimation_function = estimation_function
		
	def __call__(self):
		return self.estimation_function(self.emulator)

		
###########################################################################
class Prediction:
	def __init__(self,boundaryconditions,prediction_function):
		"""
		Parameters:
		boundaryconditions:		a boundaryconditions object
		prediction_function:	a function to make the predictions with inputs:
									bcs: the interpolated real boundary conditions 
		"""
		self.boundaryconditions = boundaryconditions
		self.prediction_function = prediction_function
		
	def __call__(self,time):
		return self.prediction_function(self.boundaryconditions(time))
		
	
###########################################################################
class Control:
	def __init__(self,stateestimation,prediction,control_function,horizon=3*24*3600,timestep=3600,receding=3600):
		"""
		Parameters:
		stateestimation :	a Stateestimation object
		prediction:			a Prediction object
		control_function:	a function which calculates the control signals ("the plan") with inputs:
								state: the current state
								predictions: a dictionary with arrays of predictions
		"""
		
		self.stateestimation = stateestimation
		self.prediction = prediction
		self.horizon = horizon
		self.timestep = timestep
		self.receding = receding
		self.control_function = control_function
	
	def __call__(self,starttime):
		"""
		Calculate the value of the control signal for the next timestep
		Parameters:
		starttime:       real start time of the control horizon
		"""
		
		time = np.arange(starttime,starttime+self.horizon+0.01*self.timestep,self.timestep,dtype=np.float)
		
		state = self.stateestimation()
		prediction = self.prediction(time)
		control = self.control_function(state,prediction)
		
		# find the samples where time <= receding and return only these
		#ind = np.invert(time > self.receding)
		
		#control['time'] = time[ind]
		#for key in control:
		#	control[key] = control[key][ind]
		control['time'] = time
		
		return control

		
###########################################################################
class MPC:

	def __init__(self,emulator,control,boundaryconditions,emulationtime=7*24*3600,resulttimestep=600):

		self.emulator = emulator
		self.control = control
		self.boundaryconditions = boundaryconditions

		self.emulationtime = emulationtime
		self.resulttimestep = resulttimestep
		
	def __call__(self):
		"""
		Runs the mpc simulation
		"""
		print('Run MPC')
		
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

			starttime = self.emulator.res['time'][-1]
			
			# update the progress bar
			if starttime/self.emulationtime*bar_width >= barvalue:
				addvalue = int(round(starttime/self.emulationtime*bar_width-barvalue))
				sys.stdout.write(addvalue*'-')
				sys.stdout.flush()
				barvalue += addvalue
		
		sys.stdout.write("\n")			
		print('done')
		
