# $Id$
##
##  This file is part of pyFormex 0.8 Release Sat Jun 13 10:22:42 2009
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Website: http://pyformex.berlios.de/
##  Copyright (C) Benedict Verhegghe (bverheg@users.berlios.de) 
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
##  along with this program.  If not, see <http://www.gnu.org/licenses/>.
##
"""OpenGL actors for populating the 3D scene."""

import pyformex as GD

from OpenGL import GL,GLU

from drawable import *
from formex import *
import elements

from connectivity import reverseIndex
from plugins.surface import TriSurface

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
        self.actor.redraw(mode=mode,color=color)
        Drawable.redraw(self,mode=mode,color=color)

    def drawGL(self,mode,color=None):
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glTranslate(*self.trl)
        self.actor.use_list()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()


class RotatedActor(Actor):
    """An Actor rotated to another position."""

    def __init__(self,A,rot=(1.,0.,0.),twist=0.0):
        """Created a new rotated actor.

        If rot is an array with shape (3), the rotation is specified
        by the direction of the local 0 axis of the actor.
        If rot is an array with shape (4,4), the rotation is specified
        by the direction of the local 0, 1 and 2 axes of the actor.
        """
        Actor.__init__(self)
        self.actor = A
        self.trans = A.trans
        if shape(rot)[0] == 3:
            self.rot = rotMatrix(rot,4)
        else:
            self.rot = rot

    def bbox(self):
        return self.actor.bbox() # TODO : rotate the bbox !

    def redraw(self,mode,color=None):
        self.actor.redraw(mode=mode,color=color)
        Drawable.redraw(self,mode=mode,color=color)

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
        self.edges = array(elements.Hex8.edges)
        self.facets = array(elements.Hex8.faces)

    def bbox(self):
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

    def __init__(self,size=1.0,pos=[0.,0.,0.],color=[red,green,blue,cyan,magenta,yellow]):
        Actor.__init__(self)
        self.color = color
        self.setPos(pos)
        self.setSize(size)

    def bbox(self):
        return self.size * array([[0.,0.,0.],[1.,1.,1.]])

    def setPos(self,pos):
        pos = Coords(pos)
        if pos.shape == (3,):
            self.pos = pos
        self.delete_list()

    def setSize(self,size):
        size = float(size)
        if size > 0.0:
            self.size = size
        self.delete_list()

    def drawGL(self,mode='wireframe',color=None):
        """Draw the triade."""
        # When entering here, the modelview matrix has been set
        # We should make sure it is unchanged on exit
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glTranslatef (*self.pos) 
        GL.glScalef (self.size,self.size,self.size) 
        # Coord axes of size 1.0
        GL.glBegin(GL.GL_LINES)
        pts = Formex(pattern('1')).f.reshape(-1,3)
        GL.glColor3f(*black)
        for i in range(3):
            #GL.glColor(*self.color[i])
            for x in pts:
                GL.glVertex3f(*x)
            pts = pts.rollAxes(1)
        GL.glEnd()
        # Coord plane triangles of size 0.5
        GL.glBegin(GL.GL_TRIANGLES)
        pts = Formex(mpattern('16')).scale(0.5).f.reshape(-1,3)
        for i in range(3):
            pts = pts.rollAxes(1)
            GL.glColor(*self.color[i])
            for x in pts:
                GL.glVertex3f(*x)
        GL.glEnd()
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()

  
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
                if self.linewidth:
                    GL.glLineWidth(self.linewidth)
                glColor(self.linecolor)
                drawGridLines(self.x0,self.x1,nx)

            if self.planes:
                glColor(self.planecolor,self.alpha)
                drawGridPlanes(self.x0,self.x1,nx)


class PlaneActor(Actor):
    """A plane in a 3D scene."""

    def __init__(self,nx=(2,2,2),ox=(0.,0.,0.),size=((0.0,1.0,1.0),(0.0,1.0,1.0)),linecolor=black,linewidth=None,planecolor=white,alpha=0.5,lines=True,planes=True):
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
        sz = asarray(size)
        self.x0,self.x1 = ox-sz[0], ox+sz[1]
        

    def bbox(self):
        return array([self.x0,self.x1])

    def drawGL(self,mode,color=None):
        """Draw the grid."""

        for i in range(3):
            nx = self.nx.copy()
            nx[i] = 0
            
            if self.lines:
                if self.linewidth:
                    GL.glLineWidth(self.linewidth)
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

    def __init__(self,F,color=None,colormap=None,bkcolor=None,bkcolormap=None,alpha=1.0,mode=None,linewidth=None,marksize=None):
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

        If the Formex has no 'eltype' attribute, or if it is not
        recognized, Formices are drawn as follows:
          plex-1: a fixed size dot,
          plex-2: a line
          plex-3: a triangle
          plex 4 and higher: a polygon: if the points are not in a single
            plane, the polygon consists of a number of flat triangles.

        The following eltypes are recognized (and should match the
        corresponding plexitude):
          plex-1: 'point3d' : a 3D cube with 6 differently colored faces is
                              drawn at each point
          plex-4: 'tet4'   : a tetrahedron
          plex-6: 'wedge6' : a wedge (triangular prism)
          plex-8: 'hex8'   : a hexahedron
        """
        Actor.__init__(self)
        # Initializing with F alone gives problems with self.p !
        Formex.__init__(self,F.f,F.p,F.eltype)

        self.mode = mode
        self.setLineWidth(linewidth)
        self.setColor(color,colormap)
        self.setBkColor(bkcolor,bkcolormap)
        self.setAlpha(alpha)
##         if coloradjust:
##             if colormap is not None:
##                 colormap /= colormap.sum(axis=1)
##             if bkcolormap is not None:
##                 bkcolormap /= bkcolormap.sum(axis=1).reshape(-1,1)
        if self.nplex() == 1:
            self.setMarkSize(marksize)
        self.list = None
        


    def atype(self):
        return 'Formex'

    def setColor(self,color=None,colormap=None):
        """Set the color of the Actor."""
        self.color,self.colormap = saneColorSet(color,colormap,self.f.shape[:-1])


    def setBkColor(self,color=None,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor,self.bkcolormap = saneColorSet(color,colormap,(self.f.shape[:-1]))

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
            marksize = self.dsize() * marksize
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
        if self.mode is not None:
            mode = self.mode

        if mode.endswith('wire'):
            self.drawGL(mode=mode[:-4],color=color,colormap=colormap,alpha=alpha)
            self.drawGL(mode='wireframe',color=asarray(black),colormap=None)
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
            
        nnod = self.nplex()
        if nnod == 1:
            if self.eltype == 'point3d':
                x = self.f.reshape((-1,3))
                drawAtPoints(x,self.mark,color)
            else:
                drawPoints(self.f,color,alpha,self.marksize)
                
        elif nnod == 2:
            drawLines(self.f,color,alpha)
        
        elif self.eltype == 'curve' and nnod == 3:
            drawQuadraticCurves(self.f,color,n=quadratic_curve_ndiv)
            
        elif self.eltype == 'nurbs' and (nnod == 3 or nnod == 4):
            drawNurbsCurves(self.f,color)
            
        elif self.eltype is None:
            if mode=='wireframe' :
                drawPolyLines(self.f,color)
            else:
                drawPolygons(self.f,mode,color,alpha)

        else:
            try:
                el = getattr(elements,self.eltype.capitalize())
            except:
                raise ValueError,"Invalid eltype %s" % str(self.eltype)
            if mode=='wireframe' :
                drawEdgeElems(self.f,el.edges,color)    
            else:
                drawFaceElems(self.f,el.faces,mode,color,alpha)
    

    def pickGL(self,mode):
        """ Allow picking of parts of the actor.

        mode can be 'element' or 'point'
        """
        if mode == 'element':
            pickPolygons(self.f)
        elif mode == 'point':
            pickPoints(self.f)


#############################################################################


class TriSurfaceActor(Actor,TriSurface):
    """Draws a triangulated surface specified by points and connectivity."""

    def __init__(self,S,color=None,colormap=None,bkcolor=None,bkcolormap=None,linewidth=None,alpha=1.0,mode=None):
        
        Actor.__init__(self)
        TriSurface.__init__(self,S.coords,S.edges,S.faces)
        
        self.setLineWidth(linewidth)
        self.setColor(color,colormap)
        self.setBkColor(bkcolor,bkcolormap)
        self.setAlpha(alpha)

        self.list = None

    def atype(self):
        return 'TriSurface'

    def setColor(self,color=None,colormap=None):
        """Set the color of the Actor."""
        self.color,self.colormap = saneColorSet(color,colormap,(self.nelems(),3)) 


    def setBkColor(self,color=None,colormap=None):
        """Set the backside color of the Actor."""
        self.bkcolor,self.bkcolormap = saneColorSet(color,colormap,(self.nelems(),3))

    def setAlpha(self,alpha):
        """Set the Actors alpha value."""
        self.alpha = float(alpha)
        self.trans = self.alpha < 1.0


    # override the defaults
    # (no longer needed as we removed the defaults from Drawable)
    #bbox = TriSurface.bbox
    #nelems = TriSurface.nelems


    def drawGL(self,mode='wireframe',color=None,colormap=None,alpha=None):
        """Draw the surface."""

        if mode.endswith('wire'):
            self.drawGL(mode='wireframe',color=asarray(black),colormap=None)
            self.drawGL(mode=mode[:-4],color=color,colormap=colormap,alpha=alpha)
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
            drawLineElems(self.coords,self.edges,color)
        else:
            self.refresh()
            drawPolygonElems(self.coords,self.elems,mode,color,alpha)
        GD.debug("Drawing time: %s seconds" % t.seconds())
    

    def pickGL(self,mode):
        """ Allow picking of parts of the actor.

        mode can be 'element' or 'point'
        """
        if mode == 'element':
            self.refresh()
            pickPolygonElems(self.coords,self.elems)
        elif mode == 'edge':
            pickPolygonEdges(self.coords,self.edges)
        elif mode == 'point':
            pickPoints(self.coords)


# End
