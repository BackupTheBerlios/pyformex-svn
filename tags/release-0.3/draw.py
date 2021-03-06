#!/usr/bin/env python
# $Id$
"""Functions for drawing and for executing pyFormex scripts."""

import globaldata as GD
from formex import *
from canvas import *
from colors import *

import utils
import pyfotemp
import gui
import widgets
import threading,os,sys,commands

######################### Exceptions #########################################

class Exit(Exception):
    """Exception raised to exit from a running script."""
    pass    

class ExitAll(Exception):
    """Exception raised to exit pyFormex from a script."""
    pass    

#################### Interacting with the user ###############################

def ask(question,choices=None,default=''):
    """Ask a question and present possible answers."""
    if choices:
        # this currently only supports 3 answers
        return info(question,choices)
    else:
        items = [ [question, default] ]
        res,accept = widgets.inputDialog(items,'Config Dialog').process()
        GD.gui.update()
        #print res
        if accept:
            return res[0][1]
        else:
            return default

def ack(question):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question,['Yes','No']) == 0
    
def error(message,actions=['OK']):
    """Show an error message and wait for user acknowledgement."""
    return gui.messageBox(message,'error',actions)
    
def warning(message,actions=['OK']):
    """Show a warning message and wait for user acknowledgement."""
    return gui.messageBox(message,'warning',actions)

def info(message,actions=['OK']):
    """Show a neutral message and wait for user acknowledgement."""
    return gui.messageBox(message,'info',actions)
   
def about(message=GD.Version):
    """Show a informative message and wait for user acknowledgement."""
    gui.messageBox(message,'about')

def askItems(items):
    """Ask the value of some items to the user. !! VERY EXPERIMENTAL!!

    Input is a dictionary of items or a list of [key,value] pairs.
    The latter is recommended, because a dictionary does not guarantee
    the order of the items.
    Returns a dictionary (maybe we should just return the list??)
    """
    if type(items) == dict:
        items = items.items()
    #print items.items()
    res,status = widgets.inputDialog(items).process()
    #print res
    items = {}
    for r in res:
        items[r[0]] = r[1]
    return items

def log(s):
    """Display a message in the cmdlog window."""
    GD.gui.showMessage(s)

# message is the preferred function to send text info to the user.
# The default message handler is set here.
# Best candidates are log/info
message = log


########################### PLAYING SCRIPTS ##############################

scriptDisabled = False
scriptRunning = False
 
def playScript(scr):
    """Play a pyformex script scr. scr should be a valid Python text.

    There is a lock to prevent multiple scripts from being executed at the
    same time.
    """
    global scriptRunning, scriptDisabled, allowwait
    # (We only allow one script executing at a time!)
    # and scripts are non-reentrant
    if scriptRunning or scriptDisabled :
        return
    scriptRunning = True
    allowwait = True
    if GD.canvas:
        GD.canvas.update()
    if GD.gui:
        #print "Activating buttons"
        GD.gui.actions['Step'].setEnabled(True)
        GD.gui.actions['Continue'].setEnabled(True)
    else:
        print "Not activating buttons"
        
    # We need to pass formex globals to the script
    # This would be done automatically if we put this function
    # in the formex.py file. But hen we need to pass other globals
    # from this file (like draw,...)
    # We might create a module with all operations accepted in
    # scripts.
    g = globals()
    #print "Voor",g.get('__name__','Geen')
    g.update(Formex.globals())
    #print "Na",g.get('__name__','Geen')
    exitall = False
    try:
        try:
            exec scr in g
        except Exit:
            pass
        except ExitAll:
            exitall = True
    finally:
        scriptRunning = False # release the lock in case of an error
        if GD.gui:
            GD.gui.actions['Step'].setEnabled(False)
            GD.gui.actions['Continue'].setEnabled(False)
    if exitall:
        exit()

def play(fn,name=None):
    """Play a formex script from file fn."""
    global currentView,drawtimeout 
    drawtimeout = GD.cfg.gui.get('drawwait',2)
    #print "drawtimeout = %d" % drawtimeout
    currentView = 'front'
    if name:
        GD.scriptName = name
    message("Running script (%s)" % fn)
    playScript(file(fn,'r'))
    message("Script finished")


############################## drawing functions ########################

def renderMode(mode):
    global allowwait
    if allowwait:
        drawwait()
    GD.canvas.glinit(mode)
    GD.canvas.redrawAll()
    
def wireframe():
    renderMode("wireframe")
    
def flat():
    renderMode("flat")
    
def smooth():
    renderMode("smooth")


    
# A timed lock to slow down drawing processes

allowwait = True
drawlocked = False
drawtimeout = 2
# set = 0 to disable wait
# what if we want an indefinite wait (until step pressed)
drawtimer = None

def drawwait():
    """Wait for the drawing lock to be released.

    While we are waiting, events are processed.
    """
    global drawlocked, drawtimeout, drawtimer
    while drawlocked:
        GD.app.processEvents()

def drawlock():
    """Lock the drawing function for the next drawtimeout seconds."""
    global drawlocked, drawtimeout, drawtimer
    if not drawlocked and drawtimeout > 0:
        drawlocked = True
        drawtimer = threading.Timer(drawtimeout,drawrelease)
        drawtimer.start()

def drawblock():
    """Lock the drawing function indefinitely."""
    global drawlocked, drawtimer
    if drawtimer:
        drawtimer.cancel()
    if not drawlocked:
        drawlocked = True

def drawrelease():
    """Release the drawing function.

    If a timer is running, cancel it.
    """
    global drawlocked, drawtimer
    drawlocked = False
    if drawtimer:
        drawtimer.cancel()

currentView = 'front'

def draw(F,view='__last__',bbox='auto',color='prop',wait=True,eltype=None):
    """Draw a Formex on the canvas.

    Draws an actor on the canvas, and directs the camera to it from
    the specified view. Named views are either predefined or can be added by
    the user.
    If view=None is specified, the camera settings remain unchanged.
    This may make the drawn object out of view!
    A special name '__last__' may be used to keep the same camera angles
    as in the last draw operation. The camera will be zoomed on the newly
    drawn object.
    The initial default view is 'front' (looking in the -z direction).

    If bbox == 'auto', the camera will zoom automatically on the shown
    object. A bbox may be specified to have other zoom settings, e.g. to
    keep the previous settings.

    If other actors are on the scene, they may or may not be visible with the
    new camera settings. Clear the canvas before drawing if you only want
    a single actor!

    If the Formex has properties and a color list is specified, then the
    the properties will be used as an index in the color list and each member
    will be drawn with the resulting color.
    If color is one color value, the whole Formex will be drawn with
    that color.
    Finally, if color=None is specified, the whole Formex is drawn in black.
    
    Each draw action activates a locking mechanism for the next draw action,
    which will only be allowed after drawtimeout seconds have elapsed. This
    makes it easier to see subsequent images and is far more elegant that an
    explicit sleep() operation, because all script processing will continue
    up to the next drawing instruction.
    The user can disable the wait cycle for the next draw operation by
    specifying wait=False. Setting drawtimeout=0 will disable the waiting
    mechanism for all subsequent draw statements (until set >0 again).
    """
    global allowwait, currentView
    if not isinstance(F,Formex):
        raise RuntimeError,"draw() can only draw Formex instances"
    if allowwait:
        drawwait()
    lastdrawn = F
    if type(color) == str:
        if color == 'prop':
            if type(F.p) == type(None):
                color = GLColor(GD.cfg.get('defaultcolor',black)) 
            else: # use the prop as entry in a color table
                color = map(GLColor,GD.cfg.get('propcolors',[black]))
        elif color == 'random':
            color = random.random((F.nelems(),3))
        else:
            color = GLColor(color)
    GD.canvas.addActor(FormexActor(F,color,GD.cfg.get('linewidth',1),eltype=eltype))
    if view:
        if view == '__last__':
            view = currentView
        if bbox == 'auto':
            bbox = F.bbox()
        GD.canvas.setView(bbox,view)
        currentView = view
        # calculate the bbox and zoom accordingly
        GD.canvas.update()
    if allowwait and wait:
        drawlock()

def drawTriade():
    """Show the global axes."""
    GD.canvas.addActor(TriadeActor(1.0))
    GD.canvas.update()


def drawtext(text,x,y,font='9x15'):
    """Show a text at position x,y using font."""
    decorate(TextActor(text,x,y,font))

def decorate(actor):
    """Draw a decoration."""
    GD.canvas.addDecoration(actor)
    GD.canvas.update()


def view(v,wait=False):
    """Show a named view, either a builtin or a user defined."""
    global allowwait,currentView
    if allowwait:
        drawwait()
    if GD.canvas.views.has_key(v):
        GD.canvas.setView(None,v)
        currentView = v
        GD.canvas.update()
        if allowwait and wait:
            drawlock()
    else:
        warning("A view named '%s' has not been created yet" % v)

def bgcolor(color):
    """Change the background color (and redraw)."""
    color = GLColor(color)
    GD.canvas.bgcolor = color
    GD.canvas.display()
    GD.canvas.update()

def linewidth(wid):
    """Set the linewidth to be used in line drawings."""
    #GD.canvas.setLinewidth(float(wid))
    GD.cfg.linewidth = wid

def clear():
    """Clear the canvas"""
    global allowwait
    if allowwait:
        drawwait()
    GD.canvas.removeAll()
    GD.canvas.clear()

def redraw():
    GD.canvas.redrawAll()

def setview(name,angles):
    """Declare a new named view (or redefine an old).

    The angles are (longitude, latitude, twist).
    If the view name is new, and there is a views toolbar,
    a view button will be added to it."""
    gui.addView(name,angles)


def pause():
    drawblock()

def step():
    drawrelease()

def fforward():
    global allowwait
    allowwait = False
    drawrelease()
    
      
def isPyFormex(filename):
    """Checks whether a file is a pyFormex script."""
    ok = filename.endswith(".py")
    if ok:
        try:
            f = file(filename,'r')
            ok = f.readline().strip().endswith('pyformex')
            f.close()
        except IOError:
            ok = False
            warning("I could not open the file %s" % filename)
    return ok

def exit(all=False):
    if scriptRunning:
        if all:
            raise ExitAll # exit from pyformex
        else:
            raise Exit # exit from script only
    else:
        gui.exit() # exit from pyformex
        
wakeupMode=0
def sleep(timeout=None):
    """Sleep until key/mouse press in the canvas or until timeout"""
    global sleeping,wakeupMode,timer
    if wakeupMode > 0:  # don't bother : sleeps inactivated
        return
    # prepare for getting wakeup event 
    qt.QObject.connect(GD.canvas,qt.PYSIGNAL("wakeup"),wakeup)
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
    qt.QObject.disconnect(GD.canvas,qt.PYSIGNAL("wakeup"),wakeup)
        
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


def drawNamed(name,*args):
    g = globals()
    if g.has_key(name):
        F = g[name]
        if isinstance(F,Formex):
            draw(F,*args)

def drawSelected(*args):
    name = ask("Which Formex shall I draw ?")
    drawNamed(name,*args)
    

def listAll():
    """Return a list of all Formices in globals()"""
    flist = []
    for n,t in globals().items():
        if isinstance(t,Formex):
            flist.append(n)
    return flist


def printall():
    """Print all Formices in globals()"""
    print "Formices currently in globals():"
    print listAll()


def printglobals():
    print globals()


def system(cmdline,result='output'):
    if result == 'status':
        return os.system(cmdline)
    elif result == 'output':
        return commands.getoutput(cmdline)
    elif result == 'both':
        return commands.getstatusoutput(cmdline)

## exit from program pyformex
def exit(all=False):
    if scriptRunning:
        if all:
            raise ExitAll # exit from pyformex
        else:
            raise Exit # exit from script only
    if GD.app and GD.app_started: # exit from GUI
        GD.app.quit() 
    else: # the gui didn't even start
        sys.exit(0)


################################ saving images ########################

def imageFormats():
    """Return a list of the valid image formats."""
    return GD.image_formats_qt + GD.image_formats_gl2ps


def checkImageFormat(fmt,verbose=False):
    """Checks image format; if verbose, warn if it is not.

    Returns the image format, or None if it is not OK.
    """ 
    if fmt in imageFormats():
        if fmt == 'TEX' and verbose:
            warning("This will only write a LaTeX fragment to include the EPS image\nYou may still have to create the .EPS format image separately.\n")
        return fmt
    else:
        if verbose:
            error("Sorry, can not save in %s format!\n"
                  "I suggest you use PNG format ;)"%fmt)
        return None
    

def saveImage(fn,fmt=None,verbose=False):
    """Save the current rendering on file fn in format fmt.

    If no format is specified, it is derived from the extension.
    fmt should be one of the valid formats as returned by imageFormats()
    If the file has no extension, one is added based on the format.
    If verbose=True, error/warnings are activated. 
    """
    ext = os.path.splitext(fn)[1]
    if not fmt:
        fmt = utils.imageFormatFromExt(ext)
    fmt = checkImageFormat(fmt,verbose)
    if fmt:
        if len(ext) == 0:
            ext = '.%s' % fmt.lower()
            fn += ext
        GD.canvas.save(fn,fmt)

    
def saveNext():
    global multisave
    print "Saving to ",multisave
    if multisave:
        name,nr,fmt = multisave
        GD.canvas.save(name % nr,fmt)
        nr += 1
        multisave = [ name,nr,fmt ]

multisave = None


def saveMulti(fn=None,fmt=None,verbose=False):
    """Save a sequence of images.

    If the filename supplied has a trailing numeric part, subsequent images
    will be numbered continuing from this number. Otherwise a numeric part
    -000, -001, will be added to the filename.

    Without filename, switches off multisave mode.
    """
    global multisave
    # Leave multisave mode
    if not fn:
        if multisave:
            log("Leaving multi save mode")
            qt.QObject.disconnect(GD.canvas,qt.PYSIGNAL("save"),saveNext)
        multisave = None
        return

    # Enter multisave mode
    log("Entering multiple save mode to files:")
    name,ext = os.path.splitext(fn)
    fmt = utils.imageFormatFromExt(ext)
    log("%s-???.%s (%s)" % (name,ext,fmt))
    fmt = checkImageFormat(fmt,verbose)
    if fmt:
        name,number = utils.splitEndDigits(name)
        if len(number) > 0:
            nr = int(number)
            name += "%%0%dd" % len(number)
        else:
            nr = 0
            name += "-%03d"
        if len(ext) == 0:
            ext = '.%s' % fmt.lower()
        name += ext
        if verbose:
            warning("Each time you hit the 'S' key,\nthe image will be saved to the next number.")
        qt.QObject.connect(GD.canvas,qt.PYSIGNAL("save"),saveNext)
        multisave = [ name,nr,fmt ]



###########################  app  ################################

def runApp(args):
    """Create and run the qt application."""
    global app_started
    GD.app = qt.QApplication(args)
    qt.QObject.connect(GD.app,qt.SIGNAL("lastWindowClosed()"),GD.app,qt.SLOT("quit()"))
    # create GUI, show it, run it
    GD.gui = gui.GUI()
    GD.canvas = GD.gui.canvas
    GD.app.setMainWidget(GD.gui.main)
    GD.gui.main.show()
    # remaining args are interpreted as scripts
    GD.app_started = False
    for arg in args:
        if os.path.exists(arg):
            play(arg)
    GD.app_started = True
    GD.app.exec_loop()

#### End
