# Makefile for pyformex
##
## This file is part of pyformex 0.1 Release Fri Mar 12 15:34:55 2004
## pyformex is a Finite Element program written in Python
## (c) 1997,2003 Benedict Verhegghe (email: benedict.verhegghe@ugent.be)
## Distributed under the General Public License, see file COPYING for details
##
#

############# SET THESE TO SUIT YOUR INSTALLATION ####################

# root of the installation tree: this is a reasonable default
ROOTDIR= /usr/local
# where to install pyformex: some prefer to use $(ROOTDIR) 
LIBDIR= $(ROOTDIR)/lib
# where to create symbolic links to the executable files
BINDIR= $(ROOTDIR)/bin
# where to install the documentation
DOCDIR= $(ROOTDIR)/share/doc
# where to install problem types for GiD: check that this is correct!
# comment this line if you do not want to install problem types

############# NOTHING CONFIGURABLE BELOW THIS LINE ###################

VERSION= 0.1
PYFORMEXDIR= pyformex-$(VERSION)
INSTDIR= $(LIBDIR)/$(PYFORMEXDIR)
DOCINSTDIR= $(DOCDIR)/$(PYFORMEXDIR)
PROGRAM= pyformex.py
SOURCE= formex.py canvas.py camera.py colors.py vector.py
DOCFILES= README COPYING History
EXAMPLES= 
STAMPABLE= README History Makefile
NONSTAMPABLE= COPYING
STAMP= ./Stamp 

.PHONY: install dist distclean

all:
	echo  "Do `make install' to install this program"


############ User installation ######################

install:
	install -d $(INSTDIR) $(BINDIR) $(DOCINSTDIR) $(DOCINSTDIR)/examples
	install -m 0664 $(SOURCE) $(INSTDIR)
	install -m 0775 $(PROGRAM) $(INSTDIR)
	install -m 0664 ${DOCFILES} $(DOCINSTDIR)
	install -m 0664 examples/* $(DOCINSTDIR)/examples
	ln -sfn $(INSTDIR)/$(PROGRAM) $(BINDIR)/$(PROGRAM)

remove:
	echo "There is no automatic installation procedure."""
	echo "Remove the entire pyformex directory from where you installed it."
	echo "Remove the symbolic link to the pyformex program."""
	echo "Remove the pyformex doc files."""

############ Creating Distribution ##################

dist:	dist.stamped

dist.stamped:
	make distclean
	mkdir $(PYFORMEXDIR) $(PYFORMEXDIR)/examples
	$(STAMP) -tStamp.template -oStamp.stamp
	$(STAMP) -tStamp.stamp -d$(PYFORMEXDIR) $(PROGRAM) $(SOURCE)
	$(STAMP) -tStamp.stamp -d$(PYFORMEXDIR)/examples $(EXAMPLES)
	$(STAMP) -tStamp.stamp -d$(PYFORMEXDIR) $(STAMPABLE)
	cp $(NONSTAMPABLE) $(PYFORMEXDIR)
	tar czf $(PYFORMEXDIR).tar.gz $(PYFORMEXDIR)
 

distclean:
	rm -rf $(PYFORMEXDIR)

