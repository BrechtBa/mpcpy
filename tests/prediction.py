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

import unittest
import mpcpy
import numpy as np


# define variables
time = np.arange(0.0,7*24*3600.+1.,900.)
y0 = np.sin(time/(24*3600.))
y1 = np.random.random(len(time))
bcs = {'time':time, 'y0':y0, 'y1':y1}

boundaryconditions = mpcpy.Disturbances(bcs)
    

class TestPrediction(unittest.TestCase):
    
    def test_create(self):
        prediction = mpcpy.Prediction(boundaryconditions)

    def test_value(self):
        prediction = mpcpy.Prediction(boundaryconditions)

        t0 = 1*24*3600.

        self.assertEqual(prediction(t0),boundaryconditions(t0))

    
    
if __name__ == '__main__':
    unittest.main()