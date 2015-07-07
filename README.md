# mpcpy

A group of classes to run model predictive control (MPC) simulations using python and Dymola.


## Workflow
In a model predictive control simulation we need several components.
At first we need an emulator to replace the real world system in our computational environment.
The system is subjected to certain boundary conditions which may vary.
Next we need a controller which will determine the inputs we must supply to the emulated system so it moves in the wanted direction.
As we are considering MPC the controller will consist of a state estimation, a prediction and an optimization

For each of these components base classes are included in mpcpy.
Some of these classes can be used out off the box, others require child class creation which will be explained below.

before we start import the package
```
import mpcpy.Emulator 
```

### Emulator
The most important method in the emulator class it the __call__ method.
This method should have the inputs to the emulator as arguments and append the results to it's "res" property.
By default a dympy Dympola connection is assumed to do the simulation work but the class can be adapted to use other simulation tools.


i.e.
if we have a dymola model opend and compyled with dympy with 3 inputs "T_amb","Q_flow_sol","Q_flow_hp" you can create an emulator object like this:
```
emulator = mpcpy.Emulator(dymola,['T_amb','Q_flow_sol','Q_flow_hp'])
```


### Boundary conditions


### Control
#### State estimation
#### Prediction





### MPC





# Cplex in Python

