#!/usr/bin/env python
# $Id$
##
##  This file is part of pyFormex 0.7.3 Release Tue Dec 30 20:45:35 2008
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
"""Predefined Formex samples with simple geometric shapes."""

from formex import *

# A collection of simple line element shapes, to be constructed by passing
# the string to the formex.pattern() function.
# The shape() function below returns the corresponding Formex.
Pattern = {
    'line'   : '1',
    'angle'  : '102',
    'square' : '1234',
    'plus'   : '1020304',
    'cross'  : '5060708',
    'diamond' : '/45678',
    'rtriangle' : '164',
    'cube'   : '1234I/aI/bI/cI/41234',
    'star'   : '102030405060708',
    'star3d' : '1/02/03/04/05/06/07/08/0A/0B/0C/0D/0E/0F/0G/0H/0a/0b/0c/0d/0e/0f/0g/0h'
    }

    
def regularGrid(x0,x1,nx):
    """Create a regular grid between points x0 and x1.

    x0 and x1 are n-dimensional points (usually 1D, 2D or 3D).
    The space between x0 and x1 is divided in nx equal parts. nx should have
    the same dimension as x0 and x1.
    The result is a rectangular grid of coordinates in an array with
    shape ( nx[0]+1, nx[1]+1, ..., n ).
    """
    x0 = asarray(x0).ravel()
    x1 = asarray(x1).ravel()
    nx = asarray(nx).ravel()
    if x0.size != x1.size or nx.size != x0.size:
        raise ValueError,"Expected equally sized 1D arrays x0,x1,nx"
    if any(nx < 0):
        raise ValueError,"nx values should be >= 0"
    n = x0.size
    ind = indices(nx+1).reshape((n,-1))
    shape = append(tuple(nx+1),n)
    nx[nx==0] = 1
    jnd = nx.reshape((n,-1)) - ind
    ind = ind.transpose()
    jnd = jnd.transpose()
    return ( (x0*jnd + x1*ind) / nx ).reshape(shape)


def shape(name):
    """Return a Formex with one of the predefined named shapes.

    This is a convenience function returning a plex-2 Formex constructed
    from one of the patterns defined in the simple.Pattern dictionary.
    """
    return Formex(pattern(Pattern[name]))


def point(x=0.,y=0.,z=0.):
    """Return a Formex which is a point, by default at the origin.
    
    Each of the coordinates can be specified and is zero by default.
    """
    return Formex([[[x,y,z]]])
 

def line(p1=[0.,0.,0.],p2=[1.,0.,0.],n=1):
    """Return a Formex which is a line between two specified points.
    
    p1: first point, p2: second point
    The line is split up in n segments.
    """
    return Formex([[p1,p2]]).divide(n)


def rectangle(nx,ny,b=None,h=None,bias=0.,diag=None):
    """Return a Formex representing a rectangle of size(b,h) with (nx,ny) cells.

    This is a convenience function to create a rectangle with given size.
    The default b/h values are equal to nx/ny, resulting in a modular grid.
    The rectangle lies in the (x,y) plane, with one corner at [0,0,0].
    By default, the elements are quads. By setting diag='u','d' of 'x',
    diagonals are added in /, resp. \ and both directions, to form triangles.
    """
    if diag == 'x':
        base = Formex([[[0.0,0.0,0.0],[1.0,-1.0,0.0],[1.0,1.0,0.0]]]).rosette(4,90.).translate([-1.0,-1.0,0.0]).scale(0.5)
    else:
        pat = { 'u': '12-34', 'd': '16-82' }.get(diag,'123')
        base = Formex(mpattern(pat))
    if b is None:
        sx = 1.
    else:
        sx = float(b)/nx
    if h is None:
        sy = 1.
    else:
        sy = float(h)/ny
    return base.replic2(nx,ny,bias=bias).scale([sx,sy,0.])
   

def circle(a1=2.,a2=0.,a3=360.):
    """Return a Formex which is a unit circle at the origin in the x-y-plane.

    a1: dash angle in degrees, a2: modular angle in degrees, a3: total angle.
    a1 == a2 gives a full circle, a1 < a2 gives a dashed circle.
    If a3 < 360, the result is an arc.

    If a2 == 0, a2 is taken equal to a1.
    The default values give a full circle.
    Large angle values result in polygones. Thus circle(120.,120.) is an
    equilateral triangle.
    """
    if a2 == 0.0:
        a2 = a1
    n = int(round(a3/a2))
    a1 *= pi/180.
    return Formex([[[1.,0.,0.],[cos(a1),sin(a1),0.]]]).rosette(n,a2,axis=2,point=[0.,0.,0.])


def polygon(n):
    """A regular polygon with n sides."""
    return circle(360./n)


def triangle():
    """An equilateral triangle with base [0,1] on axis 0"""
    return Formex([[[0.,0.,0.],[1.,0.,0.],[0.5,0.5*sqrt(3.),0.]]])


def quadraticCurve(x=None,n=8):
    """CreateDraw a collection of curves.

    x is a (3,3) shaped array of coordinates, specifying 3 points.

    Return an array with 2*n+1 points lying on the quadratic curve through
    the points x. Each of the intervals [x0,x1] and [x1,x2] will be divided
    in n segments.
    """
    #if x.shape != (3,3):
    #    raise ValueError,"Expected a (3,3) shaped array."
    # Interpolation functions in normalized coordinates (-1..1)
    h = [ lambda x: x*(x-1)/2, lambda x: (1+x)*(1-x), lambda x: x*(1+x)/2 ]
    t = arange(-n,n+1) / float(n)
    H = column_stack([ hi(t) for hi in h ])
    return dot(H,x)


def sphere2(nx,ny,r=1,bot=-90,top=90):
    """Return a sphere consisting of line elements.

    A sphere with radius r is modeled by a regular grid of nx
    longitude circles, ny latitude circles and their diagonals.
    
    The 3 sets of lines can be distinguished by their property number:
    1: diagonals, 2: meridionals, 3: horizontals.

    The sphere caps can be cut off by specifying top and bottom latitude
    angles (measured in degrees from 0 at north pole to 180 at south pole.
    """
    base = Formex(pattern("543"),[1,2,3])     # single cell
    d = base.select([0]).replic2(nx,ny,1,1)   # all diagonals
    m = base.select([1]).replic2(nx,ny,1,1)   # all meridionals
    h = base.select([2]).replic2(nx,ny+1,1,1) # all horizontals
    grid = m+d+h
    s = float(top-bot) / ny
    return grid.translate([0,bot/s,1]).spherical(scale=[360./nx,s,r])

        
def sphere3(nx,ny,r=1,bot=-90,top=90):
    """Return a sphere consisting of surface triangles

    A sphere with radius r is modeled by the triangles fromed by a regular
    grid of nx longitude circles, ny latitude circles and their diagonals.

    The two sets of triangles can be distinguished by their property number:
    1: horizontal at the bottom, 2: horizontal at the top.

    The sphere caps can be cut off by specifying top and bottom latitude
    angles (measured in degrees from 0 at north pole to 180 at south pole.
    """
    base = Formex( [[[0,0,0],[1,0,0],[1,1,0]],
                    [[1,1,0],[0,1,0],[0,0,0]]],
                   [1,2])
    grid = base.replic2(nx,ny,1,1)
    s = float(top-bot) / ny
    return grid.translate([0,bot/s,1]).spherical(scale=[360./nx,s,r])


def connectCurves(curve1,curve2,n):
    """Connect two curves to form a surface.
    
    curve1, curve2 are plex-2 Formices with the same number of elements.
    The two curves are connected by a surface of quadrilaterals, with n
    elements in the direction between the curves.
    """
    if curve1.nelems() != curve2.nelems():
        raise ValueError,"Both curves should have same number of elements"
    # Create the interpolations
    curves = interpolate(curve1,curve2,n).split(curve1.nelems())
    quads = [ connect([c1,c1,c2,c2],nodid=[0,1,1,0]) for c1,c2 in zip(curves[:-1],curves[1:]) ]
    return Formex.concatenate(quads)


def sector(r,t,nr,nt,h=0.,diag=None):
    """Constructs a Formex which is a sector of a circle/cone.

    A sector with radius r and angle t is modeled by dividing the
    radius in nr parts and the angle in nt parts and then drawing
    straight line segments.
    If a nonzero value of h is given, a conical surface results with its
    top at the origin and the base circle of the cone at z=h.
    The default is for all points to be in the (x,y) plane.

    
    By default, a plex-4 Formex results. The central quads will collapse
    into triangles.
    If diag='up' or diag = 'down', all quads are divided by an up directed
    diagonal and a plex-3 Formex results.
    """
    r = float(r)
    t = float(t)
    p = Formex(regularGrid([0.,0.,0.],[r,0.,0.],[nr,0,0]).reshape(-1,3))
    if h != 0.:
        p = p.shear(2,0,h/r)
    q = p.rotate(t/nt)
    if diag == 'up':
        F = connect([p,p,q],bias=[0,1,1]) + \
            connect([p,q,q],bias=[1,2,1])
    elif diag == 'down':
        F = connect([q,p,q],bias=[0,1,1]) + \
            connect([p,p,q],bias=[1,2,1])
    else:
        F = connect([p,p,q,q],bias=[0,1,1,0])

    F = Formex.concatenate([F.rotate(i*t/nt) for i in range(nt)])
    return F


# End
