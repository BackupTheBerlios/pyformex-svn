#!/usr/bin/env pyformex
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
"""Props

level = 'beginner'
topics = ['geometry']
techniques = ['viewport', 'color', 'symmetry']

A demonstration of propagating property numbers.
Also shows the use of multiple viewports.
"""

def vp(i):
    viewport(i)
    smooth()
    lights(False)
    clear()
    
if __name__ == "draw":

    layout(4)
    F0 = Formex('3:012934',[1,3])
    F1 = F0.replic2(2,2)
    F2 = F1 + F1.reflect(1)
    F3 = F2 + F2.rotate(180.,1)
    
    for i,F in enumerate([F0,F1,F2,F3]):
        vp(i)
        draw(F)
        #drawText("F%s"%i,10,10,size=18)
        pf.canvas.update()
        #sleep(2)
    
    
# End
