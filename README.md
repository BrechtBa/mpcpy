mpcpy
-----

A group of classes to run model predictive control (MPC) simulations using python and Dymola.


# Workflow
In a model predictive control simulation we need several components.
At first we need an emulator to replace the real world system in our computational environment.
The system is subjected to certain boundary conditions which may vary.
Next we need a controller which will determine the inputs we must supply to the emulated system so it moves in the wanted direction.
As we are considering MPC the controller will consist of a state estimation, a prediction and an optimization

For each of these components base classes are included in mpcpy.
Some of these classes can be used out off the box, others require child class creation which will be explained below.

before we start import the package and numpy
```
import numpy as np
import mpcpy
```

## Boundary conditions
As all systems are subject to some boundary conditions a Boundaryconditions class is constructed.
This class main purpose is to handle the interpolation of boundary conditions to the correct times (also for predictions which may lay outside of the emulation interval).
By default it assumes periodic boundary conditions but this can be altered to maintaining the first or last entry when time flows outside of the defined range by setting `periodic=False` as an argument on creation.

#### Example:
```
time = np.arange(0.,24.01*3600.,3600.)
T_amb = 5 + 2*np.sin(time/24./3600.)
Q_flow_sol = 500*np.ones_like(time)
bcs = {'time': time,
       'T_amb': 5 + 2*np.sin(time/24./3600.),
	   'Q_flow_sol': 500*np.ones_like(time),
	   'p_el': 0.2 + 0.05*np.sin(time/24./3600.),
	   'Q_flow_hp_max': 5000*np.ones_like(time),
	   'T_in_min': 20*np.ones_like(time),
	   'T_em_max': 30*np.ones_like(time)}
boundaryconditions = mpcpy.Boundaryconditions(bcs)
print( boundaryconditions(1800) )
print( boundaryconditions(24.5*3600) )
```


## Emulator
The emulator class creates objects used to emulate the system.
By default a [dympy](https://github.com/brechtba/dympy) Dymola connection is assumed to do the simulation work but the class can be adapted to use other simulation tools.
When creating an object the inputs the model uses need to be specified as a list of strings. These inputs can be controlled inputs or disturbances.
There is also an optional argument `initializationtime` which controls the time used for initializing the model the default value is 1 second.

The object must have a `res` property where the results of the entire emulation are stored. This property is later used to output the results to the mpcpy object.

Model parameters can be defined using the `set_parameters` method which accepts a dictionary with name, value pairs as argument. 
Initial conditions can be defined using the `set_initial_conditions` method which accepts a dictionary with name, value pairs as argument.

Each model must be initialized before a simulation or mpc run using the `initialize`.
The initialization sets all parameter values and initial conditions and runs the simulation for a short period to get initial values for all variables in the `res` dictionary.
This way rewriting all parameters before every emulation is avoided which results in considerable speed gains.

The most important method in the emulator class it the `__call__` method.
This method should accepts an input dictionary with inputs to the emulator as only argument and append the results to it's `res` property.

#### Example:
if we have a dymola model opened and compiled with dympy as `dymola` with 3 inputs `T_amb`, `Q_flow_sol`, `Q_flow_hp` and 2 parameters defined in modelica as `building.C_em.C` and `building.UA_em_in.G` which need to be set, 
you can create and run an emulator object like this:

```
emulator = mpcpy.Emulator(dymola,['T_amb','Q_flow_sol','Q_flow_hp'])
input = {'time': [0. 3600. 7200.], 'T_amb': [5.0 6.0 7.0], 'Q_flow_sol': [500. 400. 300.], 'Q_flow_hp': [2000. 2000. 2000.]}
emulator_parameters = {'building.C_em.C': 10e6, 'building.C_in.C': 5e6, 'building.UA_in_amb.G': 200, 'building.UA_em_in.G': 1600}
emulator.set_parameters(emulator_parameters)
emulator.initialize()
emulator(input)
print( emulator.res['time'] )
print( emulator.res['building.C_em.T'] )
```

## Control
The control algorithm is MPC by default as this is the goal of the project, but it could be modified to use other control techniques at discrete time intervals.
An MPC consists of a state estimation, a prediction and a control optimization which will be explained below.
The basic principle of MPC is that a model suitable for optimization (for instance a linear or quadratic program or a smooth non-linear model) which represents the system behavior is constructed.
Each time step the states of the optimization model are estimated based on measurements or the emulation model in our case.
A prediction is made for the disturbances over a certain time period (the control horizon)
The model is optimized with respect to the control signals given the predictions and certain constraints and the first sample of the control signals are implemented in the emulator.
The system hopefully evolves in the desired direction and the next time step everything starts over.

- refs on mpc

### State estimation
We start by defining a state estimation object. A base class is supplied in mpcpy but due to the specific nature of every model this has to be extended for every MPC.
During creation the estimation object has to be given an emulator object which contains the results from which the states can be estimated.
The implemented `__call__` method  take one argument, time and simply passes this to the `stateestimation` method and returns the result. 
The intention is that the `stateestimation` method can be modified in a child class without affecting the overall object behavior and multiple state estimation object can be created and used.

#### Example:
```
class Stateestimation_perfect(mpcpy.Stateestimation):
	# redefine the stateestimation method
	def stateestimation(self,time):
		state = {}
		state['T_in'] = self.emulator.res['building.C_in.T'][-1]
		state['T_em'] = self.emulator.res['building.C_em.T'][-1]
		return state

stateestimation = Stateestimation_perfect(emulator)
print( stateestimation(0) )
```

			
### Prediction
The `prediction` class is used to generate predictions from the boundary conditions over a certain time period.
On creation it takes a `boundaryconditions` object as argument.
It follows the same structure as the `Stateestimation` class but is predefined with a perfect prediction method.
This can of course be redefined to more realistic or stochastic prediction models.

#### Example:
```
prediction = mpcpy.Prediction(boundaryconditions)
print( prediction([0.,1800.,3600.]) )
```

### Control
The `Control` class combines state estimations and predictions and solves an optimal control problem.
The class is built as a base class as the optimal control program will be different for every system.
Upon initialization a `stateestimation` object, `prediction` object must be given. Several other arguments are optional.
A `parameters=None` argument can be used to pass model parameters to the optimal control problem.
The `horizon=24*3600.` argument determines how far the optimal control problem will look into the future.
The `timestep=3600.` argument determines the discretization time step of the optimal control problem.
The `receding=3600.` argument determines the time between two control optimizations

A `time` method is implemented which creates a control time array for the next control optimization based on a `starttime` argument and the above mentioned times.
The `__call__` method runs the state estimation, the predictions and tries to solve the optimal control problem.
The solving of the optimal control problem is done by calling the solution property which must contain a function which solves the problem and returns a dictionary of control inputs.

The solution function can be set by the `formulation` method.
This is done to avoid redefining the problem on every control time step which could be very slow for large optimal control problems.
In the base class the formulation method returns a blank solution function so this needs to be customized in a child class. 

In the example below IBM Cplex is used as the optimization solver. More information on Cplex can be found below.

#### Example:
```
import cplex
class Linearprogram(mpcpy.Control):
	def formulation(self):
		# define temporary times, state estimations and prediction to use while defining the problem
		time = self.time(0)
		dt = time[1]-time[0]
		N = len(time)
		sta = self.stateestimation(time[0])
		pre = self.prediction(time)
		par = self.parameters
		
		ocp = cplex.Cplex()
		
		# shorthand for 1
		ones = np.ones(N)
		
		# add variables, don't wory about bounds yet as they will be set in the solution function
		ocp.variables.add(obj = 0*ones, lb = 0*ones, ub = 1e6*ones, names = ['Q_flow_hp[%s]'%(i) for i in range(N)])
		ocp.variables.add(obj = 0*ones, lb = 0*ones, ub = 1e6*ones, names = ['T_in[%s]'%(i) for i in range(N)])
		ocp.variables.add(obj = 0*ones, lb = 0*ones, ub = 1e6*ones, names = ['T_em[%s]'%(i) for i in range(N)])
		
		# add state constraints
		for i in range(N-1):
			# T_in
			# C_in/dt*(T_in[i+1]-T_in[i]) = UA_in_amb*(T_amb[i]-T_in[i]) + UA_em_in*(T_em[i]-T_in[i]) + Q_flow_sol[i]
			ocp.linear_constraints.add(
					lin_expr = [[['T_in[%s]'%(i)                                   , 'T_in[%s]'%(i+1) , 'T_em[%s]'%(i)    ],
								 [-par['C_in']/dt+par['UA_in_amb']+par['UA_em_in'] , par['C_in']/dt   , -par['UA_em_in']  ]]],
					senses = 'E',
					rhs = [par['UA_in_amb']*pre['T_amb'][i] + pre['Q_flow_sol'][i] ],
					names = ['state_T_in[%s]'%(i)])
			
			
			# T_em
			# C_em/dt*(T_em[i+1]-T_em[i]) = UA_em_in*(T_in[i]-T_em[i]) + Q_flow_hp[i]
			ocp.linear_constraints.add(
					lin_expr = [[['T_em[%s]'%(i)                  , 'T_em[%s]'%(i+1) , 'T_in[%s]'%(i)    , 'Q_flow_hp[%s]'%(i) ],
								 [-par['C_em']/dt+par['UA_em_in'] ,  par['C_em']/dt  , -par['UA_em_in']  , -1                  ]]],
					senses = 'E',
					rhs = [0],
					names = ['state_T_em[%s]'%(i)])
			
		
		# disable output printing		
		ocp.set_log_stream(None)
		#ocp.set_error_stream(None)
		ocp.set_warning_stream(None)
		ocp.set_results_stream(None)
		
		def solution(sta,pre):
		
			# define the cost function
			ocp.objective.set_linear( [('Q_flow_hp[%s]'%(i),par['COP'][i]*pre['p_el'][i]/1000*dt/3600) for i in range(N)] )
			
			# hard bounds
			ocp.variables.set_lower_bounds( [('T_in[%s]'%(i)     ,pre['T_in_min'][i]) for i in range(N)])
			ocp.variables.set_upper_bounds( [('Q_flow_hp[%s]'%(i),pre['Q_flow_hp_max'][i]) for i in range(N)]
										   +[('T_em[%s]'%(i)     ,pre['T_em_max'][i]) for i in range(N)])
			# solve the optimal control problem
			ocp.solve()
			
			# add a propertie with the ocp problem with the solution for inspection
			self.ocp = ocp	
			
			# return the contol inputs
			sol = {}
			sol['time'] = pre['time']
			sol['Q_flow_hp'] = ocp.solution.get_values(['Q_flow_hp[%s]'%(i) for i in range(N)])

			return sol
		
	return solution	
	

control_parameters = {'C_in': emulation_parameters['building.C_in.C'],
					  'C_em': emulation_parameters['building.C_em.C'],
					  'UA_in_amb': emulation_parameters['building.UA_in_amb.G'],
					  'UA_em_in': emulation_parameters['building.UA_em_in.G'],
					  'COP': 4}
control = Linearprogram(stateestimation,prediction,parameters=control_parameters,horizon=24*3600.,timestep=3600.,receding=3600.)

print( control(0) )
```


## MPC
Everything comes toghether in the `MPC` class. This creates a callable object which runs the MPC and returns a result dictionary from the emulator.

```
mpc = mpcpy.mpc(emulator,control,boundaryconditions,emulationtime=1*24*3600.,resulttimestep=600)
res = mpc()

print(res['Q_flow_hp'])


```


# Cplex in Python

