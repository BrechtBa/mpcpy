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
			time = np.arange(starttime,starttime+self.control.receding+0.01*self.resulttimestep,self.resulttimestep,dtype=np.float)
			boundaryconditions = self.boundaryconditions(time)
			control = self.control(starttime)
			
			# create input of all controls and the required boundary conditions
			# add times at the control timesteps-0.1s to achieve zero order hold
			ind = np.where((control['time']-1e-6*self.resulttimestep > time[0]) & (control['time']-1e-6*self.resulttimestep <= time[-1]))
			inputtime = np.sort(np.concatenate((time, control['time'][ind]-1e-6*self.resulttimestep)))
			input = {'time': inputtime}
			
			for key in self.emulator.inputs:
				if key in boundaryconditions:
					input[key] = np.interp(input['time'],boundaryconditions['time'],boundaryconditions[key])
			
			for key in control:
				if not key in input:
					input[key] = interp_zoh(input['time'],control['time'],control[key])

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

def interp_zoh(x,xp,fp):
	return np.array([fp[(len(xp)-1)*(xpp-xp[0])/(xp[-1]-xp[0])] for xpp in x])