# $Id$
##
##  This file is part of pyFormex 0.8 Release Sat Jun 13 10:22:42 2009
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Website: http://pyformex.berlios.de/
##  Copyright (C) Benedict Verhegghe (bverheg@users.berlios.de) 
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
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##

"""A collection of numerical array utilities.

These are general utility functions that depend only on the numpy array model.
All pyformex modules needing numpy should import everything from this module.
"""

from numpy import *


###########################################################################
##
##   some math functions
##
#########################

# Define a wrapper function for old versions
#

if unique1d([1],True)[0][0] == 0:
    # We have the old numy version
    print "BEWARE: OLD VERSION OF NUMPY!!!!"
    def unique1d(a,return_indices=False):
        """Replacement for numpy's unique1d"""
        import numpy
        if return_indices:
            indices,uniq = numpy.unique1d(a,True)
            return uniq,indices
        else:
            return numpy.unique1d(a)


# default float and int types
Float = float32
Int = int32


###########################################################################
##
##   some math functions
##
#########################
   

def niceLogSize(f):
    """Return the smallest integer e such that 10**e > abs(f)."""
    return int(ceil(log10(abs(f))))
   

def niceNumber(f,approx=floor):
    """Return a nice number close to but not smaller than f."""
    n = int(approx(log10(f)))
    m = int(str(f)[0])
    return m*10**n

# pi is defined in numpy
# rad is a multiplier to transform degrees to radians
rad = pi/180.

# Convenience functions: trigonometric functions with argument in degrees
# Should we keep this in ???


def sind(arg):
    """Return the sin of an angle in degrees."""
    return sin(arg*rad)


def cosd(arg):
    """Return the cos of an angle in degrees."""
    return cos(arg*rad)


def tand(arg):
    """Return the tan of an angle in degrees."""
    return tan(arg*rad)


def dotpr (A,B,axis=-1):
    """Return the dot product of vectors of A and B in the direction of axis.

    The default axis is the last.
    """
    A = asarray(A)
    B = asarray(B)
    return (A*B).sum(axis)


def length(A,axis=-1):
    """Returns the length of the vectors of A in the direction of axis.

    The default axis is the last.
    """
    A = asarray(A)
    return sqrt((A*A).sum(axis))


def normalize(A,axis=-1):
    """Normalize the vectors of A in the direction of axis.

    The default axis is the last.
    """
    A = asarray(A)
    shape = list(A.shape)
    shape[axis] = 1
    return A / length(A,axis).reshape(shape)


def projection(A,B,axis=-1):
    """Return the (signed) length of the projection of vector of A on B.

    The default axis is the last.
    """
    return dotpr(A,B,axis)/length(B,axis)

def norm(v,n=2):
    """Return a norm of the vector v.

    Default is the quadratic norm (vector length)
    n == 1 returns the sum
    n <= 0 returns the max absolute value
    """
    a = asarray(v).flat
    if n == 2:
        return sqrt((a*a).sum())
    if n > 2:
        return (a**n).sum()**(1./n)
    if n == 1:
        return a.sum()
    if n <= 0:
        return abs(a).max()
    return


def inside(p,mi,ma):
    """Return true if point p is inside bbox defined by points mi and ma"""
    return p[0] >= mi[0] and p[1] >= mi[1] and p[2] >= mi[2] and \
           p[0] <= ma[0] and p[1] <= ma[1] and p[2] <= ma[2]


def isClose(values,target,rtol=1.e-5,atol=1.e-8):
    """Returns an array flagging the elements close to target.

    values is a float array, target is a float value.
    values and target should be broadcastable to the same shape.
    
    The return value is a boolean array with shape of values flagging
    where the values are close to target.
    Two values a and b  are considered close if
        | a - b | < atol + rtol * | b |
    """
    values = asarray(values)
    target = asarray(target) 
    return abs(values - target) < atol + rtol * abs(target) 


def origin():
    """Return a point with coordinates [0.,0.,0.]."""
    return zeros((3),dtype=Float)


def unitVector(axis):
    """Return a unit vector in the direction of a global axis (0,1,2).

    Use normalize() to get a unit vector in a general direction.
    """
    u = origin()
    u[axis] = 1.0
    return u


def rotationMatrix(angle,axis=None):
    """Return a rotation matrix over angle, optionally around axis.

    The angle is specified in degrees.
    If axis==None (default), a 2x2 rotation matrix is returned.
    Else, axis should specifying the rotation axis in a 3D world. It is either
    one of 0,1,2, specifying a global axis, or a vector with 3 components
    specifying an axis through the origin.
    In either case a 3x3 rotation matrix is returned.
    Note that:
      rotationMatrix(angle,[1,0,0]) == rotationMatrix(angle,0) 
      rotationMatrix(angle,[0,1,0]) == rotationMatrix(angle,1) 
      rotationMatrix(angle,[0,0,1]) == rotationMatrix(angle,2)
    but the latter functions calls are more efficient.
    The result is returned as an array.
    """
    a = angle*rad
    c = cos(a)
    s = sin(a)
    if axis==None:
        f = [[c,s],[-s,c]]
    elif type(axis) == int:
        f = [[0.0 for i in range(3)] for j in range(3)]
        axes = range(3)
        i,j,k = axes[axis:]+axes[:axis]
        f[i][i] = 1.0
        f[j][j] = c
        f[j][k] = s
        f[k][j] = -s
        f[k][k] = c
    else:
        t = 1-c
        X,Y,Z = axis
        f = [ [ t*X*X + c  , t*X*Y + s*Z, t*X*Z - s*Y ],
              [ t*Y*X - s*Z, t*Y*Y + c  , t*Y*Z + s*X ],
              [ t*Z*X + s*Y, t*Z*Y - s*X, t*Z*Z + c   ] ]
        
    return array(f)


def rotMatrix(v,n=3):
    """Create a rotation matrix that rotates axis 0 to the given vector.

    Return either a 3x3(default) or 4x4(if n==4) rotation matrix.
    """
    if n != 4:
        n = 3
    #v = array(v,dtype=float64)
    vl = length(v)
    if vl == 0.0:
        return identity(n)
    v /= vl
    w = cross([0.,0.,1.],v)
    wl = length(w)
    if wl == 0.0:
        w = cross(v,[0.,1.,0.])
        wl = length(w)
    w /= wl
    x = cross(v,w)
    x /= length(x)
    m = row_stack([v,w,x])
    if n == 3:
        return m
    else:
        a = identity(4)
        a[0:3,0:3] = m
        return a


def growAxis(a,size,axis=-1,fill=0):
    """Grow a single array axis to the given size and fill with given value."""
    if axis >= len(a.shape):
        raise ValueError,"No such axis number!"
    if size <= a.shape[axis]:
        return a
    else:
        missing = list(a.shape)
        missing[axis] = size-missing[axis]
        return concatenate([a,fill * ones(missing,dtype=a.dtype)],axis=axis)


def reverseAxis(a,axis=-1):
    """Reverse the elements along axis."""
    a = asarray(a)
    try:
        n = a.shape[axis]
    except:
        raise ValueError,"Invalid axis %s for array shape %s" % (axis,a.shape)
    return a.take(arange(n-1,-1,-1),axis)


def checkArray(a,shape=None,kind=None,allow=None):
    """Check that an array a has the correct shape and type.

    The input a is anything that can e converted into a numpy array.
    Either shape and or kind can be specified.
    The dimensions where shape contains a -1 value are not checked. The
    number of dimensions should match, though.
    If kind does not match, but is included in allow, conversion to the
    requested type is attempted.
    Returns the array if valid.
    Else, an error is raised.
    """
    try:
        a = asarray(a)
        shape = asarray(shape)
        w = where(shape >= 0)[0]
        if (asarray(a.shape)[w] != shape[w]).any():
            raise
        if kind is not None:
            if allow is None and a.dtype.kind != kind:
                raise
            if kind == 'f':
                a = a.astype(Float)
        return a
    except:
        print "Expected shape %s, kind %s, got: %s" % (shape,kind,a)
    raise ValueError


def checkArray1D(a,size=None,kind=None,allow=None):
    """Check that an array a has the correct size and type.

    Either size and or kind can be specified.
    If kind does not match, but is included in allow, conversion to the
    requested type is attempted.
    Returns the array if valid.
    Else, an error is raised.
    """
    try:
        a = asarray(a).ravel()
        if (size is not None and a.size != size):
            raise
        if kind is not None:
            if allow is None and a.dtype.kind != kind:
                raise
            if kind == 'f':
                a = a.astype(Float)
        return a
    except:
        print "Expected size %s, kind %s, got: %s" % (size,kind,a)
    raise ValueError

   
def checkUniqueNumbers(nrs,nmin=0,nmax=None,error=None):
    """Check that an array contains a set of uniqe integers in range.

    nrs is an integer array with any shape.
    All integers should be unique and in the range(nmin,nmax).
    Beware: this means that    nmin <= i < nmax  !
    Default nmax is unlimited. Set nmin to None to
    error is the value to return if the tests are not passed.
    By default, a ValueError is raised.
    On success, None is returned
    """
    nrs = asarray(nrs)
    uniq = unique1d(nrs)
    if uniq.size != nrs.size or \
           (nmin is not None and uniq.min() < nmin) or \
           (nmax is not None and uniq.max() > nmax):
        if error is None:
            raise ValueError,"Values not unique or not in range"
        else:
            return error
    return uniq
    

# End
