#!/usr/bin/env pyformex --gui
# $Id$
##
## This file is part of pyFormex 0.7.1 Release Sat May 24 13:26:21 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""Novation"""

reset()
#GD.cfg['input/timeout'] = 2


basechoices = ['Triangles','Quadrilaterals']
renderchoices = ['wireframe','flat','flatwire','smooth','smoothwire']
res = askItems([['Type of surface element','Triangles','radio',basechoices],
                ['Number of bumps',3],
                ['Render mode',None,'select',renderchoices],
                ['Transparent',False],
                ['Add a bottom plate',False],
                ['Shrink elements',False],
                ['Export to .stl',False],
                ])
if not res:
    exit()

baseGeom = basechoices.index(res['Type of surface element'])
rendermode = res['Render mode']
nbumps = int(res['Number of bumps'])
transparent = res['Transparent']
bottom = res['Add a bottom plate']
shrink = res['Shrink elements']
export = res['Export to .stl']

n = 10*nbumps

if baseGeom == 0:
    # The base consists of two triangles
    e = Formex([[[0,0,0],[1,0,0],[0,1,0]],[[1,0,0],[1,1,0],[0,1,0]]],1).replic2(n,n,1,1)
else:
    # The base is one quadrilateral
    e = Formex([[[0,0,0],[1,0,0],[1,1,0],[0,1,0]]],1).replic2(n,n,1,1)

# These are lines forming quadrilaterals
#e = Formex([[[0,0,0],[1,0,0]]]).rosad(.5,.5).rinid(n,n,1,1)

# Novation (Spots)
s = nbumps+1
r = n/s
h = 12
a = [ [r*i,r*j,h]  for j in range(1,s) for i in range(1,s) ]

if bottom:
    # create a bottom
    b = e.reverseElements()
    #b.setProp(2)
    
# create the bumps
for p in a:
    e = e.bump(2,p, lambda x:exp(-0.5*x),[0,1])
if shrink:
    e = e.shrink(0.8)

renderMode(rendermode)
if transparent:
    GD.canvas.alphablend = True
if bottom:
    draw(b,color=yellow,alpha=1.0)

draw(e,alpha=0.8)

if export:
    from plugins import surface
    f = file('novation.stl','w')
    F = e # + b
    # Create triangles
    G = F.selectNodes([0,1,2])
    # If polygones, add more triangles
    for i in range(3,F.nplex()):
        G += F.selectNodes([0,i-1,i])
    clear()
    draw(G)
    surface.write_stla(f,G.f)
    f.close()
