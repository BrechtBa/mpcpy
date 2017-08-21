Quickstart
==========
.. toctree::
    :maxdepth: 3

    
MPC programming structure
-------------------------

In Model Predictive Control (MPC) a dynamic system is controlled with some
control inputs. These inputs are computed with the aid of a model of the dynamic
system which predicts the system behavior over a certain time horizon.

An MPC simulation is here defined as a dynamic simulation of such a system. In
such a simulation the actual system is replaced by a system emulator, a dynamic 
simulation which should model the system behavior a close as possible.

The control algorithm contains a more simplified model of the dynamic system and
often uses an optimization technique to compute the control signals which
minimize some objective function over a time horizon. This is referred to as an 
Optimal Control Problem (OCP).

The system under consideration is most likely subjected to some uncontrolled
boundary conditions. The OCP thus requires a prediction of these boundary
conditions over the prediction horizon to be able to compute the system
behavior. Furthermore, an estimation of the current system state is needed,
probably requiring some (virtual) measurements.

An MPC simulation can thus be broken down into the following steps:

* Estimate the state of the system.
* Generate a prediction for the boundary conditions over the control horizon.
* Compute control signals by solving an OCP.
* Supply the control signals to a system emulator and simulate the system behavior.
* Repeat.


In mpcpy the :code:`mpcpy.mcp` object contains the main functions for
orchestrating the MPC. It depends on an :code:`mpcpy.emulator` object, an
:code:`mpcpy.boundaryconditions` object and an :code:`mpcpy.control` object.

The emulation time is split up in parts defined by the control receding time.
For each part, the above steps are executed and the emulator simulates the
system over the receding time. 

The :code:`mpcpy.control` object handles the generation of control signals.
Therfore it requires an :code:`mpcpy.stateestimation` object and an 
:code:`mpcpy.prediction` object.

Example
^^^^^^^

.. code-block:: python

    mpc = mpcpy.MPC(emulator,control,boundaryconditions,emulationtime=10000,resulttimestep=10)
    # in this statement the emulator, control and boundaryconditions parameters should be defined according to the following documentation



Emulator
--------

The :code:`mpcpy.emulator` class serves as a base class for defining emulator
objects. By default, the emulator object returns the control solution as its
result. So when no detailed emulator model is available, the 
:code:`mpcpy.emulator` class can be used to split an OCP in different parts and
solve it sequentially. Care must be taken that the OCPs overlap sufficiently, so
the receding time must be significantly shorter than the horizon.

The :code:`mpcpy.emulator` class requires a list of keys as input arguments,
this list specifies which boundary conditions and control signals should be 
passed to the simulation, all control signals are passed to the simulation.

When subclassing the :code:`mpcpy.emulator` class the main method to be
redefined is the :code:`simulate` method. This method receives a starttime,
stoptime and input dictionary as arguments and should return a results
dictionary with a time array and values for the results between the start- and
stoptime.

Internally a :code:`res` dictionary holds the results of the simulation up to
the current point in time. This :code:`res` dictionary can also be used to
determine the state required for the OCP.

The system can then be simulated by calling an :code:`mpcpy.emulator` object
with an array of input times (the time steps at which results are required) and
a dictionary of inputs. During an MPC simulation this is handled by the 
:code:`mpcpy.mpc` object.

Example
^^^^^^^

.. code-block:: python

    class Emulator(mpcpy.Emulator):
        """
        A custom system emulator
        """
        def simulate(self,starttime,stoptime,input):
            dt = 60
            time = np.arange(starttime,stoptime+dt,dt,dtype=np.float)

            # initialize
            x = np.ones_like(time)*self.res['x'][-1]
            
            # interpolate inputs
            u = np.interp(time,input['time'],input['u'])
            d = np.interp(time,input['time'],input['d'])
            
            # perform simulation
            for i,t in enumerate(time[:-1]):
                # dx/dt = A*x + d + u
                x[i+1] = x[i] + ( self.parameters['A']*x[i] + d[i] + u[i] )*dt
                
                
            # create and return a results dict    
            res = {
                'time': time,
                'x': x,
                'd': d,
                'u': u,
            }
            
            return res
    
    emulator = Emulator(['u','d'],parameters={'A':-0.2},initial_conditions={'x':0})
    emulator.initialize()
    
    
    time = np.arange(0.,1001.,100.)
    d = np.random.random(len(time)) - 0.5
    u = np.ones(len(time))
    
    res = emulator(time,{'time':time,'d',d,'u',u})


    
Boundary conditions
-------------------

The :code:`mpcpy.boundaryconditions` class is a helper class for manging the
required boundary conditions.
Signals are defined based on a dictionary which must include a :code:`time` key
and specifies the values of all signals at these time steps.
An :code:`mpcpy.boundaryconditions` object can then interpolate the values to
the required time points in the :code:`mpcpy.emulator` and
:code:`mpcpy.prediction` objects.

Example
^^^^^^^

.. code-block:: python

    time = np.arange(0.,1001.,100.)
    d = np.random.random(len(time)) - 0.5
    boundaryconditions = mpcpy.boundaryconditions({'time':time,'d',d})
    
    bcs = boundaryconditions(np.array([0,20,40,60,100]))
    

    
Control
-------
The emulator requires control inputs which are generated by an object derived
from the :code:`mpcpy.Control` base class. 
The methods that should be redefined in a child class are the 
:code:`formulation` and :code:`solution` methods.

The :code:`formulation` method is called once by the :code:`mpcpy.mpc` object
before the start of the simulation. This method can thus be used to formulate an
abstract optimal control problem and assign values that will not change through 
the course of the simulation.

The :code`solution` method should generate the control signals to be used by the
emulator. When the control signals should be generated, it is called with two 
parameters representing the current state of the system and the predictions of 
the boundary conditions over the control horizon. These are generated by the
:code:`mpcpy.stateestimation` and :code:`mpcpy.prediction` objects supplied to
the control object during initialization respectively.
The :code`solution` method must return a dictionary with a time vector and the 
control signal values over the entire control horizon.

Example
^^^^^^^
    
.. code-block:: python
  
    class RandomControl(mpcpy.Control):
        """
        A nonsense example to illustrate how a child control class can be defined
        """
        
        def formulation(self):
            self.newparameter = -1
            
        def solution(self,sta,pre):
        
            return {'time':pre['time'],'u':self.newparameter*sta['x'] + self.parameters['B']*np.random.random(len(pre['time']))}
  
  
    control = RandomControl(stateestimation,prediction,parameters={'B':0.5},horizon=1000.,timestep=100.,receding=100.)
    # in this statement the stateestimation and prediction parameters should be defined according to the following documentation

    
    
State estimation
----------------

The :code:`mpcpy.stateestimation` class is a base class for defining object that
estimate the current state required for the control based on measurements done
on the emulator. When the states required for the control problem are not
directly measurable they are often computed with a Kalman filter.
The main method to redefine in a child class is the :code`stateestimation` 
method. This method takes the time at which the states should be estimated as an
input parameter and must return a dictionary of key-value pairs representing the 
state at that time.

Example
^^^^^^^

.. code-block:: python

    class StateestimationPerfect(mpcpy.Stateestimation):
        def stateestimation(self,time):
            return {'x': np.interp(time,self.emulator.res['time'],self.emulator.res['x'])}
    
    stateestimation = StateestimationPerfect(emulator)
    
    sta = stateestimation(0)


  
Prediction
----------

The :code:`mpcpy.prediction` class is a base class for returning prediction data
required for the OCP.

It requires a :code:`mpcpy.boundaryconditions` object which represent the actual
conditions. From these values predictions may be derived.

Example
^^^^^^^

.. code-block:: python

    # continuing from the boundaryconditions object defined above
    
    prediction = mpcpy.Prediction(boundaryconditions)
    
    pre = prediction(np.array([0,20,40,60,100]))
    

    
MPC
---

The entire MPC simulation can now be run from the above defined objects. Just
call the :code:`mpcpy.mpc` object to start the simulation. Results will be
returned in a dictionary.


Example
^^^^^^^

.. code-block:: python

    control = RandomControl(stateestimation,prediction,parameters={'B':0.5},horizon=1000.,timestep=100.,receding=100.)
    mpc = mpcpy.MPC(emulator,control,boundaryconditions,emulationtime=10000,resulttimestep=10)
    res = mpc()