#!/usr/bin/env python
# $Id$
"""Functions from the File menu."""

import os
import globaldata as GD
import widgets
import gui
import draw
import utils


def newFile():
    return openFile(False)


def openFile(exist=True):
    """Open a file selection dialog and set the selection as the current file.

    The default only accepts existing files. Use newFile() to accept new files.
    """
    cur = GD.cfg.get('curfile',GD.cfg.get('workdir','.'))
    print cur,os.path.dirname(cur)
    fs = widgets.FileSelection(cur,"pyformex scripts (*.frm *.py)",exist=exist)
    fn = fs.getFilename()
    if fn:
        GD.cfg['workdir'] = os.path.dirname(fn)
        GD.gui.setcurfile(fn)

        
def edit():
    """Load the current file in the editor.

    This only works if the editor was set in the configuration.
    The author uses 'gnuclient' to load the files in a running copy
    of xemacs.
    """
    if GD.cfg['editor']:
        pid = utils.spawn(GD.cfg['editor'] % GD.cfg['curfile'])


play = draw.play
    
def saveImage():
    """Save the current rendering in image format.

    This function will open a file selection dialog, and if a valid
    file is returned, the current OpenGL rendering will be saved to it.
    """
    global canvas
    print "Saving image"
    print GD.cfg
    print GD.cfg['workdir']
    indir = GD.cfg['workdir']
    fs = widgets.FileSelection(indir,pattern="Images (*.png *.jpg *.eps)")
    fn = fs.getFilename()
    if fn:
        GD.cfg['workdir'] = os.path.dirname(fn)
        draw.saveImage(fn,verbose=True)

def multiSave():
    """Save a sequence of images.

    If the filename supplied has a trailing numeric part, subsequent images
    will be numbered continuing from this number. Otherwise a numeric part
    -000, -001, will be added to the filename.
    """
    if draw.multisave:
        fn = None
    else:
        dir = GD.cfg['workdir']
        fs = widgets.FileSelection(dir,pattern="Images (*.png *.jpg)")
        fn = fs.getFilename()
    draw.saveMulti(fn,verbose=True)

def autoSave():
    """Automatically save an image on each draw operation.
    """
    if draw.autosave:
        fn = None
    else:
        dir = GD.cfg['workdir']
        fs = widgets.FileSelection(dir,pattern="Images (*.png *.jpg)")
        fn = fs.getFilename()
    draw.saveAuto(fn,verbose=True)

