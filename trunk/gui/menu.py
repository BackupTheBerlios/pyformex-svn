#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.4.2 Release Mon Feb 26 08:57:40 2007
## pyFormex is a python implementation of Formex algebra
## Homepage: http://pyformex.berlios.de/
## Distributed under the GNU General Public License, see file COPYING
## Copyright (C) Benedict Verhegghe except where stated otherwise 
##
"""Menus for the pyFormex GUI."""

import os
from gettext import gettext as _
from PyQt4 import QtCore, QtGui
import globaldata as GD
import fileMenu
import cameraMenu
import prefMenu
import help
import draw
from plugins import stl_menu,formex_menu


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
  

# The menu actions can be simply function names instead of strings, if the
# functions have already been defined here.
#

MenuData = [
    (_('&File'),[
        (_('&New'),fileMenu.newFile),
        (_('&Open'),fileMenu.openFile),
        (_('&Play'),fileMenu.play),
        (_('&Edit'),fileMenu.edit),
#        (_('&Save'),'save'),
#        (_('Save &As'),'saveAs'),
        (_('---'),None),
        (_('Save &Image'),fileMenu.saveImage),
        (_('Start &MultiSave'),fileMenu.startMultiSave),
        (_('Stop &MultiSave'),fileMenu.stopMultiSave),
        (_('Save &Next Image'),draw.saveNext),
        (_('---'),None),
        (_('Load &Plugins'),[
            (_('Surface menu'),stl_menu.show_menu),
            (_('Formex menu'),formex_menu.show_menu),
            ]),
        (_('---'),None),
        (_('E&xit'),'GD.app.exit'),
        ]),
    (_('&Settings'),[
        (_('&Appearance'),prefMenu.setAppearance), 
        (_('&Font'),prefMenu.setFont), 
        (_('Toggle &Triade'),draw.toggleTriade), 
        (_('&Drawwait Timeout'),prefMenu.setDrawtimeout), 
        (_('&Background Color'),prefMenu.setBGcolor), 
        (_('Line&Width'),prefMenu.setLinewidth), 
        (_('&Canvas Size'),prefMenu.setCanvasSize), 
        (_('&RotFactor'),prefMenu.setRotFactor),
        (_('&PanFactor'),prefMenu.setPanFactor),
        (_('&ZoomFactor'),prefMenu.setZoomFactor),
        (_('&Wireframe'),draw.wireframe),
        (_('&Flat'),draw.flat),
        (_('&Flat + Wireframe'),draw.flatwire),
        (_('&Smooth'),draw.smooth),
        (_('&Smooth + Wireframe'),draw.smoothwire),
        (_('&Render'),prefMenu.setRender),
        (_('&Light0'),prefMenu.setLight0),
        (_('&Light1'),prefMenu.setLight1),
        (_('&Commands'),prefMenu.setCommands),
        (_('&Help'),prefMenu.setHelp),
        (_('&Save Preferences'),GD.savePreferences), ]),
    (_('&Camera'),[
        (_('&LocalAxes'),draw.setLocalAxes),
        (_('&GlobalAxes'),draw.setGlobalAxes),
        (_('&Projection'),cameraMenu.setProjection),
        (_('&Perspective'),cameraMenu.setPerspective),
        (_('&Zoom All'),draw.zoomAll), 
        (_('&Zoom In'),cameraMenu.zoomIn), 
        (_('&Zoom Out'),cameraMenu.zoomOut), 
        (_('&Dolly In'),cameraMenu.dollyIn), 
        (_('&Dolly Out'),cameraMenu.dollyOut), 
        (_('Translate &Right'),cameraMenu.transRight), 
        (_('Translate &Left'),cameraMenu.transLeft), 
        (_('Translate &Up'),cameraMenu.transUp),
        (_('Translate &Down'),cameraMenu.transDown),
        (_('Rotate &Right'),cameraMenu.rotRight),
        (_('Rotate &Left'),cameraMenu.rotLeft),
        (_('Rotate &Up'),cameraMenu.rotUp),
        (_('Rotate &Down'),cameraMenu.rotDown), 
        (_('Rotate &ClockWise'),cameraMenu.twistRight),
        (_('Rotate &CCW'),cameraMenu.twistLeft),
        ]),
    (_('&Actions'),[
        (_('&Step'),draw.step),
        (_('&Continue'),draw.fforward), 
        (_('&Clear'),draw.clear),
        (_('&Redraw'),draw.redraw),
        (_('&Reset'),draw.reset),
        (_('&Reset GUI'),resetGUI),
        (_('&ListFormices'),draw.printall),
        (_('&PrintBbox'),draw.printbbox),
        (_('&PrintGlobals'),draw.printglobals),
        (_('&PrintConfig'),draw.printconfig),
        ]),
    (_('&Help'),[
        (_('&pyformex options'),help.cmdline),
        (_('&Manual (local)'),help.manual),
        (_('&Manual (online)'),help.webman),
        (_('pyFormex &Website'),help.website),
        (_('&PyDoc'),help.pydoc,None,None,'Autogenerated documentation from the pyFormex sources'),
        (_('&Readme'),help.readme), 
        (_('&About'),help.about), 
        (_('&Warning'),help.testwarning),
        ])
    ]


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

ViewportMenuData = [
    (_('&Viewport'),[
        (_('&Add new viewport'),addViewport), 
        (_('&Remove last viewport'),removeViewport), 
        ]),
    ]


def insertViewportMenu():
    """Insert the viewport menu data into the global menu data."""
    MenuData[2:2] = ViewportMenuData

    
# End
