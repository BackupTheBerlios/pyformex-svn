"""Taster 0.1 (C) Benedict Verhegghe

This is the positioning window. 

"""
from qt import *
from qtgl import *

import sys,math

from OpenGL.GL import *
from OpenGL.GLU import *

from Colors import *
from Formex import *
from Geometry import *

class Camera:
    """This class defines a camera."""

    def __init__(self):
        """Create a new camera at position (0,0,0) looking along the -z axis"""
        self.setPosition(0.,0.,0.)
        self.setAngles(0.,0.,0.)
        self.near = None
        self.setFovy(45.,4./3.)
        self.setClip(0.1,10.)
        self.setPerspective(True)
        self.setCenter(0.,0.,0.)

    def setPosition(self,x,y,z):
        """Set the camera position"""
        self.eye = [x,y,z]
        
    def setAngles(self,x,y,z):
        """Set the camera rotation angles around x,y,z axes"""
        self.rotx,self.roty,self.rotz = x,y,z

    def loadMatrix(self):
        """Load the camera transformation matrix"""
        glRotatef(-self.rotx, 1.0, 0.0, 0.0)
        glRotatef(-self.roty, 0.0, 1.0, 0.0)
        glRotatef(-self.rotz, 0.0, 0.0, 1.0)
        glTranslatef(-self.eye[0],-self.eye[1],-self.eye[2])

    def setCenter(self,x,y,z):
        """Set the center of the scene.

        This can be used to aim the camera at the action."""
        self.center = [x,y,z]

    def setFovy(self,fovy,aspect=4./3):
        """Set the field of view of the camera.

        We set the field of view by the vertical opening angle fovy
        and the aspect ratio (width/height) of the viewing volume.
        """
        self.fovy = fovy
        self.aspect = aspect
        self.setFrustum()

    def setFrustum(self):
        """Set the frustum parameters from camera parameters"""
        if self.near and self.fovy and self.aspect:
            self.top = self.near * math.tan(math.radians(self.fovy/2))
            self.bottom = -self.top
            self.right = self.top*self.aspect
            self.left = self.bottom*self.aspect
        
    def setClip(self,near,far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near,self.far = near,far
            self.setFrustum()
        else:
            print "Error: Invalid Near/Far clipping values""" 

    def setPerspective(self,on=True):
        """Set perspective on or off"""
        self.perspective = on

    def setProjection(self):
        """Load the projection/perspective matrix."""
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
        print self.left,self.right,self.top,self.bottom,self.near,self.far
        if self.perspective:
            #gluPerspective(self.fovy,self.aspect,self.near,self.far)
            glFrustum(self.left,self.right,self.top,self.bottom,self.near,self.far)
        else:
            glOrtho(self.left,self.right,self.top,self.bottom,self.near,self.far)
	glMatrixMode(GL_MODELVIEW)     

    def lookAt(self,points):
        """Set up the camera so that the specified points become visible.

        The points are specified as a numarray of shape (n,3).
        These could e.g. be the corners of the scene's bounding box.
        The camera is aimed at the center of the specified points.
        The position of the camera is not changed.
        Then the camera's opening angle and the near and far clipping planes
        are set such that all the points are in the frustum.
        
        """
        center = add.reduce(points) / points.shape[0]
        print center
        self.setCenter(*center)
        #gluLookAt (*(self.eye+self.center+self.up))

    def zoom(val=2):
        """Zoom in/out by shrinking/enlarging the camera view angle.

        The zoom factor is relative to the current setting.
        Use setFovy() to specify an absolute setting.
        """
        if val>0:
            self.setFovy(self.fovy*val)

    def zoomDolly(val=2):
        """Zoom in/out by moving the camera towards/away from scene.
        A value > 1 zooms in, value < 1 zooms out.
        The value will approximately be the enlargement of the view.
        """
        d = distance(eye,center)
        
        


class FormexActor(Formex):
    """An OpenGL actor which is a Formex"""

    def __init__(self,F):
        Formex.__init__(self,F.formex())
        
    def display(self):
        """Draw a 2D formex of line elements.

        """
        glBegin(GL_LINES)
        for cantle in self.formex():
            if len(cantle) == 2:
                glVertex2f(float(cantle[0][0]),float(cantle[0][1]))
                glVertex2f(float(cantle[1][0]),float(cantle[1][1]))
        glEnd()


class Canvas(QGLWidget):
    """A canvas for OpenGL rendering."""
    
    def __init__(self,w=640,h=480,*args):
        self.actors = []
        self.camera = Camera()
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
        print sys._getframe().f_code.co_name
	glClearColor(*RGBA(mediumgrey))     # Clear The Background Color
	glClearDepth(1.0)	       # Enables Clearing Of The Depth Buffer
	glDepthFunc(GL_LESS)	       # The Type Of Depth Test To Do
	glEnable(GL_DEPTH_TEST)	       # Enables Depth Testing
	glShadeModel(GL_SMOOTH)	       # Enables Smooth Color Shading

        #print "set up lights"
	glLightfv(GL_LIGHT0, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
	glLightfv(GL_LIGHT0, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
	glLightfv(GL_LIGHT0, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
	glLightfv(GL_LIGHT0, GL_POSITION, (200.0, 200.0, 0.0))
	glEnable(GL_LIGHT0)
	glLightfv(GL_LIGHT1, GL_AMBIENT, (0.0, 0.0, 0.0, 1.0))
	glLightfv(GL_LIGHT1, GL_DIFFUSE, (1.0, 1.0, 1.0, 1.0))
	glLightfv(GL_LIGHT1, GL_SPECULAR, (1.0, 1.0, 1.0, 1.0))
	glLightfv(GL_LIGHT1, GL_POSITION, (-500.0, 100.0, 0.0))
	glEnable(GL_LIGHT1)
        glEnable(GL_LIGHTING)
        
        #print "set up materials"
        glEnable ( GL_COLOR_MATERIAL )
        glColorMaterial ( GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE )
        glMaterial(GL_FRONT, GL_SPECULAR, (0,0,0,1));
        glMaterial(GL_FRONT, GL_EMISSION, (0,0,0,1));
        glFinish()

        #print "set up camera"
	self.camera.setProjection()

    def setViewingVolume(self,bbox):
        print "bbox=",bbox
        x0,y0,z0 = bbox[0]
        x1,y1,z1 = bbox[1]
        corners = [[x,y,z] for x in [x0,x1] for y in [y0,y1] for z in [z0,z1]]
        self.camera.lookAt(array(corners))
        print self.camera.center,self.camera.eye
        self.camera.setProjection()
         
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
	self.camera.setProjection()
        self.display()

