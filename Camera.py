#!/usr/bin/env python
"""Camera 0.1 (C) Benedict Verhegghe

This class defines a camera for OpenGL rendering. It lets you manipulate
the camera position and viewing direction as well as the lens parameters.

The default camera is at [0,0,1] and aims at point [0,0,0], i.e. looking
in the -z direction. Near and far clipping planes are by default set to
0.1, resp 10 times the camera distance.

"""

import sys,math

from OpenGL.GL import *
from OpenGL.GLU import *

from vector import *

class Camera:
    """This class defines a camera.

    Position (eye) : position of the camera
    Scene center (center) : the point the camera is looking at.
    Up Vector
    Twist angle
    Viewing direction (rotx,roty,rotz)
    Lens angle (fovy)
    Aspect ratio (aspect)
    Clip (front/back)
    Perspective/Orthogonal
    """

    def __init__(self):
        """Create a new camera at position (0,0,0) looking along the -z axis"""
        self.setEye(0.,0.,0.)
        self.setCenter(0.,0.,-1.)
        self.setTwist(0.)
        self.setLens(45.,4./3.)
        self.setClip(0.1,10.)
        self.setPerspective(True)

    # Camera position and viewing direction

    def setEye(self,x,y,z):
        """Set the camera position"""
        self.eye = [x,y,z]

    def setCenter(self,x,y,z):
        """Set the center of the scene.

        This defines the direction of the camera axis and the focus distance.
        It will also define the default front and back clipping planes.
        """
        self.center = [x,y,z]

    def setTwist(self,twist):
        """Set the twist angle of the camera."""
        self.twist = twist

    def getRelPos(self):
        """Return the relative position of the camera"""
        return cartesianToSpherical(diff(self.eye,self.center))

    def getUpVector(self):
        """Return the up vector of the camera.

        The Up vector is computed from the tilt and twist angles"""
        sc = self.getRelPos()
        x,y,z = sphericalToCartesian([self.twist, sc[1], 1])
        return [ x,z,-y ]
        
    def loadMatrix(self):
        """Load the camera transformation matrix"""
        print "center = ",self.center
        print "eye = ",self.eye
        print "twist = ",self.twist
        print "up = ",self.getUpVector()
        gluLookAt(*(self.eye + self.center +self.getUpVector()))

    def dolly(self,val):
        """Move the camera eye towards/away from the scene center.

        This has the effect of zooming. A value > 1 zooms out,
        a value < 1 zooms in. The resulting enlargement of the view
        will approximately be 1/val.
        A zero value will move the camera to the center of the scene.
        The front and back clipping planes may need adjustment after
        a dolly operation.
        """
        eye = pointOf(self.center,self.eye,val)
        self.setEye(*eye)

    def rotate(self,val,axis=0):
        """Rotate the camera around vert/hor axis through the center.

        The camera is rotated around an axis through the center point
        and parallel with the y-axis. The viewing axis of the camera
        remains directed at the center.
        This has the effect of rotating the scene around the axis.
        A positive value rotates the camera around the pos y-axis.
        The value is specified in degrees.
        """
        sc = cartesianToSpherical(diff(self.eye,self.center))
        sc[axis] += val
        eye = add(self.center,sphericalToCartesian(sc))
        self.setEye(*eye)

    def pan(self,val):
        """Rotate the camera right/left around its own vertical axis.

        The camera is rotated around an axis through the eye point
        and parallel with the y-axis. The viewing axis of the camera
        will move away from the center. This has the effect of panning.
        A positive value rotates the camera around the pos y-axis.
        The value is specified in degrees.
        """
        az,el,di = cartesianToSpherical(diff(self.center,self.eye))
        center = add(self.eye,sphericalToCartesian([az+val,el,di]))
        self.setCenter(*center)

    def tilt(self,val):
        """Rotate the camera up/down around its own horizontal axis.

        The camera is rotated around an axis through the eye point
        and parallel with the y-axis and perpendicular to the viewing axis.
        This has the effect of a vertical pan.
        A positive value tilts the camera up, shifting the scene down.
        The value is specified in degrees.
        """
        az,el,di = cartesianToSpherical(diff(self.center,self.eye))
        center = add(self.eye,sphericalToCartesian([az,el+val,di]))
        self.setCenter(*center)

    def move(self,translation):
        """Move the camera over translation vector in global coordinates.

        This has the effect moving the scene in opposite direction.
        """
        eye = add(self.eye,translation)
        center = add(self.center,translation)
        self.setEye(*eye)
        self.setCenter(*center)

    def truck(self,val):
        """Move the camera translation vector in local coordinates.

        This has the effect moving the scene in opposite direction.
        Positive coordinates mean:
          first  coordinate : truck right,
          second coordinate : pedestal up,
          third  coordinate : dolly out.
        """ 
        pass
        

 
    # Camera viewing parameters

    def setLens(self,fovy=None,aspect=None):
        """Set the field of view of the camera.

        We set the field of view by the vertical opening angle fovy
        and the aspect ratio (width/height) of the viewing volume.
        A parameter that is not specified is left unchanged.
        """
        if fovy: self.fovy = fovy
        if aspect: self.aspect = aspect

##    def setFrustum(self):
##        """Set the frustum parameters from camera parameters"""
##        if self.near and self.fovy and self.aspect:
##            self.top = self.near * math.tan(math.radians(self.fovy/2))
##            self.bottom = -self.top
##            self.right = self.top*self.aspect
##            self.left = self.bottom*self.aspect
        
    def setClip(self,near,far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near,self.far = near,far
        else:
            print "Error: Invalid Near/Far clipping values""" 
        
    def setClipRel(self,near,far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near,self.far = near,far
        else:
            print "Error: Invalid Near/Far clipping values""" 

    def setPerspective(self,on=True):
        """Set perspective on or off"""
        self.perspective = on

    def setProjection(self):
        """Load the projection/perspective matrix."""
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
        if self.perspective:
            gluPerspective(self.fovy,self.aspect,self.near,self.far)
        else:
            glOrtho(self.left,self.right,self.top,self.bottom,self.near,self.far)
	glMatrixMode(GL_MODELVIEW)     

    def zoom(self,val=2):
        """Zoom in/out by shrinking/enlarging the camera view angle.

        The zoom factor is relative to the current setting.
        Use setFovy() to specify an absolute setting.
        """
        if val>0:
            self.setFovy(self.fovy/val)
        self.setClip(dist,2*dist+size[2])


if __name__ == "__main__":
    
    from OpenGL.GLUT import *
   
    def init():
        glClearColor (0.0, 0.0, 0.0, 0.0)
        glShadeModel (GL_FLAT)

    def display():
        global cam
        glClear (GL_COLOR_BUFFER_BIT)
        glColor3f (1.0, 1.0, 1.0)
        glLoadIdentity ()             # clear the matrix
        cam.loadMatrix()
        glutWireCube (1.0)
        glFlush ()

    def reshape (w, h):
        glViewport (0, 0, w, h)
        glMatrixMode (GL_PROJECTION)
        glLoadIdentity ()
        glFrustum (-1.0, 1.0, -1.0, 1.0, 1.5, 20.0)
        glMatrixMode (GL_MODELVIEW)

    def keyboard(key, x, y):
        global cam
        if key == 27:
            sys.exit()
        elif key == 'd':
            cam.dolly(1.1)
        elif key == 'D':
            cam.dolly(0.9)
        elif key == 'r':
            cam.rotate(5.)
        elif key == 'R':
            cam.rotate(-5.)
        elif key == 's':
            cam.rotate(5.,1)
        elif key == 'S':
            cam.rotate(-5.,1)
        elif key == 'p':
            cam.pan(5.)
        elif key == 'P':
            cam.pan(-5.)
        elif key == 't':
            cam.tilt(1.)
        elif key == 'T':
            cam.tilt(-1.)
        elif key == 'h':
            cam.move([0.2,0.,0.])
        elif key == 'H':
            cam.move([-0.2,0.,0.])
        elif key == 'v':
            cam.move([0.,0.2,0.])
        elif key == 'V':
            cam.move([0.,-0.2,0.])
        else:
            print key
        display()
            

    def main():
        global cam
        glutInit(sys.argv)
        glutInitDisplayMode (GLUT_SINGLE | GLUT_RGB)
        glutInitWindowSize (500, 500) 
        #glutInitWindowPosition (100, 100)
        glutCreateWindow (sys.argv[0])
        init ()
        
        cam = Camera()
        cam.setEye(0.0, 0.0, 5.0)
        cam.setCenter(0.0, 0.0, 0.0)
        cam.setTwist(0.0)

        glutDisplayFunc(display) 
        glutReshapeFunc(reshape)
        glutKeyboardFunc(keyboard)
        glutMainLoop()
        return 0

    main()
