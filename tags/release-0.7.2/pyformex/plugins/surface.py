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
"""Import/Export Formex structures to/from stl format.

An stl is stored as a numerical array with shape [n,3,3].
This is compatible with the pyFormex data model.
"""

import os
import pyformex as GD
from plugins import tetgen,connectivity
from utils import runCommand, changeExt,countLines,mtime,hasExternal
from formex import *
import tempfile
from numpy import *
from gui.drawable import interpolateNormals

hasExternal('admesh')
hasExternal('tetgen')
hasExternal('gts')


# Conversion of surface data models


def expandElems(elems):
    """Transform elems to edges and faces.

    elems is an (nelems,nplex) integer array of element node numbers.
    The maximum node number should be less than 2**31 or approx. 2 * 10**9 !!

    Return a tuple edges,faces where
    - edges is an (nedges,2) int32 array of edges connecting two node numbers.
    - faces is an (nelems,nplex) int32 array with the edge numbers connecting
      each pair os subsequent nodes in the elements of elems.

    The order of the edges respects the node order, and starts with nodes 0-1.
    The node numbering in the edges is always lowest node number first.

    The inverse operation is compactElems.
    """
    nelems,nplex = elems.shape
    magic = elems.max() + 1
    if magic > 2**31:
        raise RuntimeError,"Cannot compact edges for more than 2**31 nodes"
    n = arange(nplex)
    edg = column_stack([n,roll(n,-1)])
    alledges = elems[:,edg]
    # sort edge nodes with lowest number first
    alledges.sort()
    if GD.options.fastencode:
        edg = alledges.reshape((-1,2))
        codes = edg.view(int64)
    else:
        edg = alledges.astype(int64).reshape((-1,2))
        codes = edg[:,0] * magic + edg[:,1]
    # keep the unique edge numbers
    uniqid,uniq = unique1d(codes,True)
    # uniq is sorted 
    uedges = uniq.searchsorted(codes)
    edges = column_stack([uniq/magic,uniq%magic])
    faces = uedges.reshape((nelems,nplex))
    return edges,faces


def compactElems(edges,faces):
    """Return compacted elems from edges and faces.

    This is the inverse operation of expandElems.
    """
    elems = edges[faces]
    flag1 = (elems[:,0,0]==elems[:,1,0]) + (elems[:,0,0]==elems[:,1,1])
    flag2 = (elems[:,2,0]==elems[:,1,0]) + (elems[:,2,0]==elems[:,1,1])
    nod0 = where(flag1,elems[:,0,1],elems[:,0,0])
    nod1 = where(flag1,elems[:,0,0],elems[:,0,1])
    nod2 = where(flag2,elems[:,2,0],elems[:,2,1])
    elems = column_stack([nod0,nod1,nod2])
    return elems


def areaNormals(x):
    """Compute the area and normal vectors of a collection of triangles.

    x is an (ntri,3,3) array of coordinates.

    Returns a tuple of areas,normals.
    The normal vectors are normalized.
    The area is always positive.
    """
    area,normals = vectorPairAreaNormals(x[:,1]-x[:,0],x[:,2]-x[:,1])
    area *= 0.5
    return area,normals


# Conversion of surface file formats

def stlConvert(stlname,outname=None,options='-d'):
    """Transform an .stl file to .off or .gts format.

    If outname is given, it is either '.off' or '.gts' or a filename ending
    on one of these extensions. If it is only an extension, the stlname will
    be used with extension changed.

    If the outname file exists and its mtime is more recent than the stlname,
    the outname file is considered uptodate and the conversion programwill
    not be run.
    
    The conversion program will be choosen depending on the extension.
    This uses the external commands 'admesh' or 'stl2gts'.

    The return value is a tuple of the output file name, the conversion
    program exit code (0 if succesful) and the stdout of the conversion
    program (or a 'file is already uptodate' message).
    """
    if not outname:
        outname = GD.cfg.get('surface/stlread','.off')
    if outname.startswith('.'):
        outname = changeExt(stlname,outname)
    if os.path.exists(outname) and mtime(stlname) < mtime(outname):
        return outname,0,"File '%s' seems to be up to date" % outname
    
    if outname.endswith('.off'):
        cmd = "admesh %s --write-off '%s' '%s'" % (options,outname,stlname)
    elif outname.endswith('.gts'):
        cmd = "stl2gts < '%s' > '%s'" % (stlname,outname)
    else:
        return outname,1,"Can not convert file '%s' to '%s'" % (stlname,outname)
       
    sta,out = runCommand(cmd)
    return outname,sta,out


# Input of surface file formats

def read_gts(fn):
    """Read a GTS surface mesh.

    Return a coords,edges,faces tuple.
    """
    GD.message("Reading GTS file %s" % fn)
    fil = file(fn,'r')
    header = fil.readline().split()
    ncoords,nedges,nfaces = map(int,header[:3])
    if len(header) >= 7 and header[6].endswith('Binary'):
        sep=''
    else:
        sep=' '
    coords = fromfile(fil,dtype=Float,count=3*ncoords,sep=' ').reshape(-1,3)
    edges = fromfile(fil,dtype=int32,count=2*nedges,sep=' ').reshape(-1,2) - 1
    faces = fromfile(fil,dtype=int32,count=3*nfaces,sep=' ').reshape(-1,3) - 1
    GD.message("Read %d coords, %d edges, %d faces" % (ncoords,nedges,nfaces))
    if coords.shape[0] != ncoords or \
       edges.shape[0] != nedges or \
       faces.shape[0] != nfaces:
        GD.message("Error while reading GTS file: the file is probably incorrect!")
    return coords,edges,faces


def read_off(fn):
    """Read an OFF surface mesh.

    The mesh should consist of only triangles!
    Returns a nodes,elems tuple.
    """
    GD.message("Reading .OFF %s" % fn)
    fil = file(fn,'r')
    head = fil.readline().strip()
    if head != "OFF":
        print "%s is not an OFF file!" % fn
        return None,None
    nnodes,nelems,nedges = map(int,fil.readline().split())
    nodes = fromfile(file=fil, dtype=Float, count=3*nnodes, sep=' ')
    # elems have number of vertices + 3 vertex numbers
    elems = fromfile(file=fil, dtype=int32, count=4*nelems, sep=' ')
    GD.message("Read %d nodes and %d elems" % (nnodes,nelems))
    return nodes.reshape((-1,3)),elems.reshape((-1,4))[:,1:]


def read_stl(fn,intermediate=None):
    """Read a surface from .stl file.

    This is done by first coverting the .stl to .gts or .off format.
    The name of the intermediate file may be specified. If not, it will be
    generated by changing the extension of fn to '.gts' or '.off' depending
    on the setting of the 'surface/stlread' config setting.
    
    Return a coords,edges,faces or a coords,elems tuple, depending on the
    intermediate format.
    """
    ofn,sta,out = stlConvert(fn,intermediate)
    if sta:
        GD.debug("Error during conversion of file '%s' to '%s'" % (fn,ofn))
        GD.debug(out)
        return ()

    if ofn.endswith('.gts'):
        return read_gts(ofn)
    elif ofn.endswith('.off'):
        return read_off(ofn)


def read_gambit_neutral(fn):
    """Read a triangular surface mesh in Gambit neutral format.

    The .neu file nodes are numbered from 1!
    Returns a nodes,elems tuple.
    """
    runCommand("/home/pmortier/pyformex/external/gambit-neu '%s'" % fn)
    nodesf = changeExt(fn,'.nodes')
    elemsf = changeExt(fn,'.elems')
    nodes = fromfile(nodesf,sep=' ',dtype=Float).reshape((-1,3))
    elems = fromfile(elemsf,sep=' ',dtype=int32).reshape((-1,3))
    return nodes, elems-1


# Output of surface file formats

def write_gts(fn,nodes,edges,faces):
    if nodes.shape[1] != 3 or edges.shape[1] != 2 or faces.shape[1] != 3:
        raise runtimeError, "Invalid arguments or shape"
    fil = file(fn,'w')
    fil.write("%d %d %d\n" % (nodes.shape[0],edges.shape[0],faces.shape[0]))
    for nod in nodes:
        fil.write("%s %s %s\n" % tuple(nod))
    for edg in edges+1:
        fil.write("%d %d\n" % tuple(edg))
    for fac in faces+1:
        fil.write("%d %d %d\n" % tuple(fac))
    fil.write("#GTS file written by %s\n" % GD.Version)
    fil.close()


def write_stla(f,x):
    """Export an x[n,3,3] float array as an ascii .stl file."""

    own = type(f) == str
    if own:
        f = file(f,'w')
    f.write("solid  Created by %s\n" % GD.Version)
    area,norm = areaNormals(x)
    degen = degenerate(area,norm)
    print "The model contains %d degenerate triangles" % degen.shape[0]
    for e,n in zip(x,norm):
        f.write("  facet normal %s %s %s\n" % tuple(n))
        f.write("    outer loop\n")
        for p in e:
            f.write("      vertex %s %s %s\n" % tuple(p))
        f.write("    endloop\n")
        f.write("  endfacet\n")
    f.write("endsolid\n")
    if own:
        f.close()


def write_stlb(f,x):
    """Export an x[n,3,3] float array as an binary .stl file."""
    print "Cannot write binary STL files yet!" % fn
    pass


def write_gambit_neutral(fn,nodes,elems):
    print "Cannot write Gambit neutral files yet!" % fn
    pass


def write_off(fn,nodes,elems):
    if nodes.shape[1] != 3 or elems.shape[1] < 3:
        raise runtimeError, "Invalid arguments or shape"
    fil = file(fn,'w')
    fil.write("OFF\n")
    fil.write("%d %d 0\n" % (nodes.shape[0],elems.shape[0]))
    for nod in nodes:
        fil.write("%s %s %s\n" % tuple(nod))
    format = "%d %%d %%d %%d\n" % elems.shape[1]
    for el in elems:
        fil.write(format % tuple(el))
    fil.close()


def write_smesh(fn,nodes,elems):
    tetgen.writeSurface(fn,nodes,elems)


def surface_volume(x,pt=None):
    """Return the volume inside a 3-plex Formex.

    For each element of Formex, return the volume of the tetrahedron
    formed by the point pt (default the center of x) and the 3 points
    of the element.
    """
    x -= x.center()
    a,b,c = [ x[:,i,:] for i in range(3) ]
    d = cross(b,c)
    e = (a*d).sum(axis=-1)
    v = sign(e) * abs(e)/6.
    return v


############################################################################
      
def closedLoop(elems):
    """Check if a set of line elements form a closed curve.

    elems is a connection table of line elements, such as obtained
    from the feModel() method on a plex-2 Formex.

    The return value is a tuple of:
    - return code:
      - 0: the segments form a closed loop
      - 1: the segments form a single non-closed path
      - 2: the segments form multiple not connected paths
    - a new connection table which is equivalent to the input if it forms
    a closed loop. The new table has the elements in order of the loop.
    """
    srt = zeros_like(elems) - 1
    ie = 0
    je = 0
    rev = False
    k = elems[je][0]
    while True:
        if rev:
            srt[ie] = elems[je][[1,0]]
        else:
            srt[ie] = elems[je]
        elems[je] = [ -1,-1 ] # Done with this one
        j = srt[ie][1]
        if j == k:
            break
        w = where(elems == j)
        if w[0].size == 0:
            print "No match found"
            break
        je = w[0][0]
        ie += 1
        rev = w[1][0] == 1
    if any(srt == -1):
        ret = 2
    elif srt[-1][1] != srt[0][0]:
        ret = 1
    else:
        ret = 0
    return ret,srt


def partitionSegmentedCurve(elems):
    """Partition a segmented curve into connected segments.
    
    The input argument is a (nelems,2) shaped array of integers.
    Each row holds the two vertex numbers of a single line segment.

    The return value ia a list of (nsegi,2) shaped array of integers. 
    
    is returned.
    Each border is a (nelems,2) shaped array of integers in
    which the element numbers are ordered.
    """
    borders = []
    while elems.size != 0:
        closed,loop = closedLoop(elems)
        borders.append(loop[loop!=-1].reshape(-1,2))
        elems = elems[elems!=-1].reshape(-1,2)
    return borders


def surfaceInsideLoop(coords,elems):
    """Create a surface inside a closed curve defined by coords and elems.

    coords is a set of coordinates.
    elems is an (nsegments,2) shaped connectivity array defining a set of line
    segments forming a closed loop.

    The return value is coords,elems tuple where
    coords has one more point: the center of th original coords
    elems is (nsegment,3) and defines triangles describing a surface inside
    the original curve.
    """
    coords = Coords(coords)
    if coords.ndim != 2 or elems.ndim != 2 or elems.shape[1] != 2 or elems.max() >= coords.shape[0]:
        raise ValueError,"Invalid argument shape/value"
    x = coords[unique1d(elems)].center().reshape(-1,3)
    n = zeros_like(elems[:,:1]) + coords.shape[0]
    elems = concatenate([elems,n],axis=1)
    coords = Coords.concatenate([coords,x])
    return coords,elems


def fillHole(coords,elems):
    """Fill a hole surrounded by the border defined by coords and elems.
    
    Coords is a (npoints,3) shaped array of floats.
    Elems is a (nelems,2) shaped array of integers representing the border
    element numbers and must be ordered.
    """
    triangles = empty((0,3,),dtype=int)
    while shape(elems)[0] != 3:
        elems,triangle = create_border_triangle(coords,elems)
        triangles = row_stack([triangles,triangle])
    # remaining border
    triangles = row_stack([triangles,elems[:,0]])
    return triangles


def create_border_triangle(coords,elems):
    """Create a triangle within a border.
    
    The triangle is created from the two border elements with
    the sharpest angle.
    Coords is a (npoints,3) shaped array of floats.
    Elems is a (nelems,2) shaped array of integers representing
    the border element numbers and must be ordered.
    A list of two objects is returned: the new border elements and the triangle.
    """
    border = coords[elems]
    # calculate angles between edges of border
    edges1 = border[:,1]-border[:,0]
    edges2 = border[:,0]-border[:,1]
    # roll axes so that edge i of edges1 and edges2 are neighbours
    edges2 = roll(edges2,-1,0)
    len1 = length(edges1)
    len2 = length(edges2)
    inpr = diagonal(inner(edges1,edges2))
    cos = inpr/(len1*len2)
    # angle between 0 and 180 degrees
    angle = arccos(cos)/(pi/180.)
    # determine sharpest angle
    i = where(angle == angle.min())[0][0]
    # create triangle and new border elements
    j = i + 1
    n = shape(elems)[0]
    if j == n:
        j -= n
    old_edges = take(elems,[i,j],0)
    elems = delete(elems,[i,j],0)
    new_edge = asarray([old_edges[0,0],old_edges[-1,1]])
    if j == 0:
        elems = insert(elems,0,new_edge,0)
    else:
        elems = insert(elems,i,new_edge,0)
    triangle = append(old_edges[:,0],old_edges[-1,1].reshape(1),0)
    return elems,triangle


############################################################################
# The TriSurface class

def coordsmethod(f):
    """Define a TriSurface method as the equivalent Coords method.

    This decorator replaces the TriSurface's vertex coordinates with the
    ones resulting from applying the transform f.
    
    The coordinates are changed inplane, so copy them before if you do not
    want them to be lost.
    """
    def newf(self,*args,**kargs):
        repl = getattr(Coords,f.__name__)
        self.coords = repl(self.coords,*args,**kargs)
        newf.__name__ = f.__name__
        newf.__doc__ = repl.__doc__
    return newf


class TriSurface(object):
    """A class for handling triangulated 3D surfaces."""

    def __init__(self,*args):
        """Create a new surface.

        The surface contains ntri triangles, each having 3 vertices with
        3 coordinates.
        The surface can be initialized from one of the following:
        - a (ntri,3,3) shaped array of floats ;
        - a 3-plex Formex with ntri elements ;
        - an (ncoords,3) float array of vertex coordinates and
          an (ntri,3) integer array of vertex numbers ;
        - an (ncoords,3) float array of vertex coordinates,
          an (nedges,2) integer array of vertex numbers,
          an (ntri,3) integer array of edges numbers.

        Internally, the surface is stored in a (coords,edges,faces) tuple.
        """
        self.coords = self.edges = self.faces = None
        self.elems = None
        self.areas = None
        self.normals = None
        self.econn = None
        self.conn = None
        self.eadj = None
        self.adj = None
        if hasattr(self,'edglen'):
            del self.edglen
        self.p = None
        if len(args) == 0:
            return
        if len(args) == 1:
            # a Formex/STL model
            a = args[0]
            if not isinstance(a,Formex):
                a = Formex(a)
            if a.nplex() != 3:
                raise ValueError,"Expected a plex-3 Formex"
            self.coords,self.elems = a.feModel()
            self.p = a.p
            self.refresh()

        else:
            a = Coords(args[0])
            if len(a.shape) != 2:
                raise ValueError,"Expected a 2-dim coordinates array"
            self.coords = a
            
            a = asarray(args[1])
            if a.dtype.kind != 'i' or a.ndim != 2 or a.shape[1]+len(args) != 5:
                raise "Got invalid second argument"
            if a.max() >= self.coords.shape[0]:
                raise ValueError,"Some vertex number is too high"
            if len(args) == 2:
                self.elems = a
                self.refresh()
            elif len(args) == 3:
                self.edges = a

                a = asarray(args[2])
                if not (a.dtype.kind == 'i' and a.ndim == 2 and a.shape[1] == 3):
                    raise "Got invalid third argument"
                if a.max() >= self.edges.shape[0]:
                    raise ValueError,"Some edge number is too high"
                self.faces = a

            else:
                raise RuntimeError,"Too many arguments"
 

    # To keep the data consistent:
    # ANY function that uses self.elems should call self.refresh()
    #     BEFORE using it.
    # ANY function that changes self.elems should
    #     - invalidate self.edges and/or self.faces by setting them to None,
    #     - call self.refresh() AFTER changing it.

    # A safer approach is to only use getElems() and setElems()
    #

    # This may (and probably will) change in future implementations

    def getElems(self):
        """Get the elems data."""
        self.refresh()
        return self.elems

    def setElems(self,elems):
        """Change the elems data."""
        self.edges = self.faces = None
        self.elems = elems
        self.refresh()

    def refresh(self):
        """Make the internal information consistent and complete.

        This function should be called after one of the data fields
        have been changed.
        """
        if self.coords is None:
            return
        if type(self.coords) != Coords:
            self.coords = Coords(self.coords)
        if self.edges is None or self.faces is None:
            self.edges,self.faces = expandElems(self.elems)
        if self.elems is None:
            self.elems = compactElems(self.edges,self.faces)

    def compress(self):
        """Remove all nodes which are not used.

        Normally, the surface definition can hold nodes that are not
        used in the edge/facet tables. They do however influence the
        bounding box of the surface.
        This method will remove all the unconnected nodes.
        """
        newnodes = unique1d(self.edges)
        reverse = -ones(self.ncoords(),dtype=int32)
        reverse[newnodes] = arange(newnodes.size,dtype=int32)
        self.coords = self.coords[newnodes]
        self.edges = reverse[self.edges]
        self.elems = None


    def append(self,S):
        """Merge another surface with self.

        This just merges the data sets, and does not check
        whether the surfaces intersect or are connected!
        This is intended mostly for use inside higher level functions.
        """
        self.refresh()
        S.refresh()
        coords = concatenate([self.coords,S.coords])
        elems = concatenate([self.elems,S.elems+self.ncoords()])
        ## What to do if one of the surfaces has properties, the other one not?
        ## The current policy is to use zero property values for the Surface
        ## without props
        prop = None
        if self.p is not None or S.p is not None:
            if self.p is None:
                self.p = zeros(shape=self.nelems(),dtype=Int)
            if S.p is None:
                p = zeros(shape=S.nelems(),dtype=Int)
            else:
                p = S.p
            prop = concatenate((self.p,p))
        self.__init__(coords,elems)
        self.setProp(prop)


###########################################################################
    #
    #   Return information about a TriSurface
    #

    def ncoords(self):
        return self.coords.shape[0]

    def nedges(self):
        return self.edges.shape[0]

    def nfaces(self):
        return self.faces.shape[0]

    # The following are defined to get a unified interface with Formex
    nelems = nfaces
   
    def nplex(self):
        return 3
    
    def ndim(self):
        return 3

    npoints = ncoords

    def vertices(self):
        return self.coords
    
    def shape(self):
        """Return the number of ;points, edges, faces of the TriSurface."""
        return self.coords.shape[0],self.edges.shape[0],self.faces.shape[0]
       
    def copy(self):
        """Return a (deep) copy of the surface.

        If an index is given, only the specified faces are retained.
        """
        self.refresh()
        S = TriSurface(self.coords.copy(),self.elems.copy())
        if self.p is not None:
            S.setProp(self.p)
        return S
    
    def select(self,idx,compress=True):
        """Return a TriSurface which holds only elements with numbers in ids.

        idx can be a single element number or a list of numbers or
        any other index mechanism accepted by numpy's ndarray
        By default, the vertex list will be compressed to hold only those
        used in the selected elements.
        Setting compress==False will keep all original nodes in the surface.
        """
        self.refresh()
        S = TriSurface(self.coords, self.elems[idx])
        if self.p is not None:
            S.setProp(self.p[idx])
        if compress:
            S.compress()
        return S
    

    # Properties
    def setProp(self,p=None):
        """Create or delete the property array for the TriSurface.

        A property array is a rank-1 integer array with dimension equal
        to the number of elements in the TriSurface.
        You can specify a single value or a list/array of integer values.
        If the number of passed values is less than the number of elements,
        they wil be repeated. If you give more, they will be ignored.
        
        If a value None is given, the properties are removed from the TriSurface.
        """
        if p is None:
            self.p = None
        else:
            p = array(p).astype(Int)
            self.p = resize(p,(self.nelems(),))
        return self

    def prop(self):
        """Return the properties as a numpy array (ndarray)"""
        return self.p

    def maxprop(self):
        """Return the highest property value used, or None"""
        if self.p is None:
            return None
        else:
            return self.p.max()

    def propSet(self):
        """Return a list with unique property values."""
        if self.p is None:
            return None
        else:
            return unique(self.p)

    # The following functions get the corresponding information from
    # the underlying Coords object

    def x(self):
        return self.coords.x()
    def y(self):
        return self.coords.y()
    def z(self):
        return self.coords.z()

    def bbox(self):
        return self.coords.bbox()

    def center(self):
        return self.coords.center()

    def centroid(self):
        return self.coords.centroid()

    def sizes(self):
        return self.coords.sizes()

    def diagonal(self):
        return self.coords.dsize()

    def bsphere(self):
        return self.coords.bsphere()


    def centroids(self):
        """Return the centroids of all elements of the Formex.

        The centroid of an element is the point whose coordinates
        are the mean values of all points of the element.
        The return value is an (nfaces,3) shaped Coords array.
        """
        return self.toFormex().centroids()

    #  Distance

    def distanceFromPlane(self,*args,**kargs):
        return self.coords.distanceFromPlane(*args,**kargs)

    def distanceFromLine(self,*args,**kargs):
        return self.coords.distanceFromLine(*args,**kargs)

    def distanceFromPoint(self,*args,**kargs):
        return self.coords.distanceFromPoint(*args,**kargs)

 
    # Test and clipping functions
    

    def test(self,nodes='all',dir=0,min=None,max=None):
        """Flag elements having nodal coordinates between min and max.

        This function is very convenient in clipping a TriSurface in a specified
        direction. It returns a 1D integer array flagging (with a value 1 or
        True) the elements having nodal coordinates in the required range.
        Use where(result) to get a list of element numbers passing the test.
        Or directly use clip() or cclip() to create the clipped TriSurface
        
        The test plane can be defined in two ways, depending on the value of dir.
        If dir == 0, 1 or 2, it specifies a global axis and min and max are
        the minimum and maximum values for the coordinates along that axis.
        Default is the 0 (or x) direction.

        Else, dir should be compaitble with a (3,) shaped array and specifies
        the direction of the normal on the planes. In this case, min and max
        are points and should also evaluate to (3,) shaped arrays.
        
        nodes specifies which nodes are taken into account in the comparisons.
        It should be one of the following:
        - a single (integer) point number (< the number of points in the Formex)
        - a list of point numbers
        - one of the special strings: 'all', 'any', 'none'
        The default ('all') will flag all the elements that have all their
        nodes between the planes x=min and x=max, i.e. the elements that
        fall completely between these planes. One of the two clipping planes
        may be left unspecified.
        """
        if min is None and max is None:
            raise ValueError,"At least one of min or max have to be specified."
        self.refresh()
        f = self.coords[self.elems]
        if type(nodes)==str:
            nod = range(f.shape[1])
        else:
            nod = nodes

        if type(dir) == int:
            if not min is None:
                T1 = f[:,nod,dir] > min
            if not max is None:
                T2 = f[:,nod,dir] < max
        else:
            if not min is None:
                T1 = f.distanceFromPlane(min,dir) > 0
            if not max is None:
                T2 = f.distanceFromPlane(max,dir) < 0

        if min is None:
            T = T2
        elif max is None:
            T = T1
        else:
            T = T1 * T2
        if len(T.shape) == 1:
            return T
        if nodes == 'any':
            T = T.any(1)
        elif nodes == 'none':
            T = (1-T.any(1)).astype(bool)
        else:
            T = T.all(1)
        return T


    def clip(self,t):
        """Return a TriSurface with all the elements where t>0.

        t should be a 1-D integer array with length equal to the number
        of elements of the TriSurface.
        The resulting TriSurface will contain all elements where t > 0.
        """
        return self.select(t>0)


    def cclip(self,t):
        """This is the complement of clip, returning a TriSurface where t<=0.
        """
        return self.select(t<=0)


    # Some functions for offsetting a surface
    
    def pointNormals(self):
        """Compute the normal vectors in each point of a collection of triangles.
        
        The normal vector in a point is the average of the normal vectors of the neighbouring triangles.
        The normal vectors are normalized.
        """
        con = connectivity.reverseIndex(self.getElems())
        NP = self.areaNormals()[1][con] #self.normal doesn't work here???
        w = where(con == -1)
        NP[w] = 0.
        NPA = NP.sum(axis=1)
        NPA /= sqrt((NPA*NPA).sum(axis=-1)).reshape(-1,1)
        return NPA

    def offset(self,distance=1.):
        """Offset a surface with a certain distance.
        
        All the nodes of the surface are translated over a specified distance along their normal vector.
        This creates a new congruent surface.
        """
        NPA = self.pointNormals()
        coordsNew = self.coords + NPA*distance
        return TriSurface(coordsNew,self.getElems())
    
    # Data conversion
    
    def feModel(self):
        """Return a tuple of nodal coordinates and element connectivity."""
        self.refresh()
        return self.coords,self.elems


    @classmethod
    def read(clas,fn,ftype=None):
        """Read a surface from file.

        If no file type is specified, it is derived from the filename
        extension.
        Currently supported file types:
          - .stl (ASCII or BINARY)
          - .gts
          - .off
          - .neu (Gambit Neutral)
          - .smesh (Tetgen)
        """
        if ftype is None:
            ftype = os.path.splitext(fn)[1]  # deduce from extension
        ftype = ftype.strip('.').lower()
        if ftype == 'off':
            return TriSurface(*read_off(fn))
        elif ftype == 'gts':
            #print "READING GTS"
            ret = read_gts(fn)
            #print ret
            S = TriSurface(*ret)
            #print S.shape()
            return S
        elif ftype == 'stl':
            return TriSurface(*read_stl(fn))
        elif ftype == 'neu':
            return TriSurface(*read_gambit_neutral(fn))
        elif ftype == 'smesh':
            return TriSurface(*tetgen.readTriSurface(fn))
        else:
            raise "Unknown TriSurface type, cannot read file %s" % fn


    def write(self,fname,ftype=None):
        """Write the surface to file.

        If no filetype is given, it is deduced from the filename extension.
        If the filename has no extension, the 'gts' file type is used.
        """
        if ftype is None:
            ftype = os.path.splitext(fname)[1]
        if ftype == '':
            ftype = 'gts'
        else:
            ftype = ftype.strip('.').lower()

        GD.message("Writing surface to file %s" % fname)
        if ftype == 'gts':
            write_gts(fname,self.coords,self.edges,self.faces)
            GD.message("Wrote %s vertices, %s edges, %s faces" % self.shape())
        elif ftype in ['stl','off','neu','smesh']:
            self.refresh()
            if ftype == 'stl':
                write_stla(fname,self.coords[self.elems])
            elif ftype == 'off':
                write_off(fname,self.coords,self.elems)
            elif ftype == 'neu':
                write_gambit_neutral(fname,self.coords,self.elems)
            elif ftype == 'smesh':
                write_smesh(fname,self.coords,self.elems)
            GD.message("Wrote %s vertices, %s elems" % (self.ncoords(),self.nfaces()))
        else:
            print "Cannot save TriSurface as file %s" % fname


    def toFormex(self):
        """Convert the surface to a Formex."""
        self.refresh()
        return Formex(self.coords[self.elems],self.p)


    @coordsmethod
    def scale(self,*args,**kargs):
        pass
    @coordsmethod
    def translate(self,*args,**kargs):
        pass
    @coordsmethod
    def rotate(self,*args,**kargs):
        pass
    @coordsmethod
    def shear(self,*args,**kargs):
        pass
    @coordsmethod
    def reflect(self,*args,**kargs):
        pass
    @coordsmethod
    def affine(self,*args,**kargs):
        pass


####################### TriSurface Data ######################


    def avgVertexNormals(self):
        """Compute the average normals at the vertices."""
        self.refresh()
        return interpolateNormals(self.coords,self.elems,atNodes=True)


    def areaNormals(self):
        """Compute the area and normal vectors of the surface triangles.

        The normal vectors are normalized.
        The area is always positive.

        The values are returned and saved in the object.
        """
        if self.areas is None or self.normals is None:
            self.refresh()
            self.areas,self.normals = areaNormals(self.coords[self.elems])
        return self.areas,self.normals


    def facetArea(self):
        return self.areaNormals()[0]
        

    def area(self):
        """Return the area of the surface"""
        area = self.areaNormals()[0]
        return area.sum()


    def volume(self):
        """Return the enclosed volume of the surface.

        This will only be correct if the surface is a closed manifold.
        """
        self.refresh()
        x = self.coords[self.elems]
        return surface_volume(x).sum()


    def edgeConnections(self):
        """Find the elems connected to edges."""
        if self.econn is None:
            self.econn = connectivity.reverseIndex(self.faces)
        return self.econn
    

    def nodeConnections(self):
        """Find the elems connected to nodes."""
        if self.conn is None:
            self.refresh()
            self.conn = connectivity.reverseIndex(self.elems)
        return self.conn
    

    def nEdgeConnected(self):
        """Find the number of elems connected to edges."""
        return (self.edgeConnections() >=0).sum(axis=-1)
    

    def nNodeConnected(self):
        """Find the number of elems connected to nodes."""
        return (self.nodeConnections() >=0).sum(axis=-1)


    def edgeAdjacency(self):
        """Find the elems adjacent to elems via an edge."""
        if self.eadj is None:
            nfaces = self.nfaces()
            rfaces = self.edgeConnections()
            # this gives all adjacent elements including element itself
            adj = rfaces[self.faces].reshape((nfaces,-1))
            fnr = arange(nfaces).reshape((nfaces,-1))
            # remove the element itself
            self.eadj = adj[adj != fnr].reshape((nfaces,-1))
        return self.eadj


    def nEdgeAdjacent(self):
        """Find the number of adjacent elems."""
        return (self.edgeAdjacency() >=0).sum(axis=-1)


    def nodeAdjacency(self):
        """Find the elems adjacent to elems via one or two nodes."""
        if self.adj is None:
            self.refresh()
            self.adj = connectivity.adjacent(self.elems,self.nodeConnections())
        return self.adj


    def nNodeAdjacent(self):
        """Find the number of adjacent elems."""
        return (self.nodeAdjacency() >=0).sum(axis=-1)


    def surfaceType(self):
        ncon = self.nEdgeConnected()
        nadj = self.nEdgeAdjacent()
        maxcon = ncon.max()
        mincon = ncon.min()
        manifold = maxcon == 2
        closed = mincon == 2
        return manifold,closed,mincon,maxcon


    def borderEdges(self):
        """Detect the border elements of TriSurface.

        The border elements are the edges having less than 2 connected elements.
        Returns a list of edge numbers.
        """
        return self.nEdgeConnected() <= 1
        

    def isManifold(self):
        return self.surfaceType()[0] 


    def isClosedManifold(self):
        stype = self.surfaceType()
        return stype[0] and stype[1]

    def checkBorder(self):
        """Return the border of TriSurface as a set of segments."""
        border = self.edges[self.borderEdges()]
        closed,loop = closedLoop(border)
        print "the border is of type %s" % closed
        print loop


    def fillBorder(self,method=0):
        """If the surface has a single closed border, fill it.

        Filling the border is done by adding a single point inside
        the border and connectin it with all border segments.
        This works well if the border is smooth and nearly planar.
        """
        border = self.edges[self.borderEdges()]
        closed,loop = closedLoop(border)
        if closed == 0:
            if method == 0:
                coords,elems = surfaceInsideLoop(self.coords,loop)
                newS = TriSurface(coords,elems)
            else:
                elems = fillHole(self.coords,loop)
                newS = TriSurface(self.coords,elems)
            self.append(newS)


    def border(self):
        """Return the border of TriSurface as a Plex-2 Formex."""
        return Formex(self.coords[self.edges[self.borderEdges()]])


    def edgeCosAngles(self):
        """Return the cos of the angles over all edges.
        
        The surface should be a manifold (max. 2 elements per edge).
        Edges with only one element get angles = 1.0.
        """
        conn = self.edgeConnections()
        # Bail out if some edge has more than two connected faces
        if conn.shape[1] != 2:
            raise RuntimeError,"TriSurface is not a manifold"
        angles = ones(self.nedges())
        conn2 = (conn >= 0).sum(axis=-1) == 2
        n = self.areaNormals()[1][conn[conn2]]
        angles[conn2] = dotpr(n[:,0],n[:,1])
        return angles


    def edgeAngles(self):
        """Return the angles over all edges (in degrees)."""
        return arccos(self.edgeCosAngles()) / rad


    def data(self):
        """Compute data for all edges and faces."""
        if hasattr(self,'edglen'):
            return
        self.areaNormals()
        edg = self.coords[self.edges]
        edglen = length(edg[:,1]-edg[:,0])
        facedg = edglen[self.faces]
        edgmin = facedg.min(axis=-1)
        edgmax = facedg.max(axis=-1)
        altmin = 2*self.areas / edgmax
        aspect = edgmax/altmin
        self.edglen,self.facedg,self.edgmin,self.edgmax,self.altmin,self.aspect = edglen,facedg,edgmin,edgmax,altmin,aspect 


    def aspectRatio(self):
        self.data()
        return self.aspect

 
    def smallestAltitude(self):
        self.data()
        return self.altmin


    def longestEdge(self):
        self.data()
        return self.edgmax


    def shortestEdge(self):
        self.data()
        return self.edgmin

   
    def stats(self):
        """Return a text with full statistics."""
        bbox = self.bbox()
        manifold,closed,mincon,maxcon = self.surfaceType()
        self.data()
        angles = self.edgeAngles()
        area = self.area()
        if manifold and closed:
            volume = self.volume()
        else:
            volume = 0.0
        print  (
            self.ncoords(),self.nedges(),self.nfaces(),
            bbox[0],bbox[1],
            mincon,maxcon,
            manifold,closed,
            self.areas.min(),self.areas.max(),
            self.edglen.min(),self.edglen.max(),
            self.altmin.min(),self.aspect.max(),
            angles.min(),angles.max(),
            area,volume
            )
        s = """
Size: %d vertices, %s edges and %d faces
Bounding box: min %s, max %s
Minimal/maximal number of connected faces per edge: %s/%s
Surface is manifold: %s; surface is closed: %s
Smallest area: %s; largest area: %s
Shortest edge: %s; longest edge: %s
Shortest altitude: %s; largest aspect ratio: %s
Angle between adjacent faces: smallest: %s; largest: %s
Total area: %s; Enclosed volume: %s   
""" % (
            self.ncoords(),self.nedges(),self.nfaces(),
            bbox[0],bbox[1],
            mincon,maxcon,
            manifold,closed,
            self.areas.min(),self.areas.max(),
            self.edglen.min(),self.edglen.max(),
            self.altmin.min(),self.aspect.max(),
            angles.min(),angles.max(),
            area,volume
            )
        return s


##################  Partitioning a surface #############################


    def edgeFront(self,startat=0,okedges=None,front_increment=1):
        """Generator function returning the frontal elements.

        startat is an element number or list of numbers of the starting front.
        On first call, this function returns the starting front.
        Each next() call returns the next front.
        front_increment determines haw the property increases at each
        frontal step. There is an extra increment +1 at each start of
        a new part. Thus, the start of a new part can always be detected
        by a front not having the property of the previous plus front_increment.
        """
        print "FRONT_INCREMENT %s" % front_increment
        p = -ones((self.nfaces()),dtype=int)
        if self.nfaces() <= 0:
            return
        # Construct table of elements connected to each edge
        conn = self.edgeConnections()
        # Bail out if some edge has more than two connected faces
        if conn.shape[1] != 2:
            GD.warning("Surface is not a manifold")
            return
        # Check size of okedges
        if okedges is not None:
            if okedges.ndim != 1 or okedges.shape[0] != self.nedges():
                raise ValueError,"okedges has incorrect shape"

        # Remember edges left for processing
        todo = ones((self.nedges(),),dtype=bool)
        elems = clip(asarray(startat),0,self.nfaces())
        prop = 0
        while elems.size > 0:
            # Store prop value for current elems
            p[elems] = prop
            yield p

            prop += front_increment

            # Determine border
            edges = unique(self.faces[elems])
            edges = edges[todo[edges]]
            if edges.size > 0:
                # flag edges as done
                todo[edges] = 0
                # take connected elements
                if okedges is None:
                    elems = conn[edges].ravel()
                else:
                    elems = conn[edges[okedges[edges]]].ravel()
                elems = elems[(elems >= 0) * (p[elems] < 0) ]
                if elems.size > 0:
                    continue

            # No more elements in this part: start a new one
            print "NO MORE ELEMENTS"
            elems = where(p<0)[0]
            if elems.size > 0:
                # Start a new part
                elems = elems[[0]]
                prop += 1


    def nodeFront(self,startat=0,front_increment=1):
        """Generator function returning the frontal elements.

        startat is an element number or list of numbers of the starting front.
        On first call, this function returns the starting front.
        Each next() call returns the next front.
        """
        p = -ones((self.nfaces()),dtype=int)
        if self.nfaces() <= 0:
            return
        # Construct table of elements connected to each element
        adj = self.nodeAdjacency()

        # Remember nodes left for processing
        todo = ones((self.npoints(),),dtype=bool)
        elems = clip(asarray(startat),0,self.nfaces())
        prop = 0
        while elems.size > 0:
            # Store prop value for current elems
            p[elems] = prop
            yield p

            prop += front_increment

            # Determine adjacent elements
            elems = unique1d(adj[elems])
            elems = elems[(elems >= 0) * (p[elems] < 0) ]
            if elems.size > 0:
                continue

            # No more elements in this part: start a new one
            elems = where(p<0)[0]
            if elems.size > 0:
                # Start a new part
                elems = elems[[0]]
                prop += 1


    def walkEdgeFront(self,startat=0,nsteps=-1,okedges=None,front_increment=1):
        for p in self.edgeFront(startat=startat,okedges=okedges,front_increment=front_increment):
            print "NSTEPS=%d"%nsteps
            print p
            if nsteps > 0:
                nsteps -= 1
            elif nsteps == 0:
                break
        return p


    def walkNodeFront(self,startat=0,nsteps=-1,front_increment=1):
        for p in self.nodeFront(startat=startat,front_increment=front_increment):
            if nsteps > 0:
                nsteps -= 1
            elif nsteps == 0:
                break
        return p


    def growSelection(self,sel,mode='node',nsteps=1):
        """Grows a selection of a surface.

        p is a single element number or a list of numbers.
        The return value is a list of element numbers obtained by
        growing the front nsteps times.
        The mode argument specifies how a single frontal step is done:
        'node' : include all elements that have a node in common,
        'edge' : include all elements that have an edge in common.
        """
        if mode == 'node':
            p = self.walkNodeFront(startat=sel,nsteps=nsteps)
        elif mode == 'edge':
            p = self.walkEdgeFront(startat=sel,nsteps=nsteps)
        return where(p>=0)[0]
    

    def partitionByEdgeFront(self,okedges,firstprop=0,startat=0):
        """Detects different parts of the surface using a frontal method.

        okedges flags the edges where the two adjacent triangles are to be
        in the same part of the surface.
        startat is a list of elements that are in the first part. 
        The partitioning is returned as a property type array having a value
        corresponding to the part number. The lowest property number will be
        firstprop
        """
        return firstprop + self.walkEdgeFront(startat=startat,okedges=okedges,front_increment=0)
    

    def partitionByNodeFront(self,firstprop=0,startat=0):
        """Detects different parts of the surface using a frontal method.

        okedges flags the edges where the two adjacent triangles are to be
        in the same part of the surface.
        startat is a list of elements that are in the first part. 
        The partitioning is returned as a property type array having a value
        corresponding to the part number. The lowest property number will be
        firstprop
        """
        return firstprop + self.walkNodeFront(startat=startat,front_increment=0)


    def partitionByConnection(self):
        return self.partitionByNodeFront()


    def partitionByAngle(self,angle=180.,firstprop=0,startat=0):
        conn = self.edgeConnections()
        # Flag edges that connect two faces
        conn2 = (conn >= 0).sum(axis=-1) == 2
        # compute normals and flag small angles over edges
        cosangle = cosd(angle)
        n = self.areaNormals()[1][conn[conn2]]
        small_angle = ones(conn2.shape,dtype=bool)
        small_angle[conn2] = dotpr(n[:,0],n[:,1]) >= cosangle
        return firstprop + self.partitionByEdgeFront(small_angle)


    def cutAtPlane(self,*args,**kargs):
        """Cut a surface with a plane."""
        self.__init__(self.toFormex().cutAtPlane(*args,**kargs))


    def connectedElements(self,target,elemlist=None):
        """Return the elements from list connected with target"""
        if elemlist is None:
            A = self
            elemlist = arange(self.nelems())
        else:
            A = self.select(elemlist)
        if target not in elemlist:
            return []
        
        p = A.partitionByConnection()
        prop = p[elemlist == target]
        return elemlist[p==prop]


########################## Methods using GTS #############################

    def check(self,verbose=False):
        """Check the surface using gtscheck."""
        cmd = 'gtscheck'
        if verbose:
            cmd += ' -v'
        tmp = tempfile.mktemp('.gts')
        GD.message("Writing temp file %s" % tmp)
        self.write(tmp,'gts')
        GD.message("Checking with command\n %s" % cmd)
        cmd += ' < %s' % tmp
        sta,out = runCommand(cmd,False)
        os.remove(tmp)
        GD.message(out)
        if sta == 0:
            GD.message('The surface is a closed, orientable non self-intersecting manifold')
 

    def split(self,base,verbose=False):
        """Check the surface using gtscheck."""
        cmd = 'gtssplit -v %s' % base
        if verbose:
            cmd += ' -v'
        tmp = tempfile.mktemp('.gts')
        GD.message("Writing temp file %s" % tmp)
        self.write(tmp,'gts')
        GD.message("Splitting with command\n %s" % cmd)
        cmd += ' < %s' % tmp
        sta,out = runCommand(cmd)
        os.remove(tmp)
        if sta or verbose:
            GD.message(out)
   

    def coarsen(self,min_edges=None,max_cost=None,
                mid_vertex=False, length_cost=False, max_fold = 1.0,
                volume_weight=0.5, boundary_weight=0.5, shape_weight=0.0,
                progressive=False, log=False, verbose=False):
        """Coarsen the surface using gtscoarsen."""
        if min_edges is None and max_cost is None:
            min_edges = self.nedges() / 2
        cmd = 'gtscoarsen'
        if min_edges:
            cmd += ' -n %d' % min_edges
        if max_cost:
            cmd += ' -c %d' % max_cost
        if mid_vertex:
            cmd += ' -m'
        if length_cost:
            cmd += ' -l'
        if max_fold:
            cmd += ' -f %f' % max_fold
        cmd += ' -w %f' % volume_weight
        cmd += ' -b %f' % boundary_weight
        cmd += ' -s %f' % shape_weight
        if progressive:
            cmd += ' -p'
        if log:
            cmd += ' -L'
        if verbose:
            cmd += ' -v'
        tmp = tempfile.mktemp('.gts')
        tmp1 = tempfile.mktemp('.gts')
        GD.message("Writing temp file %s" % tmp)
        self.write(tmp,'gts')
        GD.message("Coarsening with command\n %s" % cmd)
        cmd += ' < %s > %s' % (tmp,tmp1)
        sta,out = runCommand(cmd)
        os.remove(tmp)
        if sta or verbose:
            GD.message(out)
        GD.message("Reading coarsened model from %s" % tmp1)
        self.__init__(*read_gts(tmp1))        
        os.remove(tmp1)
   

    def refine(self,max_edges=None,min_cost=None,
               log=False, verbose=False):
        """Refine the surface using gtsrefine."""
        if max_edges is None and min_cost is None:
            max_edges = self.nedges() * 2
        cmd = 'gtsrefine'
        if max_edges:
            cmd += ' -n %d' % max_edges
        if min_cost:
            cmd += ' -c %d' % min_cost
        if log:
            cmd += ' -L'
        if verbose:
            cmd += ' -v'
        tmp = tempfile.mktemp('.gts')
        tmp1 = tempfile.mktemp('.gts')
        GD.message("Writing temp file %s" % tmp)
        self.write(tmp,'gts')
        GD.message("Refining with command\n %s" % cmd)
        cmd += ' < %s > %s' % (tmp,tmp1)
        sta,out = runCommand(cmd)
        os.remove(tmp)
        if sta or verbose:
            GD.message(out)
        GD.message("Reading refined model from %s" % tmp1)
        self.__init__(*read_gts(tmp1))        
        os.remove(tmp1)


    def smooth(self,lambda_value=0.5,n_iterations=2,
               fold_smoothing=None,verbose=False):
        """Smooth the surface using gtssmooth."""
        cmd = 'gtssmooth'
        if fold_smoothing:
            cmd += ' -f %s' % fold_smoothing
        cmd += ' %s %s' % (lambda_value,n_iterations)
        if verbose:
            cmd += ' -v'
        tmp = tempfile.mktemp('.gts')
        tmp1 = tempfile.mktemp('.gts')
        GD.message("Writing temp file %s" % tmp)
        self.write(tmp,'gts')
        GD.message("Smoothing with command\n %s" % cmd)
        cmd += ' < %s > %s' % (tmp,tmp1)
        sta,out = runCommand(cmd)
        os.remove(tmp)
        if sta or verbose:
            GD.message(out)
        GD.message("Reading smoothed model from %s" % tmp1)
        self.__init__(*read_gts(tmp1))        
        os.remove(tmp1)


#### THIS FUNCTION RETURNS A NEW SURFACE
#### WE MIGHT DO THIS IN FUTURE FOR ALL SURFACE PROCESSING

    def boolean(self,surf,op,inter=False,check=False,verbose=False):
        """Perform a boolean operation with surface surf.

        """
        ops = {'+':'union', '-':'diff', '*':'inter'}
        cmd = 'gtsset'
        if inter:
            cmd += ' -i'
        if check:
            cmd += ' -s'
        if verbose:
            cmd += ' -v'
        cmd += ' '+ops[op]
        tmp = tempfile.mktemp('.gts')
        tmp1 = tempfile.mktemp('.gts')
        tmp2 = tempfile.mktemp('.gts')
        GD.message("Writing temp file %s" % tmp)
        self.write(tmp,'gts')
        GD.message("Writing temp file %s" % tmp1)
        surf.write(tmp1,'gts')
        GD.message("Performing boolean operation with command\n %s" % cmd)
        cmd += ' %s %s > %s' % (tmp,tmp1,tmp2)
        sta,out = runCommand(cmd)
        os.remove(tmp)
        os.remove(tmp1)
        if sta or verbose:
            GD.message(out)
        GD.message("Reading result from %s" % tmp2)
        S = TriSurface.read(tmp2)        
        os.remove(tmp2)
        return S



##########################################################################
################# Non-member and obsolete functions ######################

def read_error(cnt,line):
    """Raise an error on reading the stl file."""
    raise RuntimeError,"Invalid .stl format while reading line %s\n%s" % (cnt,line)


def degenerate(area,norm):
    """Return a list of the degenerate faces according to area and normals.

    A face is degenerate if its surface is less or equal to zero or the
    normal has a nan.
    """
    return unique(concatenate([where(area<=0)[0],where(isnan(norm))[0]]))


def read_stla(fn,dtype=Float,large=False,guess=True):
    """Read an ascii .stl file into an [n,3,3] float array.

    If the .stl is large, read_ascii_large() is recommended, as it is
    a lot faster.
    """
    if large:
        return read_ascii_large(fn,dtype=dtype)
    if guess:
        n = countLines(fn) / 7 # ASCII STL has 7 lines per triangle
    else:
        n = 100
    f = file(fn,'r')
    a = zeros(shape=[n,3,3],dtype=dtype)
    x = zeros(shape=[3,3],dtype=dtype)
    i = 0
    j = 0
    cnt = 0
    finished = False
    for line in f:
        cnt += 1
        s = line.strip().split()
        if s[0] == 'vertex':
            if j >= 3:
                read_error(cnt,line)
            x[j] = map(float,s[1:4])
            j += 1
        elif s[0] == 'outer':
            j = 0
        elif s[0] == 'endloop':
            a[i] = x
        elif s[0] == 'facet':
            if i >= a.shape[0]:
                # increase the array size
                a.resize([2*a.shape[0],3,3])
        elif s[0] == 'endfacet':
            i += 1
        elif s[0] == 'solid':
            pass
        elif s[0] == 'endsolid':
            finished = True
            break
    if f:    
        f.close()
    if finished:
        return a[:i]
    raise RuntimeError,"Incorrect stl file: read %d lines, %d facets" % (cnt,i)
        


def read_ascii_large(fn,dtype=Float):
    """Read an ascii .stl file into an [n,3,3] float array.

    This is an alternative for read_ascii, which is a lot faster on large
    STL models.
    It requires the 'awk' command though, so is probably only useful on
    Linux/UNIX. It works by first transforming  the input file to a
    .nodes file and then reading it through numpy's fromfile() function.
    """
    tmp = '%s.nodes' % fn
    runCommand("awk '/^[ ]*vertex[ ]+/{print $2,$3,$4}' '%s' | d2u > '%s'" % (fn,tmp))
    nodes = fromfile(tmp,sep=' ',dtype=dtype).reshape((-1,3,3))
    return nodes


def off_to_tet(fn):
    """Transform an .off model to tetgen (.node/.smesh) format."""
    GD.message("Transforming .OFF model %s to tetgen .smesh" % fn)
    nodes,elems = read_off(fn)
    write_node_smesh(changeExt(fn,'.smesh'),nodes,elems)


def magic_numbers(elems,magic):
    elems = elems.astype(int64)
    elems.sort(axis=1)
    mag = ( elems[:,0] * magic + elems[:,1] ) * magic + elems[:,2]
    return mag


def demagic(mag,magic):
    first2,third = mag / magic, mag % magic
    first,second = first2 / magic, first2 % magic
    return column_stack([first,second,third]).astype(int32)


def find_row(mat,row,nmatch=None):
    """Find all rows in matrix matching given row."""
    if nmatch is None:
        nmatch = mat.shape[1]
    return where((mat == row).sum(axis=1) == nmatch)[0]


def find_nodes(nodes,coords):
    """Find nodes with given coordinates in a node set.

    nodes is a (nnodes,3) float array of coordinates.
    coords is a (npts,3) float array of coordinates.

    Returns a (n,) integer array with ALL the node numbers matching EXACTLY
    ALL the coordinates of ANY of the given points.
    """
    return concatenate([ find_row(nodes,c) for c in coords])


def find_first_nodes(nodes,coords):
    """Find nodes with given coordinates in a node set.

    nodes is a (nnodes,3) float array of coordinates.
    coords is a (npts,3) float array of coordinates.

    Returns a (n,) integer array with THE FIRST node number matching EXACTLY
    ALL the coordinates of EACH of the given points.
    """
    res = [ find_row(nodes,c) for c in coords ]
    return array([ r[0] for r in res ])



def find_triangles(elems,triangles):
    """Find triangles with given node numbers in a surface mesh.

    elems is a (nelems,3) integer array of triangles.
    triangles is a (ntri,3) integer array of triangles to find.
    
    Returns a (ntri,) integer array with the triangles numbers.
    """
    magic = elems.max()+1

    mag1 = magic_numbers(elems,magic)
    mag2 = magic_numbers(triangles,magic)

    nelems = elems.shape[0]
    srt = mag1.argsort()
    old = arange(nelems)[srt]
    mag1 = mag1[srt]
    pos = mag1.searchsorted(mag2)
    tri = where(mag1[pos]==mag2, old[pos], -1)
    return tri
    

def remove_triangles(elems,remove):
    """Remove triangles from a surface mesh.

    elems is a (nelems,3) integer array of triangles.
    remove is a (nremove,3) integer array of triangles to remove.
    
    Returns a (nelems-nremove,3) integer array with the triangles of
    nelems where the triangles of remove have been removed.
    """
    #print elems,remove
    GD.message("Removing %s out of %s triangles" % (remove.shape[0],elems.shape[0]))
    magic = elems.max()+1

    mag1 = magic_numbers(elems,magic)
    mag2 = magic_numbers(remove,magic)

    mag1.sort()
    mag2.sort()

    nelems = mag1.shape[0]

    pos = mag1.searchsorted(mag2)
    mag1[pos] = -1
    mag1 = mag1[mag1 >= 0]

    elems = demagic(mag1,magic)
    GD.message("Actually removed %s triangles, leaving %s" % (nelems-mag1.shape[0],elems.shape[0]))

    return elems


### Some simple surfaces ###

def Rectangle(nx,ny):
    """Create a plane rectangular surface consisting of a nx,ny grid."""
    F = Formex(mpattern('12-34')).replic2(nx,ny,1,1)    
    return TriSurface(F)

def Cube():
    """Create a surface in the form of a cube"""
    back = Formex(mpattern('12-34'))
    fb = back.reverse() + back.translate(2,1)
    faces = fb + fb.rollAxes(1) + fb.rollAxes(2)
    return TriSurface(faces)

def Sphere(level=4,verbose=False,filename=None):
    """Create a spherical surface by caling the gtssphere command.

    If a filename is given, it is stored under that name, else a temporary
    file is created.
    Beware: this may take a lot of time if level is 8 or higher.
    """
    cmd = 'gtssphere '
    if verbose:
        cmd += ' -v'
    cmd += ' %s' % level
    if filename is None:
        tmp = tempfile.mktemp('.gts')
    else:
        tmp = filename
    cmd += ' > %s' % tmp
    GD.message("Writing file %s" % tmp)
    sta,out = runCommand(cmd)
    if sta or verbose:
        GD.message(out)
    GD.message("Reading model from %s" % tmp)
    S = TriSurface.read(tmp)
    if filename is None:
        os.remove(tmp)
    return S


# For compatibility

#Surface = TriSurface

if __name__ == '__main__':
    f = file('unit_triangle.stl','r')
    a = read_ascii(f)
    f.close()
    print a
    
# End
