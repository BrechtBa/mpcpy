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

class Control:
	"""
	Base class for defining the control for an mpc
	the "formulation" method must be redefined in a child class
	"""
	def __init__(self,stateestimation,prediction,parameters=None,horizon=3*24*3600,timestep=3600,receding=3600,savesolutions=False):
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
		
		self.savesolutions = savesolutions
		self.solutions = []
		
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
		
		def solution(state,prediction):
			sol = {}
			sol['time'] = prediction['time']
			if self.savesolutions:
				self.solutions.append(sol)
			
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