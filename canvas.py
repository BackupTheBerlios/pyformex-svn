"""Taster 0.1 (C) Benedict Verhegghe

This is the positioning window. 

"""
from qt import *
from qtgl import *

import sys,math

from OpenGL.GL import *
from OpenGL.GLU import *

from colors import *
from formex import *
from camera import *
import vector

class FormexActor(Formex):
    """An OpenGL actor which is a Formex"""

    def __init__(self,F):
        Formex.__init__(self,F.formex())
        
    def display(self):
        """Draw a formex of line elements.

        """
        glBegin(GL_LINES)
        for el in self.formex():
            if len(el)==2:
                glVertex3f(*el[0])
                glVertex3f(*(el[1]))
        glEnd()


class Canvas(QGLWidget):
    """A canvas for OpenGL rendering."""
    
    def __init__(self,w=640,h=480,*args):
        self.actors = []
        self.camera = Camera() # default Camera settings are adequate
        QGLWidget.__init__(self,*args)
        self.resize(w,h)
        self.glinit()

    def initializeGL(self):
        """Set up the OpenGL rendering state, and define display list"""
        print sys._getframe().f_code.co_name
        self.glinit()
        
    def repaintGL(self):
        print sys._getframe().f_code.co_name
        self.display()
        
    def	resizeGL(self,w,h):
        """Set up the OpenGL view port, matrix mode, etc.

        This will get called automatically on creating the QGLWidget!
        """
        print sys._getframe().f_code.co_name
        self.resize(w,h)

    def setGLColor(self,s):
        """Set the OpenGL color to the named color"""
        print sys._getframe().f_code.co_name
        self.qglColor(QColor(s))

    def clearGLColor(self,s):
        """Clear the OpenGL widget with the named background color"""
        print sys._getframe().f_code.co_name
        self.qglClearColor(QColor(s))

    def glinit(self):
	glClearColor(*RGBA(mediumgrey))     # Clear The Background Color
	glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
	glDepthFunc(GL_LESS)	       # The Type Of Depth Test To Do
	glEnable(GL_DEPTH_TEST)	       # Enables Depth Testing
	glShadeModel(GL_FLAT)	       # Enables Smooth Color Shading
##	glShadeModel(GL_SMOOTH)	       # Enables Smooth Color Shading

##        #print "set up lights"
##	glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
##	glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
##	glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
##	glLightfv(GL_LIGHT0, GL_POSITION, (200.0, 200.0, 0.0))
##	glEnable(GL_LIGHT0)
##	glLightfv(GL_LIGHT1, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
##	glLightfv(GL_LIGHT1, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
##	glLightfv(GL_LIGHT1, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
##	glLightfv(GL_LIGHT1, GL_POSITION, (-500.0, 100.0, 0.0))
##	glEnable(GL_LIGHT1)
##        glEnable(GL_LIGHTING)
        
##        #print "set up materials"
##        glEnable ( GL_COLOR_MATERIAL )
##        glColorMaterial ( GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
##        glMaterial(GL_FRONT, GL_SPECULAR, (0,0,0,1));
##        glMaterial(GL_FRONT, GL_EMISSION, (0,0,0,1));
        glFinish()

        #print "set up camera"
	self.camera.loadProjection()

##    def setViewingVolume(self,bbox):
##        print "bbox=",bbox
##        x0,y0,z0 = bbox[0]
##        x1,y1,z1 = bbox[1]
##        corners = [[x,y,z] for x in [x0,x1] for y in [y0,y1] for z in [z0,z1]]
##        #self.camera.lookAt(array(corners))
##        #print self.camera.center,self.camera.eye
##        #self.camera.setProjection()
         
    def addActor(self,actor):
        """Add an actor to the scene

        All an actor needs is a display function
        """
        self.makeCurrent()
        list = glGenLists(1)
        glNewList(list,GL_COMPILE)
        actor.display()
        glEndList ()
        self.actors.append(list)
        actor.list = list

    def removeActor(self,actor):
        """Remove an actor from the scene"""
        self.makeCurrent()
        self.actors.remove(actor.list)
        glDeleteLists(actor.list,1)

    def removeAllActors(self):
        """Remove all actors from the scene"""
        for list in self.actors:
            glDeleteLists(list,1)
        self.actors = []

    def recreateActor(self,actor):
        """Recreate an actor in the scene"""
        self.removeActor(actor)
        self.addActor(actor) 

    def clear(self):
        print sys._getframe().f_code.co_name
        self.makeCurrent()
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
	glClearColor(*RGBA(lightgrey))   # Clear The Background Color
        self.updateGL()

    def display(self):
        self.makeCurrent()
        if self.actors:
            glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
            glColor3f(*black)
            glLoadIdentity()
            self.camera.loadMatrix()
            for i in self.actors:
                glCallList(i)
        self.updateGL()
        
    def resize (self,w,h):
        self.makeCurrent()
	if h == 0:	# Prevent A Divide By Zero If The Window Is Too Small 
            h = 1
	glViewport(0, 0, w, h)
        self.aspect = float(w)/h
        self.camera.setLens(aspect=self.aspect)
	self.camera.loadProjection()
        self.display()

    def setView(self,bbox,side='front'):
        """Sets the camera looking at one of the sides of the bbox"""
        self.makeCurrent()
        center = (bbox[0]+bbox[1])/2
        self.camera.setCenter(*center)
        size = bbox[1]-bbox[0]
        if side == 'front':
            hsize,vsize,depth = size[0],size[1],size[2]
            long,lat = 0.,0.
        elif side == 'back':
            hsize,vsize,depth = size[0],size[1],size[2]
            long,lat = 180.,0.
        elif side == 'right':
            hsize,vsize,depth = size[2],size[1],size[0]
            long,lat = 90.,0.
        elif side == 'left':
            hsize,vsize,depth = size[2],size[1],size[0]
            long,lat = 270.,0.
        elif side == 'top':
            hsize,vsize,depth = size[0],size[2],size[1]
            long,lat = 0.,90.
        elif side == 'bottom':
            hsize,vsize,depth = size[0],size[2],size[1]
            long,lat = 0.,-90.
        elif side == 'iso':
            hsize = vsize = depth = vector.distance(bbox[1],bbox[0])
            long,lat = 45.,45.
        # go to a distance to have a good view with a 45 degree angle lens
        dist = max(0.6*depth, 1.5*max(hsize/self.aspect,vsize))
        self.camera.setPos(long,lat,dist)
        self.camera.setLens(45.,self.aspect)
        self.camera.setClip(0.1*dist,10*dist)
        self.camera.loadProjection()

    def zoom(self,val):
        """Zoom in/out by shrinking/enlarging the camera view angle."""
        self.makeCurrent()
        self.camera.zoom(val)
        #self.camera.loadProjection()
        

