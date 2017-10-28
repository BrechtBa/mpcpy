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


class MPC(object):

    def __init__(self, emulator, control, disturbances,
                 emulationtime=7 * 24 * 3600, resulttimestep=600, nextstepcalculator=None, plotfunction=None):
        """
        initialize an MPC object
        
        Parameters
        ----------
        emulator : mpcpy.Emulator
            The emulator object to be used.
            
        control : mpcpy.Control
            The control object to be used.
            
        disturbances : mpcpy.Disturbances
            The disturbances object to be used.
        
        emulationtime : number
            The total time of the simulation.
            
        resulttimestep : number
            The timestep for which the results are returned.
            
        nextstepcalculator : function
            Function returning an integer representing the number of receding
            timesteps to skip. When not specified, no steps are skipped and the 
            next step is 1.
            
        plotfunction : function
            A function which creates or updates a plot for live viewing of
            results, probably broken, untested.
        
        """
        
        self.emulator = emulator
        self.control = control
        self.disturbances = disturbances

        self.emulationtime = emulationtime
        self.resulttimestep = resulttimestep
        
        if nextstepcalculator == None:
            def nextstepcalculator(controlsolution):
                return 1

        self.nextstepcalculator = nextstepcalculator
            
        self.plotfunction = plotfunction
        
        self.res = {}
        self.appendres = {}

    def __call__(self, verbose=0):
        """
        Runs the mpc simulation

        Parameters
        ----------
        verbose: optional, int
            Controls the amount of print output

        Returns
        -------
        dict
            A dictionary with results, also stored in the res attribute.
            
        """
        
        # initialize the emulator
        self.emulator.initialize()
        starttime = 0

        if self.plotfunction:
            (fig,ax,pl) = self.plotfunction()

        # prepare a progress bar
        barwidth = 80-2
        barvalue = 0
        if verbose > 0:
            print('Running MPC')
            print('[' + (' '*barwidth) + ']', end='')

        while starttime < self.emulationtime:
        
            # calculate control signals for the control horizon
            control = self.control(starttime)
            
            # create a simulation time vector
            nextStep = self.nextstepcalculator(control)
            time = np.arange(
                starttime,
                min(self.emulationtime+self.resulttimestep, starttime+nextStep*self.control.receding+0.01*self.resulttimestep),
                self.resulttimestep, dtype=np.float
            )
            time[-1] = min(time[-1], self.emulationtime)
            
            # create input of all controls and the required boundary conditions
            # add times at the control time steps minus 1e-6 times the result time step to achieve zero order hold
            ind = np.where(
                (control['time']-1e-6*self.resulttimestep > time[0])
                & (control['time']-1e-6*self.resulttimestep <= time[-1])
            )
            inputtime = np.sort(np.concatenate((time, control['time'][ind]-1e-6*self.resulttimestep)))
            input = {'time': inputtime}
            
            # add controls first
            for key in control:
                if not key in input:
                    input[key] = interp_zoh(input['time'], control['time'], control[key])
            
            # add the rest of the inputs from the boundary conditions
            for key in self.emulator.inputs:
                if not key in input and key in self.disturbances:
                    input[key] = self.disturbances.interp(key, input['time'])
                elif not key in input:
                    print('Warning {} not found in disturbances object'.format(key))
                    
            # prepare and run the simulation
            self.emulator(time, input)
            
            # plot results
            if self.plotfunction:
                self.plotfunction(pl=pl, res=self.emulator.res)
            
            # update starting time
            starttime = self.emulator.res['time'][-1]

            # update the progress bar
            if verbose > 0:
                if starttime/self.emulationtime*barwidth >= barvalue:
                    barvalue += int(round(starttime/self.emulationtime*barwidth-barvalue))
                    print('\r[' + ('='*barvalue) + (' '*(barwidth-barvalue)) + ']', end='')

        # copy the results to a local res dictionary
        self.res.update(self.emulator.res)
        
        # interpolate the boundary conditions and add them to self.res
        self.res.update(self.disturbances(self.res['time']))
        if verbose > 0:
            print(' done')
        
        return self.res


def interp_zoh(x, xp, fp):
    return np.array([fp[int((len(xp)-1)*(xi-xp[0])/(xp[-1]-xp[0]))] for xi in x])
