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
		