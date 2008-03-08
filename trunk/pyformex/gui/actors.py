# $Id$
##
## This file is part of pyFormex 0.6 Release Fri Nov 16 22:39:28 2007
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""OpenGL actors for populating the 3D scene."""

import globaldata as GD

from OpenGL import GL,GLU

from drawable import *
from formex import *
from plugins import elements
from plugins.surface import Surface
from plugins.connectivity import reverseIndex

import timer



### Actors ###############################################

class Actor(Drawable):
    """An Actor is anything that can be drawn in an OpenGL 3D Scene.

    The visualisation of the Scene Actors is dependent on camera position and
    angles, clipping planes, rendering mode and lighting.
    
    An Actor subclass should minimally reimplement the following methods:
      bbox(): return the actors bounding box.
      drawGL(mode): to draw the actor. Takes a mode argument so the
        drawing function can act differently depending on the mode. There are
        currently 5 modes: wireframe, flat, smooth, flatwire, smoothwire.
      drawGL should only contain OpenGL calls that are allowed inside a display
        list. This may include calling the display list of another actor but NOT
        creating a new display list.
    """
    
    def __init__(self):
        Drawable.__init__(self)


class TranslatedActor(Actor):
    """An Actor translated to another position."""

    def __init__(self,A,trl=(0.,0.,0.)):
        Actor.__init__(self)
        self.actor = A
        self.trans = A.trans
        self.trl = asarray(trl)

    def bbox(self):
        return self.actor.bbox() + self.trl

    def redraw(self,mode,color=None):
        self.actor.redraw(mode,color)
        Drawable.redraw(self,mode,color)

    def drawGL(self,mode,color=None):
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glTranslate(*self.trl)
        self.actor.use_list()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()


     
class RotatedActor(Actor):
    """An Actor rotated to another position."""

    def __init__(self,A,normal=(1.,0.,0.),twist=0.0):
        """Created a new rotated actor.

        The rotation is specified by the direction of the local 0 axis
        of the actor.
        """
        Actor.__init__(self)
        self.actor = A
        self.trans = A.trans
        self.rot = rotMatrix(normal,4)

    def bbox(self):
        return self.actor.bbox() # TODO : rotate the bbox !

    def redraw(self,mode,color=None):
        self.actor.redraw(mode,color)
        Drawable.redraw(self,mode,color)

    def drawGL(self,mode,color=None):
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glMultMatrixf(self.rot)
        self.actor.use_list()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()


class CubeActor(Actor):
    """An OpenGL actor with cubic shape and 6 colored sides."""

    def __init__(self,size,color=[red,cyan,green,magenta,blue,yellow]):
        FacingActor.__init__(self)
        self.size = size
        self.color = color

    def bbox(self):
        return (0.5 * self.size) * array([[-1.,-1.,-1.],[1.,1.,1.]])

    def drawGL(self,mode='wireframe',color=None):
        """Draw the cube."""
        drawCube(self.size,self.color)


# This could be subclassed from GridActor
class BboxActor(Actor):
    """Draws a bbox."""

    def __init__(self,bbox,color=None,linewidth=None):
        Actor.__init__(self)
        self.color = color
        self.linewidth = linewidth
        self.bb = bbox
        self.vertices = array(elements.Hex8.vertices) * (bbox[1]-bbox[0]) + bbox[0]
        #print "VERTICES",self.vertices
        self.edges = array(elements.Hex8.edges)
        self.facets = array(elements.Hex8.faces)

    def bbox():
        return self.bb

    def drawGL(self,mode,color=None):
        """Always draws a wireframe model of the bbox."""
        if color is None:
            color = self.color
        if self.linewidth is not None:
            GL.glLineWidth(self.linewidth)
        drawLineElems(self.vertices,self.edges,color)
            

class TriadeActor(Actor):
    """An OpenGL actor representing a triade of global axes."""

    def __init__(self,size,color=[red,green,blue,cyan,magenta,yellow]):
        Actor.__init__(self)
        self.size = size
        self.color = color

    def bbox(self):
        return (0.5 * self.size) * array([[0.,0.,0.],[1.,1.,1.]])

    def drawGL(self,mode='wireframe',color=None):
        """Draw the triade."""
        #GL.glShadeModel(GL.GL_FLAT)
        #GL.glPolygonMode(GL.GL_FRONT, GL.GL_FILL)
        #GL.glPolygonMode(GL.GL_BACK, GL.GL_LINE)
        GL.glBegin(GL.GL_TRIANGLES)
        GL.glColor(*self.color[0])
        GL.glVertex3f(0.0,0.0,0.0)
        GL.glVertex3f(1.0,0.0,0.0)
        GL.glVertex3f(0.0,1.0,0.0)
        GL.glColor(*self.color[1])
        GL.glVertex3f(0.0,0.0,0.0)
        GL.glVertex3f(0.0,1.0,0.0)
        GL.glVertex3f(0.0,0.0,1.0)
        GL.glColor(*self.color[2])
        GL.glVertex3f(0.0,0.0,0.0)
        GL.glVertex3f(0.0,0.0,1.0)
        GL.glVertex3f(1.0,0.0,0.0)
##        GL.glColor(*self.color[3])
##        GL.glVertex3f(0.0,0.0,0.0)
##        GL.glVertex3f(0.0,1.0,0.0)
##        GL.glVertex3f(1.0,0.0,0.0)
##        GL.glColor(*self.color[4])
##        GL.glVertex3f(0.0,0.0,0.0)
##        GL.glVertex3f(0.0,0.0,1.0)
##        GL.glVertex3f(0.0,1.0,0.0)
##        GL.glColor(*self.color[5])
##        GL.glVertex3f(0.0,0.0,0.0)
##        GL.glVertex3f(1.0,0.0,0.0)
##        GL.glVertex3f(0.0,0.0,1.0)
        GL.glEnd()
        GL.glBegin(GL.GL_LINES)
        GL.glColor3f(*black)
        GL.glVertex3f(0.0,0.0,0.0)
        GL.glVertex3f(2.0,0.0,0.0)
        GL.glVertex3f(0.0,0.0,0.0)
        GL.glVertex3f(0.0,2.0,0.0)
        GL.glVertex3f(0.0,0.0,0.0)
        GL.glVertex3f(0.0,0.0,2.0)
        GL.glEnd()

  
class GridActor(Actor):
    """Draws a (set of) grid(s) in one of the coordinate planes."""

    def __init__(self,nx=(1,1,1),ox=(0.0,0.0,0.0),dx=(1.0,1.0,1.0),linecolor=black,linewidth=None,planecolor=white,alpha=0.2,lines=True,planes=True):
        Actor.__init__(self)
        self.linecolor = saneColor(linecolor)
        self.planecolor = saneColor(planecolor)
        self.linewidth = linewidth
        self.alpha = alpha
        self.trans = True
        self.lines = lines
        self.planes = planes
        self.nx = asarray(nx)
        self.x0 = asarray(ox)
        self.x1 = self.x0 + self.nx * asarray(dx)

    def bbox(self):
        return array([self.x0,self.x1])

    def drawGL(self,mode,color=None):
        """Draw the grid."""

        #print "BBOX %s" % self.bbox()
        if self.lines:
            if self.linewidth:
                GL.glLineWidth(self.linewidth)
            glColor(self.linecolor)
            drawGridLines(self.x0,self.x1,self.nx)
        
        if self.planes:
            glColor(self.planecolor,self.alpha)
            drawGridPlanes(self.x0,self.x1,self.nx)

            
class CoordPlaneActor(Actor):
    """Draws a set of 3 coordinate planes."""

    def __init__(self,nx=(1,1,1),ox=(0.0,0.0,0.0),dx=(1.0,1.0,1.0),linecolor=black,linewidth=None,planecolor=white,alpha=0.5,lines=True,planes=True):
        Actor.__init__(self)
        self.linecolor = saneColor(linecolor)
        self.planecolor = saneColor(planecolor)
        self.linewidth = linewidth
        self.alpha = alpha
        self.trans = True
        self.lines = lines
        self.planes = planes
        self.nx = asarray(nx)
        self.x0 = asarray(ox)
        self.x1 = self.x0 + self.nx * asarray(dx)

    def bbox(self):
        return array([self.x0,self.x1])

    def drawGL(self,mode,color=None):
        """Draw the grid."""

        for i in range(3):
            nx = self.nx.copy()
            nx[i] = 0
            
            if self.lines:
                glColor(self.linecolor)
                drawGridLines(self.x0,self.x1,nx)

            if self.planes:
                glColor(self.planecolor,self.alpha)
                drawGridPlanes(self.x0,self.x1,nx)

            
class PlaneActor(Actor):
    """A plane in a 3D scene."""

    def __init__(self,nx=(2,2,2),ox=(0.,0.,0.),size=(0.0,1.0,1.0),linecolor=black,linewidth=None,planecolor=white,alpha=0.5,lines=True,planes=True):
        """A plane perpendicular to the x-axis at the origin."""
        Actor.__init__(self)
        self.linecolor = saneColor(linecolor)
        self.planecolor = saneColor(planecolor)
        self.linewidth = linewidth
        self.alpha = alpha
        self.trans = True
        self.lines = lines
        self.planes = planes
        self.nx = asarray(nx)
        ox = asarray(ox)
        sz = 0.5*asarray(size)
        self.x0,self.x1 = ox-sz, ox+sz

    def bbox(self):
        return array([self.x0,self.x1])

    def drawGL(self,mode,color=None):
        """Draw the grid."""

        for i in range(3):
            nx = self.nx.copy()
            nx[i] = 0
            
            if self.lines:
                if color is None:
                    glColor(self.linecolor)
                else:
                    glColor(color)
                drawGridLines(self.x0,self.x1,nx)

            if self.planes:
                glColor(self.planecolor,self.alpha)
                drawGridPlanes(self.x0,self.x1,nx)
        

###########################################################################

quadratic_curve_ndiv = 8


class FormexActor(Actor,Formex):
    """An OpenGL actor which is a Formex."""
    mark = False

    def __init__(self,F,color=None,colormap=None,bkcolor=None,bkcolormap=None,linewidth=None,marksize=None,eltype=None,alpha=1.0,color1=None,color2=None):
        """Create a multicolored Formex actor.

        The colors argument specifies a list of OpenGL colors for each
        of the property values in the Formex. If the list has less
        values than the PropSet, it is wrapped around. It can also be
        a single OpenGL color, which will be used for all elements.
        For surface type elements, a bkcolor color can be given for
        the backside (inside) of the surface. Default will be the same
        as the front color.
        The user can specify a linewidth to be used when drawing
        in wireframe mode.

        plex-1: if eltype == 'point3D', a 3D cube with 6 differently colored
                faces is drawn, else a fixed size dot is drawn.
        """
        Actor.__init__(self)
        # Initializing with F alone gives problems with self.p !
        Formex.__init__(self,F.f,F.p)
        self.eltype = eltype
        
        self.setLineWidth(linewidth)
        self.setColor(color,colormap)
        self.setBkColor(bkcolor,bkcolormap)
        self.setAlpha(alpha)
        
        if self.nplex() == 1:
            self.setMarkSize(marksize)
        self.list = None
        self.color1 = None
        self.color2 = None
        if color1 is not None:
            self.color1,self.colormap = saneColorSet(color1,None,self.nelems())
        if color2 is not None:
            self.color2,self.colormap = saneColorSet(color2,None,self.nelems())

    def atype(self):
        return 'Formex'

    def setColor(self,color=None,colormap=None):
        """Set the color of the Actor."""
        self.color,self.colormap = saneColorSet(color,colormap,self.nelems())


    def setBkColor(self,color=None,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor,self.bkcolormap = saneColorSet(color,colormap,self.nelems())

    def setAlpha(self,alpha):
        """Set the Actors alpha value."""
        self.alpha = float(alpha)
        self.trans = self.alpha < 1.0
        #if self.trans:
        #    GD.debug("Setting Actor's ALPHA value to %f" % alpha)


    def setMarkSize(self,marksize):
        """Set the mark size.

        The mark size is currently only used with plex-1 Formices.
        """
#### DEFAULT MARK SIZE SHOULD BECOME A CANVAS SETTING!!
        
        if marksize is None:
            marksize = 4.0 # default size 
        if self.eltype == 'point3d':
            # ! THIS SHOULD BE SET FROM THE SCENE SIZE
            #   RATHER THAN FORMEX SIZE 
            marksize = self.diagonal() * marksize
            if marksize <= 0.0:
                marksize = 1.0
            self.setMark(marksize,"cube")
        self.marksize = marksize


    def setMark(self,size,type):
        """Create a symbol for drawing 3D points."""
        self.mark = GL.glGenLists(1)
        GL.glNewList(self.mark,GL.GL_COMPILE)
        if type == "sphere":
            drawSphere(size)
        else:
            drawCube(size)
        GL.glEndList()
        

    #bbox = Formex.bbox


    def drawGL(self,mode='wireframe',color=None,colormap=None,alpha=None):
        """Draw the formex.

        if color is None, it is drawn with the color specified on creation.
        if color == 'prop' and a colormap was installed, props define color.
        else, color should be an array of RGB values, either with shape
        (3,) for a single color, or (nelems,3) for differently colored
        elements 

        if mode ends with wire (smoothwire or flatwire), two drawing
        operations are done: one with wireframe and color black, and
        one with mode[:-4] and self.color.
        """

        if mode.endswith('wire'):
            self.drawGL(mode=mode[:-4],color=color,colormap=None)
            self.drawGL(mode='wireframe',color=asarray(black),colormap=None)
            return

        if alpha is None:
            alpha = self.alpha
            
        color1 = None
        color2 = None
        
        if color is None:  
            color,colormap = self.color,self.colormap
        else:
            color,colormap = saneColorSet(color,colormap,self.nelems())
        
        if color is None:  # no color
            pass
        
        elif color.dtype.kind == 'f' and color.ndim == 1:  # single color
            GL.glColor(append(color,alpha))
            color = None

        elif color.dtype.kind == 'i': # color index
            color = colormap[color]

        else: # a full color array : use as is
            color1 = self.color1
            color2 = self.color2

        if self.linewidth is not None:
            GL.glLineWidth(self.linewidth)
            
        nnod = self.nplex()
        if nnod == 1:
            x = self.f.reshape((-1,3))
            if self.eltype == 'point3d':
                drawAtPoints(x,self.mark,color)
            else:
                drawPoints(x,self.marksize,color)
                
        elif nnod == 2:
            drawLines(self.f,color,color1)
        
        elif nnod == 3 and self.eltype == 'curve':
            drawQuadraticCurves(self.f,color,n=quadratic_curve_ndiv)
            
        elif (nnod == 3 or nnod == 4) and self.eltype == 'nurbs':
            drawNurbsCurves(self.f,color)
            
        elif mode=='wireframe' :
            print "DRAWING WITH TYPE %s" % self.eltype
            if self.eltype == 'tet':
                edges = [ 0,1, 0,2, 0,3, 1,2, 1,3, 2,3 ]
                coords = self.f[:,edges,:]
                drawEdges(coords,color)
            elif self.eltype == 'wed':
                edges = [ 0,1, 0,2, 0,3, 1,2, 1,4, 2,5, 3,4, 3,5, 4,5]
                coords = self.f[:,edges,:]
                drawEdges(coords,color)
            elif self.eltype == 'hex':
                edges = [ 0,1, 1,2, 2,3, 0,3, 0,4, 1,5, 2,6, 3,7, 4,5, 5,6, 6,7, 7,4]
                coords = self.f[:,edges,:]
                print coords.dtype
                drawEdges(coords,color)
            else:
                drawPolyLines(self.f,color)
                
        elif nnod == 3:
            if color2 is None:
                drawTriangles(self.f,mode,color,alpha)
            else:
                color = concatenate([color,color1,color2],axis=1)
                drawPolygonColor(x,color,alpha)
            
        elif nnod == 4:
            if self.eltype=='tet':
                faces = [ 0,1,2, 0,2,3, 0,3,1, 3,2,1 ]
                coords = self.f[:,faces,:]
                drawTriangles(coords,mode,color)
            else: # (possibly non-plane) quadrilateral
                drawQuadrilaterals(self.f,mode,color)

        elif nnod == 6:
            if self.eltype=='wed':
                triFaces = [0,1,2, 3,5,4]
                triCoords = self.f[:,triFaces,:]
                drawTriangles(triCoords,mode,color)
                quadFaces = [ 0,1,4,3, 1,2,5,4, 0,2,5,3]
                quadCoords = self.f[:,quadFaces,:]
                drawQuadrilaterals(quadCoords,mode,color)
                
        elif nnod == 8:
            if self.eltype=='hex':
                faces = [0,1,2,3, 4,5,6,7, 0,3,7,4, 1,2,6,5, 0,1,5,4, 3,2,6,7]
                coords = self.f[:,faces,:]
                drawQuadrilaterals(coords,mode,color)
        
        else:
            drawPolygons(self.f,mode,color=None)
    

    def pickGL(self,mode):
        """ Allow picking of parts of the actor.

        mode can be 'element' or 'point'
        """
        if mode == 'element':
            pickPolygons(self.f)
        elif mode == 'point':
            pickPoints(self.f)


#############################################################################


class SurfaceActor(Actor,Surface):
    """Draws a triangulated surface specified by points and connectivity."""

    def __init__(self,S,color=None,colormap=None,bkcolor=None,bkcolormap=None,linewidth=None,alpha=1.0):
        
        Actor.__init__(self)
        Surface.__init__(self,S.coords,S.edges,S.faces)
        
        self.setLineWidth(linewidth)
        self.setColor(color,colormap)
        self.setBkColor(bkcolor,bkcolormap)
        self.setAlpha(alpha)

        self.list = None

    def atype(self):
        return 'Surface'

    def setColor(self,color=None,colormap=None):
        """Set the color of the Actor."""
        self.color,self.colormap = saneColorSet(color,colormap,self.nelems()) 


    def setBkColor(self,color=None,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor,self.bkcolormap = saneColorSet(color,colormap,self.nelems())

    def setAlpha(self,alpha):
        """Set the Actors alpha value."""
        self.alpha = float(alpha)
        self.trans = self.alpha < 1.0


    # override the defaults (unneeded since we commected out the defaults) 
    #bbox = Surface.bbox
    #nelems = Surface.nelems


    def drawGL(self,mode='wireframe',color=None,colormap=None,alpha=None):
        """Draw the surface."""

        if mode.endswith('wire'):
            self.drawGL(mode=mode[:-4],color=color,colormap=None)
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK,GL.GL_LINE)
            self.drawGL(mode='wireframe',color=asarray(black),colormap=None)
            GL.glPolygonMode(GL.GL_FRONT_AND_BACK,GL.GL_FILL)
            return

        if alpha is None:
            alpha = self.alpha           

        if color is None:  
            color,colormap = self.color,self.colormap
        else:
            color,colormap = saneColorSet(color,colormap,self.nelems())
        
        if color is None:  # no color
            pass
        
        elif color.dtype.kind == 'f' and color.ndim == 1:  # single color
            GL.glColor(append(color,alpha))
            color = None

        elif color.dtype.kind == 'i': # color index
            color = colormap[color]

        else: # a full color array : use as is
            pass

        if self.linewidth is not None:
            GL.glLineWidth(self.linewidth)

        t = timer.Timer()
        if mode=='wireframe' :
            rev = reverseIndex(self.faces)
            if color is not None:
                color = color[rev[:,-1]]
            drawLines(self.coords[self.edges],color)
            #drawLineElems(self.coords,self.edges,color)
        else:
            self.refresh()
            #drawTriangles(self.coords[self.elems],mode,color,alpha)
            drawTriangleElems(self.coords,self.elems,mode,color,alpha)
        GD.message("Drawing time: %s seconds" % t.seconds())
    

    def pickGL(self,mode):
        """ Allow picking of parts of the actor.

        mode can be 'element' or 'point'
        """
##         if mode == 'actor':
##             self.use_list()
##         el
        if mode == 'element':
            self.refresh()
            #pickPolygons(self.coords[self.elems])
            pickPolygonElems(self.coords,self.elems)
        elif mode == 'edge':
            pickPolygonEdges(self.coords,self.edges)
        elif mode == 'point':
            pickPoints(self.coords)


# End
