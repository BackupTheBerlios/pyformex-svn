# canvas.py
# $Id$
"""This implements an OpenGL drawing widget for painting 3D scenes."""
#
# TODO : we want to move the Qt dependencies as much as possible out of
#        this module

import globaldata as GD

import math

import OpenGL.GL as GL
import OpenGL.GLU as GLU

import qt
import qtgl

import camera
from colors import *
from actors import *
from decorations import *
from utils import stuur
import vector

GD.image_formats_qt = qt.QImage.outputFormats()

### load gl2ps if available
try:
    import gl2ps
    _has_gl2ps = True
except ImportError:
    _has_gl2ps = False

_start_message = GD.Version + ', by B. Verhegghe'

##################################################################
#
#  The Canvas
#
class Canvas(qtgl.QGLWidget):
    """A canvas for OpenGL rendering."""
    
    def __init__(self,w=640,h=480,*args):
        """Initialize an empty canvas with default settings.
        """
        qtgl.QGLWidget.__init__(self,*args)
        self.setFocusPolicy(qt.QWidget.StrongFocus)
        self.actors = []       # an empty scene
        self.decorations = []  # and no decorations
        self.views = { 'front': (0.,0.,0.),
                       'back': (180.,0.,0.),
                       'right': (90.,0.,0.),
                       'left': (270.,0.,0.),
                       'top': (0.,90.,0.),
                       'bottom': (0.,-90.,0.),
                       'iso': (45.,45.,0.),
                       }   # default views
        # angles are: longitude, latitude, twist
        self.setBbox()
        self.bgcolor = mediumgrey
        self.rendermode = GD.cfg.gui.rendermode
        self.dynamic = None    # what action on mouse move
        self.makeCurrent()     # set GL context before creating the camera
        self.camera = camera.Camera()
        text1=TextActor(_start_message,w/2,h/2,font='tr24',adjust='center',color=red)
        self.addDecoration(text1)
        
    # These three are defined by the qtgl API
    def initializeGL(self):
        #print "initializeGL:",self.rendermode
        self.glinit()

    def	resizeGL(self,w,h):
        self.setSize(w,h)

    def	paintGL(self):
        self.display()

    # The rest are our functions

    # our own name for the canvas update function
    def update(self):
        self.updateGL()

# Do we use/need these??
##    def setColor(self,s):
##        """Set the OpenGL color to the named color"""
##        self.qglColor(qt.QColor(s))

##    def clearGLColor(self,s):
##        """Clear the OpenGL widget with the named background color"""
##        self.qglClearColor(qt.QColor(s))

    def glinit(self,mode=None):
        if mode:
            self.rendermode = mode
	GL.glClearColor(*RGBA(self.bgcolor))# Clear The Background Color
	GL.glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
	GL.glDepthFunc(GL.GL_LESS)	       # The Type Of Depth Test To Do
	GL.glEnable(GL.GL_DEPTH_TEST)	       # Enables Depth Testing
        if self.rendermode == 'wireframe':
            GL.glShadeModel(GL.GL_FLAT)      # Enables Flat Color Shading
            GL.glDisable(GL.GL_LIGHTING)
        elif self.rendermode == 'flat':
            GL.glShadeModel(GL.GL_FLAT)      # Enables Flat Color Shading
            GL.glDisable(GL.GL_LIGHTING)
        elif self.rendermode == 'smooth':
            GL.glShadeModel(GL.GL_SMOOTH)    # Enables Smooth Color Shading
            #print "set up materials"
            #GL.glMaterialfv(GL.GL_FRONT,GL.GL_AMBIENT_AND_DIFFUSE,(0.5,0.5,0.5,1.))
            #print GD.cfg.render.specular
            #print GD.cfg.render.shininess
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_SPECULAR,GD.cfg.render.specular)
            GL.glMaterialfv(GL.GL_FRONT_AND_BACK,GL.GL_SHININESS,GD.cfg.render.shininess)
            GL.glColorMaterial(GL.GL_FRONT_AND_BACK,GL.GL_AMBIENT_AND_DIFFUSE)
            GL.glEnable(GL.GL_COLOR_MATERIAL)
            #print "set up lights"
            #print GD.cfg.render.keys()
            GL.glEnable(GL.GL_LIGHTING)
            for l,i in zip(['light0','light1'],[GL.GL_LIGHT0,GL.GL_LIGHT1]):
                #print "  set up light ",l,i
                if GD.cfg.render.has_key(l):
                    #print GD.cfg.render[l]
                    GL.glLightModel(GL.GL_LIGHT_MODEL_TWO_SIDE, GL.GL_TRUE)
                    GL.glLightfv(i,GL.GL_AMBIENT,GD.cfg.render[l]['ambient'])
                    GL.glLightfv(i,GL.GL_DIFFUSE,GD.cfg.render[l]['diffuse'])
                    GL.glLightfv(i,GL.GL_SPECULAR,GD.cfg.render[l]['specular'])
                    GL.glLightfv(i,GL.GL_POSITION,GD.cfg.render[l]['position'])
                    GL.glEnable(i)
        else:
            raise RuntimeError,"Unknown rendering mode"

    def setLinewidth(self,lw):
        """Set the linewidth for line rendering."""
        GL.glLineWidth (lw)

    def setBbox(self,bbox=None):
        """Set the bounding box of the scene you want to be visible."""
        # TEST: use last actor
        if type(bbox) == type(None):
            if len(self.actors) > 0:
                self.bbox = self.actors[-1].bbox()
            else:
                self.bbox = [[-1.,-1.,-1.],[1.,1.,1.]]
        else:
            self.bbox = bbox

         
    def add_actor(self,actor,list):
        """Add an actor to an actorlist."""
        self.makeCurrent()
        actor.list = GL.glGenLists(1)
        GL.glNewList(actor.list,GL.GL_COMPILE)
        actor.draw(self.rendermode)
        GL.glEndList()
        list.append(actor)

    def remove_actor(self,actor,list):
        """Remove an actor from an actorlist."""
        self.makeCurrent()
        list.remove(actor)
        GL.glDeleteLists(actor.list,1)

    def recreate_actor(self,actor,list):
        """Recreate an actor in a list."""
        self.remove_actor(actor,list)
        self.add_actor(actor,list) 
         
    def addActor(self,actor):
        """Add a 3D actor to the 3D scene."""
        self.add_actor(actor,self.actors)

    def removeActor(self,actor):
        """Remove a 3D actor from the 3D scene."""
        self.remove_actor(actor,self.actors)
         
    def addDecoration(self,actor):
        """Add a 2D decoration to the canvas."""
        self.add_actor(actor,self.decorations)

    def removeDecoration(self,actor):
        """Remove a 2D decoration from the canvas."""
        self.remove_actor(actor,self.decorations)

    def removeActors(self,actorlist=None):
        """Remove all actors in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.actors[:]
        for actor in actorlist:
            self.removeActor(actor)
        self.setBbox()

    def removeDecorations(self,actorlist=None):
        """Remove all decorations in actorlist (default = all) from the scene."""
        if actorlist == None:
            actorlist = self.decorations[:]
        for actor in actorlist:
            self.removeDecoration(actor)

    def removeAll(self):
        """Remove all actors and decorations"""
        self.removeActors()
        self.removeDecorations()

    def redrawActors(self,actorlist=None):
        """Redraw (some) actors in the scene.

        This redraws the specified actors (recreating their display list).
        This should e.g. be used after changing an actor's properties.
        Only actors that are in the current actor list will be redrawn.
        If no actor list is specified, the whole current actorlist is redrawn.
        """
        self.makeCurrent()
        if actorlist == None:
            actorlist = self.actors
        for actor in actorlist:
            if actor.list:
                GL.glDeleteLists(actor.list,1)
            actor.list = GL.glGenLists(1)
            GL.glNewList(actor.list,GL.GL_COMPILE)
            actor.draw(self.rendermode)
            GL.glEndList() 
        self.display()

    def redrawAll(self):
        """Redraw all actors in the scene."""
        self.redrawActors(self.actors)

    def clear(self):
        """Clear the canvas to the background color."""
        self.makeCurrent()
	GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)
	GL.glClearColor(*RGBA(self.bgcolor))

    def display(self):
        """(Re)display all the actors in the scene.

        This should e.g. be used when actors are added to the scene,
        or after changing  camera position or lens.
        """
        self.clear()
        self.camera.loadProjection()
        self.camera.loadMatrix()
        for i in self.actors:
            GL.glCallList(i.list)
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPushMatrix()
        # Plot viewport decorations
        GL.glLoadIdentity()
        GL.glMatrixMode (GL.GL_PROJECTION)
        GL.glLoadIdentity()
        GLU.gluOrtho2D (0, self.width(), 0, self.height())
        for i in self.decorations:
            GL.glCallList(i.list)
        # end plot viewport decorations
        GL.glMatrixMode(GL.GL_MODELVIEW)
        GL.glPopMatrix()
    
    def setSize (self,w,h):
        self.makeCurrent()
	if h == 0:	# Prevent A Divide By Zero 
            h = 1
	GL.glViewport(0, 0, w, h)
        self.aspect = float(w)/h
        self.camera.setLens(aspect=self.aspect)
        self.display()

    def createView(self,name,angles):
        """Create a named view for camera orientation long,lat.

        By default, the following views are created:
        'front', 'back', 'left', 'right', 'bottom', 'top', 'iso'.
        The user can add/delete/overwrite any number of predefined views.
        """
        self.views[name] = angles

        
    def setView(self,bbox=None,side='front'):
        """Sets the camera looking from one of the named views.

        On startup, the predefined views are 'front', 'back', 'left',
        'right', 'top', 'bottom' and 'iso'.
        This function does not only set the camera angles, but also
        adjust the zooming.
        If a bbox is specified, the camera will be zoomed to view the
        whole bbox.
        If no bbox is specified, the current scene bbox will be used.
        If no current bbox has been set, it will be calculated as the
        bbox of the whole scene.
        """
        self.makeCurrent()
        # select view angles: if undefined use (0,0,0)
        angles = self.views.get(side,(0,0,0))
        # go to a distance to have a good view with a 45 degree angle lens
        if type(bbox) == type(None):
            bbox = self.bbox
        else:
            self.bbox = bbox
        center,size = vector.centerDiff(bbox[0],bbox[1])
        #print "Setting view for bbox",bbox
        #print "center=",center
        #print "size=",size
        # calculating the bounding circle: this is rather conservative
        dist = vector.length(size)
        #print "dist = ",dist
        self.camera.setCenter(*center)
        self.camera.setRotation(*angles)
        self.camera.setDist(dist)
        self.camera.setLens(45.,self.aspect)
        if dist > 0.0:
            self.camera.setClip(0.01*dist,100*dist)
        else:
            self.camera.setClip(0.0,1.0)


    def zoom(self,f):
        self.camera.setDist(f*self.camera.getDist())

    def dyna(self,x,y):
        """Perform dynamic zoom/pan/rotation functions"""
        w,h = self.width(),self.height()
        if self.dynamic == "trirotate":
            # set all three rotations from mouse movement
            # tangential movement sets twist,
            # but only if initial vector is big enough
            x0 = self.state        # initial vector
            d = vector.length(x0)
            if d > h/8:
                x1 = [x-w/2, h/2-y, 0]     # new vector
                a0 = math.atan2(x0[0],x0[1])
                a1 = math.atan2(x1[0],x1[1])
                an = (a1-a0) / math.pi * 180
                ds = stuur(d,[-h/4,h/8,h/4],[-1,0,1],2)
                twist = - an*ds
                #print "an,d,ds = ",an,d,ds,twist
                self.camera.rotate(twist,0.,0.,1.)
                self.state = x1
            # radial movement rotates around vector in lens plane
            x0 = [self.statex-w/2, h/2-self.statey, 0]    # initial vector
            dx = [x-self.statex, self.statey-y,0]         # movement
            b = vector.projection(dx,x0)
            #print "x0,dx,b=",x0,dx,b
            if abs(b) > 5:
                val = stuur(b,[-2*h,0,2*h],[-180,0,+180],1)
                rot =  [ abs(val),-dx[1],dx[0],0 ]
                #print "val,rot=",val,rot
                self.camera.rotate(*rot)
                self.statex,self.statey = (x,y)

        elif self.dynamic == "pan":
            dist = self.camera.getDist() * 0.5
            # hor movement sets x value of center
            # vert movement sets y value of center
            #panx = stuur(x,[0,self.statex,w],[-dist,0.,+dist],1.0)
            #pany = stuur(y,[0,self.statey,h],[-dist,0.,+dist],1.0)
            #self.camera.setCenter (self.state[0] - panx, self.state[1] + pany, self.state[2])
            dx,dy = (x-self.statex,y-self.statey)
            panx = stuur(dx,[-w,0,w],[-dist,0.,+dist],1.0)
            pany = stuur(dy,[-h,0,h],[-dist,0.,+dist],1.0)
            #print dx,dy,panx,pany
            self.camera.translate(panx,-pany,0)
            self.statex,self.statey = (x,y)

        elif self.dynamic == "zoom":
            # hor movement is lens zooming
            f = stuur(x,[0,self.statex,w],[180,self.statef,0],1.2)
            self.camera.setLens(f)

        elif self.dynamic == "combizoom":
            # hor movement is lens zooming
            f = stuur(x,[0,self.statex,w],[180,self.state[1],0],1.2)
            self.camera.setLens(f)
            # vert movement is dolly zooming
            d = stuur(y,[0,self.statey,h],[0.2,1,5],1.2)
            self.camera.setDist(d*self.state[0])
        self.update()


    # Any keypress with focus in the canvas generates a 'wakeup' signal.
    # This is used to break out of a wait status.
    # An 's' keypress will generate a 'save' signal.
    # Events not handled here could also be handled by the toplevel
    # event handler.
    def keyPressEvent (self,e):
        self.emit(qt.PYSIGNAL("wakeup"),())
        if e.text() == 's':
            self.emit(qt.PYSIGNAL("save"),())
        e.ignore()
        
    def mousePressEvent(self,e):
        # Remember the place of the click
        self.statex = e.x()
        self.statey = e.y()
        self.camera.loadMatrix()
        # Other initialisations for the mouse move actions are done here 
        if e.button() == qt.Qt.LeftButton:
            self.dynamic = "trirotate"
            # the vector from the screen center to the clicked point
            # this is used for the twist angle
            self.state = [self.statex-self.width()/2, -(self.statey-self.height()/2), 0.]
        elif e.button() == qt.Qt.MidButton:
            self.dynamic = "pan"
            self.state = self.camera.getCenter()
        elif e.button() == qt.Qt.RightButton:
            self.dynamic = "combizoom"
            self.state = [self.camera.getDist(),self.camera.fovy]
        
    def mouseReleaseEvent(self,e):
        self.dynamic = None
        self.camera.saveMatrix()          
        
    def mouseMoveEvent(self,e):
        if self.dynamic:
            self.dyna(e.x(),e.y())

    def save(self,fn,fmt='PNG',options=None):
        """Save the current rendering as an image file."""
        self.makeCurrent()
        if fmt in GD.image_formats_qt:
            GL.glFinish()
            qim = self.grabFrameBuffer()
            qim.save(fn,fmt)
        elif fmt in GD.image_formats_gl2ps:
            self.savePS(fn,fmt)


    # Deprecated
    useView = setView

######################### ONLY LOADED IF GL2PS FOUND ########################

    if _has_gl2ps:

        def savePS(self,filename,filetype=None,title='',producer='',
                   viewport=None):
            """ Export OpenGL rendering to PostScript/PDF/TeX format.

            Exporting OpenGL renderings to PostScript is based on the PS2GL
            library by Christophe Geuzaine (http://geuz.org/gl2ps/), linked
            to Python by Toby Whites's wrapper
            (http://www.esc.cam.ac.uk/~twhi03/software/python-gl2ps-1.1.2.tar.gz)

            This function is only defined if the gl2ps module is found.

            The filetype should be one of 'PS', 'EPS', 'PDF' or 'TEX'.
            If not specified, the type is derived from the file extension.
            In case of the 'TEX' filetype, two files are written: one with
            the .tex extension, and one with .eps extension.
            """
            #print self.actors
            fp = file(filename, "wb")
            if filetype:
                filetype = self._gl2ps_types[filetype]
            else:
                s = filename.upper()
                for ext in _gl2ps_types.keys():
                    if s.endswith('.'+ext):
                        filetype = self._gl2ps_types[ext]
                        break
                if not filetype:
                    filetype = gl2ps.GL2PS_EPS
            if not title:
                title = filename
            if not viewport:
                viewport = GL.glGetIntegerv(GL.GL_VIEWPORT)
            bufsize = 0
            state = gl2ps.GL2PS_OVERFLOW
            options = gl2ps.GL2PS_SILENT | gl2ps.GL2PS_SIMPLE_LINE_OFFSET
            ##| gl2ps.GL2PS_NO_BLENDING | gl2ps.GL2PS_OCCLUSION_CULL | gl2ps.GL2PS_BEST_ROOT
            ##color = GL[[0.,0.,0.,0.]]
            while state == gl2ps.GL2PS_OVERFLOW:
                bufsize += 1024*1024
                #print filename,filetype
                gl2ps.gl2psBeginPage(title, self._producer, viewport, filetype,
                                     gl2ps.GL2PS_BSP_SORT, options, GL.GL_RGBA, 0,
                                     None, 0, 0, 0, bufsize, fp, filename)
                self.display()
                GL.glFinish()
                state = gl2ps.gl2psEndPage()
            fp.close()
            log("File %s written" % filename)

        #Canvas.savePS = _savePS

        _start_message += '\nCongratulations! You have gl2ps, so I activated drawPS!'

        _producer = GD.Version + ' (http://pyformex.berlios.de)'
        _gl2ps_types = { 'PS':gl2ps.GL2PS_PS, 'EPS':gl2ps.GL2PS_EPS,
                         'PDF':gl2ps.GL2PS_PDF, 'TEX':gl2ps.GL2PS_TEX }
        GD.image_formats_gl2ps = _gl2ps_types.keys()

        print _start_message
