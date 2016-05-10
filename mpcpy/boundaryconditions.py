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

class Boundaryconditions(object):
	def __init__(self,bcs,periodic=True,extra_time=7*24*3600.):
		"""
		Arguments:
		bcs:     		dict, actual boundary conditions and a time vector
		periodic:    	boolean, determines how to determine values when time is larger then the boundary conditions time
		extra_time: 	float, maximum allowed time outside the boundary conditions time
		"""
		
		self.data = {}
		
		# create a new time vector including the extra time
		# this method is about 2 times faster than figuring out the correct time during interpolation
		ind = np.where( bcs['time']-bcs['time'][0] < extra_time )[0]
		self.data['time'] = np.concatenate((bcs['time'][:-1],bcs['time'][ind]+bcs['time'][-1]-bcs['time'][0] ))
		
		if periodic:
			# the values at time lower than extra_time are repeated at the end of the dataset
			# extra_time should thus be larger than the control horizon
			for key in bcs:
				if key != 'time':
					self.data[key] =  np.concatenate((bcs[key][:-1],bcs[key][ind]))
		else:
			# last value is repeated after the actual data
			for key in bcs:
				if key != 'time':
					self.data[key] =  np.concatenate((bcs[key][:-1],bcs[key][-1]*np.ones(len(ind))))
		
	def __call__(self,time):
		"""
		Return the interpolated boundary conditions
		
		Arguments:
		time:   true value for time
		"""
		
		bcs_int = {}
		for key in self.data:
			try:
				bcs_int[key] = np.interp(time,self.data['time'],self.data[key])
			except:
				# 2d boundary conditions support
				bcs_int[key] = np.zeros((len(time),self.data[key].shape[1]))
				for j in range(self.data[key].shape[1]):
					bcs_int[key][:,j] = np.interp(time,self.data['time'],self.data[key][:,j])
					
		return bcs_int
	
	def __getitem__(self,key):
		return self.data[key]