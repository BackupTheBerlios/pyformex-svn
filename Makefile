# Makefile for calpy
##
## This file is part of calpy 0.1 Release Fri Mar 12 15:34:55 2004
## calpy is a Finite Element program written in Python
## (c) 1997,2003 Benedict Verhegghe (email: benedict.verhegghe@ugent.be)
## Distributed under the General Public License, see file COPYING for details
##
#

############# SET THESE TO SUIT YOUR INSTALLATION ####################

# root of the installation tree: this is a reasonable default
ROOTDIR= /usr/local
# where to install calpy files: some prefer to use $(ROOTDIR) 
LIBDIR= $(ROOTDIR)/lib
# where to install the executable files
BINDIR= $(ROOTDIR)/bin
# where to install the documentation
DOCDIR= $(ROOTDIR)/share/doc
# where to install problem types for GiD: check that this is correct!
# comment this line if you do not want to install problem types
GIDPROBLEMDIR=$(LIBDIR)/Gid7.2/problemtypes

############# NOTHING CONFIGURABLE BELOW THIS LINE ###################

VERSION= 0.1.2
CALPYDIR= calpy-$(VERSION)
INSTDIR= $(LIBDIR)/$(CALPYDIR)
DOCINSTDIR= $(DOCDIR)/$(CALPYDIR)
PROGRAM= cal.py
SOURCE= calpy.py femodel.py gauss.py plane.py flavia.py
FORTRAN= assemb.f quad.f solve.f
MODULES= assemb.so quad.so solve.so
DOCFILES= README COPYING History
EXAMPLES= vb7.dat vb8.dat Materials.txt
PROBLEMTYPES= elast2d
STAMPABLE= .bat .tcl
NONSTAMPABLE= .bas .prb .cnd .sim .uni
STAMP= ./Stamp 

%.so: %.f
	f2py -c --fcompiler=Gnu -m $* $< | tee $*.tmp
	gawk 'BEGIN{out=0}/Building module /{out=1;next}/Wrote C.API module/{out=0}{if (out) print}' $*.tmp >$*.itf
	rm $*.tmp

.PHONY: install dist distclean calpy

calpy: $(MODULES)

install:
	install -d $(INSTDIR) $(BINDIR) $(DOCINSTDIR) $(DOCINSTDIR)/examples
	install -m 0664 $(SOURCE) $(MODULES) $(INSTDIR)
	install -m 0775 $(PROGRAM) $(INSTDIR)
	for d in gid/*; do install -d $(INSTDIR)/gid/$d; done
	install -m 0664 ${DOCFILES} $(DOCINSTDIR)
	install -m 0664 examples/* $(DOCINSTDIR)/examples
	ln -sfn $(INSTDIR)/$(PROGRAM) $(BINDIR)/$(PROGRAM)
	if [ "$(GIDPROBLEMDIR)" != "" ]; then ln -sfn $(INSTDIR)/gid $(GIDPROBLEMDIR)/calpy; fi

dist:	dist.stamped

# stamp file from GiD problemtype $(1) with extension $(2) to $(CALPYDIR)
GIDstamp= echo $(STAMP) -tStamp.stamp -d$(CALPYDIR)/gid/$(1).gid gid/$(1).gid/$(1)$(2)
# copy file from GiD problemtype $(1) with extension $(2) to $(CALPYDIR)
GIDcopy= cp gid/$(1).gid/$(1)$(2) $(CALPYDIR)/gid/$(1).gid
# copy the problemtype $(1) to the distribution dir $(CALPYDIR)
# thereby stamping all stampable files
define Pstamp
mkdir $(CALPYDIR)/gid/$(1).gid; 
@for f in $(STAMPABLE); do $(call GIDstamp,$(1),$$f); done
@for f in $(NONSTAMPABLE); do $(call GIDcopy,$(1),$$f); done
endef

dist.stamped:
	make distclean
	mkdir $(CALPYDIR) $(CALPYDIR)/examples $(CALPYDIR)/gid
	$(STAMP) -tStamp.template -oStamp.stamp
	$(STAMP) -tStamp.stamp -d$(CALPYDIR) $(PROGRAM) $(SOURCE)
	cp $(MODULES) $(CALPYDIR)
	$(STAMP) -tStamp.stamp -d$(CALPYDIR)/examples $(EXAMPLES)
	$(foreach p,$(PROBLEMTYPES),$(call Pstamp,$(p)))
	$(STAMP) -tStamp.stamp -d$(CALPYDIR) README Makefile
	cp COPYING $(CALPYDIR)
	tar czf $(CALPYDIR).tar.gz $(CALPYDIR)
 

distclean:
	rm -rf $(CALPYDIR)

# uiteindelijk toevoegen:
# cp calpy.stamp dist.stamped
#
