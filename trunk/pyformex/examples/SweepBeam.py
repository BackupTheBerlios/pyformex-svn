#!/usr/bin/env pyformex --gui
# $Id$
##
##  This file is part of pyFormex 0.8.4 Release Sat Jul  9 14:43:11 2011
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

"""H-beam

level = 'normal'
topics = ['geometry','surface']
techniques = ['color']

"""

from plugins import curve
#from mesh import Mesh
import simple


# GEOMETRICAL PARAMETERS FOR HE200B wide flange beam
h = 200. #beam height
b = 200. #flange width 
tf = 15. #flange thickness
tw = 9.  #body thickness
l = 400. #beam length
r = 18.  #filling radius

# MESH PARAMETERS
el = 20 #number of elements along the length
etb = 2 #number of elements over half of the thickness of the body
ehb = 5 #number of elements over half of the height of the body
etf = 5 #number of elements over the thickness of the flange
ewf = 8 #number of elements over half of the width of the flange
er = 6  #number of elements in the circular segment

Body = simple.rectangle(etb,ehb,tw/2.,h/2.-tf-r)
Flange1 =  simple.rectangle(er/2,etf-etb,tw/2.+r,tf-tw/2.).translate([0.,h/2.-(tf-tw/2.),0.])
Flange2 =  simple.rectangle(ewf,etf-etb,b/2.-r-tw/2.,tf-tw/2.).translate([tw/2.+r,h/2.-(tf-tw/2.),0.])
Flange3 =  simple.rectangle(ewf,etb,b/2.-r-tw/2.,tw/2.).translate([tw/2.+r,h/2.-tf,0.])
c1a = simple.line([0,h/2-tf-r,0],[0,h/2-tf+tw/2,0],er/2)
c1b = simple.line([0,h/2-tf+tw/2,0],[tw/2+r,h/2-tf+tw/2,0],er/2)
c1 = c1a + c1b
c2 = simple.circle(90./er,0.,90.).reflect(0).scale(r).translate([tw/2+r,h/2-tf-r,0])
Filled = simple.connectCurves(c2,c1,etb)
Quarter = Body + Filled + Flange1 + Flange2 + Flange3
Half = Quarter + Quarter.reflect(1).reverse()
Full = Half + Half.reflect(0).reverse()
Section = Full.toMesh()

clear()
draw(Section,color=red)
#exit()

#pause()

method = ask("Choose extrude method:",['Cancel','Sweep','Connect','Extrude','Revolve','RevolveLoop'])


if method == 'Sweep':
    L = simple.line([0,0,0],[0,0,l],el)
    x = concatenate([L.coords[:,0],L.coords[-1:,1]])
    path = curve.PolyLine(x)
    Beam = Section.sweep(path,normal=[0.,0.,1.],upvector=[0.,1.,0.])

elif method == 'Connect':
    Section1 = Section.trl([0,0,l])
    Beam = Section.connect(Section1,el)

elif method == 'Extrude':
    Beam = Section.extrude(el,step=l/el,dir=2)

elif method == 'Revolve':
    Beam = Section.revolve(el,axis=1,angle=60.,around=[-l,0.,0.])

elif method == 'RevolveLoop':
    Beam = Section.revolve(el,axis=1,angle=240.,around=[-l,0.,0.],loop=True)

else:
    exit()
    
clear()
draw(Beam.getBorderMesh(),color='red',linewidth=2)
export({'Beam':Beam})


# End
