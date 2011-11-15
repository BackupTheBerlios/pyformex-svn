.. $Id$  -*- rst -*-
  
..
  This file is part of the pyFormex project.
  pyFormex is a tool for generating, manipulating and transforming 3D
  geometrical models by sequences of mathematical operations.
  Home page: http://pyformex.org
  Project page:  https://savannah.nongnu.org/projects/pyformex/
  Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be)
  Distributed under the GNU General Public License version 3 or later.
  
  
  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.
  
  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.
  
  You should have received a copy of the GNU General Public License
  along with this program.  If not, see http://www.gnu.org/licenses/.
  
  

.. include:: <isonum.txt>
.. include:: defines.inc
.. include:: links.inc

.. _`development`: http://savannah.nongnu.org/projects/pyformex/

About
=====
pyFormex is a program for generating, transforming and manipulating large
geometrical models of 3D structures by sequences of mathematical 
operations. Thanks to a powerful (Python based) scripting language,
pyFormex is very well suited for the automated design of spatial frame
structures. It provides a wide range of operations on surface meshes, 
like STL type triangulated surfaces. There are provisions to import medical 
scan images. pyFormex can also be used as a pre- and post-processor for 
Finite Element analysis programs. Finally, it might be used just for 
creating some nice graphics.

Using pyFormex, the topology of the elements and the final geometrical form
can be decoupled. Often, topology is created first and then mapped onto the
geometry. Through the scripting language, the user can define any sequence
of transformations, built from provided or user defined functions. 
This way, building parametric models becomes a natural thing.

While pyFormex is still under `development`_, it already provides a
fairly stable scripting language and an OpenGL GUI environment for
displaying and manipulating the generated structures.

  
`News`_
=======

.. include:: news.inc


Overview
========

.. The following fixes problems with generating the PDF docs
.. tabularcolumns:: |p{5cm}|p{5cm}|

+-------------------------------------+------------------------------------+
|  `Gallery <gallery.html>`_          |  Documentation                     |
|                                     |                                    |
|  Everyone at times needs help with  |  :doc:`contents`                   |
|  something. Our                     |                                    |
|  `support page <support.html>`_     |                                    |
|  presents different ways to         |                                    |
|  get help with installing and/or    |                                    |
|  using pyFormex.                    |                                    |
+-------------------------------------+------------------------------------+


.. toctree::
   :hidden:
 
   contents


`Gallery <gallery.html>`_
=========================
You are interested in pyFormex and want to know more about it? You
wonder how pyFormex works or what it can do for you? 
Well, to wet your appetite we have collected a
`gallery <gallery.html>`_ with screenshots, posters, videos, examples, of
pyFormex in use.


`Documentation`_
================
Our comprehensive `Documentation`_ collection is the ultimate source
of information about pyFormex. Some of the popular documents are: 
`Installing pyFormex`_, `pyFormex tutorial`_ and `pyFormex reference manual`_.

License 
======= 
This program is free software; you can redistribute it
and/or modify it under the terms of the `GNU General Public License`_
as published by the Free Software Foundation; either version 3 of the
License, or (at your option) any later version.

`Support <support.html>`_
=========================
Everyone at times needs help with something. Our `support page
<support.html>`_ presents different ways to get help with installing and/or using pyFormex. 

.. toctree::
   :hidden:
   :maxdepth: 1
 
   support

`Project page`_
===============
The development of pyFormex can be followed on the `Project page`_ at `Savannah`_.


`Links <links.html>`_
=====================
A collection of `links <links.html>`_ to some of our partners, to providers of
software components used in building and maintaining pyFormex,
to supporters and users of pyFormex, and to projects we sympatize
with.

.. toctree::
   :hidden:

   links
 
.. End
