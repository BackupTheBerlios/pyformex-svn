# Makefile for the pyFormex manual
#

PYTHONDIR=/usr/lib/python2.4
MKHOWTO=${PYTHONDIR}/doc/tools/mkhowto
TEXINPUTS=${PYTHONDIR}/doc/texinputs
TGT=manual
SRC=${TGT}.tex pyformex.help 
HTMLDIR=html
FAVICON=../favicon.ico
OPTIONS= --up-title "pyFormex Home Page" --up-link "http://pyformex.berlios.de" --image-type png --favicon ${FAVICON} 
TESTOPTIONS= --l2h-init=fix.perl --keep
TESTOPTIONS= --keep

# Default target
.PHONY all: ps pdf html

.PHONY ps: ${TGT}.ps

.PHONY pdf: ${TGT}.pdf

.PHONY html: html/${TGT}.html

pyformex.help: ../pyformex/pyformex
	../pyformex/pyformex --help > $@

${TGT}.ps: ${SRC}
	${MKHOWTO} --a4 --ps $<

${TGT}.pdf: ${SRC}
	${MKHOWTO} --a4 --pdf --keep $<

html/${TGT}.html: ${SRC}
	${MKHOWTO} --html --dir ${HTMLDIR}  ${TESTOPTIONS} $(OPTIONS)  $<
