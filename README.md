mpcpy
=====

A group of classes to run model predictive control (MPC) simulations using python and Dymola.

# Installation
requires:
* `numpy`

To install download the latest [release](https://github.com/BrechtBa/mpcpy/releases), unpack, cd to the unpacked folder and run:
```
python setup.py install
```

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
bcs = {'time': time,
       'T_amb': 5 + 2*np.sin(2*np.pi*time/24./3600.)+273.15,
       'Q_flow_sol': 500 + 500*np.sin(2*np.pi*time/24./3600.),
       'p_el': 0.2 + 0.05*np.sin(2*np.pi*time/24./3600.),
       'Q_flow_hp_max': 5000*np.ones_like(time),
       'T_in_min': 20*np.ones_like(time)+273.15,
       'T_em_max': 30*np.ones_like(time)+273.15}
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
First we need to open and compile a dymola model:
```
import dympy

dymola = dympy.Dymola()
dymola.clear()
dymola.openModel('example.mo')
dymola.compile('example')
```

if we have a dymola model opened and compiled with dympy as `dymola` with 3 inputs `T_amb`, `Q_flow_sol`, `Q_flow_hp` and some parameters defined in Modelica which need to be set, 
you can create and run an emulator object like this:


```
emulator = mpcpy.Emulator(dymola,['T_amb','Q_flow_sol','Q_flow_hp'])
inp = {'time': [0., 3600., 7200.], 'T_amb': [273.15, 274.15, 275.15], 'Q_flow_sol': [500., 400., 300.], 'Q_flow_hp': [4000., 4000., 4000.]}
emulator_parameters = {'C_em.C': 10e6, 'C_in.C': 5e6, 'UA_in_amb.G': 200, 'UA_em_in.G': 1600}
emulator.set_parameters(emulator_parameters)

emulator_initialconditions = {'C_em.T': 22+273.15, 'C_in.T': 21+273.15}
emulator.set_initial_conditions(emulator_initialconditions)

emulator.initialize()
emulator(inp)

print( emulator.res['time'] )
print( emulator.res['C_in.T'] )
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
        state['T_in'] = self.emulator.res['C_in.T'][-1]
        state['T_em'] = self.emulator.res['C_em.T'][-1]
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
        ocp.variables.add(names = ['Q_flow_hp[%s]'%(i) for i in range(N)])
        ocp.variables.add(names = ['T_in[%s]'%(i) for i in range(N)])
        ocp.variables.add(names = ['T_em[%s]'%(i) for i in range(N)])

        # add state constraints
        for i in range(N-1):
            # T_in
            # C_in/dt*(T_in[i+1]-T_in[i]) = UA_in_amb*(T_amb[i]-T_in[i]) + UA_em_in*(T_em[i]-T_in[i]) + Q_flow_sol[i]
            ocp.linear_constraints.add(
                    lin_expr = [[['T_in[%s]'%(i)                                   , 'T_in[%s]'%(i+1) , 'T_em[%s]'%(i)    ],
                                 [-par['C_in']/dt+par['UA_in_amb']+par['UA_em_in'] , par['C_in']/dt   , -par['UA_em_in']  ]]],
                    senses   = 'E',
                    rhs      = [par['UA_in_amb']*pre['T_amb'][i] + pre['Q_flow_sol'][i] ],
                    names    = ['state_T_in[%s]'%(i)])


            # T_em
            # C_em/dt*(T_em[i+1]-T_em[i]) = UA_em_in*(T_in[i]-T_em[i]) + Q_flow_hp[i]
            ocp.linear_constraints.add(
                    lin_expr = [[['T_em[%s]'%(i)                  , 'T_em[%s]'%(i+1) , 'T_in[%s]'%(i)    , 'Q_flow_hp[%s]'%(i) ],
                                 [-par['C_em']/dt+par['UA_em_in'] ,  par['C_em']/dt  , -par['UA_em_in']  , -1                  ]]],
                    senses   = 'E',
                    rhs      = [0],
                    names    = ['state_T_em[%s]'%(i)])

        # add initial values
        ocp.linear_constraints.add(lin_expr = [[['T_in[0]',   ],
                                                 [1]]],
                                   senses   = 'E',
                                   rhs      = [sta['T_in'].item()],
                                   names    = ['T_in_ini'])

        ocp.linear_constraints.add(lin_expr = [[['T_em[0]',   ],
                                                 [1]]],
                                   senses   = 'E',
                                   rhs      = [sta['T_em'].item()],
                                   names    = ['T_em_ini'])
            
            
        # disable output printing
        ocp.set_log_stream(None)
        #ocp.set_error_stream(None)
        ocp.set_warning_stream(None)
        ocp.set_results_stream(None)

        self.ocp = ocp
        
        def solution(sta,pre):
            # define the cost function
            ocp.objective.set_linear( [('Q_flow_hp[%s]'%(i),par['COP']*pre['p_el'][i]/1000*dt/3600) for i in range(N)] )

            # hard bounds
            ocp.variables.set_lower_bounds( [('T_in[%s]'%(i)     ,pre['T_in_min'][i]) for i in range(N)])
            ocp.variables.set_upper_bounds( [('Q_flow_hp[%s]'%(i),pre['Q_flow_hp_max'][i]) for i in range(N)]
                                           +[('T_em[%s]'%(i)     ,pre['T_em_max'][i]) for i in range(N)])
            
            
            # state constraints
            ocp.linear_constraints.set_rhs( [('state_T_in[%s]'%(i),par['UA_in_amb']*pre['T_amb'][i] + pre['Q_flow_sol'][i]) for i in range(N-1)]
                                           +[('state_T_em[%s]'%(i),0) for i in range(N-1)] )

            # initial conditions
            ocp.linear_constraints.set_rhs( [('T_in_ini',sta['T_in'].item())]
                                           +[('T_em_ini',sta['T_em'].item())] )
            
            # solve the optimal control problem
            ocp.solve()

            # add a properties with the ocp problem with the solution for inspection
            self.ocp = ocp

            # return the contol inputs
            sol = {}
            sol['time'] = pre['time']
            sol['Q_flow_hp'] = ocp.solution.get_values(['Q_flow_hp[%s]'%(i) for i in range(N)])

            return sol

        return solution


control_parameters = {'C_in': emulator_parameters['C_in.C'],
                      'C_em': emulator_parameters['C_em.C'],
                      'UA_in_amb': emulator_parameters['UA_in_amb.G'],
                      'UA_em_in': emulator_parameters['UA_em_in.G'],
                      'COP': 4}
control = Linearprogram(stateestimation,prediction,parameters=control_parameters,horizon=24*3600.,timestep=3600.,receding=3600.)

print( control.ocp.solution.get_status() )
print( control(0) )
```


## MPC
Everything comes together in the `MPC` class. This creates a callable object which runs the MPC and returns a result dictionary from the emulator.

```
mpc = mpcpy.MPC(emulator,control,boundaryconditions,emulationtime=1*24*3600.,resulttimestep=600)
res = mpc()
print(res['Q_flow_hp'])
```



# Cplex in Python
IBM ILOG CPlex has it's own API for python. 

## Installation
The following instructions were adapted from [here](http://www-01.ibm.com/support/knowledgecenter/SSSA5P_12.6.2/ilog.odms.cplex.help/CPLEX/GettingStarted/topics/set_up/Python_setup.html?lang=en)
Go to the directory you installed CPlex in 'YOURCPLEXDIR', on windows this could be `C:\Program Files (x86)\IBM\ILOG\CPLEX_Studio1261\cplex`.
now go to `YOURCPLEXDIR/python/VERSION/PLATFORM` where VERSION is your python version (2.7 or 3.4 most likely) and PLATFORM is your platform (for instance x86_win32 on a 32 bit windows computer). 

Now it is best to install the cplex package in your package directory ('YOURPYTHONPACKAGEDIR') as this is where python searches for packages.
On a windows system with python 2.7 this is probably `C:\Python27\Lib\site-packages`
This is done by running the following command in a terminal:
```
python setup.py install --home YOURPYTHONPACKAGEDIR/cplex
```

After this is done you should be able to run the rest of the code presented below.


## Workflow
The use of Cplex in python will here be explained by defining, solving and processing the output of an optimal control problem (OCP).

To start using the Cplex python API first import it and import numpy for array handling
```
import cplex
import numpy as np
```
a new optimization problem can be created with:
```
ocp = cplex.Cplex()
```

We will define some parameters to use in the example, they are of no importance.
```
# number of time points in the OCP
N = 25
dt = 3600.
time = np.arange(N)*dt

# prediction dictionary
pre = {'T_in_min': 20*np.ones(N),
       'T_em_max': 30*np.ones(N),
       'T_amb': 5 + 5*np.sin(2*np.pi*(time/24/3600-0.6)),
       'Q_flow_hp_max': 5000*np.ones(N),
       'Q_flow_sol': np.clip(2000*np.sin(2*np.pi*(time/24/3600-0.4)),0,10000),
       'p_el': np.clip( 0.18 + 0.10*np.sin(2*np.pi*(time/24/3600-0.0)),0,0.24 )}

# parameter dictionary
par = {'COP': 4,
       'C_in': 10e6,
       'C_em': 20e6,
       'UA_in_amb': 200,
       'UA_em_in': 1600}
```

### Variables
Variable must be added to the problem using the `cplex.variables.add` method. This method has several keyword arguments  all of which must all be a list of values.
All supplied arguments must have equal length. Arguments are:
- `names`: list of strings, variable names which can be used to reference the variable
- `obj`: list of floats, coefficient of the linear objective function accompanying the variable
- `lb`: list of floats, lower bounds of the variables, defaults to 0
- `ub`: list of floats, upper bounds of the variables, defaults to 1e20
- `type`: list of single character strings 'C','I','B' for continuous, integer, binary variables respectively?
Cplex is suitable for solving Mixed Integer Programs.

When defining an optimal control problem is is easy to use list comprehensions built into python together with string formatting to generate meaningful names for all variables.
These names will then refer to the correct column in the constraint and objective matrices.
```
ocp.variables.add(names = ['Q_flow_hp[{0}]'.format(i) for i in range(N)])
ocp.variables.add(names = ['T_in[{0}]'.format(i) for i in range(N)])
ocp.variables.add(names = ['T_em[{0}]'.format(i) for i in range(N)])
```

Boundaries for the variables can be set during variable creation or using the methods `cplex.variable.set_lower_bounds` and `cplex.variable.set_upper_bounds`.
These methods accept either a variable name/index, value pair or a list of variable name/index, value pair tuples. Again using list comprehensions makes everything easy.
It is preferred to make few calls of a function with a larger set of variables than the other way around as this reduced overhead.
```
ocp.variables.set_lower_bounds( 'T_in[0]',pre['T_in_min'][0] )
# or
ocp.variables.set_lower_bounds( [('T_in[{0}]'.format(i)     ,pre['T_in_min'][i]) for i in range(N)] )
ocp.variables.set_upper_bounds( [('Q_flow_hp[{0}]'.format(i),pre['Q_flow_hp_max'][i]) for i in range(N)]
                               +[('T_em[{0}]'.format(i)     ,pre['T_em_max'][i]) for i in range(N)] )
```

For most "set" methods in cplex there is a corresponding "get" method which can be used to retrieve values.

### Objective
The objective function can have linear and quadratic terms quadratic, cplex will select an appropriate solution method automatically.

The linear terms in the objective function can be defined using `cplex.objective.set_linear`.
This function accepts the same input argument format as the `cplex.variables.set_lower_bounds` method explained above.
```
ocp.objective.set_linear( 'Q_flow_hp[0]', par['COP']*pre['p_el'][0]/1000*dt/3600 )
# or
ocp.objective.set_linear( [('Q_flow_hp[{0}]'.format(i), par['COP']*pre['p_el'][i]/1000*dt/3600) for i in range(N)] ))
```

Quadratic terms in the objective function are easiest to define with `cplex.objective.set_quadratic_coefficients`.
Now 3 arguments or a list of tuples of 3 must be given containing two variables and the value. 
Of course care must be taken that the quadratic part remains positive semidefinite or the problem will become non-convex.
In the example below a small cost is given to the square of some variables:
```
ocp.objective.set_quadratic_coefficients( [('Q_flow_hp[%s]'%(i),'Q_flow_hp[%s]'%(i),0.01*par['COP']*pre['p_el'][i]/1000*dt/3600) for i in range(N)] )
```

### Constraints
Both linear and quadratic constraints can be defined and reside in separate attributes.

Linear constraints can be added to the problem with `cplex.linear_constraints.add`.
It accepts the following keyword arguments:
- lin_expr: list of matrices in list of lists format or a list of cplex sparce pairs, expresses the lhs of the constraint
- senses: list of single character strings which, expresses the sense of the constraint, 'G','L','E','R' for Greater, Lesser, Equal and Ranged respectively 
- rhs: list of floats, specifies the rhs of the constraints
- range_values: list of floats specifying a range for the rhs if range_values[i] > 0 : rhs[i] <= a*x <= rhs[i]+range_values[i] else rhs[i]+range_values[i] <= a*x <= rhs[i]
- names: a list of strings, names for the constraints

An custom cplex type has come up, the `cplex.SparsePair`. This type assigns values to an index which is referred to.
The example below can be used to assign values to the row of `T_in[0]` and `T_in[1]` in some constraint:
```
cplex.SparsePair(ind = ['T_in[0]', 'T_in[1]'], val = [5.0, 6.5])
```

For the optimal control problem at hand the equations have to be discretized manually (leaving you the freedom to choose how to discretize).
Again list comprehensions are useful when adding constraints to our problem:
```
# state constraints for T_in
# C_in/dt*(T_in[i+1]-T_in[i]) = UA_in_amb*(T_amb[i]-T_in[i]) + UA_em_in*(T_em[i]-T_in[i]) + Q_flow_sol[i]


ocp.linear_constraints.add( lin_expr = [ [['T_in[{0}]'.format(i)                           , 'T_in[{0}]'.format(i+1), 'T_em[{0}]'.format(i) ],
                                          [-par['C_in']/dt+par['UA_in_amb']+par['UA_em_in'], par['C_in']/dt         , -par['UA_em_in']      ]] for i in range(N-1)],
                            senses   = ['E' for i in range(N-1)],
                            rhs      = [par['UA_in_amb']*pre['T_amb'][i] + pre['Q_flow_sol'][i] for i in range(N-1)],
                            names    = ['state_T_in[{0}]'.format(i) for i in range(N-1)] )

# or
# state constraints for T_em
# C_em/dt*(T_em[i+1]-T_em[i]) = UA_em_in*(T_in[i]-T_em[i]) + Q_flow_hp[i]
ocp.linear_constraints.add( lin_expr = [ cplex.SparsePair( ind = ['T_em[{0}]'.format(i)          , 'T_em[{0}]'.format(i+1), 'T_in[{0}]'.format(i) , 'Q_flow_hp[{0}]'.format(i) ], 
                                                           val = [-par['C_em']/dt+par['UA_em_in'], par['C_em']/dt         , -par['UA_em_in']      , -1                         ]
                                                          ) for i in range(N-1)],
                            senses   = ['E' for i in range(N-1)],
                            rhs      = [0 for i in range(N-1)],
                            names    = ['state_T_em[{0}]'.format(i) for i in range(N-1)] )
```

Our problem also needs initial values which are also equality constraints:
```
# add initial values
ocp.linear_constraints.add(lin_expr = [[['T_in[0]'],
                                        [1        ]]],
                           senses   = 'E',
                           rhs      = [21],
                           names    = ['T_in_ini'])

ocp.linear_constraints.add(lin_expr = [[['T_em[0]'],
                                        [1        ]]],
                           senses   = 'E',
                           rhs      = [22],
                           names    = ['T_em_ini'])
```

When using the OCP in a model predictive control strategy it is common that the bounds and right hand side of constraints change.
As this is only a small change in the large OCP it is appropriate to only change this part of the OCP reducing unnecessary computations.
This can be done with the `cplex.linear_constraints.set_rhs` method.
It accepts a list of tuples containing a constraint name/index and a value just like `cplex.variable.set_lower_bounds` and `cplex.objective.set_linear` :
```
ocp.linear_constraints.set_rhs( [('state_T_in[{0}]'.format(i),par['UA_in_amb']*pre['T_amb'][i] + pre['Q_flow_sol'][i]) for i in range(N-1)]  
                               +[('state_T_em[{0}]'.format(i),0) for i in range(N-1)] )
```
           
### Solving and retrieving the solution
Solving is easy:
```
ocp.solve()
```
cplex does the rest.

You can suppress output if required with the following commands:
```
ocp.set_log_stream(None)
ocp.set_error_stream(None)
ocp.set_warning_stream(None)
ocp.set_results_stream(None)
```

Retrieving the solution is equally easy, pay attention though that cplex returns regular lists, not numpy arrays, best to convert them immediately:
```
sol = {}
sol['Q_flow_hp'] = np.array(ocp.solution.get_values(['Q_flow_hp[{0}]'.format(i) for i in range(N)]))
sol['T_in']      = np.array(ocp.solution.get_values(['T_in[{0}]'.format(i) for i in range(N)]))
sol['T_em']     = np.array(ocp.solution.get_values(['T_em[{0}]'.format(i) for i in range(N)]))
print(sol['T_in'])
```

