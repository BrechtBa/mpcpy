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

class Prediction(object):
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