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

import numpy as np
import matplotlib.pyplot as plt

import mpcpy
import pyomo.environ as pyomo


# Define an emulator class
class Emulator(mpcpy.Emulator):
    """
    A custom system emulator
    """
    def simulate(self, starttime, stoptime, input):
        dt = 1
        time = np.arange(starttime, stoptime+dt, dt, dtype=np.float)

        # initialize
        x = np.ones_like(time)*self.res['x'][-1]

        # interpolate inputs
        u = np.interp(time, input['time'], input['u'])
        d = np.interp(time, input['time'], input['d'])

        # perform simulation
        for i, t in enumerate(time[:-1]):
            # dx/dt = A*x + d + u
            x[i+1] = x[i] + (self.parameters['A']*x[i] + d[i] + u[i])*dt

        # create and return a results dict
        res = {
            'time': time,
            'x': x,
            'd': d,
            'u': u,
        }

        return res


# Define a control class
class SetpointControl(mpcpy.Control):
    """
    A control to keep the state as close to a set point as possible
    """
    def formulation(self):
        # create a pyomo model
        model = pyomo.AbstractModel()
        
        model.i = pyomo.Set()
        model.ip = pyomo.Set()
        
        model.time = pyomo.Param(model.ip)
        model.d = pyomo.Param(model.ip, initialize=0.)
        model.x = pyomo.Var(model.ip, domain=pyomo.Reals, initialize=0.)
        model.u = pyomo.Var(model.ip, domain=pyomo.NonNegativeReals, bounds=(0., 1.), initialize=0.)
        
        model.x0 = pyomo.Param(initialize=0.)
        
        model.initialcondition = pyomo.Constraint(
            rule=lambda model: model.x[0] == model.x0
        )
        
        model.constraint = pyomo.Constraint(
            model.i,
            rule=lambda model, i: (model.x[i+1]-model.x[i])/(model.time[i+1]-model.time[i]) ==
                          self.parameters['A']*model.x[i] + model.d[i] + model.u[i]
        )
        
        model.objective = pyomo.Objective(
            rule=lambda model: sum((model.x[i]-self.parameters['set'])**2 for i in model.i)
        )
        
        # store the model inside the object
        self.model = model
        
    def solution(self, sta, pre):
        # create data and instantiate the pyomo model
        ip = np.arange(len(pre['time']))
        data = {
            None: {
                'i': {None: ip[:-1]},
                'ip': {None: ip},
                'time': {(i,): v for i, v in enumerate(pre['time'])},
                'x0': {None: sta['x']},
                'd': {(i,): pre['d'][i] for i in ip},
            }
        }
        
        instance = self.model.create_instance(data)
        
        # solve and return the control inputs
        optimizer = pyomo.SolverFactory('ipopt')
        results = optimizer.solve(instance)
        
        sol = {
            'time': np.array([pyomo.value(instance.time[i]) for i in instance.ip]),
            'x': np.array([pyomo.value(instance.x[i]) for i in instance.ip]),
            'u': np.array([pyomo.value(instance.u[i]) for i in instance.ip]),
            'd': np.array([pyomo.value(instance.d[i]) for i in instance.ip]),
        }
        
        return sol


# Define a state estimation class
class StateestimationPerfect(mpcpy.Stateestimation):
    """
    Perfect state estimation
    """
    def stateestimation(self, time):
        return {'x': np.interp(time, self.emulator.res['time'], self.emulator.res['x'])}


# instantiate the emulator
emulator = Emulator(['u', 'd'], parameters={'A': -0.2}, initial_conditions={'x': 0})

# test the emulator with some random data
time = np.arange(0., 1001., 10.)
np.random.seed(0)
d = np.random.random(len(time)) - 0.5
u = 1.0*np.ones(len(time))

emulator.initialize()
res = emulator(time, {'time': time, 'd': d, 'u': u})
print(res)


# create a disturbances object
time = np.arange(0., 1001., 10.)
d = 0.5*np.sin(2*np.pi*time/1000)
disturbances = mpcpy.Disturbances({'time': time, 'd': d})

bcs = disturbances(np.array([0, 20, 40, 60, 100]))
print(bcs)


# create a stateestimation object
stateestimation = StateestimationPerfect(emulator)
sta = stateestimation(0)     
print(sta)        


# create a prediction object
prediction = mpcpy.Prediction(disturbances)
pre = prediction(np.array([0, 20, 40, 60, 100]))
print(pre)   


# create a control object and mpc object
control = SetpointControl(stateestimation, prediction, parameters={'A': -0.2, 'set': 3.0},
                          horizon=100., timestep=10., receding=10.)
mpc = mpcpy.MPC(emulator, control, disturbances, emulationtime=1000, resulttimestep=10)

# run the mpc
res = mpc(verbose=1)
print(res)


# plot results
fig, ax = plt.subplots(2, 1)
ax[0].plot(res['time'], res['u'])
ax[0].set_ylabel('u')

ax[1].plot(res['time'], res['x'])
ax[1].set_xlabel('time')
ax[1].set_ylabel('x')


if __name__ == '__main__':
    plt.show()