#!/usr/bin/env python pyformex
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

"""tools_menu.py

Graphic Tools plugin menu for pyFormex.
"""

import pyformex as GD

from gui import actors,colors
from formex import *
from gui.draw import *
from plugins import objects
from plugins.tools import *
#from numpy import *


def editFormex(F):
    """Edit a Formex"""
    print "I want to edit a Formex"
    print "%s" % F.__class__


Formex.edit = editFormex



##################### database tools ##########################

database = objects.Objects()
drawable = objects.DrawableObjects()


def printall():
    """Print all global variable names."""
    print listAll()
    

def printval():
    """Print selected global variables."""
    database.ask()
    database.printval()
    

def forget():
    """Forget global variables."""
    database.ask()
    database.forget()

def edit():
    """Edit a global variable."""
    database.ask(mode='single')
    F = database.check(single=True)
    if F and hasattr(F,'edit'):
        name = database[0]
        F.edit(name)

def rename():
    """Rename a global variable."""
    database.ask(mode='single')
    F = database.check(single=True)
    res = askItems([['Name',database.names[0]]],
                            caption = 'Rename variable')
    if res:
        name = res['Name']
        export({name:F})
        database.forget()
        database.set(name)

    
def editByName(name):
    pass


###################### Drawn Objects #############################

            
def draw_object_name(n):
    """Draw the name of an object at its center."""
    return drawText3D(named(n).center(),n)

def draw_elem_numbers(n):
    """Draw the numbers of an object's elements."""
    return drawNumbers(named(n))

def draw_bbox(n):
    """Draw the bbox of an object."""
    return drawBbox(named(n))
   

class DrawnObjects(dict):
    """A dictionary of drawn objects.
    """
    def __init__(self,*args,**kargs):
        dict.__init__(self,*args,**kargs)
        self.autodraw = False
        self.shrink = None
        self.annotations = [[draw_object_name,False],
                            [draw_elem_numbers,False],
                            [draw_bbox,False],
                            ]
        self._annotations = {}
        self._actors = []


    def draw(self,*args,**kargs):
        clear()
        print "SELECTION: %s" % self.names
        self._actors = draw(self.names,clear=False,shrink=self.shrink,*args,**kargs)
        #print self.annotations
        for i,a in enumerate(self.annotations):
            if a[1]:
                self.drawAnnotation(i)


    def ask(self,mode='multi'):
        """Interactively sets the current selection."""
        new = Objects.ask(self,mode)
        if new is not None:
            self.draw()


    def drawChanges(self):
        """Draws old and new version of a Formex with differrent colors.

        old and new can be a either Formex instances or names or lists thereof.
        old are drawn in yellow, new in the current color.
        """
        self.draw(wait=False)
        draw(self.values,color='yellow',bbox=None,clear=False,shrink=self.shrink)
 

    def undoChanges(self):
        """Undo the last changes of the values."""
        Objects.undoChanges(self)
        self.draw()


    def toggleAnnotation(self,i=0,onoff=None):
        """Toggle the display of number On or Off.

        If given, onoff is True or False. 
        If no onoff is given, this works as a toggle. 
        """
        active = self.annotations[i][1]
        #print "WAS"
        #print self.annotations
        if onoff is None:
            active = not active
        elif onoff:
            active = True
        else:
            active = False
        self.annotations[i][1] = active
        #print "BECOMES"
        #print self.annotations
        if active:
            self.drawAnnotation(i)
        else:
            self.removeAnnotation(i)
        #print self._annotations


    def drawAnnotation(self,i=0):
        """Draw some annotation for the current selection."""
        #print "DRAW %s" % i
        self._annotations[i] = [ self.annotations[i][0](n) for n in self.names ]


    def removeAnnotation(self,i=0):
        """Remove the annotation i."""
        #print "REMOVE %s" % i
        map(undraw,self._annotations[i])
        del self._annotations[i]


    def toggleNames(self):
        self.toggleAnnotation(0)
    def toggleNumbers(self):
        self.toggleAnnotation(1)
    def toggleBbox(self):
        self.toggleAnnotation(2)


    def setProperty(self,prop=None):
        """Set the property of the current selection.

        prop should be a single integer value or None.
        If None is given, a value will be asked from the user.
        If a negative value is given, the property is removed.
        If a selected object does not have a setProp method, it is ignored.
        """
        objects = self.check()
        if objects:
            if prop is None:
                res = askItems([['property',0]],
                               caption = 'Set Property Number for Selection (negative value to remove)')
                if res:
                    prop = int(res['property'])
                    if prop < 0:
                        prop = None
            for o in objects:
                if hasattr(o,'setProp'):
                    o.setProp(prop)
            self.draw()

##################### planes ##########################

planes = objects.DrawableObjects(clas=Plane)
pname = utils.NameSequence('Plane-0')

def editPlane(plane,name):
    res = askItems([('Point',list(plane.point())),
                    ('Normal',list(plane.normal())),
                    ('Size',(list(plane.size()[0]),list(plane.size()[1])))],
                   caption = 'Edit Plane')
    if res:
        plane.P = res['Point']
        plane.n = res['Normal']
        plane.s = res['Size']

Plane.edit = editPlane


def createPlaneCoordsPointNormal():
    res = askItems([('Name',pname.next()),
                    ('Point',(0.,0.,0.)),
                    ('Normal',(1.,0.,0.)),
                    ('Size',((1.,1.),(1.,1.)))],
                   caption = 'Create a new Plane')
    if res:
        name = res['Name']
        p = res['Point']
        n = res['Normal']
        s = res['Size']
        P = Plane(p,n,s)
        export({name:P})
        draw(P)

    
def createPlaneCoords3Points():
    res = askItems([('Name',pname.next()),
                    ('Point 1',(0.,0.,0.)),
                    ('Point 2', (0., 1., 0.)),
                    ('Point 3', (0., 0., 1.)),
                    ('Size',((1.,1.),(1.,1.)))],
                   caption = 'Create a new Plane')
    if res:
        name = res['Name']
        p1 = res['Point 1']
        p2 = res['Point 2']
        p3 = res['Point 3']
        s = res['Size']
        pts=[p1, p2, p3]
        P = Plane(pts,size=s)
        export({name:P})
        draw(P)
    

def createPlaneVisual3Points():
    res = askItems([('Name',pname.next()),
                    ('Size',((1.,1.),(1.,1.)))],
                   caption = 'Create a new Plane')
    if res:
        name = res['Name']
        s = res['Size']
        picked = pick('point')
        pts = getCollection(picked)
        pts = asarray(pts).reshape(-1,3)
        if len(pts) == 3:
            P = Plane(pts,size=s)
            export({name:P})
            draw(P)
        else:
            warning("You have to pick exactly three points.")


################# Create Selection ###################

selection = None

def set_selection(obj_type):
    global selection
    selection = pick(obj_type)

def query(mode):
    set_selection(mode)
    print report(selection)

def pick_actors():
    set_selection('actor')
def pick_elements():
    set_selection('element')
def pick_points():
    set_selection('point')
def pick_edges():
    set_selection('edge')
    
def query_actors():
    query('actor')
def query_elements():
    query('element')
def query_points():
    query('point')
def query_edges():
    query('edge')

def query_distances():
    set_selection('point')
    print reportDistances(selection)
                   

def report_selection():
    if selection is None:
        warning("You need to pick something first.")
        return
    print selection
    print report(selection)


def setprop_selection():
    """Set the property of the current selection.

    A property value is asked from the user and all items in the selection
    that have property have their value set to it.
    """
    if selection is None:
        warning("You need to pick something first.")
        return
    print selection
    res = askItems([['property',0]],
                   caption = 'Set Property Number for Selection (negative value to remove)')
    if res:
        prop = int(res['property'])
        if prop < 0:
            prop = None
        setpropCollection(selection,prop)


def grow_selection():
    if selection is None:
        warning("You need to pick something first.")
        return
    print selection
    res = askItems([('mode','node','radio',['node','edge']),
                    ('nsteps',1),
                    ],
                   caption = 'Grow method',
                   )
    if res:
        growCollection(selection,**res)
    print selection
    highlightElements(selection)


def partition_selection():
    """Partition the current selection and show the result."""
    if selection is None:
        warning("You need to pick something first.")
        return
    if not selection.obj_type in ['actor','element']:
        warning("You need to pick actors or elements.")
        return
    for A in GD.canvas.actors:
        if not A.atype() == 'TriSurface':
            warning("Currently I can only partition TriSurfaces." )
            return
    partitionCollection(selection)
    highlightPartitions(selection)
    

def get_partition():
    """Select some partitions from the current selection and show the result."""
    if selection is None:
        warning("You need to pick something first.")
        return
    if not selection.obj_type in ['partition']:
        warning("You need to partition the selection first.")
        return
    res = askItems([['property',[1]]],
                 caption='Partition property')
    if res:
        prop = res['property']
        getPartition(selection,prop)
        highlightPartitions(selection)
    

def export_selection():
    if selection is None:
        warning("You need to pick something first.")
        return
    sel = getCollection(selection)
    if len(sel) == 0:
        warning("Nothing to export!")
        return
    options = ['list','single item']
    default = options[0]
    if len(sel) == 1:
        default = options[1]
    res = askItems([('Export with name',''),
                    ('Export as',default,'radio',options),
                    ])
    if res:
        name = res['Export with name']
        if res['Export as'] == options[0]:
            export({name:sel})
        elif res['Export as'] == options[1]:
            export(dict([ (name+"-%s"%i,v) for i,v in enumerate(sel)]))


################### menu #################

def create_menu():
    """Create the Tools menu."""
    MenuData = [
        ("&Draw Variables",drawable.ask),
        ("&Show Variables",printall),
        ("&Print Variables",printval),
        ("&Edit Variable",edit),
        ("&Rename Variable",rename),
        ("&Forget Variables",forget),
        ("---",None),
        ("&Create Plane",
            [("Coordinates", 
                [("Point and normal", createPlaneCoordsPointNormal),
                ("Three points", createPlaneCoords3Points),
                ]), 
            ("Visually", 
                [("Three points", createPlaneVisual3Points),
                ]),
            ]),
        ("&Select Plane",planes.ask),
        ("&Draw Selection",planes.draw),
        ("&Forget Selection",planes.forget),
        ("---",None),
        ("&Pick Actors",pick_actors),
        ("&Pick Elements",pick_elements),
        ("&Pick Points",pick_points),
        ("&Pick Edges",pick_edges),
        ("---",None),
        ('&Selection',
         [('&Create Report',report_selection),
          ('&Set Property',setprop_selection),
          ('&Grow',grow_selection),
          ('&Partition',partition_selection),
          ('&Get Partition',get_partition),
          ('&Export',export_selection),
          ]),
        ("---",None),
        ('&Query',
         [('&Actors',query_actors),
          ('&Elements',query_elements),
          ('&Points',query_points),
          ('&Edges',query_edges),
          ('&Distances',query_distances),
          ]),
        ("---",None),
        ("&Close",close_menu),
        ]
    return widgets.Menu('Tools',items=MenuData,parent=GD.gui.menu,before='help')

    
def show_menu():
    """Show the Tools menu."""
    if not GD.gui.menu.item('Tools'):
        create_menu()


def close_menu():
    """Close the Tools menu."""
    m = GD.gui.menu.item('Tools')
    if m :
        m.remove()
    

if __name__ == "draw":
    # If executed as a pyformex script
    close_menu()
    show_menu()
    
elif __name__ == "__main__":
    print __doc__


# End
