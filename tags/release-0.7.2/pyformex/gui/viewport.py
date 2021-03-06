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
"""viewport.py: Interactive OpenGL Canvas.

This module implements user interaction with the OpenGL canvas.
QtCanvas is a single interactive OpenGL canvas, while MultiCanvas
implements a dynamic array of multiple canvases.

The basic OpenGL drawing functionality is implemented in the canvas module.
"""

import pyformex as GD

from PyQt4 import QtCore, QtGui, QtOpenGL
from OpenGL import GL

from numtools import Collection
import canvas
import decors
import image
import utils
import toolbar

import math

from coords import Coords
from numpy import asarray,where,unique,intersect1d,setdiff1d,empty,append,delete


# Some 2D vector operations
# We could do this with the general functions of coords.py,
# but that would be overkill for this simple 2D vectors

def dotpr (v,w):
    """Return the dot product of vectors v and w"""
    return v[0]*w[0] + v[1]*w[1]

def length (v):
    """Return the length of the vector v"""
    return math.sqrt(dotpr(v,v))

def projection(v,w):
    """Return the (signed) length of the projection of vector v on vector w."""
    return dotpr(v,w)/length(w)


# signals
CANCEL = QtCore.SIGNAL("Cancel")
DONE   = QtCore.SIGNAL("Done")
WAKEUP = QtCore.SIGNAL("Wakeup")

# keys
ESC = QtCore.Qt.Key_Escape
RETURN = QtCore.Qt.Key_Return    # Normal Enter
ENTER = QtCore.Qt.Key_Enter      # Num Keypad Enter

# mouse actions
PRESS = 0
MOVE = 1
RELEASE = 2

# mouse buttons
LEFT = QtCore.Qt.LeftButton
MIDDLE = QtCore.Qt.MidButton
RIGHT = QtCore.Qt.RightButton

# modifiers
NONE = QtCore.Qt.NoModifier
SHIFT = QtCore.Qt.ShiftModifier
CTRL = QtCore.Qt.ControlModifier
ALT = QtCore.Qt.AltModifier
ALLMODS = SHIFT | CTRL | ALT


def modifierName(mod):
    return {NONE:'NONE',SHIFT:'SHIFT',CTRL:'CTRL',ALT:'ALT'}.get(mod,'UNKNOWN')


############### OpenGL Format #################################

opengl_format = None

def setOpenGLFormat():
    """Set the correct OpenGL format.

    Omn a correctly installed system, the default should do well.
    The default OpenGL format can be changed by command line options.
    --dri   : use the DIrect Rendering Infrastructure
    --nodri : do not use the DRI
    --alpha : enable the alpha buffer 
    """
    global opengl_format
    fmt = QtOpenGL.QGLFormat.defaultFormat()
    if GD.options.dri is not None:
        fmt.setDirectRendering(GD.options.dri)
##     if GD.options.alpha:
##         fmt.setAlpha(True)
    QtOpenGL.QGLFormat.setDefaultFormat(fmt)
    opengl_format = fmt
    if GD.options.debug:
        print OpenGLFormat()
    return fmt

def getOpenGLContext():
    ctxt = QtOpenGL.QGLContext.currentContext()
    if ctxt is not None:
        printOpenGLContext(ctxt)
    return ctxt

def OpenGLFormat(fmt=None):
    """Some information about the OpenGL format."""
    if fmt is None:
        fmt = opengl_format
    s = """
OpenGL: %s
OpenGL Version: %s
OpenGLOverlays: %s
Double Buffer: %s
Depth Buffer: %s
RGBA: %s
Alpha Channel: %s
Accumulation Buffer: %s
Stencil Buffer: %s
Stereo: %s
Direct Rendering: %s
Overlay: %s
Plane: %s
Multisample Buffers: %s
""" % (fmt.hasOpenGL(),
       str(fmt.openGLVersionFlags()),
       fmt.hasOpenGLOverlays(),
       fmt.doubleBuffer(),fmt.depth(),
       fmt.rgba(),fmt.alpha(),
       fmt.accum(),
       fmt.stencil(),
       fmt.stereo(),
       fmt.directRendering(),
       fmt.hasOverlay(),
       fmt.plane(),
       fmt.sampleBuffers()
       )
    return s


def printOpenGLContext(ctxt):
    if ctxt:
        print "context is valid: %d" % ctxt.isValid()
        print "context is sharing: %d" % ctxt.isSharing()
    else:
        print "No OpenGL context yet!"


################# Single Interactive OpenGL Canvas ###############

class QtCanvas(QtOpenGL.QGLWidget,canvas.Canvas):
    """A canvas for OpenGL rendering.

    This class provides interactive functionality for the OpenGL canvas
    provided by the canvas.Canvas class.
    
    Interactivity is highly dependent on Qt4. Putting the interactive
    functions in a separate class makes it esier to use the Canvas class
    in non-interactive situations or combining it with other GUI toolsets.
    """
    ##
    ##
    ##  IMPORTANT : The mouse functionality should (and will) be moved
    ##              to the MultiCanvas class!
    ##
    ##  The cursor shape can/should stay here 

    # Cursor shapes used on canvas.
    cursor_shape = { 'default': QtCore.Qt.ArrowCursor,
                     'pick'   : QtCore.Qt.CrossCursor, 
                     'busy'   : QtCore.Qt.BusyCursor,
                     }
    
    def __init__(self,*args):
        """Initialize an empty canvas with default settings."""
        QtOpenGL.QGLWidget.__init__(self,*args)
        self.setMinimumSize(32,32)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        canvas.Canvas.__init__(self)
        self.cursor = None
        self.setCursorShape('default')
        self.button = None
        self.mod = NONE
        self.mousefnc = { NONE:{}, SHIFT:{}, CTRL:{}, ALT:{} }
        # Initial mouse funcs are dynamic handling
        # ALT is initially same as NONE and should never be changed
        for mod in (NONE,ALT):
            self.setMouse(LEFT,self.dynarot,mod) 
            self.setMouse(MIDDLE,self.dynapan,mod) 
            self.setMouse(RIGHT,self.dynazoom,mod)
        self.selection_mode = None
        self.selection = Collection()
        self.pick_func = {
            'actor'  : self.pick_actors,
            'element': self.pick_elements,
            'point'  : self.pick_points,
            'edge'   : self.pick_edges,
            'number' : self.pick_numbers,
            }
       

    def setCursorShape(self,t):
        if t not in QtCanvas.cursor_shape.keys():
            t = 'default'
        self.setCursor(QtGui.QCursor(QtCanvas.cursor_shape[t]))


    def setMouse(self,button,func,mod=NONE):
        self.mousefnc[mod][button] = func


    def getMouseFunc(self):
        """Return the mouse function bound to self.button and self.mod"""
        return self.mousefnc.get(int(self.mod),{}).get(self.button,None)


    def start_selection(self,mode,filtr):
        """Start an interactive picking mode.

        If selection mode was already started, mode is disregarded and
        this can be used to change the filter method.
        """
        if self.selection_mode is None:
            GD.debug("START SELECTION MODE: %s" % mode)
            self.setMouse(LEFT,self.mouse_pick)
            self.setMouse(LEFT,self.mouse_pick,SHIFT)
            self.setMouse(LEFT,self.mouse_pick,CTRL)
            self.setMouse(RIGHT,self.emit_done)
            self.setMouse(RIGHT,self.emit_cancel,SHIFT)
            self.connect(self,DONE,self.accept_selection)
            self.connect(self,CANCEL,self.cancel_selection)
            self.setCursorShape('pick')
            self.selection_mode = mode
            self.selection_front = None

        if filtr == 'none':
            filtr = None
        GD.debug("SET SELECTION FILTER: %s" % filtr)
        self.selection_filter = filtr
        if filtr is None:
            self.selection_front = None
        self.selection.clear()
        self.selection.setType(self.selection_mode)
            

    def wait_selection(self):
        """Wait for the user to interactively make a selection."""
        self.selection_timer = QtCore.QThread
        self.selection_busy = True
        self.number_selection = False
        while self.selection_busy:
            self.selection_timer.msleep(20)
            GD.app.processEvents()

    def finish_selection(self):
        """End an interactive picking mode."""
        GD.debug("END SELECTION MODE")
        self.setCursorShape('default')
        self.setMouse(LEFT,self.dynarot)
        self.setMouse(LEFT,None,SHIFT)
        self.setMouse(LEFT,None,CTRL)
        self.setMouse(RIGHT,self.dynazoom)
        self.setMouse(RIGHT,None,SHIFT)
        self.disconnect(self,DONE,self.accept_selection)
        self.disconnect(self,CANCEL,self.cancel_selection)
        self.selection_mode = None

    def accept_selection(self,clear=False):
        """Cancel an interactive picking mode.

        If clear == True, the current selection is cleared.
        """
        GD.debug("CANCEL SELECTION MODE")
        self.selection_accepted = True
        if clear:
            self.selection.clear()
            self.selection_accepted = False
        self.selection_canceled = True
        self.selection_busy = False

    def cancel_selection(self):
        """Cancel an interactive picking mode and clear the selection."""
        self.accept_selection(clear=True)
    
    def select_numbers(self):
        # selection by clicking on a list item
        selecteditems = self.number_widget.getResult()
        self.selection.set(map(int,selecteditems),0)
        self.number_selection = True
        self.selection_busy = False
    
    def pick(self,mode='actor',single=False,func=None,filter=None):
        """Interactively pick objects from the viewport.

        - mode: defines what to pick : one of
        ['actor','element','point','number','edge']
        - single: if True, the function returns as soon as the user ends
        a picking operation. The default is to let the user
        modify his selection and only to return after an explicit
        cancel (ESC or right mouse button).
        - func: if specified, this function will be called after each
        atomic pick operation. The Collection with the currently selected
        objects is passed as an argument. This can e.g. be used to highlight
        the selected objects during picking.
        - filter: defines what elements to retain from the selection: one of
        [None,'closest,'connected'].
        The default (None) will return the complete selection.
        'closest' will only keep the element closest to the user.
        'connected' will only keep elements connected to
          - the closest element (set picked)
          - what is already in the selection (add picked).
          Currently this only works when picking mode is 'element' and
          for Actors having a partitionByConnection method.

        When the picking operation is finished, the selection is returned.
        The return value is always a Collection object.
        """
        self.selection_canceled = False
        self.start_selection(mode,filter)
        while not self.selection_canceled:
            self.wait_selection()
            if not self.selection_canceled and self.number_selection == False:
                # selection by mouse_picking
                self.pick_func[self.selection_mode]()
                if self.selection_filter is None:
                    if self.mod == NONE:
                        self.selection.set(self.picked)
                    elif self.mod == SHIFT:
                        self.selection.add(self.picked)
                    elif self.mod == CTRL:
                        self.selection.remove(self.picked)
                
                elif self.selection_filter == 'single':
                    if self.mod == NONE:
                        self.selection.set([self.closest_pick[0]])
                    elif self.mod == SHIFT:
                        self.selection.add([self.closest_pick[0]])
                    elif self.mod == CTRL:
                        self.selection.remove([self.closest_pick[0]])

                elif self.selection_filter == 'closest':
                    if self.selection_front is None or self.mod == NONE or \
                           (self.mod == SHIFT and self.closest_pick[1] < self.selection_front[1]):
                        self.selection_front = self.closest_pick
                        self.selection.set([self.closest_pick[0]])

                elif self.selection_filter == 'connected':
                    if self.mod == NONE:
                        self.selection_front = self.closest_pick
                        self.selection.set(self.picked)
                    elif self.mod == SHIFT:
                        self.selection.add(self.picked)
                    elif self.mod == CTRL:
                        self.selection.remove(self.picked)
                    if self.selection_front is None:
                        self.selection_front = self.closest_pick
                    actor,elem = map(int,self.selection_front[0])
                    A = self.actors[actor]
                    elems = self.selection.get(actor)
                    if elem in elems:
                        elem = A.connectedElements(elem,elems)
                    self.selection.set(elem,actor)
                if GD.canvas.numbers_visible == True:
                    # A list widget is visible, so when part numbers are added to /
                    # removed from the selection by mouse_picking, the corresponding
                    # list items will be selected / deselected.
                    selecteditems = map(int,GD.canvas.number_widget.getResult())
                    selection = self.selection.get(0)
                    add = map(str,setdiff1d(selection,selecteditems))
                    remove = map(str,setdiff1d(selecteditems,selection))
                    GD.canvas.number_widget.setSelected(add,True)
                    GD.canvas.number_widget.setSelected(remove,False)
                if func:
                    func(self.selection)
            if single:
                self.accept_selection()
        if func and not self.selection_accepted:
            func(self.selection)
        self.finish_selection()
        return self.selection
    

    def pickNumbers(self,*args,**kargs):
        """Go into number picking mode and return the selection."""
        return self.pick('numbers',*args,**kargs)


    def start_drawing(self):
        """Start an interactive drawing mode."""
        GD.debug("START DRAWING MODE")
        self.setMouse(LEFT,self.mouse_draw)
        self.setMouse(RIGHT,self.emit_done)
        self.setMouse(RIGHT,self.emit_cancel,SHIFT)
        self.connect(self,DONE,self.accept_drawing)
        self.connect(self,CANCEL,self.cancel_drawing)
        self.setCursorShape('pick')
        self.edit_mode = None
        self.drawing = empty((0,2,2),dtype=int)

    def wait_drawing(self):
        """Wait for the user to interactively draw a line."""
        self.drawing_timer = QtCore.QThread
        self.drawing_busy = True
        while self.drawing_busy:
            self.drawing_timer.msleep(20)
            GD.app.processEvents()

    def finish_drawing(self):
        """End an interactive drawing mode."""
        GD.debug("END DRAWING MODE")
        self.setCursorShape('default')
        self.setMouse(LEFT,self.dynarot)
        self.setMouse(RIGHT,self.dynazoom)
        self.setMouse(RIGHT,None,SHIFT)
        self.disconnect(self,DONE,self.accept_selection)
        self.disconnect(self,CANCEL,self.cancel_selection)

    def accept_drawing(self,clear=False):
        """Cancel an interactive drawing mode.

        If clear == True, the current drawing is cleared.
        """
        GD.debug("CANCEL DRAWING MODE")
        self.drawing_accepted = True
        if clear:
            self.drawing = empty((0,2,2),dtype=int)
            self.drawing_accepted = False
        self.drawing_canceled = True
        self.drawing_busy = False

    def cancel_drawing(self):
        """Cancel an interactive drawing mode and clear the drawing."""
        self.accept_drawing(clear=True)
    
    def edit_drawing(self,mode):
        """Edit an interactive drawing."""
        self.edit_mode = mode
        self.drawing_busy = False     

    def drawLinesInter(self,single=False,func=None):
        """Interactively draw lines on the canvas.

        - single: if True, the function returns as soon as the user ends
        a drawing operation. The default is to let the user
        draw multiple lines and only to return after an explicit
        cancel (ESC or right mouse button).
        - func: if specified, this function will be called after each
        atomic drawing operation. The current drawing is passed as
        an argument. This can e.g. be used to show the drawing.
        When the drawing operation is finished, the drawing is returned.
        The return value is a (n,2,2) shaped array.
        """
        self.drawing_canceled = False
        self.start_drawing()
        while not self.drawing_canceled:
            self.wait_drawing()
            if not self.drawing_canceled:
                if self.edit_mode: # an edit mode from the edit combo was clicked
                    if self.edit_mode == 'undo' and self.drawing.size != 0:
                        self.drawing = delete(self.drawing,-1,0)
                    elif self.edit_mode == 'clear':
                        self.drawing = empty((0,2,2),dtype=int)
                    self.edit_mode = None
                else: # a line was drawn interactively
                    self.drawing = append(self.drawing,self.drawn.reshape(-1,2,2),0)
                if func:
                    func(self.drawing)
            if single:
                self.accept_drawing()                
        if func and not self.drawing_accepted:
            func(self.drawing)
        self.finish_drawing()
        return self.drawing


######## QtOpenGL interface ##############################
        
    def initializeGL(self):
        if GD.options.debug:
            p = self.sizePolicy()
            print p.horizontalPolicy(), p.verticalPolicy(), p.horizontalStretch(), p.verticalStretch()
        self.initCamera()
        self.glinit()
        self.resizeGL(self.width(),self.height())
        self.setCamera()

    def	resizeGL(self,w,h):
        self.setSize(w,h)

    def	paintGL(self):
        if not self.mode2D:
            #GD.debugt("CANVAS DISPLAY")
            self.display()

    def getSize(self):
        return int(self.width()),int(self.height())

####### MOUSE EVENT HANDLERS ############################

    # Mouse functions can be bound to any of the mouse buttons
    # LEFT, MIDDLE or RIGHT.
    # Each mouse function should accept three possible actions:
    # PRESS, MOVE, RELEASE.
    # On a mouse button PRESS, the mouse screen position and the pressed
    # button are always saved in self.statex,self.statey,self.button.
    # The mouse function does not need to save these and can directly use
    # their values.
    # On a mouse button RELEASE, self.button is cleared, to avoid further
    # move actions.
    # Functions that change the camera settings should call saveMatrix()
    # when they are done.
    # ATTENTION! The y argument is positive upwards, as in normal OpenGL
    # operations!


    def dynarot(self,x,y,action):
        """Perform dynamic rotation operation.

        This function processes mouse button events controlling a dynamic
        rotation operation. The action is one of PRESS, MOVE or RELEASE.
        """
        if action == PRESS:
            w,h = self.getSize()
            self.state = [self.statex-w/2, self.statey-h/2 ]

        elif action == MOVE:
            w,h = self.getSize()
            # set all three rotations from mouse movement
            # tangential movement sets twist,
            # but only if initial vector is big enough
            x0 = self.state        # initial vector
            d = length(x0)
            if d > h/8:
                # GD.debug(d)
                x1 = [x-w/2, y-h/2]     # new vector
                a0 = math.atan2(x0[0],x0[1])
                a1 = math.atan2(x1[0],x1[1])
                an = (a1-a0) / math.pi * 180
                ds = utils.stuur(d,[-h/4,h/8,h/4],[-1,0,1],2)
                twist = - an*ds
                self.camera.rotate(twist,0.,0.,1.)
                self.state = x1
            # radial movement rotates around vector in lens plane
            x0 = [self.statex-w/2, self.statey-h/2]    # initial vector
            if x0 == [0.,0.]:
                x0 = [1.,0.]
            dx = [x-self.statex, y-self.statey]        # movement
            b = projection(dx,x0)
            if abs(b) > 5:
                val = utils.stuur(b,[-2*h,0,2*h],[-180,0,+180],1)
                rot =  [ abs(val),-dx[1],dx[0],0 ]
                self.camera.rotate(*rot)
                self.statex,self.statey = (x,y)
            self.update()

        elif action == RELEASE:
            self.update()
            self.camera.saveMatrix()

            
    def dynapan(self,x,y,action):
        """Perform dynamic pan operation.

        This function processes mouse button events controlling a dynamic
        pan operation. The action is one of PRESS, MOVE or RELEASE.
        """
        if action == PRESS:
            pass

        elif action == MOVE:
            w,h = self.getSize()
            dist = self.camera.getDist() * 0.5
            # get distance from where button was pressed
            dx,dy = (x-self.statex,y-self.statey)
            panx = utils.stuur(dx,[-w,0,w],[-dist,0.,+dist],1.0)
            pany = utils.stuur(dy,[-h,0,h],[-dist,0.,+dist],1.0)
            # print dx,dy,panx,pany
            self.camera.translate(panx,pany,0)
            self.statex,self.statey = (x,y)
            self.update()

        elif action == RELEASE:
            self.update()
            self.camera.saveMatrix()          

            
    def dynazoom(self,x,y,action):
        """Perform dynamic zoom operation.

        This function processes mouse button events controlling a dynamic
        zoom operation. The action is one of PRESS, MOVE or RELEASE.
        """
        if action == PRESS:
            self.state = [self.camera.getDist(),self.camera.fovy]

        elif action == MOVE:
            w,h = self.getSize()
            # hor movement is lens zooming
            f = utils.stuur(x,[0,self.statex,w],[180,self.state[1],0],1.2)
            #print "Lens Zooming: %s" % f
            self.camera.setLens(f)
            # vert movement is dolly zooming
            d = utils.stuur(y,[0,self.statey,h],[5,1,0.2],1.2)
            self.camera.setDist(d*self.state[0])
            self.update()

        elif action == RELEASE:
            self.update()
            self.camera.saveMatrix()


    def emit_done(self,x,y,action):
        """Emit a DONE event by clicking the mouse.

        This is equivalent to pressing the ENTER button."""
        if action == RELEASE:
            self.emit(DONE,())
            
    def emit_cancel(self,x,y,action):
        """Emit a CANCEL event by clicking the mouse.

        This is equivalent to pressing the ESC button."""
        if action == RELEASE:
            self.emit(CANCEL,())


    def draw_state_rect(self,x,y):
        """Store the pos and draw a rectangle to it."""
        self.state = x,y
        #GD.debug("Rect (%s,%s) - (%s,%s)" % (self.statex,self.statey,x,y))
        decors.drawRect(self.statex,self.statey,x,y)


    def mouse_pick(self,x,y,action):
        """Process mouse events during interactive picking.

        On PRESS, record the mouse position.
        On MOVE, create a rectangular picking window.
        On RELEASE, pick the objects inside the rectangle.
        """
        if action == PRESS:
            self.makeCurrent()
            self.update()
            self.begin_2D_drawing()
            self.swapBuffers()
            GL.glEnable(GL.GL_COLOR_LOGIC_OP)
            # An alternative is GL_XOR #
            GL.glLogicOp(GL.GL_INVERT)        
            # Draw rectangle
            self.draw_state_rect(x,y)
            self.swapBuffers()

        elif action == MOVE:
            # Remove old rectangle
            self.swapBuffers()
            self.draw_state_rect(*self.state)
            # Draw new rectangle
            self.draw_state_rect(x,y)
            self.swapBuffers()

        elif action == RELEASE:
            GL.glDisable(GL.GL_COLOR_LOGIC_OP)
            #self.swapBuffers()
            self.end_2D_drawing()

            x,y = (x+self.statex)/2., (y+self.statey)/2.
            w,h = abs(x-self.statex)*2., abs(y-self.statey)*2.
            if w <= 0 or h <= 0:
               w,h = GD.cfg.get('pick/size',(20,20))
            vp = GL.glGetIntegerv(GL.GL_VIEWPORT)
            self.pick_window = (x,y,w,h,vp)
            self.selection_busy = False


    def pick_actors(self,store_closest=False):
        """Set the list of actors inside the pick_window."""
        self.camera.loadProjection(pick=self.pick_window)
        self.camera.loadMatrix()
        stackdepth = 1
        npickable = len(self.actors)
        GL.glSelectBuffer(npickable*(3+stackdepth))
        GL.glRenderMode(GL.GL_SELECT)
        GL.glInitNames()
        for i,a in enumerate(self.actors):
            GD.debug("PICK actor %s = %s" % (i,a.list))
            GL.glPushName(i)
            GL.glCallList(a.list)
            GL.glPopName()
        buf = GL.glRenderMode(GL.GL_RENDER)
        self.picked = [ r[2][0] for r in buf]
        if store_closest and len(buf) > 0:
            d = asarray([ r[0] for r in buf ])
            dmin = d.min()
            w = where(d == dmin)[0][0]
            self.closest_pick = (self.picked[w], dmin)


    def pick_parts(self,obj_type,max_objects,store_closest=False):
        """Set the list of actor parts inside the pick_window.

        obj_type can be 'element', 'point' or 'edge'(SurfaceActor only)
        max_objects specifies the maximum number of objects

        The picked object numbers are stored in self.picked.
        If store_closest==True, the closest picked object is stored in as a
        tuple ( [actor,object] ,distance) in self.picked_closest
        """
        GD.debugt("PICKPARTS")
        self.camera.loadProjection(pick=self.pick_window)
        self.camera.loadMatrix()
        stackdepth = 2
        GL.glSelectBuffer(max_objects*(3+stackdepth))
        GL.glRenderMode(GL.GL_SELECT)
        GL.glInitNames()
        GD.debugt("pickGL from %s" % len(self.actors))
        for i,a in enumerate(self.actors):
            GL.glPushName(i)
            a.pickGL(obj_type)
            GL.glPopName()
        GD.debugt("getpickbuf")
        buf = GL.glRenderMode(GL.GL_RENDER)
        GD.debugt("translate getpickbuf")
        self.picked = [ r[2] for r in buf ]
        GD.debugt("store closest")
        if store_closest and len(buf) > 0:
            d = asarray([ r[0] for r in buf ])
            dmin = d.min()
            w = where(d == dmin)[0][0]
            self.closest_pick = (self.picked[w], dmin)
        GD.debugt("PICKPARTS DONE")


    def pick_elements(self):
        """Set the list of actor elements inside the pick_window."""
        npickable = 0
        for a in self.actors:
            npickable += a.nelems()
        self.pick_parts('element',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest' or\
                        self.selection_filter == 'connected'
                        )


    def pick_points(self):
        """Set the list of actor points inside the pick_window."""
        npickable = 0
        for a in self.actors:
            npickable += a.npoints()
        self.pick_parts('point',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest'
                        )


    def pick_edges(self):
        """Set the list of actor edges inside the pick_window."""
        npickable = 0
        for a in self.actors:
            if hasattr(a,'nedges'):
                npickable += a.nedges()
        self.pick_parts('edge',npickable,store_closest=\
                        self.selection_filter == 'single' or\
                        self.selection_filter == 'closest'
                        )


    def pick_numbers(self):
        """Return the numbers inside the pick_window."""
        self.camera.loadProjection(pick=self.pick_window)
        self.camera.loadMatrix()
        self.picked = [0,1,2,3]
        if self.numbers:
            self.picked = self.numbers.drawpick()


    def draw_state_line(self,x,y):
        """Store the pos and draw a line to it."""
        self.state = x,y
        #GD.debug("Rect (%s,%s) - (%s,%s)" % (self.statex,self.statey,x,y))
        decors.drawLine(self.statex,self.statey,x,y)


    def mouse_draw(self,x,y,action):
        """Process mouse events during interactive drawing.

        On PRESS, record the mouse position.
        On MOVE, draw a line.
        On RELEASE, add the line to the drawing.
        """
        if action == PRESS:
            self.makeCurrent()
            self.update()
            self.begin_2D_drawing()
            self.swapBuffers()
            GL.glEnable(GL.GL_COLOR_LOGIC_OP)
            # An alternative is GL_XOR #
            GL.glLogicOp(GL.GL_INVERT)        
            # Draw rectangle
            if self.drawing.size != 0:
                self.statex,self.statey = self.drawing[-1,-1]
            self.draw_state_line(x,y)
            self.swapBuffers()

        elif action == MOVE:
            # Remove old rectangle
            self.swapBuffers()
            self.draw_state_line(*self.state)
            # Draw new rectangle
            self.draw_state_line(x,y)
            self.swapBuffers()

        elif action == RELEASE:
            GL.glDisable(GL.GL_COLOR_LOGIC_OP)
            #self.swapBuffers()
            self.end_2D_drawing()

            self.drawn = asarray([[self.statex,self.statey],[x,y]])
            self.drawing_busy = False


    @classmethod
    def has_modifier(clas,e,mod):
        return ( e.modifiers() & mod ) == mod
        
    def mousePressEvent(self,e):
        """Process a mouse press event."""
        GD.gui.viewports.setCurrent(self)
        # on PRESS, always remember mouse position and button
        self.statex,self.statey = e.x(), self.height()-e.y()
        self.button = e.button()
        self.mod = e.modifiers() & ALLMODS
        #GD.debug("PRESS BUTTON %s WITH MODIFIER %s" % (self.button,self.mod))
        func = self.getMouseFunc()
        if func:
            func(self.statex,self.statey,PRESS)
        e.accept()
        
    def mouseMoveEvent(self,e):
        """Process a mouse move event."""
        # the MOVE event does not identify a button, use the saved one
        func = self.getMouseFunc()
        if func:
            func(e.x(),self.height()-e.y(),MOVE)
        e.accept()

    def mouseReleaseEvent(self,e):
        """Process a mouse release event."""
        func = self.getMouseFunc()
        self.button = None        # clear the stored button
        if func:
            func(e.x(),self.height()-e.y(),RELEASE)
        e.accept()


    # Any keypress with focus in the canvas generates a 'wakeup' signal.
    # This is used to break out of a wait status.
    # Events not handled here could also be handled by the toplevel
    # event handler.
    def keyPressEvent (self,e):
        self.emit(WAKEUP,())
        if e.key() == ESC:
            self.emit(CANCEL,())
            e.accept()
        elif e.key() == ENTER or e.key() == RETURN:
            self.emit(DONE,())
            e.accept()
        else:
            e.ignore()


################# Multiple Viewports ###############


class MultiCanvas(QtGui.QGridLayout):
    """A viewport that can be splitted."""
    
    def __init__(self,parent=None):
        """Initialize the multicanvas."""
        QtGui.QGridLayout.__init__(self)
        self.all = []
        self.active = []
        self.current = None
        self.ncols = 2
        self.rowwise = True
        self.parent = parent

        
    def setDefaults(self,dict):
        """Update the default settings of the canvas class."""
        GD.debug("Setting canvas defaults:\n%s" % dict)
        canvas.CanvasSettings.default.update(canvas.CanvasSettings.checkDict(dict))

    def newView(self,shared=None):
        "Create a new viewport"
        canv = QtCanvas(self.parent,shared)
        return(canv)
        

    def addView(self):
        """Add a new viewport to the widget"""
        canv = self.newView()
        self.all.append(canv)
        self.active.append(canv)
        self.showWidget(canv)
        canv.initializeGL()   # Initialize OpenGL context and camera
        # DO NOT USE self.setCurrent(canv) HERE, because no camera yet
        GD.canvas = self.current = canv


    def setCurrent(self,canv):
        if type(canv) == int and canv in range(len(self.all)):
            canv = self.all[canv]
        # TEST SKIP IF ALREADY CURRENT
        if self.current == canv:
            return
        if canv in self.all:
            GD.canvas = self.current = canv
            toolbar.setTransparency(self.current.alphablend)
            toolbar.setPerspective(self.current.camera.perspective)
            toolbar.setLight(self.current.lighting)
            #toolbar.setNormals(self.current.avgnormals)
            #
            # TEST WITHOUT DISPLAY
            GL.glFlush()
            # TEST WITH DISPLAY
            #self.current.display()
            

    def currentView(self):
        return self.all.index(GD.canvas)


    def showWidget(self,w):
        """Show the view w"""
        row,col = divmod(self.all.index(w),self.ncols)
        if self.rowwise:
            self.addWidget(w,row,col)
        else:
            self.addWidget(w,col,row)
        w.raise_()


    def removeView(self):
        if len(self.all) > 1:
            w = self.all.pop()
            if self.current == w:
                self.setCurrent(self.all[-1])
            if w in self.active:
                self.active.remove(w)
            self.removeWidget(w)
            w.close()


##     def setCamera(self,bbox,view):
##         self.current.setCamera(bbox,view)
            
    def updateAll(self):
         GD.debug("UPDATING ALL VIEWPORTS")
         for v in self.all:
             v.update()
         GD.app.processEvents()

    def removeAll(self):
        for v in self.active:
            v.removeAll()

##     def clear(self):
##         self.current.clear()  

    def addActor(self,actor):
        for v in self.active:
            v.addActor(actor)


    def printSettings(self):
        for i,v in enumerate(self.all):
            GD.message("""
## VIEWPORTS ##
Viewport %s;  Active:%s;  Current:%s;  Settings:
%s
""" % (i,v in self.active, v == self.current, v.settings))


    def changeLayout(self, nvps=None,ncols=None, nrows=None):
        """Lay out the viewports.

        You can specify the number of viewports and the number of columns or
        rows.

        If a number of viewports is given, viewports will be added
        or removed to match the number requested.
        By default they are layed out rowwise over two columns.

        If ncols is an int, viewports are laid out rowwise over ncols
        columns and nrows is ignored. If ncols is None and nrows is an int,
        viewports are laid out columnwise over nrows rows.
        """
        if type(nvps) == int:
            while len(self.all) > nvps:
                self.removeView()
            while len(self.all) < nvps:
                self.addView()

        if type(ncols) == int:
            rowwise = True
        elif type(nrows) == int:
            ncols = nrows
            rowwise = False
        else:
            return

        for w in self.all:
            self.removeWidget(w)
        self.ncols = ncols
        self.rowwise = rowwise
        for w in self.all:
            self.showWidget(w)


    def link(self,vp,to):
        """Link viewport vp to to"""
        nvps = len(self.all)
        if vp < nvps and to < nvps:
            to = self.all[to]
            oldvp = self.all[vp]
            newvp = self.newView(to)
            self.all[vp] = newvp
            self.removeWidget(oldvp)
            oldvp.close()
            self.showWidget(newvp)
            vp = newvp
            vp.actors = to.actors
            vp.bbox = to.bbox
            vp.show()
            vp.setCamera()
            vp.redrawAll()
            #vp.updateGL()
            GD.app.processEvents()


if __name__ == "__main__":
    print "Testing the Collection object"
    a = Collection()
    a.add(range(7),3)
    a.add(range(4))
    a.remove([2,4],3)
    print a
    a.add([[2,0],[2,3],[-1,7],[3,88]])
    print a
    a[2] = [1,2,3]
    print a
    a[2] = []
    print a
    a.set([[2,0],[2,3],[-1,7],[3,88]])
    print a

                    
# End
