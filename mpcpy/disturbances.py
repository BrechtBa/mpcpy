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


class Disturbances(object):
    """
    A class to define disturbances in the format required by mpcpy.

    """
    
    def __init__(self, data, periodic=True, extra_time=7*24*3600., zoh_keys=None):
        """
        Create a disturbances object.
        
        Parameters
        ----------
        data : dict
            Actual boundary conditions and a time vector.
            
        periodic : boolean, optional
            Determines how to determine values when time is larger than the
            boundary conditions time.
            
        extra_time : float, optional
            Maximum allowed time outside the boundary conditions time, should be
            at least as large as the control horizon.
    
        zoh_keys : list of strings, optional
            Keys which will be interpolated with zero-order hold. All other
            values are interpolated linearly.
    
        Examples
        --------
        >>> dst = Disturbances({'time': np.arange(0.,24*3600.+1,3600.), 'T_amb':np.random.random(25)})
        >>> dst(12.1*3600)
            
        """
        
        self.data = {}
        
        # create a new time vector including the extra time
        # this method is about 2 times faster than figuring out the correct time during interpolation
        ind = np.where(data['time']-data['time'][0] < extra_time)[0]
        self.data['time'] = np.concatenate((data['time'][:-1], data['time'][ind]+data['time'][-1]-data['time'][0]))
        
        if periodic:
            # the values at time lower than extra_time are repeated at the end of the dataset
            # extra_time should thus be larger than the control horizon
            for key in data:
                if key != 'time':
                    self.data[key] = np.concatenate((data[key][:-1], data[key][ind]))
        else:
            # last value is repeated after the actual data
            for key in data:
                if key != 'time':
                    self.data[key] = np.concatenate((data[key][:-1], data[key][-1]*np.ones(len(ind))))
        
        if zoh_keys is None:
            self.zoh_keys = []
        else:
            self.zoh_keys = zoh_keys

    def interp(self, key, time):
        """
        Interpolate a value to an array of timesteps
        
        Parameters
        ----------
        key : str
            The key to interpolate.
            
        time : np.array
            An array of times to interpolate to.
            
        """
        
        if len(np.array(self.data[key]).shape) == 1:
            if key in self.zoh_keys:
                value = interp_zoh(time, self.data['time'], self.data[key])
            else:
                value = np.interp(time, self.data['time'], self.data[key])
                
        elif len(np.array(self.data[key]).shape) == 2:
            # 2d boundary conditions support
            value = np.zeros((len(time), self.data[key].shape[1]))
            if key in self.zoh_keys:
                for j in range(self.data[key].shape[1]):
                    value[:, j] = interp_zoh(time, self.data['time'], self.data[key][:, j])
            else:
                for j in range(self.data[key].shape[1]):
                    value[:, j] = np.interp(time, self.data['time'], self.data[key][:, j])
        else:
                raise Exception('Only 1D or 2D data allowed as boundary conditions')
                
        return value
        
    def __call__(self, time):
        """
        Return the interpolated boundary conditions
        
        Parameters
        ----------
        time : number or np.array
            true value for time
        
        Returns
        -------
        dict
            Dictionary with interpolated boundary conditions.
            
        """
        
        dst_int = {}
        for key in self.data:
            dst_int[key] = self.interp(key, time)
            
        return dst_int

    def __getitem__(self, key):
        return self.data[key]
        
    def has_key(self, key):
        return self.data.has_key(key)
        
    def __contains__(self, item):
        return item in self.data
        
    def __iter__(self):
        return self.data.__iter__()


def interp_zoh(x, xp, fp):
    """
    Interpolate with zero order hold
    
    Parameters
    ----------
    x : np.array
        An array of independent variables where the values are required.
        
    xp : np.array
        An array of independent variables where the values are known, must be
        monotonic and increasing.
        
    fp : np.array
        The known values at points xp.
        
    Returns
    -------
    np.array
        The interpolated values
    
    """
    
    return np.array([fp[int((len(xp)-1)*(xi-xp[0])/(xp[-1]-xp[0]))] for xi in x])
