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
"""This implements an OpenGL drawing widget for painting 3D scenes."""

import pyformex as GD

from numpy import *
from OpenGL import GL,GLU

from formex import length
import colors
import camera
import actors
import decors
import marks
import utils



def gl_pickbuffer():
    "Return a list of the 2nd numbers in the openGL pick buffer."
    buf = GL.glRenderMode(GL.GL_RENDER)
    GD.debugt("translate getpickbuf")
    return asarray([ r[2] for r in buf ])


fill_modes = [ GL.GL_FRONT_AND_BACK, GL.GL_FRONT, GL.GL_BACK ]
fill_mode = GL.GL_FRONT_AND_BACK

def glFillMode(mode):
    global fill_mode
    if mode in fill_modes:
        fill_mode = mode
def glFrontFill():
    glFillMode(GL.GL_FRONT)
def glBackFill():
    glFillMode(GL.GL_BACK)
def glBothFill():
    glFillMode(GL.GL_FRONT_AND_BACK)
def glFill():
    GL.glPolygonMode(fill_mode,GL.GL_FILL)
def glLine():
    GL.glPolygonMode(GL.GL_FRONT_AND_BACK,GL.GL_LINE)

## def glLight(onoff):
##     """Toggle lights on/off."""
##     if onoff:
##         GL.glEnable(GL.GL_LIGHTING)
##     else:
##         GL.glDisable(GL.GL_LIGHTING)

def glSmooth():
    """Enable smooth shading"""
    GL.glShadeModel(GL.GL_SMOOTH)
def glFlat():
    """Disable smooth shading"""
    GL.glShadeModel(GL.GL_FLAT)

def glCulling():
    """Enable culling"""
    GL.glEnable(GL.GL_CULL_FACE)
def glNoCulling():
    """Disable culling"""
    GL.glDisable(GL.GL_CULL_FACE)


    
class ActorList(list):

    def __init__(self,canvas):
        self.canvas = canvas
        list.__init__(self)
        
    def add(self,actor):
        """Add an actor to an actorlist."""
        self.append(actor)

    def delete(self,actor):
        """Remove an actor from an actorlist."""
        if actor in self:
            self.remove(actor)

    def redraw(self):
        """Redraw (some) actors in the scene.

        This redraws the specified actors (recreating their display list).
        This should e.g. be used after changing an actor's properties.
        """
        for actor in self:
            actor.redraw(mode=self.canvas.rendermode)



##################################################################
#
#  The Canvas Settings
#

class CanvasSettings(object):
    """A collection of settings for an OpenGL Canvas."""

    default = dict(
        linewidth = 1.0,
        bgcolor = colors.mediumgrey,
        fgcolor = colors.black,
        slcolor = colors.red,     # color for selected items
        transparency = 1.0,       # opaque
        # colormap for mapping property values
        propcolors = [ colors.black, colors.red, colors.green, colors.blue,
                       colors.cyan, colors.magenta, colors.yellow, colors.white ],
        )

    @classmethod
    def checkDict(clas,dict):
        """Transform a dict to acceptable settings."""
        ok = {}
        keys = dict.keys()
##        if 'rendermode' in keys:
##            ok['rendermode'] = dict['rendermode']
        if 'linewidth' in keys:
            ok['linewidth'] =  float(dict['linewidth'])
        for c in [ 'bgcolor', 'fgcolor', 'slcolor' ]:
            if c in keys:
                ok[c] = colors.GLColor(dict[c])
        if 'propcolors' in keys:
            ok['propcolors'] = map(colors.GLColor,dict['propcolors'])
        return ok
        
    def __init__(self,dict={}):
        """Create a new set of CanvasSettings, possibly changing defaults."""
        self.reset(dict)

    def reset(self,dict={}):
        """Reset to default settings

        If a dict is specified, these settings will override defaults.
        """
        self.__dict__.update(CanvasSettings.checkDict(CanvasSettings.default))
        if dict:
            self.__dict__.update(CanvasSettings.checkDict(dict))
    
    def __str__(self):
        return utils.formatDict(self.__dict__)


############### OpenGL Lighting #################################
    

class Light(object):

    def __init__(self,nr,*args,**kargs):
        self.light = GL.GL_LIGHT0 + (nr % GL.GL_MAX_LIGHTS)
        self.set(**kargs)

    def set(self,ambient=0.5,diffuse=0.5,specular=0.5,position=(0.,0.,1.,0.)):
        self.ambient = colors.GREY(ambient)
        self.diffuse = colors.GREY(diffuse)
        self.specular = colors.GREY(specular)
        self.position = position

    def enable(self):
        GL.glLightfv(self.light,GL.GL_POSITION,self.position)
        GL.glLightfv(self.light,GL.GL_AMBIENT,self.ambient)
        GL.glLightfv(self.light,GL.GL_DIFFUSE,self.diffuse)
        GL.glLightfv(self.light,GL.GL_SPECULAR,self.specular)
        GL.glEnable(self.light)

    def disable(self):
        GL.glDisable(self.light)


##################################################################
#
#  The Canvas
#
class Canvas(object):
    """A canvas for OpenGL rendering."""

    rendermodes = ['wireframe','flat','flatwire','smooth','smoothwire',
                   'smooth-avg']

    def __init__(self):
        """Initialize an empty canvas with default settings."""
        self.actors = ActorList(self)       # start with an empty scene
        self.annotations = ActorList(self)  # without annotations
        self.decorations = ActorList(self)  # and no decorations either
        self.triade = None
        self.resetLighting()
        self.resetLights()
        self.setBbox()
        self.settings = CanvasSettings()
        self.mode2D = False
        self.rendermode = 'wireframe'
        self.polygonfill = False
        self.lighting = True
        self.avgnormals = False
        self.alphablend = False
        self.dynamouse = True  # dynamic mouse action works on mouse move
        self.dynamic = None    # what action on mouse move
        self.camera = None
        self.view_angles = camera.view_angles
        GD.debug("Canvas Setting:\n%s"% self.settings)


    def glMatSpec(self):
        GL.glMaterialfv(fill_mode,GL.GL_SPECULAR,colors.GREY(self.specular))
        GL.glMaterialfv(fill_mode,GL.GL_EMISSION,colors.GREY(self.emission))
        GL.glMaterialfv(fill_mode,GL.GL_SHININESS,self.shininess)
        GL.glColorMaterial(fill_mode,GL.GL_AMBIENT_AND_DIFFUSE)
        GL.glEnable(GL.GL_COLOR_MATERIAL)

    def glLightSpec(self):
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT,colors.GREY(self.ambient))
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE, 1)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_LOCAL_VIEWER, 0)
        if GD.canvas:
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glPushMatrix()
            GL.glLoadIdentity()
            for l in GD.canvas.lights:
                l.enable()
            GL.glPopMatrix()
        self.glMatSpec()

    def glLight(self,onoff):
        """Toggle lights on/off."""
        if onoff:
            self.glLightSpec()
            GL.glEnable(GL.GL_LIGHTING)
        else:
            GL.glDisable(GL.GL_LIGHTING)

    def resetDefaults(self,dict={}):
        """Return all the settings to their default values."""
        self.settings.reset(dict)
        self.resetLights()

    def resetLighting(self):
        self.ambient = GD.cfg['render/ambient']
        self.specular = GD.cfg['render/specular']
        self.emission = GD.cfg['render/emission']
        self.shininess = GD.cfg['render/shininess']
        
    def resetLights(self):
        self.lights = []
        for i in range(8):
            light = GD.cfg.get('render/light%d' % i, None)
            if light is not None:
                self.lights.append(Light(i,light))


    def setRenderMode(self,rm):
        """Set the rendermode.

        This changes the rendermode and redraws everything with the new mode.
        """
        GD.debug("Changing Render Mode to %s" % rm)
        if rm != self.rendermode:
            if rm not in Canvas.rendermodes:
                rm = Canvas.rendermodes[0]
            self.rendermode = rm
            GD.debug("Redrawing with mode %s" % self.rendermode)
            self.glinit(self.rendermode)
            self.redrawAll()


    def setTransparency(self,mode):
        self.alphablend = mode

    def setLighting(self,mode):
        self.lighting = mode
        self.glLight(self.lighting)

    def setAveragedNormals(self,mode):
        self.avgnormals = mode
        change = (self.rendermode == 'smooth' and self.avgnormals) or \
                 (self.rendermode == 'smooth-avg' and not self.avgnormals)
        if change:
            if self.avgnormals:
                self.rendermode = 'smooth-avg'
            else:
                self.rendermode = 'smooth'
            self.actors.redraw()
            self.display()
       

    def setLineWidth(self,lw):
        """Set the linewidth for line rendering."""
        self.settings.linewidth = float(lw)


    def setBgColor(self,bg):
        """Set the background color."""
        self.settings.bgcolor = colors.GLColor(bg)
        self.clear()
        self.redrawAll()
        

    def setFgColor(self,fg):
        """Set the default foreground color."""
        self.settings.fgcolor = colors.GLColor(fg)

    
    def setLight(self,nr,ambient,diffuse,specular,position):
        """(Re)Define a light on the scene."""
        self.lights[nr].set(ambient,diffuse,specular,position)

    def enableLight(self,nr):
        """Enable an existing light."""
        self.lights[nr].enable()

    def disableLight(self,nr):
        """Disable an existing light."""
        self.lights[nr].disable()
    

    def initCamera(self):
        #if GD.options.makecurrent:
        self.makeCurrent()  # we need correct OpenGL context for camera
        self.camera = camera.Camera()
        GD.debug("camera.rot = %s" % self.camera.rot)
        GD.debug("view angles: %s" % self.view_angles)


    def glinit(self,mode=None):
        if mode:
            self.rendermode = mode

        self.clear()
        #GL.glClearColor(*colors.RGBA(self.default.bgcolor))# Clear The Background Color
        GL.glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
        GL.glDepthFunc(GL.GL_LESS)	       # The Type Of Depth Test To Do
        GL.glEnable(GL.GL_DEPTH_TEST)	       # Enables Depth Testing
        #GL.glEnable(GL.GL_CULL_FACE)
        

        # On initializing a rendering mode, we also set default lighting
        if self.rendermode == 'wireframe':
            glFlat()
            glLine()
            self.lighting = False
            self.glLight(False)

                
        elif self.rendermode.startswith('flat'):
            glFlat()
            glFill()
            self.lighting = False
            self.glLight(False)
               
        elif self.rendermode.startswith('smooth'):
            glSmooth()
            glFill()
            self.lighting = True
            self.glLight(True)
            
        else:
            raise RuntimeError,"Unknown rendering mode"


    def glupdate(self):
        """Flush all OpenGL commands, making sure the display is updated."""
        #GD.debugt("UPDATING CURRENT OPENGL CANVAS")
        GL.glFlush()
        

    def clear(self):
        """Clear the canvas to the background color."""
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glClearColor(*colors.RGBA(self.settings.bgcolor))
        self.setDefaults()


    def setDefaults(self):
        """Activate the canvas settings in the GL machine."""
        GL.glColor3fv(self.settings.fgcolor)
        GL.glLineWidth(self.settings.linewidth)

    
    def setSize (self,w,h):
        if h == 0:	# prevent divide by zero 
            h = 1
        GL.glViewport(0, 0, w, h)
        self.aspect = float(w)/h
        self.camera.setLens(aspect=self.aspect)
        self.display()


    def display(self):
        """(Re)display all the actors in the scene.

        This should e.g. be used when actors are added to the scene,
        or after changing  camera position/orientation or lens.
        """
        #GD.debugt("UPDATING CURRENT OPENGL CANVAS")
        self.makeCurrent()
        self.clear()
        self.glLight(self.lighting)

        # Draw Scene Actors
        self.camera.loadProjection()
        self.camera.loadMatrix()
        if self.alphablend:
            opaque = [ a for a in self.actors if not a.trans ]
            transp = [ a for a in self.actors if a.trans ]
            for actor in opaque:
               actor.draw(mode=self.rendermode)
            GL.glEnable (GL.GL_BLEND)
            GL.glDepthMask (GL.GL_FALSE)
            GL.glBlendFunc (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            for actor in transp:
                actor.draw(mode=self.rendermode)
            GL.glDepthMask (GL.GL_TRUE)
            GL.glDisable (GL.GL_BLEND)
        else:
            for actor in self.actors:
                self.setDefaults()
                actor.draw(mode=self.rendermode)

        # annotations are drawn in 3D space
        for actor in self.annotations:
            self.setDefaults()
            actor.draw(mode=self.rendermode)

        # decorations are drawn in 2D mode
        self.begin_2D_drawing()
        for actor in self.decorations:
            self.setDefaults()
            actor.draw(mode=self.rendermode)
        self.end_2D_drawing()

        # make sure canvas is updated
        GL.glFlush()


    def begin_2D_drawing(self):
        """Set up the canvas for 2D drawing on top of 3D canvas.

        The 2D drawing operation should be ended by calling end_2D_drawing. 
        It is assumed that you will not try to change/refresh the normal
        3D drawing cycle during this operation.
        """
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluOrtho2D(0,self.width(),0,self.height())
        GL.glDisable(GL.GL_DEPTH_TEST)
        self.glLight(False)
        self.mode2D = True

 
    def end_2D_drawing(self):
        """Cancel the 2D drawing mode initiated by begin_2D_drawing."""
        GL.glEnable(GL.GL_DEPTH_TEST)    
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()
        self.glLight(self.lighting)
        self.mode2D = False
       
        
    def setBbox(self,bbox=None):
        """Set the bounding box of the scene you want to be visible."""
        # TEST: use last actor
        if bbox is None:
            if len(self.actors) > 0:
                bbox = self.actors[-1].bbox()
            else:
                bbox = [[-1.,-1.,-1.],[1.,1.,1.]]
        self.bbox = asarray(bbox)

         
    def addActor(self,actor):
        """Add a 3D actor to the 3D scene."""
        self.actors.add(actor)

    def removeActor(self,actor):
        """Remove a 3D actor from the 3D scene."""
        self.actors.delete(actor)
         
    def addAnnotation(self,actor):
        """Add an annotation to the 3D scene."""
        self.annotations.add(actor)

    def removeAnnotation(self,actor):
        """Remove an annotation from the 3D scene."""
        if actor == self.triade:
            self.triade = None
        self.annotations.delete(actor)
         
    def addDecoration(self,actor):
        """Add a 2D decoration to the canvas."""
        self.decorations.add(actor)

    def removeDecoration(self,actor):
        """Remove a 2D decoration from the canvas."""
        self.decorations.delete(actor)

    def remove(self,itemlist):
        """Remove a list of any actor/annotation/decoration items.

        itemlist can also be a single item instead of a list.
        """
        if not type(itemlist) == list:
            itemlist = [ itemlist ]
        for item in itemlist:
            if isinstance(item,actors.Actor):
                self.actors.delete(item)
            elif isinstance(item,marks.Mark):
                self.annotations.delete(item)
            elif isinstance(item,decors.Decoration):
                self.decorations.delete(item)
        

    def removeActors(self,actorlist=None):
        """Remove all actors in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.actors[:]
        for actor in actorlist:
            self.removeActor(actor)
        self.setBbox()


    def removeAnnotations(self,actorlist=None):
        """Remove all actors in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.annotations[:]
        for actor in actorlist:
            self.removeAnnotation(actor)


    def removeDecorations(self,actorlist=None):
        """Remove all decorations in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.decorations[:]
        for actor in actorlist:
            self.removeDecoration(actor)


    def removeAll(self):
        """Remove all actors and decorations"""
        self.removeActors()
        self.removeAnnotations()
        self.removeDecorations()


    def redrawAll(self):
        """Redraw all actors in the scene."""
        self.actors.redraw()
        self.annotations.redraw()
        self.decorations.redraw()
        self.display()

        
##     def setView(self,bbox=None,side=None):
##         """Sets the camera looking from one of the named views."""
## ##         # select view angles: if undefined use (0,0,0)
## ##         if side:
## ##             angles = self.camera.getAngles(side)
## ##         else:
## ##             angles = None
##         self.setCamera(bbox,angles)

        
    def setCamera(self,bbox=None,angles=None):
        """Sets the camera looking under angles at bbox.

        This function sets the camera angles and adjusts the zooming.
        The camera distance remains unchanged.
        
        If a bbox is specified, the camera will be zoomed to make the whole
        bbox visible.
        If no bbox is specified, the current scene bbox will be used.
        If no current bbox has been set, it will be calculated as the
        bbox of the whole scene.

        If no camera angles are given, the camera orientation is kept.
        """
        self.makeCurrent()
        # go to a distance to have a good view with a 45 degree angle lens
        if not bbox is None:
            self.setBbox(bbox)
        bbox = self.bbox
        center = 0.5 * (bbox[0]+bbox[1])
        # calculating the bounding circle: this is rather conservative
        dist = length(bbox[1] - bbox[0])
        if dist <= 0.0:
            dist = 1.0
        self.camera.setCenter(*center)
        if angles:
            self.camera.setAngles(angles)
#            self.camera.setRotation(*angles)
        self.camera.setDist(dist)
        self.camera.setLens(45.,self.aspect)
        self.camera.setClip(0.01*dist,100.*dist)


    def zoom(self,f):
        """Dolly zooming."""
        self.camera.setDist(f*self.camera.getDist())


##     def draw_cursor(self,x,y):
##         if self.cursor:
##             self.removeDecoration(self.cursor)
##         w,h = GD.cfg.get('pick/size',(20,20))
##         col = GD.cfg.get('pick/color','yellow')
##         self.cursor = decors.Grid(x-w/2,y-h/2,x+w/2,y+h/2,color=col,linewidth=1)
##         self.addDecoration(self.cursor)

##     def draw_rectangle(self,x,y):
##         GD.debugt("DRAWRECTANGLE")
##         if self.cursor:
##             self.removeDecoration(self.cursor)
##         col = GD.cfg.get('pick/color','yellow')
##         self.cursor = decors.Grid(self.statex,self.statey,x,y,color=col,linewidth=1)
##         self.addDecoration(self.cursor)


    def saveBuffer(self):
        """Save the current OpenGL buffer"""
        GD.debugt("saveBuffer")
        self.save_buffer = GL.glGetIntegerv(GL.GL_DRAW_BUFFER)

    def showBuffer(self):
        """Show the saved buffer"""
        pass

    def draw_cursor(self,x,y):
        """draw the cursor"""
        if self.cursor:
            self.removeDecoration(self.cursor)
        w,h = GD.cfg.get('pick/size',(20,20))
        col = GD.cfg.get('pick/color','yellow')
        self.cursor = decors.Grid(x-w/2,y-h/2,x+w/2,y+h/2,color=col,linewidth=1)
        self.addDecoration(self.cursor)

    def draw_rectangle(self,x,y):
        GD.debugt("DRAWRECTANGLE")
        if self.cursor:
            self.removeDecoration(self.cursor)
        col = GD.cfg.get('pick/color','yellow')
        self.cursor = decors.Grid(self.statex,self.statey,x,y,color=col,linewidth=1)
        self.addDecoration(self.cursor)

## NSRect rectView = [self bounds]; //Get the bounds of the OpenGL view

## w = rectView.size.width;
## h = rectView.size.height;
## [[self openGLContext] makeCurrentContext];
## glViewport(0, 0, w, h);
## glMatrixMode (GL_PROJECTION);
## glLoadIdentity();
## glOrtho(0, w, 0, h, 1, -1);
## glMatrixMode (GL_MODELVIEW);
## glLoadIdentity();

## glDisable(GL_LIGHTING); //turn off lighting effects
## glEnable(GL_COLOR_LOGIC_OP);
## glLogicOp(GL_XOR);
## glDisable(GL_DEPTH_TEST);
## glColor4f(1.0f, 1.0f, 1.0f, 1.0f);
## glPolygonMode(GL_FRONT_AND_BACK, GL_LINE);

## //Save the current buffer target
## glDrawBuffer(GL_FRONT); //set the drawbuffer to the front readbuffer.
## }

### End
