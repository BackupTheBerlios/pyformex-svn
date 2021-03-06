#!/usr/bin/env pyformex
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
"""Create tetraeder mesh in side .STL surface and export in Abaqus format.

Usage: pyformex --nogui stl_abq input.stl
Generates input-surface.inp and input-volume.inp with the
surface and volume modules in Abaqus(R) input format. 
"""

from utils import runCommand
from plugins import surface, fe_abq, tetgen
import os


def abq_export(fn,nodes,elems,eltype,header="Exported by stl_examples.py"):
    """Export a finite element model in Abaqus .inp format."""
    fil = file(fn,'w')
    fe_abq.writeHeading(fil,header)
    fe_abq.writeNodes(fil,nodes)
    fe_abq.writeElems(fil,elems,eltype,nofs=1)
    fil.close()
    print "Abaqus file %s written." % fn


def stl_tetgen(fn):
    """Generate a volume tetraeder mesh inside an stl surface."""
    sta,out = runCommand('tetgen %s' % fn)
    message(out)


def stl_to_abaqus(fn):
    print "Converting %s to Abaqus .INP format" % fn
    stl_tetgen(fn)
    fb = os.path.splitext(fn)[0]
    nodes = tetgen.readNodes(fb+'.1.node')
    elems = tetgen.readElems(fb+'.1.ele')
    faces = tetgen.readSurface(fb+'.1.smesh')
    print "Exporting surface model"
    abq_export(fb+'-surface.inp',nodes,faces,'S3',"Abaqus model generated by tetgen from surface in STL file %s" % fn)
    print "Exporting volume model"
    abq_export(fb+'-volume.inp',nodes,elems,'C3D%d' % elems.shape[1],"Abaqus model generated by tetgen from surface in STL file %s" % fn)
     

# Processing starts here

if __name__ == "script":
    import sys

    for f in sys.argv[2:]:
        if f.endswith('.stl') and os.path.exists(f):
            print "Processing %s" % f
            stl_to_abaqus(f)
        else:
            print "Ignore argument %s" % f

           

# End
