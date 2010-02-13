# $Id$
##
##  This file is part of pyFormex 0.8.1 Release Wed Dec  9 11:27:53 2009
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Homepage: http://pyformex.org   (http://pyformex.berlios.de)
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
"""Graphical User Interface for pyFormex."""

import pyformex as GD
from pyformex.gui import signals

import sys,utils
if not ( utils.hasModule('numpy') and
         utils.hasModule('pyopengl') and
         utils.hasModule('pyqt4') ):
    sys.exit()

import time,os.path,string,re

from PyQt4 import QtCore, QtGui

import menu
import cameraMenu
import fileMenu
import scriptMenu
import prefMenu
import toolbar
import canvas
import viewport

import script
import draw
import widgets
import drawlock

############### General Qt utility functions #######

## might go to a qtutils module

def Size(widget):
    """Return the size of a widget as a tuple."""
    s = widget.size()
    return s.width(),s.height()

def Pos(widget):
    """Return the position of a widget as a tuple."""
    p = widget.pos()
    return p.x(),p.y()

def printpos(w,t=None):
    print("%s %s x %s" % (t,w.x(),w.y()))
def printsize(w,t=None):
    print("%s %s x %s" % (t,w.width(),w.height()))

################# Message Board ###############

class Board(QtGui.QTextEdit):
    """Message board for displaying read-only plain text messages."""
    
    def __init__(self,parent=None):
        """Construct the Message Board widget."""
        QtGui.QTextEdit.__init__(self,parent)
        self.setReadOnly(True) 
        self.setAcceptRichText(False)
        self.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.setMinimumSize(24,24)
        self.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
        self.cursor = self.textCursor()
        #self.buffer = ''

    def write(self,s):
        """Write a string to the message board."""
        # Skip a single blank character seems to be generated by a print
        # instruction containing a comma: skip it
        if s == ' ':
            return
        #self.buffer += '[%s:%s]' % (len(s),s)
        s = s.rstrip('\n')
        if len(s) > 0:
            self.append(s)
            self.cursor.movePosition(QtGui.QTextCursor.End)
            self.setTextCursor(self.cursor)

    def flush(self):
        self.update()


#####################################
################# GUI ###############
#####################################

def set_view(view):
    """Change the view angles of the current camera, keeping the bbox."""
    GD.canvas.setCamera(angles=view)
    GD.canvas.update()
    

class GUI(QtGui.QMainWindow):
    """Implements a GUI for pyformex."""

    toolbarArea = { 'top': QtCore.Qt.TopToolBarArea,
                    'bottom': QtCore.Qt.BottomToolBarArea,
                    'left': QtCore.Qt.LeftToolBarArea,
                    'right': QtCore.Qt.RightToolBarArea,
                    }

    def __init__(self,windowname,size=(800,600),pos=(0,0),bdsize=(0,0)):
        """Constructs the GUI.

        The GUI has a central canvas for drawing, a menubar and a toolbar
        on top, and a statusbar at the bottom.
        """

        
        self.on_exit = [fileMenu.askCloseProject] 
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle(windowname)
        # add widgets to the main window


        # The status bar
        self.statusbar = self.statusBar()
        self.curproj = widgets.ButtonBox('Project:',[('None',fileMenu.openProject)])
        self.curfile = widgets.ButtonBox('Script:',[('None',fileMenu.openScript)])
        self.canPlay = False
        
        # The menu bar
        self.menu = menu.MenuBar('TopMenu')
        self.setMenuBar(self.menu)

        # The toolbar
        self.toolbar = self.addToolBar('Top ToolBar')
        self.editor = None
        # Create a box for the central widget
        self.box = QtGui.QWidget()
        self.setCentralWidget(self.box)
        self.boxlayout = QtGui.QVBoxLayout()
        self.box.setLayout(self.boxlayout)
        #self.box.setFrameStyle(qt.QFrame.Sunken | qt.QFrame.Panel)
        #self.box.setLineWidth(2)
        # Create a splitter
        self.splitter = QtGui.QSplitter()
        self.boxlayout.addWidget(self.splitter)
        self.splitter.setOrientation(QtCore.Qt.Vertical)
        self.splitter.show()

        # self.central is the complete central widget of the main window
        self.central = QtGui.QWidget()
        self.central.autoFillBackground()
          #self.central.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.central.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
        self.central.resize(*GD.cfg['gui/size'])

        
        # Create an OpenGL canvas with a nice frame around it
        GD.debug("Setting canvas defaults:\n%s" % dict)
        canvas.CanvasSettings.default.update(canvas.CanvasSettings.checkDict(GD.cfg['canvas']))

        self.viewports = viewport.MultiCanvas()
        self.central.setLayout(self.viewports)

        # Create the message board
        self.board = Board()
        #self.board.setPlainText(GD.Version+' started')
        # Put everything together
        self.splitter.addWidget(self.central)
        self.splitter.addWidget(self.board)
        #self.splitter.setSizes([(800,200),(800,600)])
        self.box.setLayout(self.boxlayout)
        # Create the top menu
        menu.createMenuData()
        self.menu.insertItems(menu.MenuData)
        # ... and the toolbar
        self.actions = toolbar.addActionButtons(self.toolbar)

        # timeout button 
        toolbar.addTimeoutButton(self.toolbar)

        self.menu.show()

        # Define Toolbars
        self.toolbardefs = [ ('Camera ToolBar','camerabar'),
                             ('RenderMode ToolBar','modebar'),
                             ('Views ToolBar','viewbar'),
                             ]
        ###############  CAMERA menu and toolbar #############
        self.camerabar = self.activateToolBar('Camera ToolBar','camerabar')
        if self.camerabar:
            toolbar.addCameraButtons(self.camerabar)
            toolbar.addPerspectiveButton(self.camerabar)

        ###############  RENDERMODE menu and toolbar #############
        modes = [ 'wireframe', 'smooth', 'smoothwire', 'flat', 'flatwire' ]
        if GD.cfg['gui/modemenu']:
            mmenu = QtGui.QMenu('Render Mode')
        else:
            mmenu = None
        self.modebar = self.activateToolBar('RenderMode ToolBar','modebar')
            
        #menutext = '&' + name.capitalize()
        self.modebtns = menu.ActionList(
            modes,draw.renderMode,menu=mmenu,toolbar=self.modebar)
        
        # Add the toggle type buttons
        if self.modebar:
            toolbar.addTransparencyButton(self.modebar)
        if self.modebar and GD.cfg['gui/lightbutton']:
            toolbar.addLightButton(self.modebar)
        if self.modebar and GD.cfg['gui/normalsbutton']:
            toolbar.addNormalsButton(self.modebar)
        if self.modebar and GD.cfg['gui/shrinkbutton']:
            toolbar.addShrinkButton(self.modebar)
         
        if mmenu:
            # insert the mode menu in the viewport menu
            pmenu = self.menu.item('viewport')
            pmenu.insertMenu(pmenu.item('background color'),mmenu)

        ###############  VIEWS menu and toolbar ################
        self.viewsMenu = None
        if GD.cfg['gui/viewmenu']:
            self.viewsMenu = menu.Menu('&Views',parent=self.menu,before='help')
        self.viewbar = self.activateToolBar('Views ToolBar','viewbar')

        defviews = GD.cfg['gui/defviews']
        views = [ v[0] for v in defviews ]
        viewicons = [ v[1] for v in defviews ]

        self.viewbtns = menu.ActionList(
            views,set_view,
            menu=self.viewsMenu,
            toolbar=self.viewbar,
            icons = viewicons
            )

        # Restore previous pos/size
        self.resize(*size)
        self.move(*pos)
        self.board.resize(*bdsize)
        
        self.setcurfile()
        if GD.options.redirect:
            sys.stderr = self.board
            sys.stdout = self.board
        if GD.options.debug:
            printsize(self,'DEBUG: Main:')
            printsize(self.central,'DEBUG: Canvas:')
            printsize(self.board,'DEBUG: Board:')

        # Drawing lock
        self.drawwait = GD.cfg['draw/wait']
        self.drawlock = drawlock.DrawLock()
 


    def activateToolBar(self,fullname,shortname):
        """Add a new toolbar to the GUI main window.

        The full name is the name as displayed to the user.
        The short name is the name as used in the config settings.

        The config setting for the toolbar determines its placement:
        - None: the toolbar is not created
        - 'left', 'right', 'top' or 'bottom': a separate toolbar is created
        - 'default': the default top toolbar is used and a separator is added.
        """
        area = GD.cfg['gui/%s' % shortname]
        if area:
            area = self.toolbarArea.get(area,None)
            if area:
                toolbar = QtGui.QToolBar(fullname,self)
                self.addToolBar(area,toolbar)
            else: # default
                toolbar = self.toolbar
                self.toolbar.addSeparator()
        else:
            toolbar = None
        return toolbar


    def addStatusBarButtons(self):
        sbh = self.statusbar.height()
        #self.curproj.setFixedHeight(32)
        #self.curfile.setFixedHeight(32)
        self.statusbar.addWidget(self.curproj)
        self.statusbar.addWidget(self.curfile)


    def addInputBox(self):
        self.input = widgets.InputBox()
        self.statusbar.addWidget(self.input)


    def toggleInputBox(self,onoff=None):
        if onoff is None:
            onoff = self.input.isHidden()
        self.input.setVisible(onoff)


    def addCoordsTracker(self):
        self.coordsbox = widgets.CoordsBox()
        self.statusbar.addPermanentWidget(self.coordsbox)

        
    def toggleCoordsTracker(self,onoff=None):
        def track(x,y,z):
            X,Y,Z = GD.canvas.unProject(x,y,z)
            print "%s --> %s" % ((x,y,z),(X,Y,Z))
            GD.GUI.coordsbox.setValues([X,Y,Z])

        if onoff is None:
            onoff = self.coordsbox.isHidden()
        if onoff:
            func = track
        else:
            func = None
        for vp in self.viewports.all:
            vp.trackfunc = func
        self.coordsbox.setVisible(onoff)
         
    
    def resizeCanvas(self,wd,ht):
        """Resize the canvas."""
        self.central.resize(wd,ht)
        self.box.resize(wd,ht+self.board.height())
        self.adjustSize()
        print("RESIZED",Pos(self))
    
    def showEditor(self):
        """Start the editor."""
        if not hasattr(self,'editor'):
            self.editor = Editor(self,'Editor')
            self.editor.show()
            self.editor.setText("Hallo\n")

    def closeEditor(self):
        """Close the editor."""
        if hasattr(self,'editor'):
            self.editor.close()
            self.editor = None
    

    def setcurproj(self,project=''):
        """Show the current project name."""
        if project:
            project = os.path.basename(project)
        self.curproj.setText(project)


    def setcurfile(self,filename=''):
        """Set the current file and check whether it is a pyFormex script.

        The checking is done by the function isPyFormex().
        A file that is not a pyFormex script can be loaded in the editor,
        but it can not be played as a pyFormex script.
        """
        if filename:
            # We always set it to be saved in the prefs
            GD.prefcfg['curfile'] = filename
        else:
            filename = GD.cfg['curfile']
        if filename:
            self.canPlay = utils.isPyFormex(filename) or filename.endswith('.pye')
            self.curfile.setText(os.path.basename(filename))
            self.actions['Play'].setEnabled(self.canPlay)
            self.actions['Step'].setEnabled(self.canPlay)
            if self.canPlay:
                icon = 'ok'
            else:
                icon = 'notok'
            self.curfile.setIcon(QtGui.QIcon(QtGui.QPixmap(os.path.join(GD.cfg['icondir'],icon)+GD.cfg['gui/icontype'])),0)


    def setViewAngles(self,name,angles):
        """Create a new view and add it to the list of predefined views.

        This creates a named view with specified angles for the canvas.
        If the name already exists in the canvas views, it is overwritten
        by the new angles.
        It adds the view to the views Menu and Toolbar, if these exist and
        do not have the name yet.
        """
        if name not in self.viewbtns.names():
            iconpath = os.path.join(GD.cfg['icondir'],'userview')+GD.cfg['gui/icontype']
            self.viewbtns.add(name,iconpath)
        GD.canvas.view_angles[name] = angles


    def setBusy(self,busy=True):
        if busy:
            GD.app.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        else:
            GD.app.restoreOverrideCursor()
        GD.app.processEvents()


    def keyPressEvent(self,e):
        """Top level key press event handler.

        Events get here if they are not handled by a lower level handler.
        Every key press arriving here generates a WAKEUP signal, and if a
        dedicated signal for the key was installed in the keypress table,
        that signal is emitted too.
        Finally, the event is removed.
        """
        key = e.key()
        GD.debug('Key %s pressed' % key)
        self.emit(signals.WAKEUP,())
        signal = signals.keypress_signal.get(key,None)
        if signal:
            self.emit(signal,())
        e.ignore()


    def XPos(self):
        """Get the main window position from the xwininfo command.

        The (Py)Qt4 position does not get updated when
        changing the window size from the left.
        This substitute function will find the correct position from
        the xwininfo command output.
        """
        res = xwininfo(self.winId())
        ax,ay,rx,ry = [ int(res[key]) for key in [
            'Absolute upper-left X','Absolute upper-left Y',
            'Relative upper-left X','Relative upper-left Y',
            ]]
        return ax-rx,ay-ry


    def writeSettings(self):
        """Store th GUI settings"""
        # FIX QT4 BUG
        # Make sure QT4 has position right
        self.move(*self.XPos())

        # store the history and main window size/pos
        GD.cfg['history'] = GD.GUI.history.files

        GD.cfg.update({'size':Size(GD.GUI),
                       'pos':Pos(GD.GUI),
                       'bdsize':Size(GD.GUI.board),
                       },name='gui')


    def cleanup(self):
        """Cleanup the GUI (restore default state)."""
        GD.debug('GUI cleanup')
        self.drawlock.release()
        GD.canvas.cancel_selection()
        GD.canvas.cancel_draw()
        draw.clear_canvas()
        self.setBusy(False)


    def closeEvent(self,event):
        """Close Main Window Event Handler"""
##         if draw.ack("Do you really want to quit?"):
##             print("YES:EXIT")
        self.cleanup()
        GD.debug("Executing registered exit functions")
        for f in self.on_exit:
            GD.debug(f)
            f()
        self.writeSettings()
        event.accept()
##         else:
##             print("NO:STAY")
##             event.ignore()

    def onExit(self,func):
        """Register a function for execution on exit"""
        self.on_exit.append(func)
            
# THESE FUNCTION SHOULD BECOME app FUNCTIONS

    def currentStyle(self):
        return GD.app.style().metaObject().className()[1:-5]


    def getStyles(self):
        return map(str,QtGui.QStyleFactory().keys())


    def setStyle(self,style):
        """Set the main application style."""
        style = QtGui.QStyleFactory().create(style)
        GD.app.setStyle(style)
        self.update()


    def setFont(self,font):
        """Set the main application font.

        font is either a QFont or a string resulting from the
        QFont.toString() method
        """
        if not isinstance(font,QtGui.QFont):
            f = QtGui.QFont()
            f.fromString(font)
            font = f
        GD.app.setFont(font)
        self.update()


    def setFontFamily(self,family):
        """Set the main application font family to the given family."""
        font = GD.app.font()
        font.setFamily(family)
        self.setFont(font)


    def setFontSize(self,size):
        """Set the main application font size to the given point size."""
        font = GD.app.font()
        font.setPointSize(int(size))
        self.setFont(font)


    def setAppearence(self):
        style = GD.cfg['gui/style']
        font = GD.cfg['gui/font']
        family = GD.cfg['gui/fontfamily']
        size = GD.cfg['gui/fontsize']
        if style:
            self.setStyle(style)
        if font:
            self.setFont(font)
        if family:
            self.setFontFamily(family)
        if size:
            self.setFontSize(size)
        


def xwininfo(windowid):
    """Returns the X window info parsed as a dict.

    windowid is the unique integer window identifier
    """
    sta,out = utils.runCommand('xwininfo -id %d' % windowid,quiet=True)
    res = {}
    for line in out.split('\n'):
        s = line.split(':')
        if len(s) < 2:
            s = s[0].strip().split(' ')
        if len(s) < 2:
            continue
        elif len(s) > 2:
            if s[0] == 'xwininfo':
                s = s [-2:]
        if s[0][0] == '-':
            s[0] = s[0][1:]
        res[s[0].strip()] = s[1].strip()
    return res


def windowExists(windowname):
    """Check if a GUI window with the given name exists.

    On X-Window systems, we can use the xwininfo command to find out whether
    a window with the specified name exists.
    """
    return not os.system('xwininfo -name "%s" > /dev/null 2>&1' % windowname)


def quit():
    """Quit the GUI"""
    sys.stderr = sys.__stderr__
    sys.stdout = sys.__stdout__
    if GD.app:
        GD.app.exit()


def startGUI(args):
    """Create the QT4 application and GUI.

    A (possibly empty) list of command line options should be provided.
    QT4 wil remove the recognized QT4 and X11 options.
    """
    # This seems to be the only way to make sure the numeric conversion is
    # always correct
    #
    QtCore.QLocale.setDefault(QtCore.QLocale.c())
    #
    #GD.options.debug = -1
    GD.debug("Arguments passed to the QApplication: %s" % args)
    GD.app = QtGui.QApplication(args)
    
    #
    GD.debug("Arguments left after constructing the QApplication: %s" % args)
    GD.debug("Arguments left after constructing the QApplication: %s" % GD.app.arguments().join('\n'))
    #GD.options.debug = 0
    # As far as I have been testing this, the args passed to the Qt application are
    # NOT acknowledged and neither are they removed!!


    GD.app.setOrganizationName("pyformex.org")
    GD.app.setOrganizationDomain("pyformex.org")
    GD.app.setApplicationName("pyFormex")
    GD.app.setApplicationVersion(GD.__version__)
    ## GD.settings = QtCore.QSettings("pyformex.org", "pyFormex")
    ## GD.settings.setValue("testje","testvalue")
    ## print "%s" % GD.settings
    

    #
    #
    
    QtCore.QObject.connect(GD.app,QtCore.SIGNAL("lastWindowClosed()"),GD.app,QtCore.SLOT("quit()"))
    QtCore.QObject.connect(GD.app,QtCore.SIGNAL("aboutToQuit()"),quit)
        
    # Load the splash image
    splash = None
    if os.path.exists(GD.cfg['gui/splash']):
        GD.debug('Loading splash %s' % GD.cfg['gui/splash'])
        splashimage = QtGui.QPixmap(GD.cfg['gui/splash'])
        splash = QtGui.QSplashScreen(splashimage)
        splash.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        splash.setFont(QtGui.QFont("Helvetica",24))
        splash.showMessage(GD.Version,QtCore.Qt.AlignHCenter,QtCore.Qt.red)
        splash.show()

    # create GUI, show it, run it
    viewport.setOpenGLFormat()
    dri = viewport.opengl_format.directRendering()

    windowname = GD.Version
    count = 0
    while windowExists(windowname):
        if count > 255:
            print("Can not open the main window --- bailing out")
            return -1
        count += 1
        windowname = '%s (%s)' % (GD.Version,count)

    if count > 0:
        warning = """..
        
Another instance of pyFormex is already running
on this screen. This may be a leftover from a
previously crashed program. In that case you should
bail out now and first kill the crashed program.

On the other hand, if you really want to run another
pyFormex in parallel, you can just continue now.
"""
        actions = ['Really Continue','Bail out and fix the problem']
        if dri:
            answer = draw.ask(warning,actions)
        if not dri:
            warning += """
I have detected that the Direct Rendering Infrastructure
is not activated on your system. Continuing with a second
instance of pyFormex may crash you XWindow system.
You should seriously consider to bail out now!!!
"""
            answer = draw.warning(warning,actions)
        if answer != 'Really Continue':
            return -1

    GD.GUI = GUI(windowname,
                 GD.cfg.get('gui/size',(800,600)),
                 GD.cfg.get('gui/pos',(0,0)),
                 GD.cfg.get('gui/bdsize',(800,600)),
                 )

    # set the appearance
    GD.GUI.setAppearence()
    ## GD.GUI.setStyle(GD.cfg.get('gui/style','Plastique'))
    ## font = GD.cfg.get('gui/font',None)
    ## if font:
    ##     GD.GUI.setFont(font)
    ## else:
    ##     fontfamily = GD.cfg.get('gui/fontfamily',None)
    ##     if fontfamily:
    ##         GD.GUI.setFontFamily(fontfamily)
    ##     fontsize =  GD.cfg.get('gui/fontsize',None)
    ##     if fontsize:
    ##         GD.GUI.setFontSize(fontsize)
    # THIS OCCASIONALLy CAUSE fpbug ON bumper
    GD.GUI.viewports.changeLayout(1)
    GD.GUI.viewports.setCurrent(0)
    GD.board = GD.GUI.board
    GD.board.write("""%s  (C) Benedict Verhegghe

pyFormex comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to redistribute it under the conditions of the
GNU General Public License, version 3 or later.
See Help->License or the file COPYING for details.
""" % GD.Version)
    GD.GUI.addInputBox()
    GD.GUI.toggleInputBox(False)
    GD.GUI.addCoordsTracker()
    GD.GUI.toggleCoordsTracker(GD.cfg.get('gui/coordsbox',False))
    GD.GUI.show()
    GD.debug("Using window name %s" % GD.GUI.windowTitle())
    
    # Create additional menus (put them in a list to save)
    
    # History Menu
    history = GD.cfg.get('history',None)
    if type(history) == list:
        GD.GUI.history = scriptMenu.ScriptMenu('History',files=history,max=20)

    if GD.cfg.get('gui/history_in_main_menu',False):
        before = GD.GUI.menu.item('help')
        GD.GUI.menu.insertMenu(before,GD.GUI.history)
    else:
        filemenu = GD.GUI.menu.item('file')
        before = filemenu.item('---1')
        filemenu.insertMenu(before,GD.GUI.history)
    

    # Scripts menu
    GD.GUI.scriptmenu = scriptMenu.createScriptMenu(GD.GUI.menu,before='help')

    # PLugin menus
    import plugins
    ## filemenu = GD.GUI.menu.item('file')
    ## GD.gui.saveobj = plugins.create_plugin_menus(filemenu,before='options')
    ## # Load configured plugins, ignore if not found
    plugins.loadConfiguredPlugins()
    #for p in GD.cfg['gui/plugins']:
    #    plugins.load(p)
    
    # Set interaction functions
    GD.message = draw.message
    GD.warning = draw.warning
    draw.reset()

    GD.GUI.setBusy(False)
    GD.GUI.addStatusBarButtons()
    GD.GUI.update()

    # remove the splash window
    if splash is not None:
        splash.finish(GD.GUI)

    GD.GUI.setBusy(False)
    GD.GUI.update()
    
    if os.path.isdir(GD.cfg['workdir']):
        # Make the workdir the current dir
        os.chdir(GD.cfg['workdir'])
    else:
        # Save the current dir as workdir
        prefMenu.updateSettings({'workdir':os.getcwd(),'Save changes':True})
    GD.app_started = True
    GD.app.processEvents()
    return 0



def runGUI():
    """Go into interactive mode"""

    egg = GD.cfg.get('gui/easter_egg',None)
    GD.debug('EGG: %s' % str(egg))
    if egg:
        GD.debug('EGG')
        if type(egg) is str:
            pye = egg.endswith('pye')
            egg = file(egg).read()
        else:
            pye = True
            egg = ''.join(egg)
        draw.playScript(egg,pye=True)

    GD.debug("Start main loop")
    #utils.procInfo('runGUI')
    #from multiprocessing import Process
    #p = Process(target=GD.app.exec_)
    #p.start()
    #res = p.join()
    res = GD.app.exec_()
    GD.debug("Exit main loop with value %s" % res)
    return res


def classify_examples():
    m = GD.GUI.menu.item('Examples')
    #print(m)
    #print(str(m.title()))
    
        


#### End
