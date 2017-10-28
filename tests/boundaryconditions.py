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

class TestBoundaryconditions(unittest.TestCase):
    
    def test_create(self):
        boundaryconditions = mpcpy.Disturbances(bcs)
    
    def test_create_periodic(self):
        boundaryconditions = mpcpy.Disturbances(bcs, periodic=True)
        boundaryconditions = mpcpy.Disturbances(bcs, periodic=False)
        
    def test_create_extratime(self):
        boundaryconditions = mpcpy.Disturbances(bcs, extra_time=1 * 24 * 3600)
        boundaryconditions = mpcpy.Disturbances(bcs, periodic=False, extra_time=1 * 24 * 3600)
    
    def test_getitem(self):
        boundaryconditions = mpcpy.Disturbances(bcs)
        temp = boundaryconditions['y0']

    def test_value(self):
        boundaryconditions = mpcpy.Disturbances(bcs)
        
        t0 = 1*24*3600.
        val = boundaryconditions(t0)

        self.assertEqual(val,{'time':t0,'y0':np.interp(t0,time,y0),'y1':np.interp(t0,time,y1)})

    def test_value_periodic(self):
        boundaryconditions = mpcpy.Disturbances(bcs)
        
        t0 = 1*24*3600.
        t1 = t0 + time[-1]
        
        val0 = boundaryconditions(t0)
        val1 = boundaryconditions(t1)

        self.assertEqual(val0['y0'],val1['y0'])
        self.assertEqual(val0['y1'],val1['y1'])
    
    def test_value_periodic_timeoffset(self):
        bcs_timeoffset = dict(bcs)
        bcs_timeoffset['time'] = bcs_timeoffset['time'] + 2*24*3600.
        boundaryconditions = mpcpy.Disturbances(bcs_timeoffset)
        
        t0 = 3*24*3600.
        t1 = t0 + (time[-1]-time[0])
        
        val0 = boundaryconditions(t0)
        val1 = boundaryconditions(t1)

        self.assertEqual(val0['y0'],val1['y0'])
        self.assertEqual(val0['y1'],val1['y1'])
    
    def test_value_notperiodic(self):
        boundaryconditions = mpcpy.Disturbances(bcs, periodic=False)
        
        t0 = 1*24*3600.
        t1 = t0 + time[-1]
        
        val0 = boundaryconditions(time[-1])
        val1 = boundaryconditions(t1)

        self.assertEqual(val0['y0'],val1['y0'])
        self.assertEqual(val0['y1'],val1['y1'])
    
    
    
if __name__ == '__main__':
    unittest.main()