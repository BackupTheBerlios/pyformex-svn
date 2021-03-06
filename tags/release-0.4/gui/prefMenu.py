#!/usr/bin/env python
# $Id$
"""Functions from the Pref menu."""

import globaldata as GD

import os

import gui
import draw
import widgets


def askConfigPreferences(items,prefix=None,store=None):
    """Ask preferences stored in config variables.

    Items in list should only be keys. store is usually a dictionary, but
    can be any class that allow the setdefault method for lookup while
    setting the default, and the store[key]=val syntax for setting the
    value.
    If a prefix is given, actual keys will be 'prefix/key'. 
    The current values are retrieved from the store, and the type returned
    will be in accordance.
    If no store is specified, the global config GD.cfg is used.
    """
    if not store:
        store = GD.cfg
    if prefix:
        items = [ '%s/%s' % (prefix,i) for i in items ]
    itemlist = [ [ i,store.setdefault(i,'') ] for i in items ]
    res,accept = widgets.inputDialog(itemlist,'Config Dialog').process()
    if accept:
        for i,r in zip(itemlist,res):
            GD.debug("IN : %s\nOUT: %s" % (i,r))
            if type(i[1]) == str:
                store[r[0]] = r[1]
            else:
                store[r[0]] = eval(r[1])
    return accept


def setHelp():
    askConfigPreferences(['viewer','help/manual','help/pydocs'])

def setDrawtimeout():
    askConfigPreferences(['draw/wait'])

def setBGcolor():
    col = GD.cfg['draw/bgcolor']
    col = widgets.getColor(col)
    if col:
        GD.cfg['draw/bgcolor'] = col
        draw.bgcolor(col)

def setLinewidth():
    askConfigPreferences(['draw/linewidth'])

def setSize():
    GD.gui.resize(800,600)
    
def setCanvasSize():
    res = draw.askItems([['w',GD.canvas.width()],['h',GD.canvas.height()]])
    GD.canvas.resize(int(res['w']),int(res['h']))
        
    
def setRender():
    if askConfigPreferences(['ambient', 'specular', 'emission', 'shininess'],'render'):
        draw.smooth()

def setLight(light=0):
    keys = [ 'ambient', 'diffuse', 'specular', 'position' ]
    tgt = 'render/light%s'%light
    localcopy = {}
    localcopy.update(GD.cfg[tgt])
    if askConfigPreferences(keys,store=localcopy):
        GD.cfg[tgt] = localcopy
        draw.smooth()

def setLight0():
    setLight(0)

def setLight1():
    setLight(1)

def setLocalAxes():
    GD.cfg['draw/localaxes'] = True 
def setGlobalAxes():
    GD.cfg['draw/localaxes'] = False

def setRotFactor():
    askConfigPreferences(['gui/rotfactor'])
def setPanFactor():
    askConfigPreferences(['gui/panfactor'])
def setZoomFactor():
    askConfigPreferences(['gui/zoomfactor'])



def setFont():
    """Set the main application font from a user dialog widget."""
    font,ok = widgets.selectFont()
    if ok:
        GD.app.setFont(font)


def setFontSize():
    askConfigPreferences(['gui/fontsize'])
    gui.setFontSize()
   

    
# End
