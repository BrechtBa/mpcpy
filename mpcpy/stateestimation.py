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
    the "stateestimation" method must be redefined in a child class.
    
    """
    
    def __init__(self,emulator,parameters=None):
        """
        Parameters
        ----------
        emulator : mpcpy.Emulator
            An :code:`mpcpy.Emulator` object from which the state should be estimated.
            
        parameters : dict, optional
            Optional parameter dictionary.
            
        """
        
        self.emulator = emulator
        self.parameters = parameters
        
        
    def stateestimation(self,time):
        """
        Must be redefined in a child class to return a dictionary with the
        estimated state at the specified time as required by the control object.
        
        Parameters
        ----------
        time : number
            The time at which the state should be estimated.
    
        Returns
        -------
        dict
            A dictionary with key-value pairs representing the state.
            
        """
        
        return None

        
    def __call__(self,time):
        """
        Returns the state at a given time as computed by the
        :code:`stateestimation` method.
        
        Parameters
        ----------
        time : number
            The time at which the state should be estimated.
    
        Returns
        -------
        dict
            A dictionary with key-value pairs representing the state.
            
        """
        return self.stateestimation(time)