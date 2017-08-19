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
val = 123

class TestStateestimation(unittest.TestCase):
    
    def test_create(self):
        class Stateestimation(mpcpy.Stateestimation):
            def stateestimation(self,time):
                return val
    
        stateestimation = Stateestimation(None)

    def test_value(self):
        class Stateestimation(mpcpy.Stateestimation):
            def stateestimation(self,time):
                return val
    
        stateestimation = Stateestimation(None)

        self.assertEqual(stateestimation(0),val)

    
    
if __name__ == '__main__':
    unittest.main()