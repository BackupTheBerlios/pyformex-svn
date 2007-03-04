#!/usr/bin/env pyformex
# $Id$

"""Formex.py

Executing this script creates a Formex menu in the menubar.
"""

import globaldata as GD
from gui.draw import *

#from PyQt4 import QtCore,QtGui
#from gui import widgets
import commands, os


selection = None


def drawChanges(F,oldF):
    clear()
    draw(oldF,color='yellow',wait=False)
    draw(F)

        
def get_selection(mode=None):
    """Show the list of formices (and return a selection)"""
    return widgets.Selection(listAll(),'Known Formices',mode,sort=True,\
                             selected=selection).getResult()

##def formex_list():
##    """Show a list of known formices."""
##    message(get_selection())
    
def make_selection():
    global selection
    selection = get_selection('multi')


def draw_selection():
    global selection
    if selection:
        draw(selection)


def translate_selection():
    """Translate the selected Formices."""
    global selection
    itemlist = [ [ 'direction',0], ['distance','1.0'] ] 
    res,accept = widgets.inputDialog(itemlist,'Translation Parameters').getResult()
    if accept:
        dir = int(res[0][1])
        dist = float(res[1][1])
        oldF = map(named,selection)
        F = [ Fi.translate(dir,dist) for Fi in oldF ]
        drawChanges(F,oldF)
        if ack("Keep the changes?"):
            Export(zip(selection,F))
            clear()
            draw(selection)

def center_selection():
    """Center the selection."""
    global selection
    for F in map(named,selection):
        oldF = F
        F = F.translate(F.center())
        drawChanges(F,oldF)


def rotate_selection():
    """Rotate the selection."""
    global selection
    itemlist = [ [ 'axis',0], ['angle','0.0'] ] 
    res,accept = widgets.inputDialog(itemlist,'Rotation Parameters').process()
    if accept:
        axis = int(res[0][1])
        angle = float(res[1][1])
        for F in byName(selection):
            oldF = F
            F = F.rotate(angle,axis)
            drawChanges(F,oldF)

        
def clip_selection():
    """Clip the stl model."""
    global F
    itemlist = [['axis',0],['begin',0.0],['end',1.0]]
    res,accept = widgets.inputDialog(itemlist,'Clipping Parameters').process()
    if accept:
        Flist = byName(selection)
        bb = bbox(Flist)
        axis = int(res[0][1])
        xmi = bb[0][axis]
        xma = bb[1][axis]
        dx = xma-xmi
        xc1 = xmi + float(res[1][1]) * dx
        xc2 = xmi + float(res[2][1]) * dx
        for F in Flist:
            w = F.test(dir=axis,min=xc1,max=xc2)
            oldF = F.cclip(w)
            F = F.clip(w)
            drawChanges(F,oldF)



################### menu #################

_menu = None

def create_menu():
    """Create the Formex menu."""
    print "formex_menu.create_menu"
    menu = widgets.Menu('Formex')
    MenuData = [
#        ("&List Formices",formex_list),
        ("&Select",make_selection),
        ("&Draw Selection",draw_selection),
        ("&Translate Selection",translate_selection),
        ("&Center Selection",center_selection),
        ("&Rotate Selection",rotate_selection),
        ("&Clip Selection",clip_selection),
        ("&Close",close_menu),
        ]
    menu.addItems(MenuData)
    return menu

def close_menu():
    """Close the Formex menu."""
    global _menu
    if _menu:
        _menu.close()
    _menu = None
    
def show_menu():
    """Show the Formex menu."""
    global _menu
    print _menu
    if not _menu:
        print "Adding the formex menu"
        _menu = create_menu()
    

if __name__ == "main":
    print __doc__

# End

