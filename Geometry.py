from numarray import *

# These functions return a scalar:

def length(a):
    """Return the length of a coordinate vector.

    The vector can be specified as a list or as an array.
    """
    return sqrt(dot(a,a))
    
def distance(a,b):
    """Calculate the distance between two points.

    Apoint is a list of three coordinates.
    """
    return length(array(b) - array(a))

def projection(a,b):
    """Return the length of the projection of vector a on vector b."""
    return dot(a,b)/length(b)

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
