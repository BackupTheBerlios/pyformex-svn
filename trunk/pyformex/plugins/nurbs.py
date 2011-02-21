#!/usr/bin/env python
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

"""Using NURBS in pyFormex.

The :mod:`nurbs` module defines functions and classes to manipulate
NURBS curves and surface in pyFormex.
"""
from coords import *
from lib import _nurbs_ as nu
from pyformex import options
from gui.actors import NurbsActor
import olist


###########################################################################
##
##   class Coords4
##
#########################
#
class Coords4(ndarray):
    """A collection of points represented by their homogeneous coordinates.
    
    While most of the pyFormex implementation is based on the 3D Cartesian
    coordinates class :class:`Coords`, some applications may benefit from using
    homogeneous coordinates. The class :class:`Coords4` provides some basic
    functions and conversion to and from cartesian coordinates.
    Through the conversion, all other pyFormex functions, such as
    transformations, are available.
    
    :class:`Coords4` is implemented as a float type :class:`numpy.ndarray`
    whose last axis has a length equal to 4.
    Each set of 4 values (x,y,z,w) along the last axis represents a
    single point in 3D space. The cartesian coordinates of the point
    are obtained by dividing the first three values by the fourth:
    (x/w, y/w, z/w). A zero w-value represents a point at infinity.
    Converting such points to :class:`Coords` will result in Inf or NaN
    values in the resulting object.
    
    The float datatype is only checked at creation time. It is the
    responsibility of the user to keep this consistent throughout the
    lifetime of the object.

    Just like :class:`Coords`, the class :class:`Coords4` is derived from
    :class:`numpy.ndarray`.

    Parameters
        
    data : array_like
        If specified, data should evaluate to an array of floats, with the
        length of its last axis not larger than 4. When equal to four, each
        tuple along the last axis represents a ingle point in homogeneous
        coordinates.
        If smaller than four, the last axis will be expanded to four by adding
        values zero in the second and third position and values 1 in the last
        position.
        If no data are given, a single point (0.,0.,0.) will be created.

    w : array_like
        If specified, the w values are used to denormalize the homogeneous
        data such that the last component becomes w.

    dtyp : data-type
        The datatype to be used. It not specified, the datatype of `data`
        is used, or the default :data:`Float` (which is equivalent to
        :data:`numpy.float32`).

    copy : boolean
        If ``True``, the data are copied. By default, the original data are
        used if possible, e.g. if a correctly shaped and typed
        :class:`numpy.ndarray` is specified.
    """
            
    def __new__(cls, data=None, w=None, dtyp=Float, copy=False):
        """Create a new instance of :class:`Coords4`."""
        if data is None:
            # create an empty array
            ar = ndarray((0,4),dtype=dtyp)
        else:
            # turn the data into an array, and copy if requested
            ar = array(data, dtype=dtyp, copy=copy)
            
        if ar.shape[-1] in [3,4]:
            pass
        elif ar.shape[-1] in [1,2]:
            # make last axis length 3, adding 0 values
            ar = growAxis(ar,3-ar.shape[-1],-1)
        elif ar.shape[-1] == 0:
            # allow empty coords objects 
            ar = ar.reshape(0,3)
        else:
            raise ValueError,"Expected a length 1,2,3 or 4 for last array axis"

        # Make sure dtype is a float type
        if ar.dtype.kind != 'f':
            ar = ar.astype(Float)

        # We should now have a float array with last axis 3 or 4
        if ar.shape[-1] == 3:
            # Expand last axis to length 4, adding values 1
            ar = growAxis(ar,1,-1,1.0)

        # Denormalize if w is specified
        if w is not None:
            self.deNormalize(w)
 
        # Transform 'subarr' from an ndarray to our new subclass.
        ar = ar.view(cls)

        return ar


    def normalize(self):
        """Normalize the homogeneous coordinates.

        Two sets of homogeneous coordinates that differ only by a
        multiplicative constant refer to the same points in cartesian space.
        Normalization of the coordinates is a way to make the representation
        of a single point unique. Normalization is done so that the last
        component (w) is equal to 1.

        The normalization of the coordinates is done in place.

        .. warning:: Normalizing points at infinity will result in Inf or
           NaN values.
        """
        self /= self[...,3:]


    def deNormalize(self,w):
        """Denormalizes the homogeneous coordinates.

        This multiplies the homogeneous coordinates with the values w.
        w normally is a constant or an array with shape self.shape[:-1].
        It then multiplies all 4 coordinates of a point with the same
        value, thus resulting in a denormalization while keeping the
        position of the point unchanged.

        The denormalization of the coordinates is done in place.
        If the Coords4 object was normalized, it will have precisely w as
        its 4-th coordinate value after the call.
        """
        self *= w


    def toCoords(self):
        """Convert homogeneous coordinates to cartesian coordinates.

        Returns a :class:`Coords` object with the cartesian coordinates
        of the points. Points at infinity (w=0) will result in
        Inf or NaN value. If there are no points at infinity, the
        resulting :class:`Coords` point set is equivalent to the
        :class:`Coords4` one.
        """
        return Coords(self[...,:3] / self[...,3:])


    def npoints(self):
        """Return the total number of points."""
        return asarray(self.shape[:-1]).prod()


    ncoords = npoints


    def x(self):
        """Return the x-plane"""
        return self[...,0]
    def y(self):
        """Return the y-plane"""
        return self[...,1]
    def z(self):
        """Return the z-plane"""
        return self[...,2]
    def w(self):
        """Return the w-plane"""
        return self[...,3]

    
    def bbox(self):
        """Return the bounding box of a set of points.

        Returns the bounding box of the cartesian coordinates of
        the object.
        """
        return self.toCoords().bbox()


    def actor(self,**kargs):
        """Graphical representation"""
        return self.toCoords().actor()


class NurbsCurve(object):

    """A NURBS curve

    The Nurbs curve is defined by nctrl control points, a degree (>= 1) and
    a knot vector with knots = nctrl+degree+1 parameter values, in ascending
    order.
    The knot values are only defined upon a multiplicative constant, equal to
    the largest value. Sensible default values are constructed automatically
    by a call to the knotVector() function.

    
    order (2,3,4,...) = degree+1 = min. number of control points
    ncontrol >= order
    nknots = order + ncontrol >= 2*order

    convenient solutions:
    OPEN:
      nparts = (ncontrol-1) / degree
      nintern = 
    """
    
    def __init__(self,control,degree=None,wts=None,knots=None,closed=False,blended=True):
        self.closed = closed
        nctrl = len(control)
        
        if degree is None:
            if knots is None:
                raise ValueError,'Either degree or knots has to be specified'
            else:
                degree = len(knots) - nctrl -1
                if degree <= 0:
                    raise ValueError,"Length of knot vector (%s) must be at least number of control points (%s) plus 2" % (len(knots),nctrl)

        order = degree+1
        control = Coords4(control)
        if wts is not None:
            control.deNormalize(wts)

        if closed:
            if knots is None:
                nextra = degree
            else:
                nextra = len(knots) - nctrl - order
            nextra1 = (nextra+1) // 2
            nextra2 = nextra-nextra1
            #print "extra %s = %s + %s" % (nextra,nextra1,nextra2)
            control = Coords4(concatenate([control[-nextra1:],control,control[:nextra2]],axis=0))

        nctrl = len(control)

        if nctrl < order:
            raise ValueError,"Number of control points (%s) must not be smaller than order (%s)" % (nctrl,order)

        if knots is None:
            knots = knotsVector(nctrl,degree,blended=blended,closed=closed)
            #print "KNOTS",knots

        nknots = len(knots)
        #print "Nurbs curve of degree %s with %s control points and %s knots" % (degree,nctrl,nknots)
        
        if nknots != nctrl+order:
            raise ValueError,"Length of knot vector (%s) must be equal to number of control points (%s) plus order (%s)" % (nknots,nctrl,order)

       
        self.control = control
        self.knots = asarray(knots)
        self.degree = degree
        self.closed = closed


    def order(self):
        return len(self.knots)-len(self.control)
        
    def bbox(self):
        return self.control.toCoords().bbox()


    def pointsAt(self,u=None,n=10):
        if u is None:
            umin = self.knots[0]
            umax = self.knots[-1]
            u = umin + arange(n+1) * (umax-umin) / n
        
        ctrl = self.control.astype(double)
        knots = self.knots.astype(double)
        u = asarray(u).astype(double)

        try:
            pts = nu.bspeval(self.order()-1,ctrl,knots,u)
            if isnan(pts).any():
                print "We got a NaN"
                raise RuntimeError
        except:
            raise RuntimeError,"Some error occurred during the evaluation of the Nurbs curve"

        if pts.shape[-1] == 4:
            pts = Coords4(pts).toCoords()
        else:
            pts = Coords(pts)
        return pts
        

    def actor(self,**kargs):
        """Graphical representation"""
        return NurbsActor(self,**kargs)
    

def unitRange(n):
    """Divide the range 0..1 in n equidistant points"""
    if n > 1:
        return (arange(n) * (1.0/(n-1))).tolist()
    elif n == 1:
        return [0.5]
    else:
        return []


def knotsVector(nctrl,degree,blended=True,closed=False):
    """Compute knots vector for a fully blended Nurbs curve.

    A Nurbs curve with nctrl points and of given degree needs a knots vector
    nknots = nctrl+degree+1 values.
    
    """
    nknots = nctrl+degree+1
    if closed:
        knots = unitRange(nknots)
    else:
        if blended:
            npts = nknots - 2*degree
            knots = [0.]*degree + unitRange(npts) + [1.]*degree
        else:
            nparts = (nctrl-1) / degree
            if nparts*degree+1 != nctrl:
                raise ValueError,"Discrete knot vectors can only be used if the number of control points is a multiple of the degree, plus one."
            knots = [0.] + [ [float(i)]*degree for i in range(nparts+1) ] + [float(nparts)]
            knots = olist.flatten(knots)
            
    return knots


def toCoords4(x):
    """Convert cartesian coordinates to homogeneous

    x: :class:Coords
       Array with cartesian coordinates.
       
    Returns a Coords4 object corresponding to the input cartesian coordinates.
    """
    return Coords4(x)

Coords.toCoords4 = toCoords4

### End
