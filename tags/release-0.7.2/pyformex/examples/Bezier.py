#!/usr/bin/env pyformex --gui
# $Id$
##
## This file is part of pyFormex 0.7.2 Release Tue Sep 23 16:18:43 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
 
"""Bezier

level = 'beginner'
topic = ['geometry','curves']
techniques = ['colors','solve']

"""

def build_matrix(atoms,vars):
    """Build a matrix of functions of coords.

    atoms is a list of text strings each representing a function of variables
    defined in vars.
    vars is a dictionary where the keys are variable names appearing in atoms
    and the values are 1-dim arrays of values. All variables should have the
    same shape !
    A matrix is returned where each row contains the values of atoms evaluated
    for one set of the variables.
    """
    nval = len(vars[vars.keys()[0]])
    aa = zeros((nval,len(atoms)),Float)
    for k,a in enumerate(atoms):
        res = eval(a,vars)
        aa[:,k] = eval(a,vars)
    return aa   


class Bezier(object):
    """A class representing a Bezier curve"""

    atoms = {
        1 : ('1-t','t'),
        2 : ('(1-t)**2','2*t*(1-t)','t**2'),
        3 : ('(1-t)**3','3*t*(1-t)**2','3*t**2*(1-t)','t**3'),
        }

    def __init__(self,pts):
        """Create a bezier curve.

        pts is an Coords array with at least 2 points.
        A Bezier curve of degree npts-1 is constructed between the first
        and the last points.
        """
        self.pts = pts


    def at(self,t):
        """Returns the points of the curve for parameter values t"""
        deg = self.pts.shape[0] - 1
        aa = build_matrix(Bezier.atoms[deg],{'t':t})
        return dot(aa,self.pts)



def drawNumberedPoints(x,color):
    x = Formex(x)
    draw(x,color=color)
    drawNumbers(x,color=color)
    

n = 100
t = arange(n+1)/float(n)

clear()

for d in arange(4) * 0.2:
    #clear()

    x = Coords([ [0.,0.], [1./3.,d], [2./3.,4*d**2], [1.,0.] ])

    drawNumberedPoints(x,red)

    H = Formex(x.reshape(2,2,3))
    draw(H,color=red)

    curve = Bezier(x)
    F = Formex(curve.at(t))
    #draw(F)

    G = connect([F,F],bias=[0,1])
    draw(G)
    
    #zoomAll()

# End
