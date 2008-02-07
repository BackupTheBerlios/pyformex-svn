# $Id$
##
## This file is part of pyFormex 0.6 Release Fri Nov 16 22:39:28 2007
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""Graphical User Interface for pyFormex."""

import globaldata as GD
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


## # WHERE SHOULD THIS GO?
## def initViewActions(parent,viewlist):
##     """Create the initial set of view actions."""
##     global views
##     views = []
##     for name in viewlist:
##         icon = name+"view"+GD.cfg['gui/icontype']
##         Name = string.capitalize(name)
##         tooltip = Name+" View"
##         menutext = "&"+Name
##         createViewAction(parent,name,icon,tooltip,menutext)


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
        self.curproj = QtGui.QLabel('No Project')
        self.curproj.setLineWidth(0)
        self.statusbar.addWidget(self.curproj)
        cf = QtGui.QWidget()
        hl = QtGui.QHBoxLayout()
        hl.setSpacing(0)
        hl.setMargin(0)
        cf.setLayout(hl) 
        self.curfile = QtGui.QLabel('No File')
        self.curfile.setLineWidth(0)
        self.smiley = QtGui.QLabel()
        hl.addWidget(self.smiley)
        hl.addWidget(self.curfile)
        self.statusbar.addWidget(cf)

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
        # and update the default settings
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
        views = GD.cfg['gui/builtinviews']
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
            icons=['%sview' % t for t in views]
            )
        
        # Display the main menubar
        #self.menu.show()
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


    def setcurfile(self,filename=None):
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
            GD.canPlay = utils.isPyFormex(filename)
            self.curfile.setText(os.path.basename(filename))
            self.actions['Play'].setEnabled(GD.canPlay)
            self.actions['Step'].setEnabled(GD.canPlay)
            if GD.canPlay:
                icon = 'ok'
            else:
                icon = 'notok'
            self.smiley.setPixmap(QtGui.QPixmap(os.path.join(GD.cfg['icondir'],icon)+GD.cfg['gui/icontype']))


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


    def keyPressEvent (self,e):
        """Top level key press event handler.

        Events get here if they are not handled by a lower level handler.
        """
        self.emit(QtCore.SIGNAL("Wakeup"),())
        if e.key() == QtCore.Qt.Key_F2:
            GD.debug('F2 pressed!')
            self.emit(QtCore.SIGNAL("Save"),())
        e.ignore()


def windowExists(windowname):
    """Check if a GUI window with the given name exists.

    On X-Window systems, we can use the xwininfo cammand to find out whether
    a window with the specified name exists.
    """
    return not os.system('xwininfo -name "%s" > /dev/null 2>&1' % windowname)


def quit():
    """Quit the GUI"""
    sys.stderr = sys.__stderr__
    sys.stdout = sys.__stdout__
    draw.drawrelease()
    if GD.app:
        GD.app.exit()


    
def createScriptMenu(scriptdirs,menu,recursive=True):
    """Create a menu with pyFormex scripts and insert it in specified menu.

    scriptsdirs is a list of (title,dir) tuples, where title is the menu
    title and dir is a directory to be scanned for scripts.
    If recursive is True, subdirectories will be added as a submenu.
    As a convenience, if an empty dirname is specified and the title
    is one of the keys in known_scriptdirs, the corresponding dir entry
    will be used. This enables the user to add pyFormex system script dirs
    into his config.
    Returns the list of created menu items.
    """
    menus = []
    known_scriptdirs = { 'examples': GD.cfg['examplesdir'] }

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
        if not dirname:
            dirname = known_scriptdirs[title.lower()]
        if os.path.exists(dirname):
            m = scriptsMenu.ScriptsMenu(title,dirname,autoplay=True)
            scriptsmenu.insert_menu(m,before)
            menus.append(m)   # Needed to keep m linked to a name
    return menus



def runApp(args):
    """Create and run the qt application."""
    GD.app = QtGui.QApplication(args)
    QtCore.QObject.connect(GD.app,QtCore.SIGNAL("lastWindowClosed()"),GD.app,QtCore.SLOT("quit()"))
    QtCore.QObject.connect(GD.app,QtCore.SIGNAL("aboutToQuit()"),quit)
        
     # Set some globals
    GD.image_formats_qt = map(str,QtGui.QImageWriter.supportedImageFormats())
    GD.image_formats_qtr = map(str,QtGui.QImageReader.supportedImageFormats())
    if GD.cfg.get('imagesfromeps',False):
        GD.image_formats_qt = []
    if GD.options.debug:
        print "Qt image types for saving: ",GD.image_formats_qt
        print "Qt image types for input: ",GD.image_formats_qtr
        print "gl2ps image types:",GD.image_formats_gl2ps
        print "image types converted from EPS:",GD.image_formats_fromeps
        
    # Load the splash image
    splash = None
    print "XXXXXXXXXXX %s XXXXXXXXXXXXXX" % GD.cfg['gui/splash']
    if os.path.exists(GD.cfg['gui/splash']):
        GD.debug('Loading splash %s' % GD.cfg['gui/splash'])
        splashimage = QtGui.QPixmap(GD.cfg['gui/splash'])
        splash = QtGui.QSplashScreen(splashimage)
        splash.showMessage(GD.Version,QtCore.Qt.AlignHCenter,QtCore.Qt.red)
        splash.show()
        
    # create GUI, show it, run it
    windowname = GD.Version
    count = 0
    while windowExists(windowname):
        if count > 255:
            print "Can not open the main window --- bailing out"
            return 1
        count += 1
        windowname = '%s (%s)' % (GD.Version,count)

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
    GD.board = GD.gui.board
    GD.board.write("""%s  (C) B. Verhegghe

pyFormex comes with ABSOLUTELY NO WARRANTY. This is free software,
and you are welcome to redistribute it under certain conditions.
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


    # Create a menu with pyFormex examples
    # and insert it before the help menu
    menus = []
    scriptdirs = GD.cfg['scriptdirs']
    knownscriptdirs = { 'examples': GD.cfg['examplesdir'] }

    if GD.cfg.get('gui/separate_script_dirs',False):
        # This will create separate menus for all scriptdirs
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
            if not dirname:
                dirname = knownscriptdirs[title.lower()]
            if os.path.exists(dirname):
                m = scriptsMenu.ScriptsMenu(title,dirname,autoplay=True)
                scriptsmenu.insert_menu(m,before)
                menus.append(m)   # Needed to keep m linked to a name,
                                  # else the menu is destroyed!

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

    # remove the splash window
    if splash is not None:
        splash.finish(GD.gui)

    # remaining args are interpreted as scripts
    for arg in args:
        if os.path.exists(arg):
            draw.play(arg)

    GD.gui.setBusy(False)
    GD.gui.update()
    if os.path.isdir(GD.cfg['workdir']):
        # Make the workdir the current dir
        os.chdir(GD.cfg['workdir'])
    else:
        # Save the current dir as workdir
        GD.cfg['workdir'] = os.getcwd()
    GD.app_started = True
    GD.app.exec_()

    # Cleanup
    draw.drawrelease()
    GD.gui.setBusy(False)

    # store the history and main window size/pos
    GD.cfg['history'] = GD.gui.history.files

    # Sometimes, a negative value is stored, making restart partially obscured
    x,y = Pos(GD.gui)
    if x < 0:
        x = 0
    if y < 0:
        y = 0
    GD.cfg.update({'size':Size(GD.gui),
                   'pos':(x,y),
                   'bdsize':Size(GD.gui.board),
                   },name='gui')
    return 0

#### End
