#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.2 Release Mon Jan  3 14:54:38 2005
## pyFormex is a python implementation of Formex algebra
## Homepage: http://pyformex.berlios.de/
## Copyright (C) 2004 Benedict Verhegghe (benedict.verhegghe@ugent.be)
## Copyright (C) 2004 Bart Desloovere (bart.desloovere@telenet.be)
## Distributed under the General Public License, see file COPYING for details
##
"""camera 0.1 (C) Benedict Verhegghe"""

import sys,math

import OpenGL.GL as GL
import OpenGL.GLU as GLU

from vector import *

class Camera:
    """This class defines a camera for OpenGL rendering.

    It provides functions for manipulating the camera position and viewing
    direction as well as the lens parameters.

    The camera viewing line can be defined by two points : the position of
    the camera and the center of the scene the camera is looking at.
    To enable continuous camera rotations however, it is essential that the
    camera angles are stored as such, and not be calculated from the camera
    position and the center point, because the transformation from cartesian
    to spherical coordinates is not unique.
    Therefore we store the camera as follows:
        ctr : [ x,y,z ] : the reference point of the camera : this is always
              a point on the viewing axis. Usualy, it is the center point of
              the scene we are looking at.
        eye : [ long,lat,dist ] : relative position of the camera with respect
              to the center point. This is measured in spherical coordinates:
              long is the rotation around the y-axis,
              lat is the rotation around the rotated x-axis,
              dist is the distance from the center.
              
        twist : rotation angle around the camera's viewing axis
        
    The default camera is at [0,0,1] and aims at point [0,0,0],
    i.e. looking in the -z direction. Near and far clipping planes are by
    default set to 0.1, resp 10 times the camera distance.
    
    Position (eye) : position of the camera
    Scene center (ctr) : the point the camera is looking at.
    Up Vector : a vector pointing up from the camera.
    Viewing direction (rotx,roty,rotz)
    Lens angle (fovy)
    Aspect ratio (aspect)
    Clip (front/back)
    Perspective/Orthogonal
    """

    def __init__(self,center=[0.,0.,0.],position=[0.,0.,1.],twist=0.):
        """Create a new camera at position (0,0,1) looking along the -z axis"""
        self.setCenter(*center)
        self.setEye(*position)
        self.setTwist(twist)
        self.setLens(45.,4./3.)
        self.setClip(0.1,10.)
        self.setPerspective(True)

    # Camera position and viewing direction
    # !! These functions do not automatically reload the transformation matrix
    # !! Clients should explicitely call loadMatrix() before displaying

    def setCenter(self,x,y,z):
        """Set the center of the camera in global cartesian coordinates."""
        self.ctr = [x,y,z]

    def setEye(self,long,lat,dist):
        """Set the position of the camera in relative spherical coordinates.

        We store the position of the camera in spherical coordinates,
        relative to the center. This allows for easy camera movements.
        Longitude (azimuth) and latitude (elevation) are in degrees.
        """
        self.eye = [long % 360,lat % 360,dist]

    def setDirection(self,long,lat):
        self.eye[0] = long % 360
        self.eye[1] = lat % 360

    def setDistance(self,dist):
        self.eye[2] = dist

    def setTwist(self,t):
        self.twist = t % 360
        
    def getCenter(self):
        """Return the camera reference point (the scene center)."""
        return self.ctr[0:2]
        
    def getEye(self):
        """Return the camera eye."""
        return self.eye[0:2]
        
    def getDistance(self):
        """Return the camera distance from the center."""
        return self.eye[2]
        
    def getAngles(self):
        """Return the three rotation angles of the camera."""
        return [ -self.eye[1], self.eye[0], self.twist ]
        
    def getPosition(self):
        """Return the cartesian coordinates of the camera (eye)."""
        return add(self.ctr,sphericalToCartesian(self.eye))

    def dolly(self,val):
        """Move the camera eye towards/away from the scene center.

        This has the effect of zooming. A value > 1 zooms out,
        a value < 1 zooms in. The resulting enlargement of the view
        will approximately be 1/val.
        A zero value will move the camera to the center of the scene.
        The front and back clipping planes may need adjustment after
        a dolly operation.
        """
        self.eye[2] *= val

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
            self.eye[axis] = (self.eye[axis] + val) % 360
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
            pos = self.getPosition()
            self.eye[axis] = (self.eye[axis] + val) % 360
            center = diff(pos,sphericalToCartesian(self.eye))
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

        This has the effect of moving the scene in opposite direction.
        Positive coordinates mean:
          first  coordinate : truck right,
          second coordinate : pedestal up,
          third  coordinate : dolly out.
        """
        #pos = self.getPosition()
        ang = self.getAngles()
        tr = [translation]
        for i in [1,0,2]:
            r = rotationMatrix(i,ang[i])
            tr = matrixMultiply(tr, r)
        self.move(tr[0])
        

    # Camera Lens Setting.
    #
    # These include :
    #   - the vertical lens opening angle (fovy),
    #   - the aspect ratio (aspect = width/height)
    #   - the front and back clipping planes (near,far)
    #
    # These functions do not auto-reload the projection matrix, so you
    # do not need to make the GL-environment current before using them.
    # The client has to explicitely call the loadProjection() method to
    # make the settings acive 
    # These functions will flag a change in the camera settings, which
    # can be tested by your display() function to know if it has to reload
    # the projection matrix.

    def setLens(self,fovy=None,aspect=None):
        """Set the field of view of the camera.

        We set the field of view by the vertical opening angle fovy
        and the aspect ratio (width/height) of the viewing volume.
        A parameter that is not specified is left unchanged.
        """
        if fovy: self.fovy = min(abs(fovy),180)
        if aspect: self.aspect = abs(aspect)
        self.lensChanged = True
        
    def setClip(self,near,far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near,self.far = near,far
            self.lensChanged = True
        else:
            print "Error: Invalid Near/Far clipping values""" 
        self.lensChanged = True
        
    def setClipRel(self,near,far):
        """Set the near and far clipping planes"""
        if near > 0 and near < far:
            self.near,self.far = near,far
            self.lensChanged = True
        else:
            print "Error: Invalid Near/Far clipping values""" 

    def setPerspective(self,on=True):
        """Set perspective on or off"""
        self.perspective = on
        self.lensChanged = True

    def zoom(self,val=0.5):
        """Zoom in/out by shrinking/enlarging the camera view angle.

        The zoom factor is relative to the current setting.
        Use setFovy() to specify an absolute setting.
        """
        if val>0:
            self.fovy *= val
        #self.setClip(dist,2*dist+size[2])
        #print "Lens = ",self.fovy,self.aspect
        self.lensChanged = True


    # Finally the activation of the camera settings
    #
    # You should make the GL environment current before calling
    # these. Typically your OpenGL widget will have a display() function
    # like this:
    #     self.makeCurrent()
    #     camera.loadProjection()
    #     camera.loadMatrix()
    

    def loadMatrix(self):
        """Load the camera transformation matrix.

        The caller will have to setup the correct GL environment beforehand.
        He also should make sure that matrix mode is GL_MODELVIEW. Since
        this is usually the default, we do not set it here.
        """
        #print "Center = ",self.getCenter()
        #print "Eye = ",self.getEye()
        #print "Position = ",self.getPosition()
        #print "Angles = ",self.getAngles()
        rot = self.getAngles()
        eye = self.getPosition()
        GL.glRotatef(-rot[2], 0.0, 0.0, 1.0)
        GL.glRotatef(-rot[0], 1.0, 0.0, 0.0)
        GL.glRotatef(-rot[1], 0.0, 1.0, 0.0)
        GL.glTranslatef(-eye[0],-eye[1],-eye[2])

    def loadProjection(self,force=False):
        """Load the projection/perspective matrix.

        The caller will have to setup the correct GL environment beforehand.
        No need to set matrix mode though. This function will switch to
        GL_PROJECTION mode before loading the matrix, and go back to
        GL_MODELVIEW mode on exit.

        This function does it best at autodetecting changes in the lens
        settings, and will only reload the matrix if such changes are
        detected. You can optionally force loading the matrix.
        """
        if self.lensChanged or force:
            GL.glMatrixMode(GL.GL_PROJECTION)
            GL.glLoadIdentity()
            if self.perspective:
                GLU.gluPerspective(self.fovy,self.aspect,self.near,self.far)
            else:
                GL.glOrtho(self.left,self.right,self.top,self.bottom,self.near,self.far)
            GL.glMatrixMode(GL.GL_MODELVIEW)     


if __name__ == "__main__":
    
    from OpenGL.GLUT import *
   
    def init():
        GL.glClearColor (0.0, 0.0, 0.0, 0.0)
        GL.glShadeModel (GL.GL_FLAT)

    def display():
        global cam
        GL.glClear (GL.GL_COLOR_BUFFER_BIT)
        GL.glColor3f (1.0, 1.0, 1.0)
        GL.glLoadIdentity ()             # clear the matrix
        cam.loadMatrix()
        glutWireCube (1.0)
        GL.glFlush ()

    def reshape (w, h):
        GL.glViewport (0, 0, w, h)
        GL.glMatrixMode (GL.GL_PROJECTION)
        GL.glLoadIdentity ()
        GL.glFrustum (-1.0, 1.0, -1.0, 1.0, 1.5, 20.0)
        GL.glMatrixMode (GL.GL_MODELVIEW)

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
            cam.setEye(0.,0.,5.)
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
