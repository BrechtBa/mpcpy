#!/usr/bin/env python
# mpcPy
# Documentation


# import libraries
import sys
import numpy as np
import matplotlib.pyplot as plt

###########################################################################
class Emulator:
	def __init__(self,dympymodel,inputs,initializationtime = 1):
		"""
		Initialize a dympy object for use as an MPC emulation
		
		Arguments:
		dympymodel: a dympy object with an opened and compiled dymola model
		inputs: a list of strings of the variable names of the inputs
		"""
		
		self.inputs = inputs
		self.initializationtime = initializationtime
		
		self.model = dympymodel
		self.initial_conditions = {}
		self.parameters = {}
		self.res = {}
		
	def initialize(self):
		self.model.set_parameters(self.initial_conditions)
		self.model.set_parameters(self.parameters)
		
		# clear the result dict
		self.res = {}
		
		# simulate the model for a very short time to get the initial states in the res dict
		self.model.simulate(StartTime=0,StopTime=self.initializationtime)
		res = self.model.get_result()
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
		self.model.write_dsu(input)
		try:
			self.model.dsfinal2dsin()
		except:
			pass
			
		self.model.simulate(StartTime=input['time'][0],StopTime=input['time'][-1])
		res = self.model.get_result()
		
		# interpolate results to the points in time	
		if self.res != {}:
			for key in self.res.keys():
				self.res[key] = np.append(self.res[key][:-1],np.interp(input['time'],res['time'],res[key]))
		else:
			for key in res.keys():
				self.res[key] = np.interp(input['time'],res['time'],res[key])
			


###########################################################################
class Boundaryconditions:
	def __init__(self,bcs,periodic=True):
		"""
		Arguments:
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
		
		Arguments:
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
		Arguments:
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
		Arguments:
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
	def __init__(self,stateestimation,prediction,parameters=None,horizon=3*24*3600,timestep=3600,receding=3600):
		"""
		Arguments:
		stateestimation :	an mpcpy.Stateestimation object
		prediction:			an mpcpy.Prediction object
		"""
		
		self.stateestimation = stateestimation
		self.prediction = prediction
		self.horizon = horizon
		self.timestep = timestep
		self.receding = receding
		self.parameters = parameters
		self.solution = self.formulation()
		
	def time(self,starttime):
		"""
		Arguments:
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
		Arguments:
		starttime:       real start time of the control horizon
		"""
		
		state = self.stateestimation(starttime)
		prediction = self.prediction(self.time(starttime))
		solution = self.solution(state,prediction)
		
		return solution

		
###########################################################################
class MPC:

	def __init__(self,emulator,control,boundaryconditions,emulationtime=7*24*3600,resulttimestep=600,plotfunction=None):
		"""
		Arguments:
		emulator:     			an mpcpy.Emulator object
		control:    	 		an mpcpy.Control object
		boundaryconditions:     an mpcpy.Boundaryconditions object
		...
		"""
		
		self.emulator = emulator
		self.control = control
		self.boundaryconditions = boundaryconditions

		self.emulationtime = emulationtime
		self.resulttimestep = resulttimestep
		self.plotfunction = plotfunction
		
		self.res = {}
		
	def __call__(self):
		"""
		Runs the mpc simulation
		"""
		
		# initialize the emulator
		self.emulator.initialize()
		starttime = 0
		
		if self.plotfunction:
			(fig,ax,pl) = self.plotfunction()

		# prepare a progress bar
		barwidth = 80
		barvalue = 0
		print('Run MPC %s |' %(' '*(barwidth-10)))
		#sys.stdout.write('[%s]\n' % (' ' * barwidth))
		#sys.stdout.flush()
		#sys.stdout.write('\b' * (barwidth+1))
		

		while starttime < self.emulationtime:
			# create time vector
			time = np.arange(starttime,starttime+self.control.receding+0.01*self.resulttimestep,self.resulttimestep)
			
			boundaryconditions = self.boundaryconditions(time)
			control = self.control(starttime)
			
			# create input
			input = {'time':time}
			for key in self.emulator.inputs:
				if key in boundaryconditions:
					input[key] = np.interp(time,boundaryconditions['time'],boundaryconditions[key])
				elif key in control:
					input[key] = np.interp(time,control['time'],control[key])
			
			# prepare and run the simulation
			self.emulator(input)
			
			# plot results
			if self.plotfunction:
				self.plotfunction(pl=pl,res=self.emulator.res)
			
			# update starting time
			starttime = self.emulator.res['time'][-1]
			
			# update the progress bar
			if starttime/self.emulationtime*barwidth >= barvalue:
				addbars = int(round(starttime/self.emulationtime*barwidth-barvalue))
				sys.stdout.write(addbars*'-')
				sys.stdout.flush()
				barvalue += addbars
		
		# copy the results to a local res dictionary
		self.res.update( self.emulator.res )
		
		# interpolate the boundary conditions and add the to self.res
		self.res.update( self.boundaryconditions(self.res['time']) )
		
		
		sys.stdout.write('  done')
		sys.stdout.write("\n")
		sys.stdout.flush()
		
		return self.res
		
###########################################################################
