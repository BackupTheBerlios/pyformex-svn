#!/usr/bin/env pyformex
##
## This file is part of pyformex 0.1.2 Release Fri Jul  9 14:48:57 2004
## pyformex is a python implementation of Formex algebra
## (c) 2004 Benedict Verhegghe (email: benedict.verhegghe@ugent.be)
## Releases can be found at ftp://mecatrix.ugent.be/pub/pyformex/
## Distributed under the General Public License, see file COPYING for details
##
#
n = 40
# These two look the same in wireframe
# These are quadrilaterals
e = Formex([[[0,0,0],[1,0,0],[1,1,0],[0,1,0]]]).rinid(n,n,1,1)
# These are lines
e = Formex([[[0,0,0],[1,0,0]]]).rosad(.5,.5).rinid(n,n,1,1)
# Novation (Spots)
m = 4
h = 12
c = 7
r = n/m
s = n/r
print "s=",s
a1 = [ [r*i,r*j,h]  for j in range(1,s) for i in range(1,s) ]
print a1

def nov(x,p,c=0.5):
    from numarray import sqrt,exp # we need to import this
    for a in p:
        d = x[:,:,0:2] - a[0:2]
        d = d*d
        d = sqrt(d[:,:,0] + d[:,:,1])
        d = a[2]*exp(-c*d)
        x[:,:,2] += d




f = e.formex()
nov(f,a1,0.4) # This changes the formex inplace !

# This creates already a nice picture, but the implementation in formex
# should be somewhat more useful:
#  - using any of the three coordinates
#  - result in a surface acutally going through the specified indentation
#    instead of accumulating them ; this requires to solve a system
#    of equations first, to calculate the respective weights of the points
  
out = e
draw (out)
	
		
	

 
		
