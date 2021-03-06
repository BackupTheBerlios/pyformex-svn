#!/usr/bin/env pyformex
# $Id$
#
"""Sphere"""
clear()
nx=32   # number of modules in circumferential direction
ny=32   # number of modules in meridional direction
rd=100  # radius of the sphere cap
bot=160 # slope of the dome at its bottom (= half angle of the sphere cap)
top=20   # slope of the dome at its top opening (0 = no opening) 
a=ny*float(top)/(bot-top)

# First, a line based model

base = Formex(pattern("543"),[1,2,3]) # single cell
draw(base)

d = base.select([0]).replic2(nx,ny,1,1)   # all diagonals
m = base.select([1]).replic2(nx,ny,1,1)   # all meridionals
h = base.select([2]).replic2(nx,ny+1,1,1) # all horizontals
f = m+d+h
draw(f)

g = f.translate([0,a,1]).cospherical(scale=[360./nx,bot/(ny+a),rd])
clear()
draw(g)

# Second, a surface model

clear()
base = Formex( [[[0,0,0],[1,0,0],[1,1,0]],
                [[1,1,0],[0,1,0],[0,0,0]]],
               [1,3] )
draw(base)

f = base.replic2(nx,ny,1,1)
draw(f)

h = f.translate([0,a,1]).cospherical(scale=[360./nx,bot/(ny+a),rd])
clear()
draw(h)

# Both

g = g.translate([-rd,0,0])
h = h.translate([rd,0,0])
clear()
#GD.cfg['render/ambient'] = 0.4
#GD.cfg['render/specular'] = 0.1
#bb = (Formex([g.bbox()]) + Formex([h.bbox()])).bbox()
bb = bbox([g,h])
draw(g,bbox=bb)
draw(h,bbox=bb)

smooth()
GD.canvas.update()
