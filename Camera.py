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
    Viewing direction (rotx,roty,rotz)
    
    For enabling continuous rotations, it is essential that the camera angles
    are stored as such, and not be calculated form the camera position and
    center point, because the transformation from cartesian to spherical
    coordinates is not unique.
    Therefore we store the camera as follows:
        center : [ x,y,z ] : the reference point of the camera : this is always
                a point on the viewing axis. 
        pos : [ long,lat,dist ] : relative position in spherical coordinates
                of the camera with respect to the center point. 
        twist : rotation angles around the camera's viewing axis
   
    Lens angle (fovy)
    Aspect ratio (aspect)
    Clip (front/back)
    Perspective/Orthogonal
    """

    def __init__(self,center=[0.,0.,0.],position=[0.,0.,1.],twist=0.):
        """Create a new camera at position (0,0,1) looking along the -z axis"""
        self.setCenter(*center)
        self.setPos(*position)
        self.setTwist(twist)
        self.setLens(45.,4./3.)
        self.setClip(0.1,10.)
        self.setPerspective(True)

    # Camera position and viewing direction

    def setCenter(self,x,y,z):
        """Set thecenter of the camera in cartesian coordinates."""
        self.ctr = [x,y,z]

    def setPos(self,x,y,z):
        self.pos = [x % 360,y % 360,z]

    def setTwist(self,t):
        self.twist = t % 360
        
    def getEye(self):
        """Return the cartesian coordinates of the camera (eye)."""
        return add(self.ctr,sphericalToCartesian(self.pos))
        
    def getAngles(self):
        """Return the three rotation angles of the camera."""
        return [ -self.pos[1], self.pos[0], self.twist ]

    def setEye(self,lat,long,dist):
        """Set the position of the camera in relative spherical coordinates.

        We store the position of the camera in spherical coordinates,
        relative to the center. This allows for easy camera movements.
        Latitude (azimuth) and longitude (elevation) are in degrees.
        lat is the rotation around the y-axis, (0 is z-axis)
        long is the rotation around the (rotated) x-axis, (0 is x-z plane)
        dist is the distance from the center.
        """
        self.eye = [lat,long,dist]

    def loadMatrix(self):
        """Load the camera transformation matrix"""
        print "Center = ",self.ctr
        print "Position = ",self.pos
        print "Eye = ",self.getEye()
        print "Angles = ",self.getAngles()
        rot = self.getAngles()
        eye = self.getEye()
        glRotatef(-rot[2], 0.0, 0.0, 1.0)
        glRotatef(-rot[0], 1.0, 0.0, 0.0)
        glRotatef(-rot[1], 0.0, 1.0, 0.0)
        glTranslatef(-eye[0],-eye[1],-eye[2])

    def dolly(self,val):
        """Move the camera eye towards/away from the scene center.

        This has the effect of zooming. A value > 1 zooms out,
        a value < 1 zooms in. The resulting enlargement of the view
        will approximately be 1/val.
        A zero value will move the camera to the center of the scene.
        The front and back clipping planes may need adjustment after
        a dolly operation.
        """
        self.pos[2] *= val

    def rotate(self,val,axis=0):
        """Rotate the camera around axis through the center.

        The camera is rotated around an axis through the center point
        and parallel with the y-axis. The viewing axis of the camera
        remains directed at the center.
        This has the effect of rotating the scene around the axis.
        A positive value rotates the camera around the pos y-axis.
        The value is specified in degrees.
        """
        if axis==0 or axis ==1:
            self.pos[axis] = (self.pos[axis] + val) % 360
        elif axis==2:
            self.twist = (self.twist + val) % 360

    def pan(self,val,axis=0):
        """Rotate the camera around axis through its eye. 

        The camera is rotated around an axis through the eye point.
        For axes 0 and 1, this will move the center, creating a panning
        effect. The default axis is parallel to the y-axis, resulting in
        horizontal panning. For vertical panning (axis=1) a convenience
        alias tilt is created.
        For axis = 2 the operation is equivalent to the rotate operation.
        """
        if axis==0 or axis ==1:
            eye = self.getEye()
            self.pos[axis] = (self.pos[axis] + val) % 360
            center = diff(eye,sphericalToCartesian(self.pos))
            self.setCenter(*center)
        elif axis==2:
            self.twist = (self.twist + val) % 360

    def tilt(self,val):
        """Rotate the camera up/down around its own horizontal axis.

        The camera is rotated around and perpendicular to the plane of the
        y-axis and the viewing axis. This has the effect of a vertical pan.
        A positive value tilts the camera up, shifting the scene down.
        The value is specified in degrees.
        """
        self.pan(val,1)

    def move(self,translation):
        """Move the camera over translation vector in global coordinates.

        The center of the camera is moved over the specified translation
        vector. This has the effect of moving the scene in opposite direction.
        """
        center = add(self.ctr,translation)
        self.setCenter(*center)

    def truck(self,translation):
        """Move the camera translation vector in local coordinates.

        This has the effect moving the scene in opposite direction.
        Positive coordinates mean:
          first  coordinate : truck right,
          second coordinate : pedestal up,
          third  coordinate : dolly out.
        """
        eye = self.getEye()
        ang = self.getAngles()
        tr = [translation]
        print "orig:",tr
        for i in [1,0,2]:
            r = rotationMatrix(i,ang[i])
            print r
            tr = matrixMultiply(tr, r)
            print "na trf ",i,tr
        self.move(tr[0])
        

    # Camera viewing parameters

    def setLens(self,fovy=None,aspect=None):
        """Set the field of view of the camera.

        We set the field of view by the vertical opening angle fovy
        and the aspect ratio (width/height) of the viewing volume.
        A parameter that is not specified is left unchanged.
        """
        if fovy: self.fovy = fovy
        if aspect: self.aspect = aspect
        
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

    def loadProjection(self):
        """Load the projection/perspective matrix."""
	glMatrixMode(GL_PROJECTION)
	glLoadIdentity()
        if self.perspective:
            gluPerspective(self.fovy,self.aspect,self.near,self.far)
        else:
            glOrtho(self.left,self.right,self.top,self.bottom,self.near,self.far)
	glMatrixMode(GL_MODELVIEW)     

    def zoom(self,val=0.5):
        """Zoom in/out by shrinking/enlarging the camera view angle.

        The zoom factor is relative to the current setting.
        Use setFovy() to specify an absolute setting.
        """
        if val>0:
            self.fovy *= val
        #self.setClip(dist,2*dist+size[2])
        print "Lens = ",self.fovy,self.aspect
        self.loadProjection()


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
        elif key == 'w':
            cam.rotate(5.,2)
        elif key == 'W':
            cam.rotate(-5.,2)
        elif key == 'p':
            cam.pan(5.)
        elif key == 'P':
            cam.pan(-5.)
        elif key == 't':
            cam.tilt(5.)
        elif key == 'T':
            cam.tilt(-5.)
        elif key == 'h':
            cam.move([0.2,0.,0.])
        elif key == 'H':
            cam.move([-0.2,0.,0.])
        elif key == 'v':
            cam.move([0.,0.2,0.])
        elif key == 'V':
            cam.move([0.,-0.2,0.])
        elif key == '+':
            cam.zoom(0.8)
        elif key == '-':
            cam.zoom(1.25)
        elif key == 'x':
            cam.truck([0.5,0.,0.])
        elif key == 'X':
            cam.truck([-0.5,0.,0.])
        elif key == 'y':
            cam.truck([0.,0.5,0.])
        elif key == 'Y':
            cam.truck([0.,-0.5,0.])
        elif key == 'z':
            cam.truck([0.,0.,0.5])
        elif key == 'Z':
            cam.truck([0.,0.,-0.5])
        elif key == '=':
            cam.setCenter(0.,0.,0.)
            cam.setPos(0.,0.,5.)
            cam.setTwist(0.)
        elif key == 'o':
            cam.setPerspective(not cam.perspective)
            cam.loadProjection
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
        
        cam = Camera(center=[0.,0.,0.],position=[0.,0.,5.])
        cam.setLens(45.,1.)

        glutDisplayFunc(display) 
        glutReshapeFunc(reshape)
        glutKeyboardFunc(keyboard)
        glutMainLoop()
        return 0

    main()
