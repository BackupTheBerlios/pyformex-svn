"""Operations on 3-D vectors.

An input vector can be specified as a list or as a numarray.
"""

from numarray import *

# These functions return a scalar:

def length(a):
    """Return the length of a coordinate vector.

    The vector can be specified as a list or as an array.
    """
    return sqrt(dot(a,a))
    
def diff(a,b):
    """Return the difference between two vectors.

    The vector can be specified as a list or as an array.
    """
    return array(b) - array(a)
    
def distance(a,b):
    """Return the distance between two points."""
    return length(array(b) - array(a))

def projection(a,b):
    """Return the length of the projection of vector a on vector b."""
    return dot(a,b)/length(b)

def fromSpherical(a):
    """Transforms spherical coordinates to cartesian.

    Input vector a = [ distance, azimuth, elevation ], where
    azimuth = angle in degrees around y-axis, starting from z-axis (90 is x)
    elevation = angle in degrees around the x-axis (+90 is the -y direction)
    """
    az = math.radians(a[1])
    el = math.radians(a[2])
    c = a[0]*math.cos(el)
    s = a[0]*math.sin(el)
    return [ c*math.sin(az), -s, c*math.cos(az) ]


# The following functions return a vector (as a numarray)
def unitvector(a):
    """Return a unit vector in the direction of a"""
    return array(a)/length(a)

def parallel(a,b):
    """Returns the part of vector a that is parallel to vector b"""
    return projection(a,b)*unitvector(b)

def orthogonal(a,b):
    """Returns the part of vector a that is orthogonal to vector b"""
    return a-projection(a,b)*unitvector(b)
