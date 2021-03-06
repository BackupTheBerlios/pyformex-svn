## $Id$
##
##  This file is part of pyFormex 0.7.3 Release Tue Dec 30 20:45:35 2008
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
"""Functions for drawing and for executing pyFormex scripts."""

import pyformex as GD

import threading,os,sys,types,copy,commands,time

from PyQt4 import QtCore, QtGui  # needed for events, signals

import numpy
import utils
import widgets
import toolbar
import drawable
import actors
import decors
import marks
import image
import canvas
import colors
import coords
import formex
from script import *

from plugins import surface,tools
from formex import Formex

        
#################### Interacting with the user ###############################

def startGui():
    """Start the gui"""
    print "Currently, the GUI can only be started by the pyformex command"


def closeGui():
    GD.debug("Closing the GUI: currently, this will also terminate pyformex.")
    GD.gui.close()
    

def ask(question,choices=None,default=None,**kargs):
    """Ask a question and present possible answers.

    Return answer if accepted or default if rejected.
    The remaining arguments are passed to the InputDialog getResult method.
    """
    if choices:
        return widgets.messageBox(question,'question',choices)

    if choices is None:
        if default is None:
            default = choices[0]
        items = [ [question, default] ]
    else:
        items = [ [question, choices, 'combo', default] ]

    res = widgets.InputDialog(items,'Ask Question').getResult(**kargs)
    if GD.gui:
        GD.gui.update()
    if res:
        return res[question]
    else:
        return default


def ack(question):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question,['No','Yes']) == 'Yes'
    
def error(message,actions=['OK']):
    """Show an error message and wait for user acknowledgement."""
    widgets.messageBox(message,'error',actions)
    
def warning(message,actions=['OK']):
    """Show a warning message and wait for user acknowledgement."""
    widgets.messageBox(message,'warning',actions)

def showInfo(message,actions=['OK']):
    """Show a neutral message and wait for user acknowledgement."""
    widgets.messageBox(message,'info',actions)

def showText(text,actions=['OK']):
    """Display a text and wait for user response.

    This can display a large text and will add scrollbars when needed.
    """
    return widgets.textBox(text,actions)


def askItems(items,caption=None,**kargs):
    """Ask the value of some items to the user.

    Create an interactive widget to let the user set the value of some items.
    Input is a list of input items (basically [key,value] pairs).
    See the widgets.InputDialog class for complete description of the
    available input items.

    The remaining arguments are keyword arguments that are passed to the
    InputDialog.getResult method.
    A timeout (in seconds) can be specified to have the input dialog
    interrupted automatically.

    Return a dictionary with the results: for each input item there is a
    (key,value) pair. Returns an empty dictionary if the dialog was canceled.
    Sets the dialog timeout and accepted status in global variables.
    """
    if type(items) == dict:
        items = items.items()
    w = widgets.InputDialog(items,caption)
    res = w.getResult(**kargs)
    GD.dialog_timeout = w.timedOut
    GD.dialog_accepted = w.accepted
    return res


def askFilename(cur=None,filter="All files (*.*)",exist=False,multi=False):
    """Ask for a file name or multiple file names using a file dialog.

    cur is a directory or filename. All the files matching the filter in that
    directory (or that file's directory) will be shown.
    If cur is a file, it will be selected as the current filename.
    """
    if cur is None:
        cur = GD.cfg['workdir']
    if os.path.isdir(cur):
        cur += '/'
    fn = os.path.basename(cur)
    cur = os.path.dirname(cur)
    w = widgets.FileSelection(cur,filter,exist,multi)
    if fn:
        w.selectFile(fn)
    fn = w.getFilename()
    if fn:
        if multi:
            chdir(fn[0])
        else:
            chdir(fn)
    GD.gui.update()
    GD.canvas.update()
    GD.app.processEvents()
    return fn


def askDirname(cur=None):
    """Ask for an existing directory name.

    cur is a directory. All the directories in that directory will
    initially be shown.
    """
    if cur is None:
        cur = GD.cfg['workdir']
    cur = os.path.dirname(cur)
    fn = widgets.FileSelection(cur,'*',dir=True).getFilename()
    if fn:
        chdir(fn)
    GD.gui.update()
    GD.canvas.update()
    GD.app.processEvents()
    return fn


def log(s):
    """Display a message in the cmdlog window."""
    GD.gui.board.write(str(s))
    GD.gui.update()
    GD.app.processEvents()

# message is the preferred function to send text info to the user.
# The default message handler is set here.
# Best candidates are log/info
message = log


############################## drawing functions ########################

def draw(F, view=None,bbox=None,
         color='prop',colormap=None,alpha=0.5,
         mode=None,linewidth=None,shrink=None,marksize=None,
         wait=True,clear=None,allviews=False):
    """Draw object(s) with specified settings and direct camera to it.

    The first argument is an object to be drawn. All other arguments are
    settings that influence how  the object is being drawn.

    F is either a Formex or a TriSurface object, or a name of such object
    (global or exported), or a list thereof.
    If F is a list, the draw() function is called repeatedly with each of
    ithe items of the list as first argument and with the remaining arguments
    unchanged.

    The remaining arguments are drawing options. If None, they are filled in
    from the current viewport drawing options.
    
    view is either the name of a defined view or 'last' or None.
    Predefined views are 'front','back','top','bottom','left','right','iso'.
    With view=None the camera settings remain unchanged (but might be changed
    interactively through the user interface). This may make the drawn object
    out of view!
    With view='last', the camera angles will be set to the same camera angles
    as in the last draw operation, undoing any interactive changes.
    The initial default view is 'front' (looking in the -z direction).

    bbox specifies the 3D volume at which the camera will be aimed (using the
    angles set by view). The camera position wil be set so that the volume
    comes in view using the current lens (default 45 degrees).
    bbox is a list of two points or compatible (array with shape (2,3)).
    Setting the bbox to a volume not enclosing the object may make the object
    invisible on the canvas.
    The special value bbox='auto' will use the bounding box of the objects
    getting drawn (object.bbox()), thus ensuring that the camera will focus
    on these objects.
    The special value bbox=None will use the bounding box of the previous
    drawing operation, thus ensuring that the camera's target volume remains
    unchanged.

    color,colormap,linewidth,alpha,marksize are passed to the
    creation of the 3D actor.

    shrink is a floating point shrink factor that will be applied to object
    before drawing it.

    If the Formex has properties and a color list is specified, then the
    the properties will be used as an index in the color list and each member
    will be drawn with the resulting color.
    If color is one color value, the whole Formex will be drawn with
    that color.
    Finally, if color=None is specified, the whole Formex is drawn in black.
    
    Each draw action activates a locking mechanism for the next draw action,
    which will only be allowed after drawdelay seconds have elapsed. This
    makes it easier to see subsequent images and is far more elegant that an
    explicit sleep() operation, because all script processing will continue
    up to the next drawing instruction.
    The value of drawdelay is set in the config, or 2 seconds by default.
    The user can disable the wait cycle for the next draw operation by
    specifying wait=False. Setting drawdelay=0 will disable the waiting
    mechanism for all subsequent draw statements (until set >0 again).
    """
    if type(F) == list:
        actor = []
        nowait = False
        for Fi in F:
            if Fi == F[-1]:
                nowait = wait
            actor.append(draw(Fi,view,bbox,
                              color,colormap,alpha,
                              mode,linewidth,shrink,marksize,
                              wait=nowait,clear=clear,allviews=allviews))
            if Fi == F[0]:
                clear = False
                view = None
        return actor

    if type(F) == str:
        F = named(F)
        if F is None:
            return None


    if isinstance(F,formex.Formex):
        pass
    elif isinstance(F,surface.TriSurface):
        pass
    elif isinstance(F,tools.Plane):
        pass
    elif hasattr(F,'asFormex'):
        F = F.asFormex()
    # keep this after trying the 'asFormex'
    elif isinstance(F,coords.Coords):
        F = Formex(F)
    else:
        # Don't know how to draw this object
        raise RuntimeError,"draw() can not draw objects of type %s" % type(F)

    GD.gui.drawlock.wait()

    if clear is None:
        clear = GD.canvas.options.get('clear',False)
    if clear:
        clear_canvas()

    if bbox is None:
        bbox = GD.canvas.options.get('bbox','auto')

    if view is not None and view != 'last':
        GD.debug("SETTING VIEW to %s" % view)
        setView(view)

    if shrink is None:
        shrink = GD.canvas.options.get('shrink',None)
 
    if marksize is None:
        marksize = GD.canvas.options.get('marksize',GD.cfg.get('marksize',5.0))
       
    # Create the colors
    if color == 'prop':
        if hasattr(F,'p'):
            color = F.p
        else:
            color = colors.black
    elif color == 'random':
        # create random colors
        color = numpy.random.random((F.nelems(),3),dtype=float32)

    GD.gui.setBusy()
    if shrink is not None:
        #GD.debug("DRAWING WITH SHRINK = %s" % shrink)
        F = _shrink(F,shrink)
    try:
        if isinstance(F,formex.Formex):
            if F.nelems() == 0:
                return None
            actor = actors.FormexActor(F,color=color,colormap=colormap,alpha=alpha,mode=mode,linewidth=linewidth,marksize=marksize)
        elif isinstance(F,surface.TriSurface):
            if F.nelems() == 0:
                return None
            actor = actors.TriSurfaceActor(F,color=color,colormap=colormap,alpha=alpha,mode=mode,linewidth=linewidth)
        elif isinstance(F,tools.Plane):
            return drawPlane(F.point(),F.normal(),F.size())
        GD.canvas.addActor(actor)
        if view is not None or bbox not in [None,'last']:
            #GD.debug("CHANGING VIEW to %s" % view)
            if view == 'last':
                view = GD.canvas.options['view']
            if bbox == 'auto':
                bbox = F.bbox()
            #GD.debug("SET CAMERA TO: bbox=%s, view=%s" % (bbox,view))
            GD.canvas.setCamera(bbox,view)
            #setView(view)
        GD.canvas.update()
        GD.app.processEvents()
        #GD.debug("AUTOSAVE %s" % image.autoSaveOn())
        if image.autoSaveOn():
            image.saveNext()
        if wait: # make sure next drawing operation is retarded
            GD.gui.drawlock.lock()
    finally:
        GD.gui.setBusy(False)
    return actor



def reset():
    GD.canvas.resetOptions()
    GD.gui.drawwait = GD.cfg['draw/wait']
    GD.canvas.resetDefaults(GD.cfg['canvas'])
    clear()
    view('front')

def resetAll():
    wireframe()
    reset()
    
def setDrawOptions(d):
    GD.canvas.options.update(d)
    
def showDrawOptions():
    GD.message("Current Drawing Options: %s" % GD.canvas.options)


def shrink(v):
    setDrawOptions({'shrink':v})
    

def setView(name,angles=None):
    """Set the default view for future drawing operations.

    If no angles are specified, the name should be an existing view, or
    the predefined value '__last__'.
    If angles are specified, this is equivalent to createView(name,angles)
    followed by setView(name).
    """
    if name != '__last__' and angles:
        createView(name,angles)
    setDrawOptions({'view':name})


def _shrink(F,factor):
    """Return a shrinked object.

    A shrinked object is one where each element is shrinked with a factor
    around its own center.
    """
    if isinstance(F,surface.TriSurface):
        F = F.toFormex()
    return F.shrink(factor)


def drawPlane(P,N,size):
    actor = actors.PlaneActor(size=size)
    actor.create_list(mode=GD.canvas.rendermode)
    actor = actors.RotatedActor(actor,N)
    actor.create_list(mode=GD.canvas.rendermode)
    actor = actors.TranslatedActor(actor,P)
    GD.canvas.addActor(actor)
    GD.canvas.update()
    return actor


def drawNumbers(F,color=colors.black,trl=None,offset=0):
    """Draw numbers on all elements of F.

    Normally, the numbers are drawn at the centroids of the elements.
    A translation may be given to put the numbers out of the centroids,
    e.g. to put them in front of the objects to make them visible,
    or to allow to view a mark at the centroids.
    """
    FC = F.centroids()
    if trl is not None:
        FC = FC.trl(trl)
    M = marks.MarkList(FC,numpy.arange(FC.shape[0])+offset,color=color)
    GD.canvas.addAnnotation(M)
    GD.canvas.numbers = M
    GD.canvas.update()
    return M


def drawVertexNumbers(F,color=colors.black,trl=None):
    """Draw (local) numbers on all vertices of F.

    Normally, the numbers are drawn at the location of the vertices.
    A translation may be given to put the numbers out of the location,
    e.g. to put them in front of the objects to make them visible,
    or to allow to view a mark at the vertices.
    """
    FC = F.f.reshape((-1,3))
    if trl is not None:
        FC = FC.trl(trl)
    M = marks.MarkList(FC,numpy.resize(numpy.arange(F.f.shape[1]),(FC.shape[0])),color=color)
    GD.canvas.addAnnotation(M)
    GD.canvas.numbers = M
    GD.canvas.update()
    return M


def drawText3D(P,text,color=colors.black,font=None):
    """Draw a text at a 3D point."""
    M = marks.TextMark(P,text,color=color,font=font)
    GD.canvas.addAnnotation(M)
    GD.canvas.update()
    return M


def drawViewportAxes3D(pos,color=None):
    """Draw two viewport axes at a 3D position."""
    M = marks.AxesMark(pos,color)
    annotate(M)
    return M


def drawBbox(A):
    """Draw the bbox of the actor A."""
    B = actors.BboxActor(A.bbox())
    drawActor(B)
    return B


def drawActor(A):
    """Draw an actor and update the screen."""
    GD.canvas.addActor(A)
    GD.canvas.update()


def undraw(itemlist):
    """Remove an item or a number of items from the canvas.

    Use the return value from one of the draw... functions to remove
    the item that was drawn from the canvas.
    A single item or a list of items may be specified.
    """
    GD.canvas.remove(itemlist)
    GD.canvas.update()
    GD.app.processEvents()


def focus(object):
    """Move the camera thus that object comes fully into view.

    object can be anything having a bbox() method.

    The camera is moved with fixed axis directions to a place
    where the whole object can be viewed using a 45. degrees lens opening.
    This technique may change in future!
    """
    GD.canvas.setCamera(bbox=object.bbox())
    

def view(v,wait=False):
    """Show a named view, either a builtin or a user defined."""
    GD.gui.drawlock.wait()
    if v != '__last__':
        angles = GD.canvas.view_angles.get(v)
        if not angles:
            warning("A view named '%s' has not been created yet" % v)
            return
        GD.canvas.setCamera(None,angles)
    setView(v)
    GD.canvas.update()
    if wait:
        GD.gui.drawlock.lock()


def setTriade(on=None):
    """Toggle the display of the global axes on or off.

    If on is True, the axes triade is displayed, if False it is
    removed. The default (None) toggles between on and off.
    """
    if on is None:
        on = not hasattr(GD.canvas,'triade') or GD.canvas.triade is None
    if on:
        GD.canvas.triade = actors.TriadeActor(1.0)
        GD.canvas.addAnnotation(GD.canvas.triade)
    else:
        GD.canvas.removeAnnotation(GD.canvas.triade)
        GD.canvas.triade = None
    GD.canvas.update()
    GD.app.processEvents()


# DOES NOT WORK ??
## def drawTextQt(text,x,y,font=None):
##     """Show a text at position x,y using font."""
##     print x,y,text
##     GD.canvas.renderText(x,y,'hallo')



def drawtext(text,x,y,font='9x15',adjust='left',color=None):
    """Show a text at position x,y using font."""
    TA = decors.Text(text,x,y,font,adjust,color)
    decorate(TA)
    return TA

def annotate(annot):
    """Draw an annotation."""
    GD.canvas.addAnnotation(annot)
    GD.canvas.update()

def unannotate(annot):
    GD.canvas.removeAnnotation(annot)
    GD.canvas.update()

def decorate(decor):
    """Draw a decoration."""
    GD.canvas.addDecoration(decor)
    GD.canvas.update()

def undecorate(decor):
    GD.canvas.removeDecoration(decor)
    GD.canvas.update()




def frontView():
    view("front")
def backView():
    view("back")
def leftView():
    view("left")
def rightView():
    view("right")
def topView():
    view("top");
def bottomView():
    view("bottom")
def isoView():
    view("iso")

def createView(name,angles):
    """Create a new named view (or redefine an old).

    The angles are (longitude, latitude, twist).
    If the view name is new, and there is a views toolbar,
    a view button will be added to it.
    """
    GD.gui.setViewAngles(name,angles)   
    

def zoomBbox(bb):
    """Zoom thus that the specified bbox becomes visible."""
    GD.canvas.setBbox(bb)
    GD.canvas.setCamera()
    GD.canvas.update()


def zoomAll():
    """Zoom thus that all actors become visible."""
    if GD.canvas.actors:
        zoomBbox(coords.bbox(GD.canvas.actors))

# An alias, currently not deprecated
zoomall = zoomAll

def zoom(f):
    GD.canvas.zoom(f)
    GD.canvas.update()

def bgcolor(color):
    """Change the background color (and redraw)."""
    GD.canvas.setBgColor(color)
    GD.canvas.display()
    GD.canvas.update()

def fgcolor(color):
    """Set the default foreground color."""
    GD.canvas.setFgColor(color)


def renderMode(mode):
    GD.canvas.setRenderMode(mode)
    toolbar.setLight(GD.canvas.lighting)
    GD.canvas.update()
    GD.app.processEvents()
    
def wireframe():
    renderMode("wireframe")
    
def flat():
    renderMode("flat")
    
def smooth():
    renderMode("smooth")

def smoothwire():
    renderMode("smoothwire")
    
def flatwire():
    renderMode("flatwire")

def opacity(alpha):
    """Set the viewports transparency."""
    GD.canvas.alpha = float(alpha)

def lights(onoff):
    """Set the lights on or off"""
    toolbar.setLight(onoff)


def set_light_value(typ,val):
    """Set the value of one of the lighting parameters for the currrent view

    typ is one of 'ambient','specular','emission','shininess'
    val is a value between 0.0 and 1.0
    """
    setattr(GD.canvas,typ,val)
    GD.canvas.setLighting(True)
    GD.canvas.update()
    GD.app.processEvents()

def set_ambient(i):
    set_light_value('ambient',i)

def set_specular(i):
    set_light_value('specular',i)

def set_emission(i):
    set_light_value('emission',i)

def set_shininess(i):
    set_light_value('shininess',i)

transparent = toolbar.setTransparency
perspective = toolbar.setPerspective
timeout = toolbar.timeout


def linewidth(wid):
    """Set the linewidth to be used in line drawings."""
    GD.canvas.setLineWidth(wid)


def clear_canvas():
    """Clear the canvas.

    This is a low level function not intended for the user.
    """
    GD.canvas.removeAll()
    GD.canvas.clear()


def clear():
    """Clear the canvas"""
    GD.gui.drawlock.wait()
    clear_canvas()
    GD.canvas.update()


def redraw():
    GD.canvas.redrawAll()
    GD.canvas.update()


def pause(msg="Use the Step/Continue buttons to proceed"):
    if msg:
        GD.message(msg)
    if GD.gui.drawlock.allowed:
        GD.gui.drawlock.lock()    # will need external event to release it
        while (GD.gui.drawlock.locked):
            sleep(0.5)
            GD.app.processEvents()


def step():
    """Perform one step of a script.

    A step is a set of instructions until the next draw operation.
    If a script is running, this just releases the draw lock.
    Else, it starts the script in step mode.
    """
    if scriptRunning:
        GD.gui.drawlock.release()
    else:
        if ack("""
STEP MODE is currently only possible with specially designed,
very well behaving scripts. If you're not sure what you are
doing, you should cancel the operation now.

Are you REALLY SURE you want to run this script in step mode?
"""):
            play(step=True)
        

def fforward():
    GD.gui.drawlock.free()


def delay(i):
    """Set the draw delay in seconds."""
    i = int(i)
    if i >= 0:
        GD.cfg['draw/wait'] = i
    

        
wakeupMode=0
def sleep(timeout=None):
    """Sleep until key/mouse press in the canvas or until timeout"""
    global sleeping,wakeupMode,timer
    if wakeupMode > 0 or timeout == 0:  # don't bother
        return
    # prepare for getting wakeup event 
    QtCore.QObject.connect(GD.canvas,QtCore.SIGNAL("Wakeup"),wakeup)
    # create a Timer to wakeup after timeout
    if timeout and timeout > 0:
        timer = threading.Timer(timeout,wakeup)
        timer.start()
    else:
        timer = None
    # go into sleep mode
    sleeping = True
    ## while sleeping, we have to process events
    ## (we could start another thread for this)
    while sleeping:
        GD.app.processEvents()
        #time.sleep(0.1)
    # ignore further wakeup events
    QtCore.QObject.disconnect(GD.canvas,QtCore.SIGNAL("Wakeup"),wakeup)

        
def wakeup(mode=0):
    """Wake up from the sleep function.

    This is the only way to exit the sleep() function.
    Default is to wake up from the current sleep. A mode > 0
    forces wakeup for longer period.
    """
    global timer,sleeping,wakeupMode
    if timer:
        timer.cancel()
    sleeping = False
    wakeupMode = mode


########################## print information ################################


def printbbox():
    print GD.canvas.bbox

def printviewportsettings():
    GD.gui.viewports.printSettings()


#################### viewports ##################################

def layout(nvps=None,ncols=None,nrows=None):
    """Set the viewports layout."""
    GD.gui.viewports.changeLayout(nvps,ncols,nrows)

def addViewport():
    """Add a new viewport."""
    GD.gui.viewports.addView()

def removeViewport():
    """Remove a new viewport."""
    n = len(GD.gui.viewports.all)
    if n > 1:
        GD.gui.viewports.removeView()

def linkViewport(vp,tovp):
    """Link viewport vp to viewport tovp.

    Both vp and tovp should be numbers of viewports. 
    """
    GD.gui.viewports.link(vp,tovp)

def viewport(n):
    """Select the current viewport"""
    GD.gui.viewports.setCurrent(n)

####################

def updateGUI():
    """Update the GUI."""
    GD.gui.update()
    GD.canvas.update()
    GD.app.processEvents()


def flyAlong(path='flypath',upvector=[0.,1.,0.],sleeptime=None):
    """Fly through the scene along the flypath."""
    if type(path) is str:
        path = named(path)
    if not path:
        warning("You have to define a flypath first!")
        return
    if path.nplex() != 2:
        warning("The flypath should be a plex-2 Formex!")
        
    for seg in path:
        GD.debug("Eye: %s; Center: %s" % (seg[0],seg[1]))
        GD.canvas.camera.lookAt(seg[0],seg[1],upvector)
        GD.canvas.display()
        GD.canvas.update()
        image.saveNext()
        if sleeptime is None:
            sleeptime = GD.cfg['draw/flywait']
        sleeptime = float(sleeptime)
        if sleeptime > 0.0:
            sleep(sleeptime)

    
highlight_colormap = ['black','red']

def highlightActors(K,colormap=highlight_colormap):
    """Highlight a selection of actors on the canvas.

    K is Collection of actors as returned by the pick() method.
    colormap is a list of two colors, for the actors not in, resp. in
    the Collection K.
    """
    for i,A in enumerate(copy.copy(GD.canvas.actors)):
        if i in K.get(-1,[]):
            color = colormap[1]
        else:
            color = colormap[0]
        #
        # For some reason, redrawing a surface does not work
        # Therefore we undraw it and draw it again
        #
        if isinstance(A,surface.TriSurface):
            undraw(A)
            draw(A,color=color,bbox=None)
        else:
            A.redraw(mode=GD.canvas.rendermode,color=color)
    GD.canvas.update()


def newhighlightActors(K):
    """Highlight a selection of actors on the canvas.

    K is Collection of actors as returned by the pick() method.
    colormap is a list of two colors, for the actors not in, resp. in
    the Collection K.
    """
    for i in K.get(-1,[]):
        print "%s/%s" % (i,len(GD.canvas.actors))
        GD.canvas.addHighlight(GD.canvas.actors[i])
    GD.canvas.update()


def newhighlightElements(K):
    """Highlight a selection of actor elements on the canvas.

    K is Collection of actor elements as returned by the pick() method.
    colormap is a list of two colors, for the elements not in, resp. in
    the Collection K.
    """
    for i in K.keys():
        GD.debug("Actor %s: Selection %s" % (i,K[i]))
        actor = GD.canvas.actors[i]
        if isinstance(actor,actors.FormexActor):
            FA = actors.FormexActor(actor.f[K[i]])
            GD.canvas.addHighlight(FA)
    GD.canvas.update()


def highlightElements(K,colormap=highlight_colormap):
    """Highlight a selection of actor elements on the canvas.

    K is Collection of actor elements as returned by the pick() method.
    colormap is a list of two colors, for the elements not in, resp. in
    the Collection K.
    """
    for i,A in enumerate(copy.copy(GD.canvas.actors)):
        p = numpy.zeros((A.nelems(),),dtype=int)
        if i in K.keys():
            GD.debug("Actor %s: Selection %s" % (i,K[i]))
            p[K[i]] = 1
        if isinstance(A,surface.TriSurface):
            undraw(A)
            draw(A,color=p,colormap=colormap,bbox=None)
        else:
            A.redraw(mode=GD.canvas.rendermode,color=p,colormap=colormap)
    GD.canvas.update()


def highlightEdges(K,colormap=highlight_colormap):
    """Highlight a selection of actor edges on the canvas.

    K is Collection of TriSurface actor edges as returned by the pick() method.
    colormap is a list of two colors, for the edges not in, resp. in
    the Collection K.
    """
    for i,A in enumerate(copy.copy(GD.canvas.actors)):
        if i in K.keys() and isinstance(A,surface.TriSurface):
            GD.debug("Actor %s: Selection %s" % (i,K[i]))
            F = Formex(A.coords[A.edges[K[i]]])
            draw(F,color=highlight_colormap[1],linewidth=3,bbox=None)
            #drawable.drawLineElems(A.coords,A.edges[K[i]],color=highlight_colormap[1])

    GD.canvas.update()


highlight_pts = None

def highlightPoints(K,colormap=highlight_colormap):
    """Highlight a selection of actor elements on the canvas.

    K is Collection of actor elements as returned by the pick() method.
    
    """
    global highlight_pts
    if highlight_pts is not None:
        unannotate(highlight_pts)
        highlight_pts = None
    pts = []
    for i,A in enumerate(copy.copy(GD.canvas.actors)):
        if i in K.keys():
            pts.append(A.vertices()[K[i]])
    if pts:
        pts = Formex(numpy.concatenate(pts,axis=0))
        highlight_pts = actors.FormexActor(pts,marksize=10,color=highlight_colormap[1])
        annotate(highlight_pts)
    return highlight_pts


def highlightPartitions(K):
    """Highlight a selection of partitions on the canvas.

    K is a Collection of actor elements, where each actor element is
    connected to a collection of property numbers, as returned by the
    partitionCollection() method.
    """
    for i,A in enumerate(copy.copy(GD.canvas.actors)):
        p = numpy.zeros((A.nelems(),),dtype=int)
        if i in K.keys():
            GD.debug("Actor %s: Partitions %s" % (i,K[i][0]))
            for j in K[i][0].keys():
                p[K[i][0][j]] = j
        if isinstance(A,surface.TriSurface):
            undraw(A)
            draw(A,color=p,bbox=None)
        else:
            A.redraw(mode=GD.canvas.rendermode,color=p)
    GD.canvas.update()


highlight_funcs = { 'actor': highlightActors,
                    'element': highlightElements,
                    'point': highlightPoints,
                    'edge': highlightEdges,
                    }

if GD.options.testhighlight:
    highlight_funcs['actor'] = newhighlightActors

selection_filters = [ 'none', 'single', 'closest', 'connected' ]


def set_selection_filter(i):
    """Set the selection filter mode"""
    if i in range(len(selection_filters)):
        GD.canvas.start_selection(None,selection_filters[i])

    
def pick(mode='actor',single=False,func=None,filtr=None,numbers=False):
    """Enter interactive picking mode and return selection.

    See viewport.py for more details.
    This function differs in that it provides default highlighting
    during the picking operation, a button to stop the selection operation

    If no filter is given, the available filters are presented in a combobox.
    If numbers=True, numbers are shown?? Sofie: can you explain some more
    what it is doing?
    """
    if GD.canvas.selection_mode is not None:
        warning("You need to finish the previous picking operation first!")
        return

    pick_buttons = widgets.ButtonBox('Selection:',['Cancel','OK'],[GD.canvas.cancel_selection,GD.canvas.accept_selection])
    GD.gui.statusbar.addWidget(pick_buttons)
    
    if mode == 'element':
        filters = selection_filters
    else:
        filters = selection_filters[:3]
    filter_combo = widgets.ComboBox('Filter:',filters,set_selection_filter)
    GD.gui.statusbar.addWidget(filter_combo)

    GD.canvas.numbers_visible = False
    if mode == 'actor':
        numbers = False
    if numbers:
        number_buttons = widgets.ButtonBox('Numbers:',['Show','Hide'],[showNumbers,hideNumbers])
        GD.gui.statusbar.addWidget(number_buttons)
    if func is None:
        func = highlight_funcs.get(mode,None)
    GD.message("Select %s %s" % (filtr,mode))
    sel = GD.canvas.pick(mode,single,func,filtr)
    GD.canvas.removeHighlights()
    GD.gui.statusbar.removeWidget(pick_buttons)
    GD.gui.statusbar.removeWidget(filter_combo)
    if numbers:
        hideNumbers()
        GD.gui.statusbar.removeWidget(number_buttons)
    return sel

    
def pickActors(single=False,func=None,filtr=None):
    return pick('actor',single,func,filtr)

def pickElements(single=False,func=None,filtr=None):
    return pick('element',single,func,filtr)

def pickPoints(single=False,func=None,filtr=None):
    return pick('point',single,func,filtr)

def pickEdges(single=False,func=None,filtr=None):
    return pick('edge',single,func,filtr)


def highlight(K,mode,colormap=highlight_colormap):
    """Highlight a Collection of actor/elements.

    K is usually the return value of a pick operation, but might also
    be set by the user.
    mode is one of the pick modes.
    """
    func = highlight_funcs.get(mode,None)
    if func:
        func(K,colormap)


def pickNumbers(marks=None):
    if marks:
        GD.canvas.numbers = marks
    return GD.canvas.pickNumbers()


def showNumbers():
    """Show a list widget containing the numbers of the elements,
    points or edges. When part numbers are added to / removed from
    the selection by mouse_picking, the corresponding list items will be
    selected / deselected. Part numbers can also be added to / removed
    from the selection by clicking on a list item.
    """
    A = GD.canvas.actors[0]
    if GD.canvas.selection_mode == 'element':
        numbers = [str(i) for i in range(A.nelems())]
        drawNumbers(A,color=colors.blue)
    elif GD.canvas.selection_mode == 'point':
        numbers = [str(i) for i in range(A.npoints())]
        if isinstance(A,surface.TriSurface):
            F = Formex(A.coords)
            drawNumbers(F,color=colors.blue)
        elif isinstance(A,formex.Formex):
            drawVertexNumbers(A,color=colors.blue)
    elif GD.canvas.selection_mode == 'edge':
        numbers = [str(i) for i in range(GD.canvas.actors[0].nedges())]
        F = Formex(A.coords[A.edges])
        drawNumbers(F,color=colors.blue)
    GD.canvas.number_widget = widgets.DockedSelection(numbers,'Numbers',mode='multi',func=GD.canvas.select_numbers)
    selection = map(str,GD.canvas.selection.get(0))
    GD.canvas.number_widget.setSelected(selection,True)
    GD.gui.addDockWidget(QtCore.Qt.LeftDockWidgetArea,GD.canvas.number_widget)
    GD.canvas.numbers_visible = True

    
def hideNumbers():
    """Hide the list widget."""
    if GD.canvas.numbers_visible:
        undraw(GD.canvas.numbers)
        GD.gui.removeDockWidget(GD.canvas.number_widget)
    GD.canvas.numbers_visible = False


LineDrawing = None
edit_modes = ['undo', 'clear','close']


def set_edit_mode(i):
    """Set the drawing edit mode."""
    if i in range(len(edit_modes)):
        GD.canvas.edit_drawing(edit_modes[i])


def drawLinesInter(mode ='line',single=False,func=None):
    """Enter interactive drawing mode and return the line drawing.

    See viewport.py for more details.
    This function differs in that it provides default displaying
    during the drawing operation and a button to stop the drawing operation.

    The drawing can be edited using the methods 'undo', 'clear' and 'close', which
    are presented in a combobox.
    """
    if GD.canvas.drawing_mode is not None:
        warning("You need to finish the previous drawing operation first!")
        return
    if func == None:
        func = showLineDrawing
    drawing_buttons = widgets.ButtonBox('Drawing:',['Cancel','OK'],[GD.canvas.cancel_drawing,GD.canvas.accept_drawing])
    GD.gui.statusbar.addWidget(drawing_buttons)
    edit_combo = widgets.ComboBox('Edit:',edit_modes,set_edit_mode)
    GD.gui.statusbar.addWidget(edit_combo)
    lines = GD.canvas.drawLinesInter(mode,single,func)
    GD.gui.statusbar.removeWidget(drawing_buttons)
    GD.gui.statusbar.removeWidget(edit_combo)
    return lines


def showLineDrawing(L):
    """Show a line drawing.

    L is usually the return value of an interactive draw operation, but
    might also be set by the user.
    """
    global LineDrawing
    if LineDrawing:
        undecorate(LineDrawing)
        LineDrawing = None
    if L.size != 0:
        LineDrawing = decors.LineDrawing(L,color='yellow',linewidth=3)
        decorate(LineDrawing)


################################ saving images ########################
         


#### Change settings

def setLocalAxes(mode=True):
    GD.cfg['draw/localaxes'] = mode 

def setGlobalAxes(mode=True):
    setLocalAxes(not mode)



#### End
