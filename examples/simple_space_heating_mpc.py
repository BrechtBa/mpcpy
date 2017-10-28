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
import pyomo.environ as pyomo

import mpcpy

# Disturbances
time = np.arange(0.,24.01*3600.,3600.)
dst = {
    'time': time,
    'T_am': 5 + 2*np.sin(2*np.pi*time/24./3600.)+273.15,
    'Q_flow_so': 500 + 500*np.sin(2*np.pi*time/24./3600.),
    'p_el': 0.2 + 0.05*np.sin(2*np.pi*time/24./3600.),
    'Q_flow_hp_max': 5000*np.ones_like(time),
    'T_in_min': 20*np.ones_like(time)+273.15,
    'T_em_max': 30*np.ones_like(time)+273.15
}

disturbances = mpcpy.Disturbances(dst, periodic=False)
# test
print(disturbances(1800))
print(disturbances(24.5 * 3600))  # extrapolation


# Emulator
class Emulator(mpcpy.Emulator):
    """
    A custom system emulator
    """
    def simulate(self, starttime, stoptime, input):
        dt = 60
        time = np.arange(starttime, stoptime+dt, dt, dtype=np.float)

        # initialize
        T_em = np.ones_like(time)*self.res['T_em'][-1]
        T_in = np.ones_like(time)*self.res['T_in'][-1]

        # interpolate inputs
        Q_flow_hp = np.interp(time, input['time'], input['Q_flow_hp'])
        Q_flow_so = np.interp(time, input['time'], input['Q_flow_so'])
        T_am      = np.interp(time, input['time'], input['T_am'])

        for i,t in enumerate(time[:-1]):
            # C_em dT_em/dt = Q_flow_hp - UA_em_in*(T_em-T_in)
            T_em[i+1] = T_em[i] + (Q_flow_hp[i] - self.parameters['UA_em_in']*(T_em[i]-T_in[i]))*dt/self.parameters['C_em']

            # C_in dT_in/dt = Q_flow_so - UA_em_in*(T_in-T_em) - UA_in_am*(T_in-T_am)
            T_in[i+1] = T_in[i] + (Q_flow_so[i] - self.parameters['UA_em_in']*(T_in[i]-T_em[i]) - self.parameters['UA_in_am']*(T_in[i]-T_am[i]))*dt/self.parameters['C_em']

        # create and return a results dict
        res = {
            'time': time,
            'Q_flow_hp':Q_flow_hp,
            'Q_flow_so':Q_flow_so,
            'T_em':T_em,
            'T_in':T_in,
            'T_am':T_am,
        }

        return res


# Emulator parameters and initial conditions:
emulator_parameters = {
    'C_em': 10e6,
    'C_in': 5e6,
    'UA_in_am': 200,
    'UA_em_in': 1600
}
emulator_initial_conditions = {
    'T_em': 22+273.15,
    'T_in': 21+273.15
}

emulator = Emulator(['T_am','Q_flow_so','Q_flow_hp'],parameters=emulator_parameters,initial_conditions=emulator_initial_conditions)
emulator.initialize()
# test
inp = {
    'time': [0., 3600., 7200.],
    'T_am': [273.15, 274.15, 275.15],
    'Q_flow_so': [500., 400., 300.],
    'Q_flow_hp': [4000., 4000., 4000.]
}
emulator(np.arange(0., 7201., 1200.), inp)

print(emulator.res['time'])
print(emulator.res['T_em'])


# State estimation
class StateestimationPerfect(mpcpy.Stateestimation):
    """
    Custom state estimation method
    """
    def stateestimation(self, time):
        state = {}
        state['T_in'] = np.interp(time, self.emulator.res['time'], self.emulator.res['T_in'])
        state['T_em'] = np.interp(time, self.emulator.res['time'], self.emulator.res['T_em'])

        return state

stateestimation = StateestimationPerfect(emulator)
# test
print(stateestimation(0))


# Prediction
prediction = mpcpy.Prediction(disturbances)
# test
print(prediction([0., 1800., 3600.]))


# Control
class LinearProgram(mpcpy.Control):
    def formulation(self):
        """
        formulates the abstract optimal control problem
        """
        model = pyomo.AbstractModel()

        # sets
        model.i = pyomo.Set()   # initialize=range(len(time)-1)
        model.ip = pyomo.Set()  # initialize=range(len(time))

        # parameters
        model.time = pyomo.Param(model.ip)

        model.UA_em_in = pyomo.Param(initialize=800.)
        model.UA_in_am = pyomo.Param(initialize=200.)

        model.C_in = pyomo.Param(initialize=5.0e6)
        model.C_em = pyomo.Param(initialize=20.0e6)

        model.T_in_ini = pyomo.Param(initialize=21.+273.15)
        model.T_em_ini = pyomo.Param(initialize=22.+273.15)

        model.T_in_min = pyomo.Param(initialize=20.+273.15)
        model.T_in_max = pyomo.Param(initialize=24.+273.15)

        model.T_am = pyomo.Param(model.i, initialize=0.+273.15)
        model.Q_flow_so = pyomo.Param(model.i, initialize=0.)

        # variables
        model.T_in = pyomo.Var(model.ip,domain=pyomo.Reals, initialize=20.+273.15)
        model.T_em = pyomo.Var(model.ip,domain=pyomo.Reals,initialize=20.+273.15)

        model.T_in_min_slack = pyomo.Var(model.ip,domain=pyomo.NonNegativeReals, initialize=0)
        model.T_in_max_slack = pyomo.Var(model.ip,domain=pyomo.NonNegativeReals, initialize=0)

        model.Q_flow_hp = pyomo.Var(model.i,domain=pyomo.NonNegativeReals,bounds=(0.,10000.),initialize=0.)

        # constraints
        model.state_T_em = pyomo.Constraint(
            model.i,
            rule=lambda model,i: model.C_em*(model.T_em[i+1]-model.T_em[i])/(model.time[i+1]-model.time[i]) == \
                          model.Q_flow_hp[i] \
                        - model.UA_em_in*(model.T_em[i]-model.T_in[i])
        )
        model.ini_T_em = pyomo.Constraint(rule=lambda model: model.T_em[0] == model.T_em_ini)

        model.state_T_in = pyomo.Constraint(
            model.i,
            rule=lambda model,i: model.C_in*(model.T_in[i+1]-model.T_in[i])/(model.time[i+1]-model.time[i]) == \
                          model.Q_flow_so[i] \
                        - model.UA_em_in*(model.T_in[i]-model.T_em[i]) \
                        - model.UA_in_am*(model.T_in[i]-model.T_am[i])
        )
        model.ini_T_in = pyomo.Constraint(rule=lambda model: model.T_in[0] == model.T_in_ini)

        # soft constraints
        model.constraint_T_in_min_slack = pyomo.Constraint(
            model.ip,
            rule=lambda model,i: model.T_in_min_slack[i] >= model.T_in_min-model.T_in[i]
        )

        model.constraint_T_in_max_slack = pyomo.Constraint(
            model.ip,
            rule=lambda model,i: model.T_in_max_slack[i] >= model.T_in[i]-model.T_in_max
        )

        # a large number
        L = 1e6

        # objective
        model.objective = pyomo.Objective(
            rule=lambda model: sum(model.Q_flow_hp[i]*(model.time[i+1]-model.time[i])/3600/1000 for i in model.i) \
                              +sum(model.T_in_min_slack[i]*(model.time[i+1]-model.time[i])/3600 for i in model.i)*L\
                              +sum(model.T_in_max_slack[i]*(model.time[i+1]-model.time[i])/3600 for i in model.i)*L\
        )

        self.model = model

    def solution(self, sta, pre):
        """
        instanciate the optimal control problem, solve it and return a solution dictionary
        """

        ip = np.arange(len(pre['time']))

        data = {
            None: {
                'i': {None: ip[:-1]},
                'ip': {None: ip},
                'time': {(i,): v for i, v in enumerate(pre['time'])},
                'T_am': {(i,): pre['T_am'][i] for i in ip[:-1]},
                'Q_flow_so': {(i,): pre['Q_flow_so'][i] for i in ip[:-1]},
                'T_em_ini': {None: sta['T_em']},
                'T_in_ini': {None: sta['T_in']},
                'C_em': {None: self.parameters['C_em']},
                'C_in': {None: self.parameters['C_in']},
                'UA_em_in': {None: self.parameters['UA_em_in']},
                'UA_in_am': {None: self.parameters['UA_in_am']},
            }
        }

        instance = self.model.create_instance(data)
        optimizer = pyomo.SolverFactory('ipopt')
        results = optimizer.solve(instance)

        # return the contol inputs
        sol = {
            'time': np.array([pyomo.value(instance.time[i]) for i in instance.ip]),
            'T_em': np.array([pyomo.value(instance.T_em[i]) for i in instance.ip]),
            'T_in': np.array([pyomo.value(instance.T_in[i]) for i in instance.ip]),
            'Q_flow_hp': np.array([pyomo.value(instance.Q_flow_hp[i]) for i in instance.i]),
        }

        return sol


# Control parameters
control_parameters = {
    'C_in': emulator_parameters['C_in'],
    'C_em': emulator_parameters['C_em'],
    'UA_in_am': emulator_parameters['UA_in_am'],
    'UA_em_in': emulator_parameters['UA_em_in'],
}
# create an instance
control = LinearProgram(stateestimation, prediction, parameters=control_parameters, horizon=24*3600., timestep=3600.)
# test
print(control(0))


# MPC
mpc = mpcpy.MPC(emulator, control, disturbances, emulationtime=1*24*3600., resulttimestep=60)
res = mpc(verbose=1)


# Plot results
fix, ax = plt.subplots(2, 1)
ax[0].plot(res['time']/3600, res['Q_flow_hp'], 'k', label='hp')
ax[0].plot(res['time']/3600, res['Q_flow_so'], 'g', label='sol')
ax[0].set_ylabel('Heat flow rate (W)')
ax[0].legend(loc='lower right')

ax[1].plot(res['time']/3600, res['T_in']-273.17, 'k', label='in')
ax[1].plot(res['time']/3600, res['T_em']-273.17, 'b', label='em')
ax[1].plot(res['time']/3600, res['T_am']-273.17, 'g', label='amb')
ax[1].set_ylabel('Temperature ($^\circ$C)')
ax[1].set_xlabel('Time (h)')
ax[1].legend(loc='lower right')


# Using the default emulator
# The default emulator simply reuses the control solution. The results are a bit different due to model mismatch.
def_emulator = mpcpy.Emulator(['T_am', 'Q_flow_so', 'Q_flow_hp'],initial_conditions=emulator_initial_conditions)
emulator.initialize()

def_stateestimation = StateestimationPerfect(def_emulator)
def_control = LinearProgram(def_stateestimation, prediction,
                            parameters=control_parameters, horizon=24*3600., timestep=3600.)
def_mpc = mpcpy.MPC(def_emulator, def_control, disturbances, emulationtime=1*24*3600., resulttimestep=60)
def_res = def_mpc(verbose=1)

fix, ax = plt.subplots(2, 1)
ax[0].plot(def_res['time']/3600, def_res['Q_flow_hp'], 'k', label='hp')
ax[0].plot(res['time']/3600, res['Q_flow_hp'], 'k--')
ax[0].plot(def_res['time']/3600, def_res['Q_flow_so'], 'g', label='sol')
ax[0].set_ylabel('Heat flow rate (W)')
ax[0].legend(loc='lower right')

ax[1].plot(def_res['time']/3600, def_res['T_in']-273.17, 'k', label='in')
ax[1].plot(def_res['time']/3600, def_res['T_em']-273.17, 'b', label='em')
ax[1].plot(def_res['time']/3600, def_res['T_am']-273.17, 'g', label='amb')
ax[1].plot(res['time']/3600, res['T_in']-273.17, 'k--')
ax[1].plot(res['time']/3600, res['T_em']-273.17, 'b--')
ax[1].set_ylabel('Temperature ($^\circ$C)')
ax[1].set_xlabel('Time (h)')
ax[1].legend(loc='lower right')


if __name__ == '__main__':
    plt.show()
