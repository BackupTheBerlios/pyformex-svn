# A python class for 3D vector operations
#
# (c) 2004 Benedict Verhegghe
#
"""A python class for 3D vector operations"""

from math import *

def reverse (v):
    """Return the reverse vector [-x, -y, -z] of v[x,y,z]"""
    return [ -x for x in v ]

def scale (v,a):
    """Return the a * [x, y, z], where a is a scalar"""
    return [ a*x for x in v ]

def square (v):
    """Return the squared components [x^2, y^2, z^2] of v[x,y,z]"""
    return [ x*x for x in v ]

def norm (v):
    """Return the square length [x^2 + y^2 + z^2 of a vector v"""
    return sum(square(v))
 
def length (v):
    """Return the length of the vector v"""
    return sqrt(norm(v))

def unitvector (v):
    """Return the normalized (unit length) vector in direction v"""
    return scale(v, 1/length(v))

def add (v,w):
    """Return the sum of the vectors v and w"""
    return [ x+y for x,y in zip(v,w) ]

def diff (v,w):
    """Return the difference vector v-w"""
    return [ x-y for x,y in zip(v,w) ]

def pointOf (v,w,pos=0.5):
    """Return the point on the line v-w defined by the relative coordinate pos.

    v has pos 0, w has pos 1. For values 0..1 the point lies between v and w.
    """
    return add(v, scale(diff(w,v),pos))

def dotpr (v,w):
    """Return the dot product of vectors v and w"""
    return sum( [ x*y for x,y in zip(v,w) ] )

def cosangle (v,w):
    """Return the cosine of the angle between two vectors"""
    return dotpr(v,w)/length(v)/length(w)

def projection(v,w):
    """Return the length of the projection of vector v on vector w."""
    return dot(v,w)/length(w)

def parallel(v,w):
    """Returns the part of vector v that is parallel to vector w"""
    return projection(v,w)*unitvector(w)

def orthogonal(v,w):
    """Returns the part of vector v that is orthogonal to vector w"""
    return v-projection(v,w)*unitvector(w)

def cross (v,w):
    """Return the cross product between two vectors"""
    return [ v[1]*w[2]-v[2]*w[1],  v[2]*w[0]-v[0]*w[2], v[0]*w[1]-v[1]*w[0] ]

def cartesianToSpherical (v) :
    """Convert cartesian coordinates [x,y,z] to spherical [long,lat,dist]
    
    Angles are given in degrees: lat: -90..90, long:0..360
    """
    distance = length(v)
    longitude = degrees( atan2(v[0],v[2]) )
    latitude = degrees( asin(v[1]/distance) )
    return [ longitude, latitude, distance]

def sphericalToCartesian (v) :
    """Convert spherical coordinates [lat,long,dist] to cartesian [x,y,z]"""
    long = radians(v[0])
    lat = radians(v[1])
    return scale ([ cos(lat)*sin(long), sin(lat), cos(lat)*cos(long) ], v[2])

