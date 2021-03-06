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
"""This implements an OpenGL drawing widget for painting 3D scenes."""

import pyformex as pf
from coords import tand

from numpy import *
from OpenGL import GL,GLU

from formex import length
from drawable import saneColor
import colors
import camera
import actors
import decors
import marks
import utils
from mydict import Dict


def gl_pickbuffer():
    "Return a list of the 2nd numbers in the openGL pick buffer."
    buf = GL.glRenderMode(GL.GL_RENDER)
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

def glLineSmooth(onoff):
    if onoff is True:
        GL.glEnable(GL.GL_LINE_SMOOTH)
        GL.glHint(GL.GL_LINE_SMOOTH_HINT, GL.GL_NICEST)
    elif onoff is False:
        GL.glDisable(GL.GL_LINE_SMOOTH)


def glLineStipple(factor,pattern):
    """Set the line stipple pattern.

    When drawing lines, OpenGl can use a stipple pattern. The stipple
    is defined by two values: a pattern (on/off) of maximum 16 bits,
    used on the pixel level, and a multiplier factor for each bit.

    If factor <= 0, the stippling is disabled.
    """
    if factor > 0:
        GL.glLineStipple(factor,pattern)
        GL.glEnable(GL.GL_LINE_STIPPLE)    
    else:
        GL.glDisable(GL.GL_LINE_STIPPLE)


def glSmooth():
    """Enable smooth shading"""
    GL.glShadeModel(GL.GL_SMOOTH)
def glFlat():
    """Disable smooth shading"""
    GL.glShadeModel(GL.GL_FLAT)
    

def onOff(onoff):
    """Convert On/Off strings to a boolean"""
    if type(onoff) is str:
        return (onoff.lower() == 'on')
    else:
        if onoff:
            return True
        else:
            return False


def glEnable(facility,onoff):
    """Enable/Disable an OpenGL facility, depending on onoff value

    facility is an OpenGL facility.
    onoff can be True or False to enable, resp. disable the facility, or
    None to leave it unchanged.
    """
    pf.debug("%s: %s" % (facility,onoff))
    if onOff(onoff):
        pf.debug("ENABLE")
        GL.glEnable(facility)
    else:
        pf.debug("DISABLE")
        GL.glDisable(facility)
        

def glCulling(onoff=True):
    glEnable(GL.GL_CULL_FACE,onoff)
def glNoCulling():
    glCulling(False)

def glLighting(onoff):
    glEnable(GL.GL_LIGHTING,onoff)


def glPolygonFillMode(mode):
    if type(mode) is str:
        mode = mode.lower()
        if mode == 'Front and Back':
            glBothFill()
        elif mode == 'Front':
            glFrontFill()
        elif mode == 'Back':
            glBackFill()

            
def glPolygonMode(mode):
    if type(mode) is str:
        mode = mode.lower()
        if mode == 'fill':
            glFill()
        elif mode == 'line':
            glLine()
    

def glShadeModel(model):
    if type(model) is str:
        model = model.lower()
        if model == 'smooth':
            glSmooth()
        elif model == 'flat':
            glFlat()
        
def glSettings(settings):
    pf.debug("GL SETTINGS: %s" % settings)
    glCulling(settings.get('Culling',None))
    glLighting(settings.get('Lighting',None))
    glShadeModel(settings.get('Shading',None))
    glLineSmooth(onOff(settings.get('Line Smoothing',None)))
    glPolygonFillMode(settings.get('Polygon Fill',None))
    glPolygonMode(settings.get('Polygon Mode',None))
    pf.canvas.update()

    
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
        """Redraw all actors in the list.

        This redraws the specified actors (recreating their display list).
        This could e.g. be used after changing an actor's properties.
        """
        for actor in self:
            actor.redraw()



############### OpenGL Lighting #################################

class Material(object):
    def __init__(self,name,ambient=0.2,diffuse=0.2,specular=0.9,emission=0.1,shininess=2.0):
        self.name = str(name)
        self.ambient = float(ambient)
        self.diffuse = float(diffuse)
        self.specular = float(specular)
        self.emission = float(emission)
        self.shininess = float(shininess)


    def setValues(self,**kargs):
        #print "setValues",kargs
        for k in kargs:
            #print k,kargs[k]
            if hasattr(self,k):
                #print getattr(self,k)
                setattr(self,k,float(kargs[k]))
                #print getattr(self,k)


    def activate(self):   
        GL.glMaterialfv(fill_mode,GL.GL_AMBIENT,colors.GREY(self.ambient))
        GL.glMaterialfv(fill_mode,GL.GL_DIFFUSE,colors.GREY(self.diffuse))
        GL.glMaterialfv(fill_mode,GL.GL_SPECULAR,colors.GREY(self.specular))
        GL.glMaterialfv(fill_mode,GL.GL_EMISSION,colors.GREY(self.emission))
        GL.glMaterialfv(fill_mode,GL.GL_SHININESS,self.shininess)


    def dict(self):
        """Return the material light parameters as a dict"""
        return dict([(k,getattr(self,k)) for k in ['ambient','diffuse','specular','emission','shininess']])
    

    def __str__(self):
        return """MATERIAL: %s
    ambient:  %s
    diffuse:  %s
    specular: %s
    emission: %s
    shininess: %s
""" % (self.name,self.ambient,self.diffuse,self.specular,self.emission,self.shininess)
        


def getMaterials():
    mats = pf.refcfg['material']
    mats.update(pf.prefcfg['material'])
    mats.update(pf.cfg['material'])
    return mats


def createMaterials():
    mats = getMaterials()
    matdb = {}
    for m in mats:
        matdb[m] = Material(m,**mats[m])
    return matdb


class Light(object):

    def __init__(self,nr,**kargs):
        self.light = GL.GL_LIGHT0 + (nr % GL.GL_MAX_LIGHTS)
        self.set(ambient=0.5,diffuse=0.5,specular=0.5,position=[0.,0.,1.,0.],enabled=False)

    def set(self,**kargs):
        for k in kargs:
            self.set_value(k,kargs[k])

    def set_value(self,key,value):
        if key in [ 'ambient','diffuse','specular' ]:
            value = colors.GREY(value)
        setattr(self,key,value)

    def enable(self):
        GL.glEnable(self.light)
        GL.glLightfv(self.light,GL.GL_AMBIENT,self.ambient)
        GL.glLightfv(self.light,GL.GL_DIFFUSE,self.diffuse)
        GL.glLightfv(self.light,GL.GL_SPECULAR,self.specular)
        GL.glLightfv(self.light,GL.GL_POSITION,self.position)

    def disable(self):
        GL.glDisable(self.light)

    def __str__(self):
        return """LIGHT %s:
    ambient color:  %s
    diffuse color:  %s
    specular color: %s
    position: %s
""" % (self.light-GL.GL_LIGHT0,self.ambient,self.diffuse,self.specular,self.position)


class LightProfile(object):

    light_model = {
        'ambient': GL.GL_AMBIENT,
        'diffuse': GL.GL_DIFFUSE,
        'ambient and diffuse': GL.GL_AMBIENT_AND_DIFFUSE,
        'emission': GL.GL_EMISSION,
        'specular': GL.GL_SPECULAR,
        }
    
    def __init__(self,model,ambient,lights):
        self.model = self.light_model[model]
        self.ambient = ambient
        self.lights = lights

    def activate(self):
        #GL.glEnable(GL.GL_LIGHTING)
        GL.glEnable(GL.GL_COLOR_MATERIAL)
        GL.glColorMaterial(fill_mode,self.model)
        GL.glLightModelfv(GL.GL_LIGHT_MODEL_AMBIENT,colors.GREY(self.ambient))
        GL.glLightModeli(GL.GL_LIGHT_MODEL_TWO_SIDE, 1)
        GL.glLightModeli(GL.GL_LIGHT_MODEL_LOCAL_VIEWER, 0)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        for light in self.lights:
            light.enable()
        GL.glPopMatrix()
        


##################################################################
#
#  The Canvas Settings
#

class CanvasSettings(Dict):
    """A collection of settings for an OpenGL Canvas.

    The canvas settings are a collection of settings and default values
    affecting the rendering in an individual viewport. There are two type of settings:
    
    - mode settings are set during the initialization of the canvas and can/should not be
      changed during the drawing of actors and decorations;
    - default settings can be used as default values but may be changed during the drawing
      of actors/decorations: they are reset before each individual draw instruction.
      
    Currently the following mode settings are defined:
    
    - bgcolor: the viewport background color
    - bgcolor2: None for a single color background, bottom color for a
      graded background (the top color then being bgcolor)
    - slcolor: the highlight color
    - rendermode: the rendering mode
    - shading: True is smooth, False is flat
    - lighting: True or False

    The list of default settings includes:

    - fgcolor: the default drawing color
    - bkcolor: the default backface color
    - colormap: the default color map to be used if color is an index
    - bklormap: the default color map to be used if bkcolor is an index
    - pointsize: the default size for drawing points
    - marksize: the default size for drawing markers
    - linewidth: the default width for drawing lines

    Any of these values can be set in the constructor using a keyword argument.
    All items that are not set, will get their value from the configuration
    file(s).
    """

    def __init__(self,**kargs):
        """Create a new set of CanvasSettings."""
        Dict.__init__(self)
        self.reset(kargs)

    def reset(self,d={}):
        """Reset the CanvasSettings to its defaults.

        The default values are taken from the configuration files.
        An optional dictionary may be specified to override (some of) these defaults.
        """
        self.update(pf.refcfg['canvas'])
        self.update(pf.prefcfg['canvas'])
        self.update(pf.cfg['canvas'])
        if d:
            self.update(d)

    def update(self,d,strict=True):
        """Update current values with the specified settings

        Returns the sanitized update values.
        """
        ok = self.checkDict(d,strict)
        #print "UPDATING %s" % ok
        Dict.update(self,ok)
        ## THIS SHOULD BE DONE WHILE SETTING THE CFG !!
        ## if (self.bgcolor2 == self.bgcolor).all():
        ##     self.bgcolor2 = None

    @classmethod
    def checkDict(clas,dict,strict=True):
        """Transform a dict to acceptable settings."""
        ok = {}
        for k,v in dict.items():
            try:
                if k in [ 'bgcolor', 'bgcolor2', 'fgcolor', 'bkcolor', 'slcolor']:
                    if v is not None:
                        v = saneColor(v)
                elif k in ['colormap','bkcolormap']:
                    if v is not None:
                        v =  map(saneColor,v)
                elif k in ['smoothshading', 'lighting', 'culling']:
                    v = bool(v)
                elif k in ['linewidth', 'pointsize', 'marksize']:
                    v = float(v)
                elif k == 'linestipple':
                    v = map(int,v)
                elif k == 'transparency':
                    v = max(min(float(v),1.0),0.0)
                elif k == 'rendermode':
                    if not v in Canvas.rendermodes:
                        raise
                elif k == 'marktype':
                    pass
                else:
                    raise
                ok[k] = v
            except:
                if strict:
                    raise ValueError,"Invalid key/value for CanvasSettings: %s = %s" % (k,v)
        return ok
    
    def __str__(self):
        return utils.formatDict(self)


    def setMode(self):
        """Activate the mode canvas settings in the GL machine."""
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
        GL.glClearColor(*colors.RGBA(self.bgcolor))
 

    def setDefault(self):
        """Activate the default canvas settings in the GL machine."""
        GL.glColor3fv(self.fgcolor)
        GL.glLineWidth(self.linewidth)
        glLineStipple(*self.linestipple)
        GL.glPointSize(self.pointsize)


##################################################################
#
#  The Canvas
#
class Canvas(object):
    """A canvas for OpenGL rendering.

    The Canvas is a class holding all global data of an OpenGL scene rendering. This includes
    colors, line types, rendering mode. It also keeps lists of all the actors and decorations
    in the scene. It always has a Camera object holding import viewing parameters. And finally
    it stores the lighting information.
    
    It does not however contain the viewport size and position.
    """

    rendermodes = ['wireframe','flat','flatwire','smooth','smoothwire',
                   'smooth_avg']

    def __init__(self,settings={}):
        """Initialize an empty canvas with default settings."""
        self.actors = ActorList(self)
        self.highlights = ActorList(self)
        self.annotations = ActorList(self)
        self.decorations = ActorList(self)
        self.triade = None
        self.background = None
        self.bbox = None
        self.resetLighting()
        self.setBbox()
        self.settings = CanvasSettings(**settings)
        self.mode2D = False
        self.rendermode = pf.cfg['render/mode']
        self.lighting = pf.cfg['render/lighting']
        if self.lighting not in [True,False]:
            self.lighting = self.rendermode.startswith('smooth')
        self.polygonfill = False
        self.avgnormals = False
        self.alphablend = False
        self.camera = None
        self.view_angles = camera.view_angles
        self.cursor = None
        self.focus = False
        pf.debug("Canvas Setting:\n%s"% self.settings)


    def Size(self):
        return self.width(),self.height()


    def do_lighting(self,onoff):
        """Toggle lights on/off."""
        if onoff:
            self.lightprof.activate()
            self.material.activate()
            GL.glEnable(GL.GL_LIGHTING)
        else:
            GL.glDisable(GL.GL_LIGHTING)


    def has_lighting(self):
        """Return the status of the lighting."""
        return GL.glIsEnabled(GL.GL_LIGHTING)
        

    def resetDefaults(self,dict={}):
        """Return all the settings to their default values."""
        self.settings.reset(dict)
        self.resetLighting()
        ## self.resetLights()

    def setAmbient(self,ambient):
        """Set the global ambient lighting for the canvas"""
        self.lightprof.ambient = float(ambient)
        
    def setMaterial(self,matname):
        """Set the default material light properties for the canvas"""
        self.material = pf.GUI.materials[matname]
        

    def resetLighting(self):
        """Change the light parameters"""
        self.lightmodel = pf.cfg['render/lightmodel']
        self.setMaterial(pf.cfg['render/material'])
        self.lightset = pf.cfg['render/lights']
        lights = [ Light(int(light[-1:]),**pf.cfg['light/%s' % light]) for light in self.lightset ]
        self.lightprof = LightProfile(self.lightmodel,pf.cfg['render/ambient'],lights)


    def setRenderMode(self,mode,lighting=None):
        """Set the rendering mode.

        This sets or changes the rendermode and lighting attributes.
        If lighting is not specified, it is set depending on the rendermode.
        
        If the canvas has not been initialized, this merely sets the
        attributes self.rendermode and self.lighting.
        If the canvas was already initialized (it has a camera), and one of
        the specified settings is fdifferent from the existing, the new mode
        is set, the canvas is re-initialized according to the newly set mode,
        and everything is redrawn with the new mode.
        """
        if mode not in Canvas.rendermodes:
            raise ValueError,"Invalid render mode %s" % mode
        if lighting not in [True,False]:
            lighting = mode.startswith('smooth')

        if mode != self.rendermode or lighting != self.lighting:
            self.rendermode = mode
            self.lighting = lighting
            #print "GLINIT %s %s" % (self.rendermode,self.lighting)
            self.glinit()
            #print "REDRAWALL %s %s" % (self.rendermode,self.lighting)
            #self.redrawAll()
            #print "SWITCH TO NRE RENDERMODE COMPLETED"
        else:
            #print "KEEP MODE  %s %s" % (self.rendermode,self.lighting)
            pass

    def setToggle(self,attr,onoff):
        if onoff not in [True,False]:
            onoff = not getattr(self,attr)
        setattr(self,attr,onoff)
        try:
            func = getattr(self,'do_'+attr)#.capitalize())
            func(onoff)
        except:
            pass
        
    ## def setTransparency(self,onoff):
    ##     self.alphablend = onoff

    def setLighting(self,onoff):
        self.setToggle('lighting',onoff)
        
    ## def setLighting(self,onoff):
    ##     self.lighting = onoff
    ##     print "canvas.setLighting %s" % onoff
    ##     self.glLight(self.lighting)

    ## def setAveragedNormals(self,onoff):
    ##     self.avgnormals = onoff
    ##     self.do_avgnormals(onoff)
        
    def do_avgnormals(self,onoff):
        change = (self.rendermode == 'smooth' and self.avgnormals) or \
                 (self.rendermode == 'smooth_avg' and not self.avgnormals)
        if change:
            if self.avgnormals:
                self.rendermode = 'smooth_avg'
            else:
                self.rendermode = 'smooth'
            self.actors.redraw()
            self.display()
       

    def setLineWidth(self,lw):
        """Set the linewidth for line rendering."""
        self.settings.linewidth = float(lw)
       

    def setLineStipple(self,repeat,pattern):
        """Set the linestipple for line rendering."""
        self.settings.update({'linestipple':(repeat,pattern)})
        

    def setPointSize(self,sz):
        """Set the size for point drawing."""
        self.settings.pointsize = float(sz)


    def setBgColor(self,color1,color2=None):
        """Set the background color.

        If one color is specified, a solid background is set.
        If two colors are specified, a graded background is set
        and an object is created to display the background.
        """
        self.settings.bgcolor = colors.GLColor(color1)
        if color2 is None:
            pf.debug("Clearing twocolor background")
            self.settings.bgcolor2 = None
            self.background = None
        else:
            self.settings.bgcolor2 = colors.GLColor(color2)
            self.createBackground()
            glSmooth()
            glFill()
        self.clear()
        self.redrawAll()


    def createBackground(self):
        """Create the background object."""
        x1,y1 = 0,0
        x2,y2 = self.Size()
        color4 = [self.settings.bgcolor2,self.settings.bgcolor2,self.settings.bgcolor,self.settings.bgcolor]
        self.background = decors.Rectangle(x1,y1,x2,y2,color=color4)
        

    def setFgColor(self,color):
        """Set the default foreground color."""
        self.settings.fgcolor = colors.GLColor(color)
        

    def setSlColor(self,color):
        """Set the highlight color."""
        self.settings.slcolor = colors.GLColor(color)


    ## def updateSettings(self,settings):
    ##     """Update the viewport settings"""
    ##     for k,v in settings.items():
    ##         if k == 'linewidth':
    ##             self.setLineWidth(v)
    ##         elif k == 'bgcolor':
    ##             if 'bgcolor2' in settings:
    ##                 self.setBgColor(v,settings.get('bgcolor2',None))
    ##         elif k == 'bgcolor2':
    ##             if 'bgcolor' in settings:
    ##                 pass
    ##             else:
    ##                 self.setBgColor(self.settings.bgcolor,v)
    ##         elif k == 'color':
    ##             self.setFgColor(v)
    ##         elif k == 'slcolor':
    ##             self.setSlColor(v)
        
        
    ## def setLightValue(self,nr,key,val):
    ##     """(Re)Define a light on the scene."""
    ##     self.lights.set_value(nr,key,val)
    ##     self.lights.enable(nr)

    ## def enableLight(self,nr):
    ##     """Enable an existing light."""
    ##     self.lights[nr].enable()

    ## def disableLight(self,nr):
    ##     """Disable an existing light."""
    ##     self.lights[nr].disable()


    def setTriade(self,on=None,pos='lb',siz=100):
        """Toggle the display of the global axes on or off.

        If on is True, a triade of global axes is displayed, if False it is
        removed. The default (None) toggles between on and off.
        """
        if on is None:
            on = self.triade is None
        pf.debug("SETTING TRIADE %s" % on)
        if self.triade:
            self.removeAnnotation(self.triade)
            self.triade = None
        if on:
            self.triade = decors.Triade(pos,siz)
            self.addAnnotation(self.triade)
    

    def initCamera(self):
        #if pf.options.makecurrent:
        self.makeCurrent()  # we need correct OpenGL context for camera
        self.camera = camera.Camera()
        #pf.debug("camera.rot = %s" % self.camera.rot)
        #pf.debug("view angles: %s" % self.view_angles)


    def glinit(self):
        """Initialize the rendering machine.

        The rendering machine is initialized according to:
        - self.rendermode: one of
        - self.lighting
        """
        self.setBgColor(self.settings.bgcolor,self.settings.bgcolor2)
        self.clear()
        #GL.glClearColor(*colors.RGBA(self.default.bgcolor))# Clear The Background Color
        GL.glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
        GL.glEnable(GL.GL_DEPTH_TEST)	       # Enables Depth Testing
        #GL.glEnable(GL.GL_CULL_FACE)
        
        if self.rendermode == 'wireframe':
            if self.background:
                glSmooth()
                glFill()
            else:
                glLine()
                
        elif self.rendermode.startswith('flat'):
            if self.background:
                glSmooth()
            else:
                glFlat()
            glFill()
               
        elif self.rendermode.startswith('smooth'):
            glSmooth()
            glFill()
            
        else:
            raise RuntimeError,"Unknown rendering mode"

        self.setLighting(self.lighting)

        if self.rendermode.endswith('wire'):
            GL.glEnable(GL.GL_POLYGON_OFFSET_FILL)
            GL.glPolygonOffset(1.0,1.0) 
        else:
            GL.glDisable(GL.GL_POLYGON_OFFSET_FILL)
            

    def glupdate(self):
        """Flush all OpenGL commands, making sure the display is updated."""
        GL.glFlush()
        

    def clear(self):
        """Clear the canvas to the background color."""
        self.settings.setMode()
        self.setDefaults()


    def setDefaults(self):
        """Activate the canvas settings in the GL machine."""
        self.settings.setDefault()
        self.do_lighting(self.lighting)
        GL.glDepthFunc(GL.GL_LESS)

    
    def setSize (self,w,h):
        if h == 0:	# prevent divide by zero 
            h = 1
        GL.glViewport(0, 0, w, h)
        self.aspect = float(w)/h
        self.camera.setLens(aspect=self.aspect)
        if self.background:
            # recreate the background to match the current size
            self.createBackground()
        self.display()


    def display(self):
        """(Re)display all the actors in the scene.

        This should e.g. be used when actors are added to the scene,
        or after changing  camera position/orientation or lens.
        """
        #pf.debugt("UPDATING CURRENT OPENGL CANVAS")
        #print "DISPLAY"
        self.makeCurrent()
        self.clear()
        
        # decorations are drawn in 2D mode
        self.begin_2D_drawing()
        
        if self.background:
            #pf.debug("Displaying background")
            self.background.draw(mode='smooth')

        if len(self.decorations) > 0:
            for actor in self.decorations:
                self.setDefaults()
                ## if hasattr(actor,'zoom'):
                ##     self.zoom_2D(actor.zoom)
                actor.draw(canvas=self)
                ## if hasattr(actor,'zoom'):
                ##     self.zoom_2D()

        # draw the focus rectangle if more than one viewport
        if len(pf.GUI.viewports.all) > 1 and pf.cfg['gui/showfocus']:
            if self.hasFocus():
                self.draw_focus_rectangle(2)
            elif self.focus:
                self.draw_focus_rectangle(1)
                
        self.end_2D_drawing()

        # start 3D drawing
        self.camera.set3DMatrices()
        
        # draw the highlighted actors
        if self.highlights:
            for actor in self.highlights:
                self.setDefaults()
                actor.draw(canvas=self)

        # draw the scene actors
        sorted_actors =  [ a for a in self.actors if not a.ontop ] + [ a for a in self.actors if a.ontop ]
        if self.alphablend:
            opaque = [ a for a in sorted_actors if not a.trans ]
            transp = [ a for a in sorted_actors if a.trans ]
            for actor in opaque:
                self.setDefaults()
                actor.draw(canvas=self)
            GL.glEnable (GL.GL_BLEND)
            GL.glDepthMask (GL.GL_FALSE)
            GL.glBlendFunc (GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)
            for actor in transp:
                self.setDefaults()
                actor.draw(canvas=self)
            GL.glDepthMask (GL.GL_TRUE)
            GL.glDisable (GL.GL_BLEND)
        else:
            for actor in sorted_actors:
                self.setDefaults()
                actor.draw(canvas=self)

        # annotations are decorations drawn in 3D space
        for actor in self.annotations:
            self.setDefaults()
            actor.draw(canvas=self)

        # make sure canvas is updated
        GL.glFlush()


    def zoom_2D(self,zoom=None):
        if zoom is None:
            zoom = (0,self.width(),0,self.height())
        GLU.gluOrtho2D(*zoom)
            

    def begin_2D_drawing(self):
        """Set up the canvas for 2D drawing on top of 3D canvas.

        The 2D drawing operation should be ended by calling end_2D_drawing. 
        It is assumed that you will not try to change/refresh the normal
        3D drawing cycle during this operation.
        """
        #pf.debug("Start 2D drawing")
        if self.mode2D:
            #pf.debug("WARNING: ALREADY IN 2D MODE")
            return
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        GL.glMatrixMode(GL.GL_PROJECTION)
        GL.glPushMatrix()
        GL.glLoadIdentity()
        self.zoom_2D()
        GL.glDisable(GL.GL_DEPTH_TEST)
        self.do_lighting(False)
        self.mode2D = True

 
    def end_2D_drawing(self):
        """Cancel the 2D drawing mode initiated by begin_2D_drawing."""
        #pf.debug("End 2D drawing")
        if self.mode2D:
            GL.glEnable(GL.GL_DEPTH_TEST)    
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glPopMatrix()
            GL.glMatrixMode(GL.GL_MODELVIEW)
            GL.glPopMatrix()
            self.do_lighting(self.lighting)
            self.mode2D = False
       
        
    def setBbox(self,bbox=None):
        """Set the bounding box of the scene you want to be visible."""
        # TEST: use last actor
        #pf.debug("BBOX WAS: %s" % self.bbox)
        if bbox is None:
            if len(self.actors) > 0:
                bbox = self.actors[-1].bbox()
            else:
                bbox = [[-1.,-1.,-1.],[1.,1.,1.]]
        bbox = asarray(bbox)
        try:
            self.bbox = nan_to_num(bbox)
        except:
        # if bbox.any() == nan:
            pf.message("Invalid Bbox: %s" % bbox)
        #pf.debug("BBOX BECOMES: %s" % self.bbox)

         
    def addActor(self,actor):
        """Add a 3D actor to the 3D scene."""
        self.actors.add(actor)

    def removeActor(self,actor):
        """Remove a 3D actor from the 3D scene."""
        self.actors.delete(actor)
        #self.highlights.delete(actor)

    def addHighlight(self,actor):
        """Add a 3D actor highlight to the 3D scene."""
        self.highlights.add(actor)

    def removeHighlight(self,actor):
        """Remove a 3D actor highlight from the 3D scene."""
        self.highlights.delete(actor)
         
    def addAnnotation(self,actor):
        """Add an annotation to the 3D scene."""
        self.annotations.add(actor)

    def removeAnnotation(self,actor):
        """Remove an annotation from the 3D scene."""
        if actor == self.triade:
            pf.debug("REMOVING TRIADE")
            self.triade = None
        self.annotations.delete(actor)
         
    def addDecoration(self,actor):
        """Add a 2D decoration to the canvas."""
        self.decorations.add(actor)

    def removeDecoration(self,actor):
        """Remove a 2D decoration from the canvas."""
        self.decorations.delete(actor)

    def remove(self,itemlist):
        """Remove a list of any actor/highlights/annotation/decoration items.

        This will remove the items from any of the canvas lists in which the
        item appears.
        itemlist can also be a single item instead of a list.
        """
        if not type(itemlist) in (list,tuple):
            itemlist = [ itemlist ]
        for item in itemlist:
            self.actors.delete(item)
            self.highlights.delete(item)
            self.annotations.delete(item)
            self.decorations.delete(item)
        

    def removeActors(self,actorlist=None):
        """Remove all actors in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.actors[:]
        for actor in actorlist:
            self.removeActor(actor)
        self.setBbox()
        

    def removeHighlights(self,actorlist=None):
        """Remove all highlights in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.highlights[:]
        for actor in actorlist:
            self.removeHighlight(actor)


    def removeAnnotations(self,actorlist=None):
        """Remove all annotations in actorlist (default = all) from the scene."""
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
        self.removeHighlights()
        self.removeAnnotations()
        self.removeDecorations()


    def redrawAll(self):
        """Redraw all actors in the scene."""
        #print "REDRAWALL"
        self.actors.redraw()
        self.highlights.redraw()
        self.annotations.redraw()
        self.decorations.redraw()
        self.display()

        
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
        angles can be a set of 3 angles, or a string
        """
        self.makeCurrent()
        # go to a distance to have a good view with a 45 degree angle lens
        if bbox is not None:
            pf.debug("SETTING BBOX: %s" % self.bbox)
            self.setBbox(bbox)
        pf.debug("USING BBOX: %s" % self.bbox)
        X0,X1 = self.bbox
        center = 0.5*(X0+X1)
        # calculating the bounding circle: this is rather conservative
        self.camera.setCenter(*center)
        if type(angles) is str:
            angles = self.view_angles.get(angles)
        if angles is not None:
            try:
                self.camera.setAngles(angles)
            except:
                raise ValueError,'Invalid view angles specified'
        # Currently, we keep the default fovy/aspect
        # and change the camera distance to focus
        fovy = self.camera.fovy
        #pf.debug("FOVY: %s" % fovy)
        self.camera.setLens(fovy,self.aspect)
        # Default correction is sqrt(3)
        correction = float(pf.cfg.get('gui/autozoomfactor',1.732))
        tf = tand(fovy/2.)

        import simple,coords
        bbix = simple.regularGrid(X0,X1,[1,1,1])
        bbix = dot(bbix,self.camera.rot[:3,:3])
        bbox = coords.Coords(bbix).bbox()
        dx,dy,dz = bbox[1] - bbox[0]
        vsize = max(dx/self.aspect,dy)
        offset = dz
        dist = (vsize/tf + offset) / correction
        
        if dist == nan or dist == inf:
            pf.debug("DIST: %s" % dist)
            return
        if dist <= 0.0:
            dist = 1.0
        self.camera.setDist(dist)
        self.camera.setClip(0.01*dist,100.*dist)
        self.camera.resetArea()


    def project(self,x,y,z,locked=False):
        "Map the object coordinates (x,y,z) to window coordinates."""
        locked=False
        if locked:
            model,proj,view = self.projection_matrices
        else:
            self.makeCurrent()
            self.camera.loadProjection()
            model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
            proj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
            view = GL.glGetIntegerv(GL.GL_VIEWPORT)
        winx,winy,winz = GLU.gluProject(x,y,z,model,proj,view)
        return winx,winy,winz
        return self.camera.project(x,y,z)


    def unProject(self,x,y,z,locked=False):
        "Map the window coordinates (x,y,z) to object coordinates."""
        locked=False
        if locked:
            model,proj,view = self.projection_matrices
        else:
            self.makeCurrent()
            self.camera.loadProjection()
            model = GL.glGetDoublev(GL.GL_MODELVIEW_MATRIX)
            proj = GL.glGetDoublev(GL.GL_PROJECTION_MATRIX)
            view = GL.glGetIntegerv(GL.GL_VIEWPORT)
        objx, objy, objz = GLU.gluUnProject(x,y,z,model,proj,view)
        return (objx,objy,objz)
        return self.camera.unProject(x,y,z)


    def zoom(self,f,dolly=True):
        """Dolly zooming.

        Zooms in with a factor `f` by moving the camera closer
        to the scene. This does noet change the camera's FOV setting.
        It will change the perspective view though.
        """
        if dolly:
            self.camera.dolly(f)


    def zoomRectangle(self,x0,y0,x1,y1):
        """Rectangle zooming.

        Zooms in/out by changing the area and position of the visible
        part of the lens.
        Unlike zoom(), this does not change the perspective view.

        `x0,y0,x1,y1` are pixel coordinates of the lower left and upper right
        corners of the area of the lens that will be mapped on the
        canvas viewport.
        Specifying values that lead to smaller width/height will zoom in.
        """
        w,h = float(self.width()),float(self.height())
        self.camera.setArea(x0/w,y0/h,x1/w,y1/h)


    def zoomCentered(self,w,h,x=None,y=None):
        """Rectangle zooming with specified center.

        This is like zoomRectangle, but the zoom rectangle is specified
        by its center and size, which may be more appropriate when using
        off-center zooming.
        """
        self.zoomRectangle(x-w/2,y-h/2,x+w/2,y+w/2)


    def zoomAll(self):
        """Rectangle zoom to make full scene visible.

        """
        self.camera.resetArea()


    def saveBuffer(self):
        """Save the current OpenGL buffer"""
        self.save_buffer = GL.glGetIntegerv(GL.GL_DRAW_BUFFER)

    def showBuffer(self):
        """Show the saved buffer"""
        pass

    def draw_focus_rectangle(self,width=2):
        """Draw the focus rectangle.

        The specified width is HALF of the line width"""
        lw = width
        w,h = self.width(),self.height()
        self._focus = decors.Grid(lw,lw,w-lw,h-lw,color=colors.pyformex_pink,linewidth=2*lw)
        self._focus.draw()

    def draw_cursor(self,x,y):
        """draw the cursor"""
        if self.cursor:
            self.removeDecoration(self.cursor)
        w,h = pf.cfg.get('pick/size',(20,20))
        col = pf.cfg.get('pick/color','yellow')
        self.cursor = decors.Grid(x-w/2,y-h/2,x+w/2,y+h/2,color=col,linewidth=1)
        self.addDecoration(self.cursor)

    def draw_rectangle(self,x,y):
        if self.cursor:
            self.removeDecoration(self.cursor)
        col = pf.cfg.get('pick/color','yellow')
        self.cursor = decors.Grid(self.statex,self.statey,x,y,color=col,linewidth=1)
        self.addDecoration(self.cursor)


### End
