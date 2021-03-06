#!/usr/bin/env pyformex --gui
# $Id$
##
##  This file is part of pyFormex 0.8.5     Sun Nov  6 17:27:05 CET 2011
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  https://savannah.nongnu.org/projects/pyformex/
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
"""Torus

level = 'beginner'
topics = ['geometry']
techniques = ['color']

"""
m = 36 # number of cells along torus big circle
n = 36 # number of cells along torus small circle
message("Create a triangle with three colored members")
F = Formex('l:164',[1,2,3])
clear();draw(F);pause()
message("Replicate it into a rectangular pattern")
F = F.replic2(m,n,1,1)
clear();draw(F);pause()
message("Fold the rectangle into a tube")
G = F.translate(2,1).cylindrical([2,1,0],[1.,360./n,1.])
clear();draw(G,view='right');pause()
message("Bend the tube into a torus with mean radius 5")
H = G.translate(0,5).cylindrical([0,2,1],[1.,360./m,1.])
clear();draw(H,view='iso');pause()
message("Cut a part from the torus")

K = H.cutWithPlane([0.,-2.,0.],[1.,1.,1.],side='+')
clear()
draw(K)

