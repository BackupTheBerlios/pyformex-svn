#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.4.2 Release Sat Mar 10 20:05:55 2007
## pyFormex is a python implementation of Formex algebra
## Homepage: http://pyformex.berlios.de/
## Distributed under the GNU General Public License, see file COPYING
## Copyright (C) Benedict Verhegghe except where stated otherwise 
##
"""read/write tetgen format files."""

import os
from utils import changeExt
from formex import *

def invalid(line,fn):
    """Print message for invalid line."""
    print "The following line in file %s is invalid:" % fn
    print line
    

def readNodes(fn):
    """Read a tetgen .node file.

    Returns a tuple of two arrays: nodal coordinates and node numbers.
    """
    fil = file(fn,'r')
    line = fil.readline()
    s = line.strip('\n').split()
    npts,ndim,nattr,nbmark = map(int,s)
    nodes = fromfile(fil,sep=' ',dtype=Float).reshape((npts,ndim+1))
    return nodes[:,1:],nodes[:,0].astype(int32)


def readElems(fn):
    """Read a tetgen .ele file.

    Returns a tuple of 3 arrays:
      elems : the element connectivity
      elemnr : the element numbers
      attr: the element attributes.
    """
    fil = file(fn,'r')
    line = fil.readline()
    s = line.strip('\n').split()
    nelems,nplex,nattr = map(int,s)
    elems = fromfile(fil,sep=' ',dtype=int32).reshape((nelems,nplex+nattr+1))
    return elems[:,1:nplex+1],elems[:,0],elems[:,nplex+1:]


def readSmesh(fn):
    """Read a tetgen .smesh file.

    Returns an array of triangle elements.
    """
    fil = file(fn,'r')
    part = 0
    elems = None
    line = fil.readline()
    while not line.startswith('# part 2:'):
        line = fil.readline()
    line = fil.readline()
    s = line.strip('\n').split()
    nelems = int(s[0])
    elems = fromfile(fil,sep=' ',dtype=int32, count=4*nelems)
    print elems.shape
    elems = elems.reshape((-1,4))
    return elems[:,1:]


def readSurface(fn):
    """Read a tetgen surface from a .node/.smesh file pair.

    The given filename is either the .node or .smesh file.
    Returns a tuple of (nodes,elems).
    """
    nodes,numbers = readNodes(changeExt(fn,'.node'))
    print "Read %s nodes" % nodes.shape[0]
    elems = readSmesh(changeExt(fn,'.smesh'))
    if numbers[0] > 0:
        elems = elems-1
    return nodes,elems


def writeNodes(fn,nodes):
    """Write a tetgen .node file."""
    fil = file(fn,'w')
    fil.write("%d %d 0 0\n" % nodes.shape)
    for i,n in enumerate(nodes):
        fil.write("%d %s %s %s\n" % (i,n[0],n[1],n[2]))
    fil.close()


def writeSmesh(fn,facets,nodes=None,holes=None,regions=None):
    """Write a tetgen .smesh file.

    Currently it only writes the facets of a triangular surface mesh.
    Nodes should be written independently to a .node file.
    """
    fil = file(fn,'w')
    fil.write("# part 1: node list.\n")
    if nodes is None:
        fil.write("0  3  0  0  # nodes are found in %s.node.\n")
    fil.write("# part 2: facet list.\n")
    fil.write("%s 0\n" % facets.shape[0])
    for i,n in enumerate(facets):
        # adding comments breaks fast readback
        # fil.write("3 %s %s %s # %s\n" % (n[0],n[1],n[2],i))
        fil.write("3 %s %s %s\n" % (n[0],n[1],n[2]))
    fil.write("# part 3: hole list.\n")
    if holes is None:
        fil.write("0\n")
    fil.write("# part 4: region list.\n")
    if regions is None:
        fil.write("0\n")
    fil.write("# Generated by pyFormex\n")


def writeSurface(fn,nodes,elems):
    """Write a tetgen surface model to .node and .smesh files.

    The provided file name is the .node or the .smesh filename.
    """
    writeNodes(changeExt(fn,'.node'),nodes)
    writeSmesh(changeExt(fn,'.smesh'),elems)



def nextFilename(fn):
    """Returns the next file name in a family of tetgen file names."""
    m = re.compile("(?P<base>.*)\.(?P<id>\d*)\.(?P<ext>.*)").match(fn)
    if m:
        return "%s.%s.%s" % (m.group('base'),int(m.group('id'))+1,m.group('ext'))
    else:
        return '.1'.join(os.path.splitext(fn))



if __name__ == "__main__":
    import sys

    for f in sys.argv[1:]:
        if f.endswith('.node'):
            nodes = readNodes(f)
            print "Read %d nodes" % nodes.shape[0]
        elif f.endswith('.ele'):
            elems = readElems(f)
            print "Read %d elems" % elems.shape[0]
        elif f.endswith('.smesh'):
            elems = readSmesh(f)
            print "Read %d triangles" % elems.shape[0]
        
    
