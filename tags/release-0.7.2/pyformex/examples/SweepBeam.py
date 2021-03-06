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

"""H-beam

level = 'normal'
topics = ['geometry','surface']
techniques = ['colors']

"""

from plugins import mesh
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
c2 = simple.circle(90./er,0.,90.).mirror(0).scale(r).translate([tw/2+r,h/2-tf-r,0])
Filled = simple.connectCurves(c2,c1,etb)

Quarter = Body + Filled + Flange1 + Flange2 + Flange3

Half = Quarter + Quarter.mirror(1).reverse()

Full = Half + Half.mirror(0).reverse()

draw(Full,color=red)

method = ask("Choose extrude method:",['Cancel','Sweep','Connect'])
if method == 'Cancel':
    exit()

nodesF,elemsF = Full.feModel()

if method == 'Sweep':
    path = simple.line([0,0,0],[0,0,l],el)
    nodesF = nodesF.rollAxes(1)
    nodes,elems = mesh.sweepGrid(nodesF,elemsF,path,a1='last',a2='last')

else:
    nodesF1 = nodesF.trl([0,0,l])#.scale(2)
    nodes,elems = mesh.connectMesh(nodesF,nodesF1,elemsF,el)

smooth()
clear()
Beam = Formex(nodes[elems].reshape(-1,8,3),eltype='Hex8')
draw(Beam,color='red',linewidth=2)


# End
