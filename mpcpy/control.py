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
	def __init__(self,stateestimation,prediction,parameters=None,horizon=3*24*3600,timestep=3600,receding=3600,savesolutions=0):
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
		self.solution = None
		
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
			
		return solution
	
	def __call__(self,starttime):
		"""
		Calculate the value of the control signal for the next timestep
		Arguments:
		starttime:       real start time of the control horizon
		"""
		
		# formulate the ocp during the first call
		if self.solution == None:
			self.solution = self.formulation()
		
		state = self.stateestimation(starttime)
		prediction = self.prediction(self.time(starttime))
		solution = self.solution(state,prediction)
		
		if self.savesolutions == -1:
			# save all solutions
			self.solutions.append(solution)
			
		elif self.savesolutions > 0:
			# save only the last x solutions
			self.solutions.append(solution)
			if len(self.solutions) > self.savesolutions:
				self.solutions.pop(0)
				
		return solution
		
	def cplex_infeasibilityanalysis(self,ocp):
		"""
		Give information about infeasible constraints in cplex
		
		Arguments:
		ocp:   CPlex object
		"""
		
		ocp.conflict.refine(ocp.conflict.all_constraints())
		for conflict,v in enumerate(ocp.conflict.get()):
			if v > 0:
				for c in ocp.conflict.get_groups(conflict)[1]:
					if c[0]==1:
						print( 'Lower bound constraint on variable {}: {}'.format(c[1],ocp.variables.get_names(c[1])) )
					if c[0]==2:
						print( 'Upper bound constraint on variable {}: {}'.format(c[1],ocp.variables.get_names(c[1])) )
					if c[0]==3:
						print( 'Linear constraint {}: {}'.format(c[1],ocp.linear_constraints.get_names(c[1])) )
					else:
						print(ocp.conflict.get_groups(conflict))
						
						

def state_equation_collocation(derivative_coefficients,variable_coefficients,disturbance_coefficients,disturbances,zoh=[]):
	"""
	calculates the coefficients of a central discrete difference equation through collocation
	
	Arguments:
	derivative_coefficient:		dict, the coefficient of the variable which is derived on the lhs
	variable_coefficients: 		dict, the coefficient of the non derived variables on the rhs
	disturbance_coefficients:	dict, the coefficient of the distrubances on the rhs					
	disturbances:  				dict, the values of the distrubances, including a time vector
	zoh = []:    				list of strings, list of variables or disturbances for which the value is assumed to be constant over the discretization interval

	Returns:
	coefficients:     list of dicts, indexed variable names and coefficients at all timesteps but the last
	right_hand_side:  list of floats, the right hand side of the discretized equation at all timesteps but the last
	
	Example:
	expression = 'C*dT/dt = UA*(T_amb-T) + Q'
	C = 500e3
	UA = 100
	time = np.arange(0,24.1)*3600
	state_equation_collocation({'T':C},{'T':-UA,'Q':1.},{'T_amb':UA},{'time':time,'T_amb':5.*np.ones_like(time)})
	"""
	
	coefficients = []
	righthandside = []
	
	for i in range(len(disturbances['time'])-1):
		dt = disturbances['time'][i+1]-disturbances['time'][i]
		
		temp_coefficients = {}
		temp_righthandside = 0

		# check inputs
		if not len(derivative_coefficient) == 1:
			raise ValueError('derivative_coefficient can only have one key')
		
		# calculate coefficients	
		for key in derivative_coefficient:
			temp_coefficients[ key+'[{}]'.format(i) ] = -derivative_coefficient[key]/dt
			temp_coefficients[ key+'[{}]'.format(i+1) ] = derivative_coefficient[key]/dt

		for key in variable_coefficients:
			if key in zoh:
				tempkey = key+'[{}]'.format(i)
				if not tempkey in temp_coefficients:
					temp_coefficients[ tempkey ] = 0
					
				temp_coefficients[ tempkey ] = temp_coefficients[ tempkey ] - variable_coefficients[key]
				
			else:
				tempkey = key+'[{}]'.format(i)
				if not tempkey in temp_coefficients:
					temp_coefficients[ tempkey ] = 0
					
				temp_coefficients[ tempkey ] = temp_coefficients[ tempkey ] - 0.5*variable_coefficients[key]
		
				tempkey = key+'[{}]'.format(i+1)
				if not tempkey in temp_coefficients:
					temp_coefficients[ tempkey ] = 0
					
				temp_coefficients[ tempkey ] = temp_coefficients[ tempkey ] - 0.5*variable_coefficients[key]
		
		# calculate rhs					
		for key in disturbance_coefficients:
			if key in zoh:	
				temp_righthandside = temp_righthandside + disturbance_coefficients[key]*disturbance_values[key][i]
			else:
				temp_righthandside = temp_righthandside + disturbance_coefficients[key]*(0.5*disturbance_values[key][i]+0.5*disturbance_values[key][i+1])


		coefficients.append(temp_coefficients)
		righthandside.append(temp_righthandside)
				
	return (coefficients,righthandside)
			
			
					
def parse_state_equation(expression,variables,coeffients,indices):
	"""
	parses a state differential equation
	
	Arguments:
	expression:    string, a string form of the continuous time differential equation
	variables:     list, a list of strings with the variable names
	coeffients:    dict, values for the coefficients
	disturbances:  dict, values for the disturbances
	indices:       list, a list of indices
	
	Example:
	parse_state_equation( 'C*dT/dt = UA*(T_amb-T) + Q', ['T','Q'], {'C':500e3,'UA':100}, {'T_amb':np.zeros(25)}, range(24) )
	"""
	
	pass
	
	

