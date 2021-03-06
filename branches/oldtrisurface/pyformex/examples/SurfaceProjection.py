#!/usr/bin/env pyformex
# $Id$

"""IntersectTriSurfaceWithLines.py

level = 'normal'
topics = ['surface']
techniques = ['transform','projection','dialog','image']
original idea: gianluca

.. Description

IntersectTriSurfaceWithLines
----------------------------

This example illustrates the use of intersectSurfaceWithLines.

"""
from plugins.trisurface import TriSurface
import elements
from connectivity import inverseIndex
from gui.widgets import ImageView,simpleInputItem as I
from gui.imagecolor import *


def selectImage(fn):
    fn = askImageFile(fn)
    if fn:
        viewer.showImage(fn)
    return fn


def loadImage(fn):
    global image, scaled_image
    image = QImage(fn)
    if image.isNull():
        warning("Could not load image '%s'" % fn)
        return None

    return image.width(),image.height()


def makeGrid(nx,ny,eltype):
    """Create a 2D grid of nx*ny elements of type eltype.

    The grid is scaled to unit size and centered.
    """
    elem = getattr(elements,eltype)
    x = array(elem.vertices)
    e = array(elem.element)
    return Formex([x[e]],eltype=eltype).replic2(nx,ny).resized(1.).centered()


clear()
smooth()
lights(True)
transparent(False)
view('iso')

image = None
scaled_image = None

# read the teapot surface
T = TriSurface.read(getcfg('datadir')+'/teapot.off')
xmin,xmax = T.bbox()
T= T.translate(-T.center()).scale(1./(xmax[0]-xmin[0])).scale(4.).setProp(2)
draw(T)

# default image file
filename = getcfg('datadir')+'/benedict_6.jpg'
viewer = ImageView(filename)

px,py = 5,5 #control points for projection of patches
kx,ky = 60,50 #number of cells in each patch

res = askItems([
    I('filename',filename,text='Image file',itemtype='button',func=selectImage),
#    viewer,   # uncomment this line to add the image previewer
    I('px',px,text='Number of patches in x-direction'),
    I('py',py,text='Number of patches in y-direction'),
    I('kx',kx,text='Width of a patch in pixels'), 
    I('ky',ky,text='Height of a patch in pixels'), 
    ])

if not res:
    exit()

globals().update(res)

nx,ny = px*kx,py*ky # pixels
print 'the picture is reconstructed with %d x %d pixels'%(nx, ny)

F = Formex(mpattern('123')).replic2(nx,ny).centered()
if image is None:
    print "Loading image"
    wpic, hpic=loadImage(filename)

if image is None:
    exit()

# Create the colors
color,colortable = image2glcolor(image.scaled(nx,ny))
# Reorder by patch
pcolor = color.reshape((py,ky,px,kx,3)).swapaxes(1,2).reshape(-1,kx*ky,3)
print pcolor.shape

mH = makeGrid(px,py,'Quad8')

try:
    hpic, wpic
    ratioYX = float(hpic)/wpic
    mH = mH.scale(ratioYX,1) # Keep original aspect ratio
except: pass

mH0 = mH.translate([-0.5,0.1,2.])
mH1 = mH.rotate(-30.,0).scale(0.5).translate([0.,-.7,-2.])

dg0 = draw(mH0,mode='wireframe')
dg1 = draw(mH1,mode='wireframe')
zoomAll()
zoom(0.5)
pause('Create %s x %s patches at both sides of the surface > STEP' % (px,py))

# Create the transforms
base = makeGrid(1,1,'Quad8').coords[0]
patch = makeGrid(kx,ky,'Quad4').toMesh()


def drawImage(grid):
    """Draw the image on the specified patch grid.

    grid is a Formex with px*py Quad8 elements.
    Each element of grid will be filled by a kx*jy patch of colors.
    """
    mT = [ patch.isopar('quad8',x,base) for x in grid.coords ]
    return [ draw(i,color=c,bbox='last') for i,c in zip (mT,pcolor)]


d0 = drawImage(mH0)
d1 = drawImage(mH1)


def intersectSurfaceWithSegments2(s1, segm, atol=1.e-5, max1xperline=True):
    """it takes a TriSurface ts and a set of segments (-1,2,3) and intersect the segments with the TriSurface.
    It returns the points of intersections and, for each point, the indices of the intersected segment and triangle. If max1xperline is True, only 1 intersection per line is returned (in order to remove multiple intersections due to the tolerance) together with the index of line and triangle (at the moment the selection of one intersection among the others is random: it does not take into account the distances). If some segments do not intersect the surface, their indices are also returned."""
    segm = segm.coords
    p, il, it=trisurface.intersectSurfaceWithLines(s1, segm[:, 0], normalize(segm[:, 1]-segm[:, 0]))
    win= length(p-segm[:, 0][il])+ length(p-segm[:, 1][il])< length(segm[:, 1][il]-segm[:, 0][il])+atol
    px, ilx, itx=p[win], il[win], it[win]
    if max1xperline:
        ip= inverseIndex(ilx.reshape(-1, 1))
        sp=sort(ip, axis=1)[:, -1]
        w= where(sp>-1)[0]
        sw=sp[w]
        return px[sw], w, itx[sw], delete( arange(len(segm)),  w)
    else:return px, ilx, itx




x = connect([mH0.points(), mH1.points()])

dx = draw(x)
pause('Creating intersection with surface > STEP')

pts, il, it, mil=intersectSurfaceWithSegments2(T, x, max1xperline=True)

if len(x) != len(pts):
    print "Some of the lines do not intersect the surface:"
    print " %d lines, %d intersections %d missing" % (len(x),len(pts),len(mil))
    exit()
    
dp=draw(pts, marksize=6, color='white')
print pts.shape
mH2 = Formex(pts.reshape(-1,8,3))

pause('Finally use the intersection points to map the image > STEP')
undraw(dp)
undraw(dx)
undraw(d0)
undraw(d1)
undraw(dg0)
undraw(dg1)

d0 = drawImage(mH2.trl([0.,0.,0.01]))
# small translation to make sure the image is above the surface, not cutting it
view('front')
zoomAll()

# End
