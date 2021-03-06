# $Id$
##
##  This file is part of pyFormex 0.8.3 Release Sun Dec  5 18:01:17 2010
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Homepage: http://pyformex.org   (http://pyformex.berlios.de)
##  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##  Distributed under the GNU General Public License version 3 or later.
##
##
##  This program is free software: you can redistribute it and/or modify
##  it under the terms of the GNU General Public License as published by
##  the Free Software Foundation, either version 3 of the License, or
##  (at your option) any later version.
##
##  This program is distributed in the hope that it will be useful,
##  but WITHOUT ANY WARRANTY; without even the implied warranty of
##  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
##  GNU General Public License for more details.
##
##  You should have received a copy of the GNU General Public License
##  along with this program.  If not, see http://www.gnu.org/licenses/.
##

"""Postprocessing functions

Postprocessing means collecting a geometrical model and computed values
from a numerical simulation, and render the values on the domain.
"""

from numpy import *



# Some functions to calculate a scalar value from a vector

def norm2(A):
    return sqrt(square(asarray(A)).sum(axis=-1))

def norm(A,x):
    return power(power(asarray(A),x).sum(axis=-1),1./x)

def max(A):
    return asarray(A).max(axis=-1)

def min(A):
    return asarray(A).min(axis=-1)
   

def niceNumber(f,approx=floor):
    """Returns a nice number close to but not smaller than f."""
    n = int(approx(log10(f)))
    m = int(str(f)[0])
    return m*10**n


def argNearestValue(values,target):
    """Return the index of the item nearest to target.

    ``values``: a list of float values
    
    ``target``: a single value

    Return value: the position of the item in ``values`` values that is
    nearest to ``target``.
    """
    v = array(values).ravel()
    c = v - target
    return argmin(c*c)


def nearestValue(values,target):
    """Return the item nearest to target.

    ``values``: a list of float values
    
    ``target``: a single value

    Return value: the item in ``values`` values that is
    nearest to ``target``.
    """
    return values[argNearestValue(values,target)]


def frameScale(nframes=10,cycle='up',shape='linear'):
    """Return a sequence of scale values between -1 and +1.

    ``nframes`` : the number of steps between 0 and -1/+1 values.

    ``cycle``: determines how subsequent cycles occur:
      
      ``'up'``: ramping up
      
      ``'updown'``: ramping up and down
      
      ``'revert'``: ramping up and down then reverse up and down

    ``shape``: determines the shape of the amplitude curve:
    
      ``'linear'``: linear scaling
      
      ``'sine'``: sinusoidal scaling
    """
    s = arange(nframes+1)
    if cycle in [ 'updown', 'revert' ]:
        s = concatenate([s, fliplr(s[:-1].reshape((1,-1)))[0]])
    if cycle in [ 'revert' ]: 
        s = concatenate([s, -fliplr(s[:-1].reshape((1,-1)))[0]])
    return s.astype(float)/nframes


# End
