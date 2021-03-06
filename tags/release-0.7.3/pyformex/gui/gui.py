# $Id$
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
"""Graphical User Interface for pyFormex."""

import pyformex as GD
from pyformex.gui import *

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
import scriptsMenu
import prefMenu
import toolbar
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
    print "%s %s x %s" % (t,w.x(),w.y())
def printsize(w,t=None):
    print "%s %s x %s" % (t,w.width(),w.height())

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


#####################################
################# GUI ###############
#####################################


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
        QtGui.QMainWindow.__init__(self)
        self.setWindowTitle(windowname)
        # add widgets to the main window


        # The status bar
        self.statusbar = self.statusBar()
        self.curproj = widgets.ButtonBox('Project:',['None'],[fileMenu.openProject])
        self.curfile = widgets.ButtonBox('Script:',['None'],[fileMenu.openScript])
        self.canPlay = False
        
        #cf = QtGui.QWidget()
        #hl = QtGui.QHBoxLayout()
        #hl.setSpacing(0)
        #hl.setMargin(0)
        #cf.setLayout(hl) 
        #self.curfile = QtGui.QLabel('No File')
        #self.curfile.setLineWidth(0)
        #self.smiley = QtGui.QLabel()
        #hl.addWidget(self.smiley)
        #hl.addWidget(self.curfile)
        #self.statusbar.addWidget(cf)

        # The menu bar
        self.menu = widgets.MenuBar()
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
        #### Do not touch the next line unless you know what you're doing !!
        self.easter_egg = None

        #s.moveSplitter(300,0)
        #s.moveSplitter(300,1)
        #s.setLineWidth(0)

        # self.central is the complete central widget of the main window
        self.central = QtGui.QWidget()
        self.central.autoFillBackground()
          #self.central.setFrameStyle(QtGui.QFrame.StyledPanel | QtGui.QFrame.Sunken)
        self.central.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
        self.central.resize(*GD.cfg['gui/size'])

        
        # Create an OpenGL canvas with a nice frame around it
        self.viewports = viewport.MultiCanvas()
        self.viewports.setDefaults(GD.cfg['canvas'])
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
        if GD.cfg.get('gui/timeoutbutton',False):
            toolbar.addTimeoutButton(self.toolbar)

    
        # camera buttons
        if GD.cfg.get('gui/camerabuttons',True):
            self.toolbar.addSeparator()
            toolbar.addCameraButtons(self.toolbar)
        self.menu.show()

        ##  RENDER MODE menu and toolbar ##
        modes = [ 'wireframe', 'smooth', 'smoothwire', 'flat', 'flatwire' ]
        if GD.cfg['gui/modemenu']:
            mmenu = QtGui.QMenu('Render Mode')
        else:
            mmenu = None
        # we add a modebar depending on the config:
        # modebar = None: forget it
        # modebar = 'left', 'right', 'top' or 'bottom' : separate toolbar
        # modebar = 'default' (or anything else): in the default top toolbar
        area = GD.cfg['gui/modebar']
        if area:
            area = self.toolbarArea.get(area,None)
            if area:
                self.modebar = QtGui.QToolBar('Render Mode ToolBar',self)
                self.addToolBar(area,self.modebar)
            else: # default
                self.modebar = self.toolbar
                self.toolbar.addSeparator()
        else:
            self.modebar = None
            
        # OK, we know where the actions will go, so create them
        # Add the perspective button
        if self.modebar:
            toolbar.addPerspectiveButton(self.modebar)
        self.modebtns = widgets.ActionList(
            modes,draw.renderMode,menu=mmenu,toolbar=self.modebar)
        # Add the transparency button
        if self.modebar:
            toolbar.addTransparencyButton(self.modebar)
        # Add the lights button
        if self.modebar and GD.cfg.get('gui/lightbutton',False):
            toolbar.addLightButton(self.modebar)
        # Add the normals button
        if self.modebar and GD.cfg.get('gui/normalsbutton',False):
            toolbar.addNormalsButton(self.modebar)
        # Add the shrink button
        if self.modebar and GD.cfg.get('gui/shrinkbutton',False):
            toolbar.addShrinkButton(self.modebar)
         
        if mmenu:
            # insert the mode menu in the viewport menu
            pmenu = self.menu.item('viewport')
            pmenu.insertMenu(pmenu.item('background color'),mmenu)

        ##  VIEWS menu and toolbar
        self.viewsMenu = None
        if GD.cfg.get('gui/viewmenu',True):
            self.viewsMenu = widgets.Menu('&Views',parent=self.menu,before='help')
        defviews = GD.cfg['gui/defviews']
        views = [ v[0] for v in defviews ]
        viewicons = [ v[1] for v in defviews ]
        area = GD.cfg['gui/viewbar']
        if area:
            area = self.toolbarArea.get(area,None)
            if area:
                self.viewbar = QtGui.QToolBar('Views ToolBar',self)
                self.addToolBar(area,self.viewbar)
            else: # default
                self.viewbar = self.toolbar
                self.toolbar.addSeparator()
        else:
            self.viewbar = None

        self.viewbtns = widgets.ActionList(
            views,draw.view,
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
 


    def addStatusBarButtons(self):
        sbh = self.statusbar.height()
        self.curproj.setFixedHeight(32)
        self.curfile.setFixedHeight(32)
        GD.gui.statusbar.addWidget(self.curproj)
        GD.gui.statusbar.addWidget(self.curfile)


    def setStyle(self,style):
        """Set the main application style."""
        GD.debug('Setting new style: %s' % style)
        GD.app.setStyle(style)
        self.update()


    def setFont(self,font):
        """Set the main application font."""
        if type(font) == str:
            f = QtGui.QFont()
            f.fromString(font)
            font = f
        GD.app.setFont(font)
        self.update()


    def setFontFamily(self,family):
        """Set the main application font size to the given point size."""
        font = GD.app.font()
        font.setFamily(family)
        self.setFont(font)


    def setFontSize(self,size):
        """Set the main application font size to the given point size."""
        font = GD.app.font()
        font.setPointSize(int(size))
        self.setFont(font)
         
    
    def resizeCanvas(self,wd,ht):
        """Resize the canvas."""
        self.central.resize(wd,ht)
        self.box.resize(wd,ht+self.board.height())
        self.adjustSize()
        print "RESIZED",Pos(self)
    
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
            GD.cfg['curfile'] = filename
        else:
            filename = GD.cfg.get('curfile','')
        if filename:
            self.canPlay = utils.isPyFormex(filename)
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
        """
        self.emit(QtCore.SIGNAL("Wakeup"),())
        if e.key() == QtCore.Qt.Key_F2:
            GD.debug('F2 pressed!')
            self.emit(QtCore.SIGNAL("Save"),())
        e.ignore()

##     def writeSettings(self):
##         settings = QtCore.QSettings("pyFormex", "pyFormex")
##         settings.setValue("pos", 30)
##         settings.sync()

##     def readSettings(self):
##         settings = QtCore.QSettings("pyFormex", "pyFormex")
##         pos = settings.value(QtCore.QString("pos"),QtCore.QPoint(200, 200)).toPoint()
##         size = settings.value("size", QtCore.QSize(400, 400)).toSize()
##         self.resize(size)
##         self.move(pos)

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
        GD.cfg['history'] = GD.gui.history.files

        GD.cfg.update({'size':Size(GD.gui),
                       'pos':Pos(GD.gui),
                       'bdsize':Size(GD.gui.board),
                       },name='gui')


    def cleanup(self):
        """Cleanup the GUI (restore default state)."""
        GD.debug('GUI cleanup')
        self.drawlock.release()
        GD.canvas.cancel_selection()
        self.setBusy(False)


    def closeEvent(self,event):
        """Close Main Window Event Handler"""
##         if draw.ack("Do you really want to quit?"):
##             print "YES:EXIT"
        self.cleanup()
        self.writeSettings()
        event.accept()
##         else:
##             print "NO:STAY"
##             event.ignore()




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


def createScriptMenu():
    """Create the menu(s) with pyFormex scripts

    The default is to create an entry in the toplevel menu with
    all the examples distributed with pyFormex. The user can add his
    own script directories through the configuration settings.
    """
    menus = []
    # Create a copy to leave the cfg unchanged!
    scriptdirs = [] + GD.cfg['scriptdirs']
    # Fill in missing default locations : this enables the user
    # to keep the pyFormex installed examples in his config
    knownscriptdirs = { 'examples': GD.cfg['examplesdir'] }
    for i,item in enumerate(scriptdirs):
        if type(item[0]) is str and not item[1] and item[0].lower() in knownscriptdirs:
            scriptdirs[i] = (item[0],knownscriptdirs[item[0].lower()])

    if GD.cfg.get('gui/separate_script_dirs',False):
        # This should create separate menus for all scriptdirs
        # But has not been implemented yet
        pass
    else:
        # The default is to collect all scriptdirs in a single main menu
        if len(scriptdirs) > 1:
            scriptsmenu = widgets.Menu('Scripts',GD.gui.menu)
            before = GD.gui.menu.item('help').menuAction()
            GD.gui.menu.insertMenu(before,scriptsmenu)
            before = None
        else:
            scriptsmenu = GD.gui.menu
            before = scriptsmenu.itemAction('help')

        for title,dirname in scriptdirs:
            GD.debug("Loading script dir %s" % dirname)
            if os.path.exists(dirname):
                m = scriptsMenu.ScriptsMenu(title,dir=dirname,autoplay=True)
                scriptsmenu.insert_menu(m,before)
                menus.append(m)   # Needed to keep m linked to a name !

                # This is not good, because normal users do not have
                # write access to the installed examples
##                 if title.lower() in GD.cfg.get('gui/classify_scripts',[]):
##                     m._classify()


    return menus


def runApp(args):
    """Create and run the qt application."""
    #
    # FIX FOR A BUG IN NUMPY (It's always sane anyway)
    #
    import locale
    GD.debug("LC_NUMERIC = %s" %  locale.setlocale(locale.LC_NUMERIC))
    #
    GD.app = QtGui.QApplication(args)
    #
    GD.debug("LC_NUMERIC = %s" %  locale.setlocale(locale.LC_NUMERIC))
    locale.setlocale(locale.LC_NUMERIC, 'C')
    GD.debug("LC_NUMERIC = %s" %  locale.setlocale(locale.LC_NUMERIC))
    #
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
            print "Can not open the main window --- bailing out"
            return 1
        count += 1
        windowname = '%s (%s)' % (GD.Version,count)

    if count > 0:
        warning = """
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
            return 1

    GD.gui = GUI(windowname,
                 GD.cfg.get('gui/size',(800,600)),
                 GD.cfg.get('gui/pos',(0,0)),
                 GD.cfg.get('gui/bdsize',(800,600))
                 )

    # set the appearence
    GD.gui.setStyle(GD.cfg.get('gui/style','Plastique'))
    font = GD.cfg.get('gui/font',None)
    if font:
        GD.gui.setFont(font)
    else:
        fontfamily = GD.cfg.get('gui/fontfamily',None)
        if fontfamily:
            GD.gui.setFontFamily(fontfamily)
        fontsize =  GD.cfg.get('gui/fontsize',None)
        if fontsize:
            GD.gui.setFontSize(fontsize)
    GD.gui.viewports.changeLayout(1)
    GD.gui.viewports.setCurrent(0)
    GD.board = GD.gui.board
    GD.board.write("""%s  (C) Benedict Verhegghe

pyFormex comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to redistribute it under the conditions of the
GNU General Public License, version 3 or later.
See Help->License or the file COPYING for details.
""" % GD.Version)
    GD.gui.show()
    GD.debug("Using window name %s" % GD.gui.windowTitle())
    
    # Create additional menus (put them in a list to save)
    
    # History Menu
    history = GD.cfg.get('history',None)
    if type(history) == list:
        GD.gui.history = scriptsMenu.ScriptsMenu('History',files=history,max=20)

    if GD.cfg.get('gui/history_in_main_menu',False):
        before = GD.gui.menu.item('help').menuAction()
        GD.gui.menu.insertMenu(before,GD.gui.history)
    else:
        filemenu = GD.gui.menu.item('file')
        before = filemenu.item('---1')
        filemenu.insertMenu(before,GD.gui.history)


    # Script menu
    scriptmenu = createScriptMenu()


    # Set interaction functions
    GD.message = draw.message
    GD.warning = draw.warning
    draw.reset()
    # Load plugins, ignore if not found
    import plugins
    for p in GD.cfg.get('gui/plugins',[]):
        try:
            m = getattr(plugins,p)
            if hasattr(m,'show_menu'):
                m.show_menu()
        except:
            GD.debug('ERROR while loading plugin %s' % p)
    GD.gui.setBusy(False)
    GD.gui.update()
    GD.gui.addStatusBarButtons()

    # remove the splash window
    if splash is not None:
        splash.finish(GD.gui)

    GD.gui.setBusy(False)
    GD.gui.update()
    
    if os.path.isdir(GD.cfg['workdir']):
        # Make the workdir the current dir
        os.chdir(GD.cfg['workdir'])
    else:
        # Save the current dir as workdir
        GD.cfg['workdir'] = os.getcwd()
    GD.app_started = True

    if GD.gui.easter_egg:
        draw.playScript(utils.mergeme(*GD.gui.easter_egg))

    # remaining args are interpreted as scripts and their parameters
    script.runApp(args)
    
    # Go into interactive mode
    GD.debug("Start main loop")
    GD.app.exec_()
    GD.debug("Exit main loop")

    return 0


def classify_examples():
    m = GD.gui.menu.item('Examples')
    print m
    print str(m.title())
    
        


#### End
