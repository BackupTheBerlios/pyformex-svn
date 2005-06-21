#!/usr/bin/env pyformex
# $Id$
##
## This file is part of pyformex 0.1.2 Release Fri Jul  9 14:48:57 2004
## pyformex is a python implementation of Formex algebra
## (c) 2004 Benedict Verhegghe (email: benedict.verhegghe@ugent.be)
## Releases can be found at ftp://mecatrix.ugent.be/pub/pyformex/
## Distributed under the General Public License, see file COPYING for details
##
#
"""Diamatic dome"""
u = 3.     # modular length
n = 6      # number of modules in one sector
r = 36.    # radius of the dome

# Topology for 1 sector
T = Formex(pattern("164"),3).replic2(n,n,1,1,0,1,0,-1)


# 4 sectors
m = 4
angle = 360./m
D = T.copy()
# circulize sector
D.scale(u).circulize(angle)
D.mapd(2,lambda d:sqrt(r**2-d**2),[0,0,0],[0,1])
dome1=D.rosette(m,angle)
clear()
draw(dome1)

# 6 sectors
m = 6
angle = 360./m
a = sqrt(3.)/2
D = T.copy().shear(0,1,0.5).scale([1,a,1])
#D = T.replic2(n,n,1,a,0,1,0.5,-1)
D.scale(u).circulize(angle)
D.mapd(2,lambda d:sqrt(r**2-d**2),[0,0,0],[0,1])
dome2=D.rosette(m,angle)
sleep()
clear()
draw(dome2)

# 8 sectors
m = 8
angle = 360./m
a = sqrt(2.)/2
T = Formex([[[0,0],[1,0]],[[1,0],[a,a]],[[a,a],[0,0]]],3)
D = T.replic2(n,n,1,a,0,1,a,-1)
# circulize sector
D.scale(u).circulize(angle)
D.mapd(2,lambda d:sqrt(r**2-d**2),[0,0,0],[0,1])
dome3=D.rosette(m,angle)
sleep()
clear()
draw(dome3)

# circulize1
m = 6
angle = 360./m
T = Formex(pattern("127"),3)
D = T.replic2(n,n,1,1,0,1,1,-1)
D.scale(u).circulize1()
D.mapd(2,lambda d:sqrt(r**2-d**2),[0,0,0],[0,1])
dome4=D.rosette(m,angle)
sleep()
clear()
draw(dome4)

sleep();clear()
dome4.setProp(1)
draw(dome2+dome4)


sleep()
clear()
d=1.1*r
draw(dome1+dome2.translate([d,0,0])+dome3.translate([0,d,0])+dome4.translate([d,d,0]))
