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

class Stateestimation(object):
	"""
	Base class for defining the state estimation for an mpc
	the "stateestimation" method must be redefined in a child class
	"""
	def __init__(self,emulator,parameters=None):
		"""
		Arguments:
		emulator:		an mpcpy.Emulator object
		parameters:     dict, optional parameter dictionary
		"""
		
		self.emulator = emulator
		self.parameters = parameters
		
	def stateestimation(self,time):
		"""
		"""
		return None

	def __call__(self,time):
		return self.stateestimation(time)