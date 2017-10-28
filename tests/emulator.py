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
import sys
import os


# current path
modulepath = os.path.abspath(os.path.dirname(sys.modules[__name__].__file__))


class TestEmulator(unittest.TestCase):
    def setUp(self):

        self.ini = {'C_em.T': 22+273.15, 'C_in.T': 21+273.15}
        self.par = {'C_em.C': 10e6,
               'C_in.C': 5e6,
               'UA_in_amb.G': 200,
               'UA_em_in.G': 1600}
        self.inp = {
            'time':  np.array([0.    , 3600. , 7200.]),
            'T_amb':      np.array([273.15, 274.15, 275.15]),
            'Q_flow_sol': np.array([500.  , 400.  , 300.]),
            'Q_flow_hp':  np.array([4000. , 4000. , 4000.])
        }

    def test_create(self):
        emulator = mpcpy.Emulator([])

        
    def test_call(self):
        emulator = mpcpy.Emulator([])
        emulator(self.inp['time'],self.inp)
        
        self.assertEqual(emulator.res['time'][1],self.inp['time'][1])
        self.assertEqual(emulator.res['Q_flow_sol'][2],self.inp['Q_flow_sol'][2])

if __name__ == '__main__':
    unittest.main()