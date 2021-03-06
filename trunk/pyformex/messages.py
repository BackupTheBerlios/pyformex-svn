# $Id$
##
##  This file is part of pyFormex 0.8.5     Sun Nov  6 17:27:05 CET 2011
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Home page: http://pyformex.org
##  Project page:  https://savannah.nongnu.org/projects/pyformex/
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

"""Error and Warning Messages

"""

import pyformex as pf


def getMessage(msg):
    """Return the real message corresponding with the specified mnemonic.

    If no matching message was defined, the original is returned.
    """
    msg = str(msg) # allows for msg being a Warning
    return globals().get(msg,msg)



warn_flat_removed = "The 'flat=True' parameter of the draw function has been replaced with 'nolight=True'."

warn_viewport_linking = "Linking viewports is an experimental feature and is not fully functional yet."

warn_avoid_sleep = """.. warn_avoid_sleep

Avoid sleep function
--------------------
The sleep function may cause a heavy processor load during it wait cycle,
and its use should therefore be avoided. Depending on your intentions,
there are several better alternatives:

- the `Draw Wait Time` preference setting,
- the delay() and wait() functions,
- the pause() function,
"""

warn_old_table_dialog = "The use of OldTableDialog is deprecated. Please use a combination of the Dialog, Tabs and Table widgets."

warn_widgets_updatedialogitems = "gui.widgets.updateDialogItems now expects data in the new InputItem format. Use gui.widgets.updateOldDialogItems for use with old data format."

warn_deprecated_inputitem = "Using a list or tuple as InputItem data is deprecated. Please use the new dict format."

_future_deprecation = "This functionality is deprecated and will probably be removed in future, unless you explain to the developers why they should retain it."

warn_quadratic_drawing = """..

Quadratic surface drawing
-------------------------
We have started implementing quadratic surface drawing.
Currently, quad8 and quad9 elements can be drawn as quadratics in the
smooth or flat rendering style. To activate the quadratic surface drawing,
change the default in Settings->Drawing.

Developers: please test and report.
"""

warn_mesh_reverse = "The meaning of Mesh.reverse has changed. Before, it would just reorder the nodes of the elements in backwards order (just like the Formex.reverse still does. The new definition of Mesh.reverse however is to reverse the line direction for 1D eltypes, to reverse the normals for 2D eltypes and to turn 3D volumes inside out. This definition may have more practical use. It can e.g. be used to fix meshes after a mirroring operation."

warn_mesh_reflect = "The Mesh.reflect will now by default reverse the elements after the reflection, since that is what the user will want in most cases. The extra reversal can be skipped by specifying 'reverse=False' in the argument list of the `reflect` operation."

radio_enabler = "A 'radio' type input item can currently not be used as an enabler for other input fields."
# End
