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

class Control(object):
    """
    Base class for defining the control for an mpc simulation
    
    the :code:`formulation` and :code:`solution` methods must be redefined in a
    child class to generate control signals over the control horizon
    
    """
    
    def __init__(self, stateestimation, prediction,
                 parameters=None, horizon=None, timestep=None, receding=None, savesolutions=0):
        """
        Initializes the control object
        
        Parameters
        ----------
        stateestimation : mpcpy.Stateestimation
            The object used to determine the state at the beginning of the
            control horizon.
            
        prediction : mpcpy.Prediction object
            The object used to determine the predictions over the control
            horizon.
        
        parameters : dict
            Dictionary specifying control parameters.
            
        horizon : number
            The length of the control horizon.
            
        timestep : number
            The length of the control timestep.
            
        receding : number
            The receding time, i.e. the time between subsequent calls to
            this control object.
            
        savesolutions : int
            Number of control solutions to be saved in the control object. Set 
            to -1 to save all solutions.
            
        """
        
        self.stateestimation = stateestimation
        self.prediction = prediction
        
        if horizon is None:
            raise Exception('horizon parameter must be supplied')
        else:    
            self.horizon = horizon
        
        if timestep is None:
            raise Exception('timestep parameter must be supplied')
        else:    
            self.timestep = timestep        
        
        self.receding = receding
        if self.receding is None:
            self.receding = self.timestep
            
        self.parameters = {}
        if not parameters is None:
            self.parameters = parameters
        
        self.savesolutions = savesolutions
        self.solutions = []
        
        self._formulated = False

    def time(self,starttime):
        """
        Returns a time vector over the control horizon with the defined timestep
        
        Parameters
        ----------
        starttime : real
            Time at the beginning of the control horizon.
            
        """
        return np.arange(starttime, starttime+self.horizon+0.01*self.timestep, self.timestep, dtype=np.float)

    def formulation(self):
        """
        Performs actions the first time the control is run.
        
        Can be used to set up an optimal control problem. The set-up and
        solution are separated as sometimes the set-up takes a significant
        amount of time and performs actions which must not be repeated.
        
        Should be redefined in a child class to set up the actual control
        algorithm.
        
        """
        pass
        
        
    def solution(self,state,prediction):
        """
        Returns the control profiles ("the plan").
        
        Should be redefined in a child class to set up the actual control
        algorithm.
        
        Parameters
        ----------
        state : dict
            Dictionary with the states at the start of the control horizon as
            returned by the stateestimation object.
            
        prediction : dict
            Dictionary with the values of predictions over the control horizon
            as returned by the prediction object.  
          
        Returns
        -------
        dict
            Dictionary with the solution, "time" must be a key.
        """
        sol = {}
        return sol
        
    
    def __call__(self,starttime):
        """
        Calculate the value of the control signal over the control horizon.
        Calls the :code:`solution` method.
        
        Parameters
        ----------
        starttime : real
            Time at the beginning of the control horizon.
            
        Returns
        -------
        dict
            A dictionary with representing the control signals with time.
            
        """
        
        # get the state and the predictions
        state = self.stateestimation(starttime)
        prediction = self.prediction(self.time(starttime))
        
        # formulate the ocp during the first call
        if not self._formulated:
            tempsolution = self.formulation()
            if tempsolution != None:
                print('Warning: returning a solution function from the "formulation" method is depreciated. Overwrite the "solution" method instead.')
                self.solution = tempsolution

            self._formulated = True
        
        # solve the ocp    
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
        
        
def cplex_infeasibilityanalysis(ocp):
    """
    Give information about infeasible constraints in cplex.
    
    Parameters
    ----------
    ocp : CPlex object
        A CPlex optimization problem which is infeasible
        
    """
    
    ocp.conflict.refine(ocp.conflict.all_constraints())
    
    try:
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
    except Exception as e:
        pass