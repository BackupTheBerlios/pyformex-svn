#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.5 Release Fri Aug 10 12:04:07 2007
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""sectionize.py

Create, measure and approximate cross section of a Formex.
"""

import globaldata as GD
import simple
from formex import *
from gui.draw import *



def createSegments(F,ns=None,th=None):
    """Create segments along 0 axis for sectionizing the Formex F."""
    bb = F.bbox()
    GD.message("Bounding box = %s" % bb)
    if ns is None or th is None:
        itemlist = [['number of sections',20],['relative thickness',0.1]]
        res,accept = widgets.InputDialog(itemlist,'Sectioning Parameters').getResult()
        if accept:
            ns = int(res[0][1])
            th = float(res[1][1])
    if type(ns) == int and type(th) == float:
        xmin,ymin,zmin = bb[0]
        xmax,ymax,zmax = bb[1]
        xgem,ygem,zgem = F.center()
        A = [ xmin,ygem,zgem ]
        B = [ xmax,ygem,zgem ]
        segments = Formex([[A,B]]).divide(ns)
        GD.message("Segments: %s" % segments)
        return ns,th,segments
    return 0,0,[]


def sectionize(F,segments,th=0.1,visual=True):
    """Sectionize a Formex in planes perpendicular to the segments.

    F is any Formex.
    segments is a plex-2 Formex.

    Planes are chosen in each center of a segment, perpendicular to
    that segment. Then parts of the Formex F are selected in the
    neighbourhood of each plane. Each part is then approximated by a
    circle in that plane.

    th is the relative thickness of the selected part of the Formex.
    If th = 0.5, that part will be delimited by two planes in the endpoints
    of and perpendicular to the segments.
    """
    sections = []
    ctr = []
    diam = []
    if visual:
        clear()
        linewidth(1)
        draw(F,color='yellow')
        linewidth(2)
    for s in segments:
        c = 0.5 * (s[0]+s[1])
        d = s[1]-s[0]
        l = length(d)
        n = d/l
        t = th*l
        test = abs(distanceFromPlane(F.f,c,n)) < th*l
        test = test.sum(axis=-1)
        G = F.select(test==3)
        if visual:
            draw(G,color='blue',view=None)
            GD.canvas.update()
        C = G.center()
        D = 2 * distanceFromLine(G.f,C,n).mean()
        GD.message("Section Center: %s; Diameter: %s" % (C,D))
        sections.append(G)
        ctr.append(C)
        diam.append(D)
    return sections,ctr,diam


def drawCircles(sections,ctr,diam):
    """Draw circles as approximation of Formices."""
    circle = simple.circle().rotate(-90,1)
    cross = Formex(simple.Pattern['plus']).rotate(-90,1)
    circles = []
    n = len(sections)
    for i in range(n):
        C = cross.translate(ctr[i])
        B = circle.scale(diam[i]/2).translate(ctr[i])
        S = sections[i]
        clear()
        draw(S,view='left',wait=False)
        draw(C,color='red',bbox=None,wait=False)
        draw(B,color='blue',bbox=None)
        circles.append(B)
    return circles


def drawAllCircles(F,circles):
    clear()
    linewidth(1)
    draw(F,color='yellow',view='front')
    linewidth(2)
    for circ in circles:
        bb = circ.bbox()
        d = (bb[1] - bb[0]) * 0.5
        bb[0] -= d
        bb[1] += d
        draw(circ,color='blue',bbox=bb)
    zoomAll()


def connectPoints(F,close=False):
    """Return a Formex with straight segments connecting subsequent points.

    F can be a Formex or data that can be turned into a Formex (e.g. an (n,3)
    array of points). The result is a plex-2 Formex connecting the subsequent
    points of F or the first point of subsequent elements in case the plexitude
    of F > 1.    
    If close=True, the last point is connected back to the first to create a
    closed polyline.
    """
    if not isinstance(F,formex.Formex):
        F = Formex(F)
    return formex.connect([F,F],bias=[0,1],loop=close)


# End
