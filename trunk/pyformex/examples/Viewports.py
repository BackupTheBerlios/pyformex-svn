#!/usr/bin/env pyformex
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
"""Viewports.py

level = 'advanced'
topics = ['surface']
techniques = ['viewport', 'color']

Demonstrate multiple viewports.
"""

nsl = 0
F = Formex.read(getcfg('datadir')+'/horse.pgf')

## layout(2)
## viewport(0)
## draw(F)
## drawNumbers(F)
## drawText('Viewport 0',10,10)
## viewport(1)
## draw(F)
## drawNumbers(F)
## drawText('Viewport 1',10,10)
## viewport(0)
## viewport(1)
## exit()


layout(1)
FA = draw(F,view='front')
pause()

layout(2)
drawText('Viewport 2',10,10)
pf.GUI.viewports.updateAll()
pause()

layout(3)
draw(F,color='green')
pause()

viewport(1)
linkViewport(1,0)

exit()
#sleep(nsl)
layout(1)

layout(4,2)
viewport(0)
sleep(nsl)

exit()

for i in range(1,4):
    linkViewport(i,0)

colors=['indianred','olive','coral','yellow']

for i,v in enumerate(['front','right','top','iso']):
    viewport(i)
    view(v)
    bgcolor(colors[i])
    pf.canvas.setBgColor(pf.canvas.settings.bgcolor)
    pf.canvas.display()
    pf.canvas.update()

exit()

sleep(nsl)
viewport(3)
G = F.cutWithPlane([0.,0.,0.],[-1.,0.,0.],side='+')
clear()
draw(G) # this draws in the 4 viewports !
pf.GUI.viewports.updateAll()


sleep(nsl)
smooth()
pf.GUI.viewports.updateAll()

exit()
from gui import canvas
sleep(nsl)
canvas.glLine()
canvas.glFlat()
pf.GUI.viewports.updateAll()




#End
