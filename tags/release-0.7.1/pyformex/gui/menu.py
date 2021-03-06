# $Id$
##
## This file is part of pyFormex 0.7.1 Release Sat May 24 13:26:21 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""Menus for the pyFormex GUI."""

import globaldata as GD

from gettext import gettext as _
import fileMenu
import cameraMenu
import prefMenu
import viewportMenu
import toolbar
import help
import image
import draw
import script
from plugins import surface_menu,formex_menu,tools_menu,postproc_menu


save = NotImplemented
saveAs = NotImplemented

def editor():
    if GD.gui.editor:
        print "Close editor"
        GD.gui.closeEditor()
    else:
        print "Open editor"
        GD.gui.showEditor()

 
def resetGUI():
    GD.gui.setBusy(False)
    GD.gui.actions['Play'].setEnabled(True)
    GD.gui.actions['Step'].setEnabled(True)
    GD.gui.actions['Continue'].setEnabled(False)
    GD.gui.actions['Stop'].setEnabled(False)

  

def addViewport():
    """Add a new viewport."""
    n = len(GD.gui.viewports.all)
    if n < 4:
        GD.gui.viewports.addView(n/2,n%2)

def removeViewport():
    """Remove a new viewport."""
    n = len(GD.gui.viewports.all)
    if n > 1:
        GD.gui.viewports.removeView()


def viewportSettings():
    """Interactively set the viewport settings."""
    pass


def setOptions():
    options = ['test','debug','uselib','safelib','fastencode','fastfuse']
    items = [ (o,getattr(GD.options,o)) for o in options ]
    res = draw.askItems(items)
    if res:
        for o in options:
            setattr(GD.options,o,res[o])


def my_exit():
    GD.canvas.cancel_selection()
    GD.app.processEvents()
    GD.app.exit()
            
# The menu actions can be simply function names instead of strings, if the
# functions have already been defined here.
#


FileMenuData = [
    (_('&Start new project'),fileMenu.createProject),
    ('&Open existing project',fileMenu.openProject),
    ('&Save project',fileMenu.saveProject),
    ('&Save and close project',fileMenu.closeProject),
    ('---',None),
    (_('&Create new script'),fileMenu.createScript),
    (_('&Select existing script'),fileMenu.openScript),
    (_('&Play script'),draw.play),
    (_('&Edit script'),fileMenu.edit),
    (_('&Change workdir'),draw.askDirname),
    (_('---1'),None),
    (_('&Save Image'),fileMenu.saveImage),
    (_('Start &MultiSave'),fileMenu.startMultiSave),
    (_('Save &Next Image'),image.saveNext),
    (_('Create &Movie'),image.createMovie),
    (_('&Stop MultiSave'),fileMenu.stopMultiSave),
    (_('&Save Icon'),fileMenu.saveIcon),
    (_('---2'),None),
    (_('Load &Plugins'),[
        (_('Surface menu'),surface_menu.show_menu),
        (_('Formex menu'),formex_menu.show_menu),
        (_('Tools menu'),tools_menu.show_menu),
        (_('Postproc menu'),postproc_menu.show_menu),
        ]),
    (_('&Options'),setOptions),
    (_('---3'),None),
    #        (_('E&xit'),'GD.app.exit'),
    (_('E&xit'),my_exit),
]

ActionMenuData = [
    (_('&Step'),draw.step),
    (_('&Continue'),draw.fforward), 
    (_('&Reset GUI'),resetGUI),
    (_('&Force Finish Script'),draw.force_finish),
    (_('&ListFormices'),script.printall),
    (_('&PrintGlobalNames'),script.printglobalnames),
    (_('&PrintGlobals'),script.printglobals),
    (_('&PrintConfig'),script.printconfig),
    (_('&Print Detected Software'),script.printdetected),
    (_('&PrintBbox'),draw.printbbox),
    (_('&PrintViewportSettings'),draw.printviewportsettings),
    ]

CameraMenuData = [
    (_('&LocalAxes'),draw.setLocalAxes),
    (_('&GlobalAxes'),draw.setGlobalAxes),
    (_('&Projection'),toolbar.setProjection),
    (_('&Perspective'),toolbar.setPerspective),
    (_('&Zoom All'),draw.zoomAll), 
    (_('&Zoom In'),cameraMenu.zoomIn), 
    (_('&Zoom Out'),cameraMenu.zoomOut), 
    (_('&Dolly In'),cameraMenu.dollyIn), 
    (_('&Dolly Out'),cameraMenu.dollyOut), 
    (_('&Translate'),[
        (_('Translate &Right'),cameraMenu.transRight), 
        (_('Translate &Left'),cameraMenu.transLeft), 
        (_('Translate &Up'),cameraMenu.transUp),
        (_('Translate &Down'),cameraMenu.transDown),
        ]),
    (_('&Rotate'),[
        (_('Rotate &Right'),cameraMenu.rotRight),
        (_('Rotate &Left'),cameraMenu.rotLeft),
        (_('Rotate &Up'),cameraMenu.rotUp),
        (_('Rotate &Down'),cameraMenu.rotDown), 
        (_('Rotate &ClockWise'),cameraMenu.twistRight),
        (_('Rotate &CCW'),cameraMenu.twistLeft),
        ]),
    ]
             

MenuData = [
    (_('&File'),FileMenuData),
    (_('&Actions'),ActionMenuData),
    (_('&Help'),help.MenuData)
    ]


def createMenuData():
    """Returns the full data menu."""
    # Insert configurable menus
    if GD.cfg.get('gui/prefsmenu','True'):
        MenuData[1:1] = prefMenu.MenuData
    if GD.cfg.get('gui/viewportmenu','True'):
        MenuData[2:2] = viewportMenu.MenuData
    if GD.cfg.get('gui/cameramenu','True'):
        MenuData[3:3] = [(_('&Camera'),CameraMenuData)]
    
# End
