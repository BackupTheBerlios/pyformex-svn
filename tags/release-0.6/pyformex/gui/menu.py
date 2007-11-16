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
"""Menus for the pyFormex GUI."""

import os
from gettext import gettext as _
from PyQt4 import QtCore, QtGui
import globaldata as GD
import fileMenu
import cameraMenu
import prefMenu
import viewportMenu
import toolbar
import help
import image
import draw
from plugins import surface_menu,formex_menu,tools_menu


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
    

            
# The menu actions can be simply function names instead of strings, if the
# functions have already been defined here.
#

MenuData = [
    (_('&File'),[
        (_('&New'),fileMenu.newFile),
        (_('&Open'),fileMenu.openFile),
        (_('&Play'),draw.play),
        (_('&Edit'),fileMenu.edit),
        (_('&ChDir'),draw.askDirname),
        (_('---1'),None),
        (_('&Save Image'),fileMenu.saveImage),
        (_('Start &MultiSave'),fileMenu.startMultiSave),
        (_('Save &Next Image'),image.saveNext),
        (_('Create &Movie'),image.createMovie),
        (_('&Stop MultiSave'),fileMenu.stopMultiSave),
        (_('---2'),None),
        (_('Load &Plugins'),[
            (_('Surface menu'),surface_menu.show_menu),
            (_('Formex menu'),formex_menu.show_menu),
            (_('Tools menu'),tools_menu.show_menu),
            ]),
        (_('---3'),None),
        (_('E&xit'),'GD.app.exit'),
        ]),
    (_('&Actions'),[
        (_('&Step'),draw.step),
        (_('&Continue'),draw.fforward), 
        (_('&Reset GUI'),resetGUI),
        (_('&Force Finish Script'),draw.force_finish),
        (_('&Test Pick'),draw.pickDraw),
        (_('&ListFormices'),draw.printall),
        (_('&PrintBbox'),draw.printbbox),
        (_('&PrintGlobalNames'),draw.printglobalnames),
        (_('&PrintGlobals'),draw.printglobals),
        (_('&PrintConfig'),draw.printconfig),
        (_('&PrintViewportSettings'),draw.printviewportsettings),
        (_('&Print Detected Software'),draw.printdetected),
        ]),
    (_('&Help'),[
        (_('&pyformex options'),help.cmdline),
        (_('&Manual (local)'),help.manual),
        (_('&Manual (online)'),help.webman),
        (_('pyFormex &Website'),help.website),
        (_('&PyDoc'),help.pydoc,dict(tooltip='Autogenerated documentation from the pyFormex sources')),
        (_('&Readme'),help.readme), 
        (_('&About'),help.about), 
        (_('&License'),help.license), 
        (_('&Detected Software'),help.detected), 
        (_('&Warning'),help.testwarning),
        ])
    ]

CameraMenuData = [
    (_('&Camera'),[
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
        ]),
    ]


def createMenuData():
    """Returns the full data menu."""
    # Insert configurable menus
    if GD.cfg.get('gui/prefsmenu','True'):
        MenuData[1:1] = prefMenu.MenuData
    if GD.cfg.get('gui/viewportmenu','True'):
        MenuData[2:2] = viewportMenu.MenuData
    if GD.cfg.get('gui/cameramenu','True'):
        MenuData[3:3] = CameraMenuData
    
# End
