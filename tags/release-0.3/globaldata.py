#!/usr/bin/env python
# $Id$
"""Global data for pyFormex."""
Version = "pyFormex 0.3"

import config

cfg = config.Config()
gui = None
canvas = None
help = None
PyFormex = {}  # globals that will be offered to scripts
image_formats_qt = []
image_formats_gl2ps = []
prefsChanged = False
multisave = False
canPlay = False
scriptName = None

def debug(s):
    if options.debug:
        print s
