# $Id$
##
##  This file is part of pyFormex 0.8.2 Release Sat Jun  5 10:49:53 2010
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

"""Definition of curves in pyFormex.

This module defines classes and functions specialized for handling
one-dimensional geometry in pyFormex. These may be straight lines, polylines,
higher order curves and collections thereof. In general, the curves are 3D,
but special cases may be created for handling plane curves.
"""

# I wrote this software in my free time, for my joy, not as a commissioned task.
# Any copyright claims made by my employer should therefore be considered void.
# Acknowledgements: Gianluca De Santis

#from pyformex import debug
from numpy import *
from formex import *
from plugins.geomtools import triangleCircumCircle
from plugins.mesh import Mesh


##############################################################################
# THIS IS A PROPOSAL !
#
# Common interface for curves:
# attributes:
#    coords: coordinates of points defining the curve
#    parts:  number of parts (e.g. straight segments of a polyline)
#    closed: is the curve closed or not
#    range: [min,max] : range of the parameter: default 0..1
# methods:
#    subPoints(t,j): returns points with parameter values t of part j
#    points(ndiv,extend=[0.,0.]): returns points obtained by dividing each
#           part in ndiv sections at equal parameter distance.
#    pointsOn(): the defining points situated on the curve
#    pointsOff(): the defining points situated off the curve (control points)

from geometry import Geometry

class Curve(Geometry):
    """Base class for curve type classes.

    This is a virtual class intended to be subclassed.
    It defines the common definitions for all curve types.
    The subclasses should at least define the following::
    
      sub_points(t,j)
    """

    N_approx = 10

    def pointsOn(self):
        return self.coords

    def pointsOff(self):
        return Coords()

    def ncoords(self):
        return self.coords.shape[0]

    def npoints(self):
        return self.pointsOn().shape[0]
    
    def sub_points(self,t,j):
        """Return the points at values t in part j

        t can be an array of parameter values, j is a single segment number.
        """
        raise NotImplementedError

    def sub_points_2(self,t,j):
        """Return the points at values,parts given by zip(t,j)

        t and j can both be arrays, but should have the same length.
        """
        raise NotImplementedError

    def lengths(self):
        raise NotImplementedError


    def pointsAt(self,t):
        """Returns the points at parameter values t.

        Parameter values are floating point values. Their integer part
        is interpreted as the curve segment number, and the decimal part
        goes from 0 to 1 over the segment.
        """
        t = asarray(t).ravel()
        ti = floor(t).clip(min=0,max=self.nparts-1)
        t -= ti
        i = ti.astype(Int)
        try:
            allX = self.sub_points_2(t,i)
        except:
            allX = concatenate([ self.sub_points(tj,ij) for tj,ij in zip(t,i)])
        return Coords(allX)
        
    
    def subPoints(self,div=10,extend=[0., 0.]):
        """Return a series of points on the PolyLine.

        The parameter space of each segment is divided into ndiv parts.
        The coordinates of the points at these parameter values are returned
        as a Coords object.
        The extend parameter allows to extend the curve beyond the endpoints.
        The normal parameter space of each part is [0.0 .. 1.0]. The extend
        parameter will add a curve with parameter space [-extend[0] .. 0.0]
        for the first part, and a curve with parameter space
        [1.0 .. 1 + extend[0]] for the last part.
        The parameter step in the extensions will be adjusted slightly so
        that the specified extension is a multiple of the step size.
        If the curve is closed, the extend parameter is disregarded. 
        """
        # Subspline parts (without end point)
        if type(div) == int:
            u = arange(div) / float(div)

        else:
            u = array(div).ravel()
            div = len(u)
        parts = [ self.sub_points(u,j) for j in range(self.nparts) ]

        if not self.closed:
            nstart,nend = round_(asarray(extend)*div,0).astype(Int)

            # Extend at start
            if nstart > 0:
                u = arange(-nstart, 0) * extend[0] / nstart
                parts.insert(0,self.sub_points(u,0))

            # Extend at end
            if nend > 0:
                u = 1. + arange(0, nend+1) * extend[1] / nend
            else:
                # Always extend at end to include last point
                u = array([1.])
            parts.append(self.sub_points(u,self.nparts-1))

        X = concatenate(parts,axis=0)
        return Coords(X) 


    def length(self):
        """Return the total length of the curve.

        This is only available for curves that implement the 'lengths'
        method.
        """
        return self.lengths().sum()


    def approx(self,ndiv=None,ntot=None):
        """Return a PolyLine approximation of the curve

        If no `ntot` is given, the curve is approximated by `ndiv`
        straight segments over each part of the curve.
        If `ntot` is given, the curve is approximated by `ntot`
        straight segments over the total curve. This is based on a
        first approximation with ndiv segments over each part.
        """
        if ndiv is None:
            ndiv = self.N_approx
        PL = PolyLine(self.subPoints(ndiv),closed=self.closed)
        if ntot is not None:
            at = PL.atLength(ntot)
            X = PL.pointsAt(at)
            PL = PolyLine(X,closed=PL.closed)
        return PL


    def toFormex(self,*args,**kargs):
        """Convert a curve to a Formex.

        This creates a polyline approximation as a plex-2 Formex.
        This is mainly used for drawing curves that do not implement
        their own drawing routines.

        The method can be passed the same arguments as the `approx` method.
        """
        return self.approx(*args,**kargs).toFormex()
  

##############################################################################
#
#  Curves that can be transformed by Coords Transforms
#
##############################################################################
#
class PolyLine(Curve):
    """A class representing a series of straight line segments."""

    def __init__(self,coords=[],closed=False):
        """Initialize a PolyLine from a coordinate array.

        coords is a (npts,3) shaped array of coordinates of the subsequent
        vertices of the polyline (or a compatible data object).
        If closed == True, the polyline is closed by connecting the last
        point to the first. This does not change the vertex data.
        """
        if isinstance(coords,Formex):
            if coords.nplex() == 1:
                coords = coords.coords
            elif coords.nplex() == 2:
                coords = Coords.concatenate([coords.coords[:,0,:],coords.coords[-1,1,:]])
            else:
                raise ValueError,"Only Formices with plexitude 1 or 2 can be converted to PolyLine"

        else:
            coords = Coords(coords)
            
        if coords.ndim != 2 or coords.shape[1] != 3:
            raise ValueError,"Expected an (npoints,3) coordinate array"
        self.coords = coords
        self.nparts = self.coords.shape[0]
        if not closed:
            self.nparts -= 1
        self.closed = closed


    def nelems(self):
        return self.nparts
    

    def toFormex(self):
        """Return the polyline as a Formex."""
        x = self.coords
        F = connect([x,x],bias=[0,1],loop=self.closed)
        return F

    
    def toMesh(self):
        """Convert the polyLine to a plex-2 Mesh.

        This returned mesh is equivalent with the PolyLine, but does
        not guarantee the sequential order.
        """
        e1 = arange(self.ncoords())
        elems = column_stack([e1,roll(e1,-1)])
        if not self.closed:
            elems = elems[:-1]
        return Mesh(self.coords,elems,eltype='line2')


    def sub_points(self,t,j):
        """Return the points at values t in part j"""
        j = int(j)
        t = asarray(t).reshape(-1,1)
        n = self.coords.shape[0]
        X0 = self.coords[j % n]
        X1 = self.coords[(j+1) % n]
        X = (1.-t) * X0 + t * X1
        return X


    def sub_points2(self,t,j):
        """Return the points at value,part pairs (t,j)"""
        j = int(j)
        t = asarray(t).reshape(-1,1)
        n = self.coords.shape[0]
        X0 = self.coords[j % n]
        X1 = self.coords[(j+1) % n]
        X = (1.-t) * X0 + t * X1
        return X


    def vectors(self):
        """Return the vectors of each point to the next one.

        The vectors are returned as a Coords object.
        If the curve is not closed, the number of vectors returned is
        one less than the number of points.
        """
        x = self.coords
        if self.closed:
            x1 = x
            x2 = roll(x,-1,axis=0) # NEXT POINT
        else:
            x1 = x[:-1]
            x2 = x[1:]
        return x2-x1
        

    def directions(self,return_doubles=False):
        """Returns unit vectors in the direction of the next point.

        This directions are returned as a Coords object with the same
        number of elements as the point set.
        
        If two subsequent points are identical, the first one gets
        the direction of the previous segment. If more than two subsequent
        points are equal, an invalid direction (NaN) will result.

        If the curve is not closed, the last direction is set equal to the
        penultimate.

        If return_doubles is True, the return value is a tuple of the direction
        and an index of the points that are identical with their follower.
        """
        import warnings
        warnings.warn('PolyLine.directions() now always returns the same number of directions as there are points. The last direction of an open PolyLine appears twice.')
        d = normalize(self.vectors())
        w = where(isnan(d).any(axis=-1))[0]
        #print "DOUBLES:%s" % w
        d[w] = d[w-1]  
        if not self.closed:
            d = concatenate([d,d[-1:]],axis=0)
        #print "Directions",d
        if return_doubles:
            return d,w
        else:
            return d
    

    def avgDirections(self,return_doubles=False):
        """Returns the average directions at points.

        For each point the returned direction is the average of the direction
        from the preceding point to the current, and the direction from the
        current to the next point.
        
        If the curve is open, the first and last direction are equal to the
        direction of the first, resp. last segment.

        Where two subsequent points are identical, the average directions
        are set equal to those of the segment ending in the first and the
        segment starting from the last.
        """
        import warnings
        warnings.warn('PolyLine.avgDirections() now always returns the same number of directions as there are points. The first and last direction are those of the end segment.')
        d,w = self.directions(True)
        #if self.closed:
        d1 = d
        d2 = roll(d,1,axis=0) # PREVIOUS DIRECTION
        #else:
        #    d1 = d[:-1]
        #    d2 = d[1:]
        ## if not self.closed:
        ##     d = concatenate([d[:1],d],axis=0)
        #print "expanded",d
        w = concatenate([w,w+1])
        if not self.closed:
            w = concatenate([[0,self.npoints()-1],w])
        #print "Not averaging at %s" % w
        w = setdiff1d(arange(self.npoints()),w)
        #d[w] = dd[w]
        #print "Averaging at %s" % w
        d[w] = 0.5 * (d1[w]+d2[w])
        #print "AVG Directions",d
        if return_doubles:
            return d,w
        else:
            return d
    

    def lengths(self):
        """Return the length of the parts of the curve."""
        return length(self.vectors())


    def atLength(self, div):
        """Returns the parameter values for relative curve lengths div.
        
        ``div`` is a list of relative curve lengths (from 0.0 to 1.0).
        As a convenience, a single integer value may be specified,
        in which case the relative curve lengths are found by dividing
        the interval [0.0,1.0] in the specified number of subintervals.

        The function returns a list with the parameter values for the points
        at the specified relative lengths.
        """
        lens = self.lengths().cumsum()
        rlen = concatenate([[0.], lens/lens[-1]]) # relative length
        if type(div) == int:
            div = arange(div+1) / float(div)
        z = rlen.searchsorted(div)
        # we need interpolation
        wi = where(z>0)[0]
        zw = z[wi]
        L0 = rlen[zw-1]
        L1 = rlen[zw]
        ai = zw + (div[wi] - L1) / (L1-L0)
        at = zeros(len(div))
        at[wi] = ai
        return at


    def reverse(self):
        return PolyLine(reverseAxis(self.coords,axis=0),closed=self.closed)


    def split(self,i):
        """Split the curve at point i.

        Returns a list of open PolyLines: one, if the PolyLine is closed or
        i is one of the endpoints of an open PolyLine, two in other cases.
        """
        res = []
        if self.closed:
            res.append(PolyLine(roll(self.coords,-i,axis=0)))
        else:
            if i > 0:
                res.append(PolyLine(self.coords[:i+1]))
            if i < len(self.coords):
                res.append(PolyLine(self.coords[i:]))
        return res


    def cutWithPlane(self,p,n,side=''):
        """Return the parts of the polyline at one or both sides of a plane.

        If side is '+' or '-', return a list of PolyLines with the parts at
        the positive or negative side of the plane.

        For any other value, returns a tuple of two lists of PolyLines,
        the first one being the parts at the positive side.

        p is a point specified by 3 coordinates.
        n is the normal vector to a plane, specified by 3 components.
        """
        n = asarray(n)
        p = asarray(p)

        d = self.coords.distanceFromPlane(p,n)
        t = d > 0.0
        cut = t != roll(t,-1)
        if not self.closed:
            cut = cut[:-1]
        w = where(cut)[0]

        res = [[],[]]
        i = 0
        if t[0]:
            sid = 0
        else:
            sid = 1
        Q = Coords()

        for j in w:
            #print "%s -- %s" % (i,j)
            P = Formex([self.coords[j:j+2]]).intersectionPointsWithPlane(p,n)
            P = P.coords.reshape(1,3)
            #print "%s -- %s cuts at %s" % (j,j+1,P)
            x = Coords.concatenate([Q,self.coords[i:j+1],P])
            #print "%s + %s + %s = %s" % (Q.shape[0],j-i,P.shape[0],x.shape[0])
            res[sid].append(PolyLine(x))
            sid = 1-sid
            i = j+1
            Q = P

        x = Coords.concatenate([Q,self.coords[i:]])
        #print "%s + %s = %s" % (Q.shape[0],j-i,x.shape[0])
        res[sid].append(PolyLine(x))
        if self.closed:
            if len(res[sid]) > 1:
                x = Coords.concatenate([res[sid][-1].coords,res[sid][0].coords])
                res[sid] = res[sid][1:-1]
                res[sid].append(PolyLine(x))
            #print [len(r) for r in res]
            if len(res[sid]) == 1 and len(res[1-sid]) == 0:
                res[sid][0].closed = True

        # DO not use side in '+-', because '' in '+-' returns True
        if side in ['+','-']:
            return res['+-'.index(side)]
        else:
            return res


##############################################################################
#
class Polygon(PolyLine):
    """A Polygon is a closed PolyLine."""

    def __init__(self,coords=[]):
        PolyLine.__init__(self,coords,closed=True)
        

##############################################################################
#
class BezierSpline(Curve):
    """A class representing a cubic Bezier spline curve."""
    coeffs = matrix([[-1.,  3., -3., 1.],
                     [ 3., -6.,  3., 0.],
                     [-3.,  3.,  0., 0.],
                     [ 1.,  0.,  0., 0.]]
                    )

    def __init__(self,coords,deriv=None,curl=0.5,control=None,closed=False):
        """Create a cubic spline curve through the given points.

        - coords: an (npoints,3) array with ordered points on the curve
        - deriv: an (npoints,3) or (2,3) array with the directions at all
          the points or at the two endpoints only.
          For points where the direction is left unspecified or where the
          specified direction contains a `NaN` value, the direction
          is calculated as the average direction of the two
          line segments ending in the point. This will also be used
          for points where the specified direction contains a value `NaN`.
          In the two endpoints of an open curve however, this average
          direction can not be calculated: the two control points in these
          parts are set coincident.
          
          The curl parameter can be set to influence the curliness of the curve
          in between two subsequent points. A value curl=0.0 results in
          straight segments.
        
        - control: an (nparts,2,3) array of control points, two for each
          curve segemetn between two consecutive points. For a closed curve,
          nparts = npoints, while for an open curve nparts = npoints-1.
          If the control points are specified directly, they override
          the deriv and curl parameters.
        - closed: if True, the curve will be continued from the last point
          to the first to create a closed curve.
        """
        coords = Coords(coords)
        ncoords = nparts = coords.shape[0]
        if not closed:
            nparts -= 1

        if control is None:
            P = PolyLine(coords,closed=closed)
            ampl = P.lengths().reshape(-1,1)
            if deriv is None:
                deriv = array([[nan,nan,nan]]*ncoords)
            else:
                deriv = Coords(deriv)
                nderiv = deriv.shape[0]
                if nderiv < ncoords:
                    if nderiv != 2:
                        raise ValueError,"Either all or 2 directions expected (got %s)" % nderiv
                    deriv = concatenate([
                        deriv[:1],
                        [[nan,nan,nan]]*(ncoords-2),
                        deriv[-1:]])

            undefined = isnan(deriv).any(axis=-1)
            if undefined.any():
                deriv[undefined] = P.avgDirections()[undefined]
                
            if closed:
                p1 = coords + deriv*curl*ampl
                p2 = coords - deriv*curl*roll(ampl,1,axis=0)
                p2 = roll(p2,-1,axis=0)
            else:
                p1 = coords[:-1] + deriv[:-1]*curl*ampl
                p2 = coords[1:] - deriv[1:]*curl*ampl
                if isnan(p1[0]).any():
                    p1[0] = p2[0]
                if isnan(p2[-1]).any():
                    p2[-1] = p1[-1]
            control = concatenate([p1,p2],axis=1)
                
        control = asarray(control).reshape(-1,2,3)
        control = Coords(control)
        if control.shape != (nparts,2,3):
            print("coords array has shape %s" % str(coords.shape))
            print("control array has shape %s" % str(control.shape))
            raise ValueError,"Invalid control points for BezierSpline"

        # To enable easy transforms, we join the coords and controls
        # in a single array
        if not closed:
            dummy = Coords([[[0.,0.,0.],[0.,0.,0.]]])
            control = Coords.concatenate([control,dummy],axis=0)
        coords = coords[:,newaxis,:]
        self.coords = Coords.concatenate([coords,control],axis=1)
        self.nparts = nparts
        self.closed = closed


    def pointsOn(self):
        """Return the points on the curve""" 
        return self.coords[:,0,:]


    def pointsOff(self):
        """Return the points off the curve (the control points)""" 
        return self.coords[:self.nparts,1:,:]


    def sub_points(self,t,j):
        j1 = (j+1) % self.coords.shape[0]
        P = self.pointsOn()[[j,j1]]
        D = self.pointsOff()[j]
        P = concatenate([ P[0],D[0],D[1],P[1] ],axis=0).reshape(-1,3)
        C = self.coeffs * P
        U = column_stack([t**3., t**2., t, ones_like(t)])
        X = dot(U,C)
        return X

##############################################################################
#
class QuadBezierSpline(Curve):
    """A class representing a Quadratic Bezier spline curve."""
    coeffs = matrix([[ 1., -2.,  1.],
                     [-2.,  2.,  0.],
                     [ 1.,  0.,  0.]]
                    )

    def __init__(self,coords,control=None,closed=False):
        """Create a quadratic spline curve through the given points.

        """
        coords = Coords(coords)
        nparts = coords.shape[0]
        if not closed:
            nparts -= 1
            
        if control is None:
            if nparts < 2:
                control = 0.5*(coords[:-1] + coords[1:])
            else:
                if closed:
                    P0 = 0.5 * (roll(coords,1,axis=0) + roll(coords,-1,axis=0))
                    P1 = 2*coords - P0
                    Q0 = 0.5*(roll(coords,1,axis=0) + P1)
                    Q1 = 0.5*(roll(coords,-1,axis=0) + P1)
                    Q = 0.5*(roll(Q0,-1,axis=0)+Q1)
                    control = Q
                else:
                    P0 = 0.5 * (coords[:-2] + coords[2:])
                    P1 = 2*coords[1:-1] - P0
                    Q0 = 0.5*(coords[:-2] + P1)
                    Q1 = 0.5*(coords[2:] + P1)
                    Q = 0.5*(Q0[1:]+Q1[:-1])
                    control = Coords.concatenate([Q0[:1],Q,Q1[-1:]],axis=0)

        control = asarray(control).reshape(-1,3)
        control = Coords(control)
        if control.shape != (nparts,3):
            print("coords array has shape %s" % str(coords.shape))
            print("control array has shape %s" % str(control.shape))
            raise ValueError,"Invalid control points for QuadBezierSpline"

        # To enable easy transforms, we join the coords and controls
        # in a single array
        if not closed:
            dummy = Coords([[0.,0.,0.]])
            control = Coords.concatenate([control,dummy],axis=0)
        coords = coords[:,newaxis,:]
        control = control[:,newaxis,:]
        self.coords = Coords.concatenate([coords,control],axis=1)
        self.nparts = nparts
        self.closed = closed


    def pointsOn(self):
        """Return the points on the curve""" 
        return self.coords[:,0,:]


    def pointsOff(self):
        """Return the points off the curve (the control points)""" 
        return self.coords[:self.nparts,1,:]


    def sub_points(self,t,j):
        j1 = (j+1) % self.coords.shape[0]
        P = self.pointsOn()[[j,j1]]
        D = self.pointsOff()[j]
        P = concatenate([ P[0],D,P[1] ],axis=0).reshape(-1,3)
        C = self.coeffs * P
        U = column_stack([t**2., t, ones_like(t)])
        X = dot(U,C)
        return X


##############################################################################
#
class CardinalSpline(BezierSpline):
    """A class representing a cardinal spline.

    Create a natural spline through the given points.

    The Cardinal Spline with given tension is a Bezier Spline with curl
    :math: `curl = ( 1 - tension) / 3`
    The separate class name is retained for compatibility and convenience. 
    See CardinalSpline2 for a direct implementation (it misses the end
    intervals of the point set).
    """

    def __init__(self,coords,tension=0.0,closed=False):
        """Create a natural spline through the given points."""
        BezierSpline.__init__(self,coords,curl=(1.-tension)/3.,closed=closed)



##############################################################################
#
#  Curves that can NOT be transformed by Coords Transforms
#
##############################################################################

class CardinalSpline2(Curve):
    """A class representing a cardinal spline."""

    def __init__(self,coords,tension=0.0,closed=False):
        """Create a natural spline through the given points.

        This is a direct implementation of the Cardinal Spline.
        For open curves, it misses the interpolation in the two end
        intervals of the point set.
        """
        coords = Coords(coords)
        self.coords = coords
        self.nparts = self.coords.shape[0]
        if not closed:
            self.nparts -= 3
        self.closed = closed
        self.tension = float(tension)
        self.compute_coefficients()


    def compute_coefficients(self):
        s = (1.-self.tension)/2.
        M = matrix([[-s, 2-s, s-2., s], [2*s, s-3., 3.-2*s, -s], [-s, 0., s, 0.], [0., 1., 0., 0.]])#pag.429 of open GL
        self.coeffs = M


    def sub_points(self,t,j):
        n = self.coords.shape[0]
        i = (j + arange(4)) % n
        P = self.coords[i]
        C = self.coeffs * P
        U = column_stack([t**3., t**2., t, ones_like(t)])
        X = dot(U,C)
        return X  


##############################################################################

class NaturalSpline(Curve):
    """A class representing a natural spline."""

    def __init__(self,coords,endcond=['notaknot','notaknot'],closed=False):
        """Create a natural spline through the given points.

        coords specifies the coordinates of a set of points. A natural spline
        is constructed through this points.
        endcond specifies the end conditions in the first, resp. last point.
        It can be 'notaknot' or 'secder'.
        With 'notaknot', maximal continuity (up to the third derivative)
        is obtained between the first two splines.
        With 'secder', the spline ends with a zero second derivative.
        If closed is True, the spline is closed, and endcond is ignored.
        """
        coords = Coords(coords)
        if closed:
            coords = Coords.concatenate([coords,coords[:1]])
        self.coords = coords
        self.nparts = self.coords.shape[0] - 1
        self.closed = closed
        self.endcond = endcond
        self.compute_coefficients()


    def compute_coefficients(self):
        x, y, z = self.coords.x(),self.coords.y(),self.coords.z()
        n = self.nparts
        M = zeros([4*n, 4*n])
        B = zeros([4*n, 3])
        
        # constant submatrix
        m = array([[0., 0., 0., 1., 0., 0., 0., 0.],
                   [1., 1., 1., 1., 0., 0., 0., 0.],
                   [3., 2., 1., 0., 0., 0.,-1., 0.],
                   [6., 2., 0., 0., 0.,-2., 0., 0.]])

        for i in range(n-1):
            f = 4*i
            M[f:f+4,f:f+8] = m
            B[f:f+2] = self.coords[i:i+2]

        # the last spline passes through the last 2 points
        f = 4*(n-1)
        M[f:f+2, f:f+4] = m[:2,:4]
        B[f:f+2] = self.coords[-2:]

        #add the appropriate end constrains
        if self.closed:
            # first and second derivatives at starting and last point
            # (that are actually the same point) are the same
            M[f+2, f:f+4] = m[2, :4]
            M[f+2, 0:4] = m[2, 4:]
            M[f+3, f:f+4] = m[3, :4]
            M[f+3, 0:4] = m[3, 4:]

        else:
            if self.endcond[0] =='notaknot':
                # third derivative is the same between the first 2 splines
                M[f+2,  [0, 4]] = array([6.,-6.])
            else:
                # second derivatives at start is zero
                M[f+2, 0:4] = m[3, 4:]

            if self.endcond[1] =='notaknot':
                # third derivative is the same between the last 2 splines
                M[f+3, [f-4, f]] = array([6.,-6.])
            else:
                # second derivatives at end is zero
                M[f+3, f:f+4] = m[3, :4]

        #calculate the coefficients
        C = linalg.solve(M,B)
        self.coeffs = array(C).reshape(-1,4,3)


    def sub_points(self,t,j):
        C = self.coeffs[j]
        U = column_stack([t**3., t**2., t, ones_like(t)])
        X = dot(U,C)
        return X

##############################################################################

def vectorPairAngle(v1,v2):
    """Return the angle between the vectors v1 and v2."""
    v1 = asarray(v1)
    v2 = asarray(v2)
    cosangle = dotpr(v1,v2) / sqrt(dotpr(v1,v1)*dotpr(v2,v2))
    return arccos(cosangle)


class Arc3(Curve):
    """A class representing a circular arc."""

    def __init__(self,coords):
        """Create a circular arc.

        The arc is specified by 3 non-colinear points.
        """
        self.coords = Coords(coords)
        self.nparts = 1
        self.closed = False
        if self.coords.shape != (3,3):
            raise ValueError,"Expected 3 points"
        
        r,C,n = triangleCircumCircle(self.coords.reshape(-1,3,3))
        self.radius,self.center,self.normal = r[0],C[0],n[0]
        self.angles = vectorPairAngle(Coords([1.,0.,0.]),self.coords-self.center)
        print("Radius %s, Center %s, Normal %s" % (self.radius,self.center,self.normal))
        print("ANGLES=%s" % (self.angles))

    def sub_points(self,t,j):
        a = t*(self.angles[-1]-self.angles[0])
        X = Coords(column_stack([cos(a),sin(a),zeros_like(a)]))
        X = X.scale(self.radius).rotate(self.angles[0]/Deg).translate(self.center)
        return X


class Arc(Curve):
    """A class representing a circular arc."""

    def __init__(self,coords):
        """Create a circular arc.

        The arc is specified by the center and begin and end-point.
        """
        self.coords = Coords(coords)
        self.nparts = 1
        self.closed = False
        if self.coords.shape != (3,3):
            raise ValueError,"Expected 3 points"

        self.center = self.coords[1]
        v = self.coords-self.center
        self.radius = length(v[0])
        self.normal = unitVector(cross(v[0],v[2]))
        self.angles = [ vectorPairAngle(Coords([1.,0.,0.]),x-self.center) for x in self.coords[[0,-1]] ]
        print(self.coords)
        print("Radius %s, Center %s, Normal %s" % (self.radius,self.center,self.normal))
        print("ANGLES=%s" % (self.angles))

    def sub_points(self,t,j):
        a = t*(self.angles[-1]-self.angles[0])
        X = Coords(column_stack([cos(a),sin(a),zeros_like(a)]))
        X = X.scale(self.radius).rotate(self.angles[0]/Deg).translate(self.center)
        return X



class Spiral(Curve):
    """A class representing a spiral curve."""

    def __init__(self,turns=2.0,nparts=100,rfunc=None):
        if rfunc == None:
            rfunc = lambda x:x
        self.coords = Coords([0.,0.,0.]).replic(npoints+1).hypercylindrical()
        self.nparts = nparts
        self.closed = False


##############################################################################
# Other functions

def convertFormexToCurve(self,closed=False):
    """Convert a Formex to a Curve.

    The following Formices can be converted to a Curve:
    - plex 2 : to PolyLine
    - plex 3 : to QuadBezierSpline
    - plex 4 : to BezierSpline
    """
    points = Coords.concatenate([self.coords[:,0,:],self.coords[-1:,-1,:]],axis=0)
    if self.nplex() == 2:
        curve = PolyLine(points,closed=closed)
    elif self.nplex() == 3:
        control = self.coords[:,1,:]
        curve = QuadBezierSpline(points,control=control,closed=closed)
    elif self.nplex() == 4:
        control = self.coords[:,1:3,:]
        curve = BezierSpline(points,control=control,closed=closed)
    return curve

Formex.toCurve = convertFormexToCurve

# End
