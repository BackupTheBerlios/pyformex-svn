#!/usr/bin/env pyformex
# $Id: DoubleLayer.py 17 2004-10-08 14:37:45Z bene $
##
## This file is part of pyFormex 0.2.1 Release Fri Apr  8 23:30:39 2005
## pyFormex is a python implementation of Formex algebra
## Homepage: http://pyformex.berlios.de/
## Distributed under the GNU General Public License, see file COPYING
## Copyright (C) Benedict Verhegghe except where otherwise stated 
##
#
"""DoubleLayer"""
from math import *
Formex.setPrintFunction(Formex.asFormexWithProp)
clear()
n=10; a=2./3.; d=1./n;
e1 = Formex([[[0,0,d],[2,0,d]],[[2,0,d],[1,1,d]],[[1,1,d],[0,0,d]]],prop=1)
e2 = Formex([[[0,0,d],[1,1-a,0]],[[2,0,d],[1,1-a,0]],[[1,1,d],[1,1-a,0]]],prop=3)
# top and bottom layers
e4 = e1.genid(n,n,2,1,1,-1).bb(1./(2*n),1./(2*n)/tan(radians(30)))
e5 = e1.genid(n-1,n-1,2,1,1,-1).translate([1,1-a,-d]).bb(1./(2*n),1./(2*n)/tan(radians(30)))
# diagonals
e6 = e2.genid(n,n,2,1,1,-1).bb(1./(2*n),1./(2*n)/tan(radians(30)))
e5.setProp(2)
out = (e4+e5+e6).tran(3,-d)
print out.nnodes(),out.nelems()
draw(out)
