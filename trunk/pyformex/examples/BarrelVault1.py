#!/usr/bin/env pyformex --gui
# $Id$
##
##  This file is part of pyFormex 0.8.5     Sun Nov  6 17:27:05 CET 2011
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  https://savannah.nongnu.org/projects/pyformex/
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
"""Barrel Vault Shell

level = 'beginner'
topics = ['frame']
techniques = ['dialog']

"""
reset()
smoothwire()

res = askItems([
    dict(name='m',value=12,text='number of modules in axial direction'),
    dict(name='n',value=8,text='number of modules in tangential direction'),
    dict(name='r',value=10.,text='barrel radius'),
    dict(name='a',value=180.,text='barrel opening angle'),
    dict(name='l',value=30.,text='barrel length'),
    dict(name='eltype',value='quad8',text='element type',itemtype='radio',choices=['tri3','quad4','quad8','quad9']),
    ])
if not res:
    exit()

globals().update(res)

# Grid
g = Formex('4:0123').replic2(m,n).toMesh().convert(eltype)

# Create barrel
barrel = g.rotate(90,1).translate(0,r).scale([1.,a/n,l/m]).cylindrical()

draw(barrel,color=red,bkcolor=blue)
#drawNumbers(barrel.coords)
# End
