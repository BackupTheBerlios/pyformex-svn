#!/usr/bin/env pyformex --gui
# $Id$
##
##  This file is part of pyFormex 0.8 Release Mon Jun  8 11:56:55 2009
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
"""Mobius Ring

level = 'advanced'
topics = ['geometry','surface']
techniques = ['dialog', 'animation', 'colors']

"""

reset()
smoothwire()

res = askItems([('width',2),
                ('length',30),
                ('number of turns',1),
                ])
if not res:
    exit()
    
w = res['width']
l = res['length']
n = res['number of turns']

C = Formex(pattern('1234'))
cell = connect([C,C,C,C],bias=[0,1,2,3])
strip = cell.replic2(l,w,1.,1.).translate(1,-0.5*w)
TA = draw(strip,color='white')

sleep(1)

nsteps = 20
step = n*180./nsteps/l
for i in arange(nsteps+1):
    a = i*step
    torded = strip.map(lambda x,y,z: [x,y*cosd(x*a),y*sind(x*a)])
    TB = draw(torded,color='yellow')
    undraw(TA)
    TA = TB

sleep(1)
#TA = None
nsteps = 40
step = 360./nsteps
for i in arange(1,nsteps+1):
    ring = torded.trl(2,l*nsteps/pi/i).scale([i*step/l,1.,1.]).trl(0,-90).cylindrical(dir=[2,0,1])
    TB = draw(ring,color='orange')
    undraw(TA)
    TA = TB

sleep(1)
nsteps = 40
step = 720./nsteps
for i in arange(1,nsteps+1):
    mobius = ring.rotate(i*step)
    TB = draw(mobius,color='orange')
    undraw(TA)
    TA = TB

## path = ring.select(range(30)).selectNodes([2,3])

## flyAlong(path.scale(0.8))
## export({'flypath':path})


