#!/usr/bin/env pyformex
##
## This file is part of pyformex 0.1.2 Release Fri Jul  9 14:48:57 2004
## pyformex is a python implementation of Formex algebra
## (c) 2004 Benedict Verhegghe (email: benedict.verhegghe@ugent.be)
## Releases can be found at ftp://mecatrix.ugent.be/pub/pyformex/
## Distributed under the General Public License, see file COPYING for details
##
#
global out
rt = 36.
rb = 34.5
m = 6
n = 6
a = 36.
T = Formex([[[rt,0,0],[rt,0,3]],[[rt,0,0],[rt,3,3]],[[rt,0,3],[rt,3,3]]])
W1 = Formex([[[rb,1,2],[rt,0,0]],[[rb,1,2],[rt,0,3]],[[rb,1,2],[rt,3,6]]])
W2 = Formex([[[rb,2,4],[rt,3,6]],[[rb,2,4],[rt,0,3]],[[rb,2,4],[rt,3,3]]])
B1 = Formex([[[rb,2,4],[rb,1,2]],[[rb,2,4],[rb,1,5]],[[rb,2,4],[rt,4,5]]])
B2 = Formex([[[rb,1,2],[rb,-1,2]]])
top = T.genit(1,m,3,3,0,1)
web = W1.genit(1,m,3,3,0,1) + W2.genit(1,m-1,3,3,0,1)
bot = B1.genit(1,m-1,3,3,0,1) + B2.rin(3,m,3)
out = top+web+bot
draw(out)
