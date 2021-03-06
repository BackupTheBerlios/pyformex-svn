#!/usr/bin/env pyformex
# $Id$
#
"""Novation"""
clear()
n = 40
# These two look the same in wireframe
# These are quadrilaterals
e = Formex([[[0,0,0],[1,0,0],[1,1,0],[0,1,0]]],1).rinid(n,n,1,1)
# These are lines
#e = Formex([[[0,0,0],[1,0,0]]]).rosad(.5,.5).rinid(n,n,1,1)
# Novation (Spots)
m = 4
h = 12
r = n/m
s = n/r
a = [ [r*i,r*j,h]  for j in range(1,s) for i in range(1,s) ]

for p in a:
    e = e.bump(2,p, lambda x:exp(-0.5*x),[0,1])

draw (e,color=red)
