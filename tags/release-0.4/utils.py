#!/usr/bin/env python
# $Id$
"""A collection of misc. utility functions."""

import globaldata as GD
import os


def spawn(cmd):
    """Spawn a child process."""
    cmd = cmd.split()
    pid = os.spawnvp(os.P_NOWAIT,cmd[0],cmd)
    GD.debug("Spawned child process %s for command '%s'" % (pid,cmd))
    return pid

      
def isPyFormex(filename):
    """Checks whether a file is a pyFormex script.

    A script is considered to be a pyFormex script if its first line
    starts with '#!' and contains the substring 'pyformex'
    A file is considered to be a pyFormex script if its name ends in '.py'
    and the first line of the file contains the substring 'pyformex'.
    Typically, a pyFormex script starts with a line:
      #!/usr/bin/env pyformex
    """
    ok = filename.endswith(".py")
    if ok:
        try:
            f = file(filename,'r')
            ok = f.readline().strip().find('pyformex') >= 0
            f.close()
        except IOError:
            ok = False
    return ok


def imageFormatFromExt(ext):
    """Determine the image format from an extension.

    The extension may or may not have an initial dot and may be in upper or
    lower case. The format is equal to the extension characters in lower case.
    If the supplied extension is empty, the default format 'png' is returned.
    """
    if len(ext) > 0:
        if ext[0] == '.':
            ext = ext[1:]
        fmt = ext.lower()
    else:
        fmt = 'png'
    return fmt


def splitEndDigits(s):
    """Split a string in any prefix and a numerical end sequence.

    A string like 'abc-0123' will be split in 'abc-' and '0123'.
    Any of both can be empty.
    """
    i = len(s)
    if i == 0:
        return ( '', '' )
    i -= 1
    while s[i].isdigit() and i > 0:
        i -= 1
    if not s[i].isdigit():
        i += 1
    return ( s[:i], s[i:] )


def stuur(x,xval,yval,exp=2.5):
    """Returns a (non)linear response on the input x.

    xval and yval should be lists of 3 values:
      [xmin,x0,xmax], [ymin,y0,ymax].
    Together with the exponent exp, they define the response curve
    as function of x. With an exponent > 0, the variation will be
    slow in the neighbourhood of (x0,y0).
    For values x < xmin or x > xmax, the limit value ymin or ymax
    is returned.
    """
    xmin,x0,xmax = xval
    ymin,y0,ymax = yval 
    if x < xmin:
        return ymin
    elif x < x0:
        xr = float(x-x0) / (xmin-x0)
        return y0 + (ymin-y0) * xr**exp
    elif x < xmax:
        xr = float(x-x0) / (xmax-x0)
        return y0 + (ymax-y0) * xr**exp
    else:
        return ymax


def interrogate(item):
    """Print useful information about item."""
    if hasattr(item, '__name__'):
        print "NAME:    ", item.__name__
    if hasattr(item, '__class__'):
        print "CLASS:   ", item.__class__.__name__
    print "ID:      ", id(item)
    print "TYPE:    ", type(item)
    print "VALUE:   ", repr(item)
    print "CALLABLE:",
    if callable(item):
        print "Yes"
    else:
        print "No"
    if hasattr(item, '__doc__'):
        doc = getattr(item, '__doc__')
        doc = doc.strip()   # Remove leading/trailing whitespace.
        firstline = doc.split('\n')[0]
        print "DOC:     ", firstline


def deprecated(old,new):
    print "Function %s is deprecated: use %s instead" % (old,new)


def formatDict(dic):
    """Format a dict in Python source representation.

    Each (key,value) pair is formatted on a line : key = value.
    """
    s = ""
    if isinstance(dic,dict):
        for k,v in dic.iteritems():
            if type(v) == str:
                s += '%s = "%s"\n' % (k,v)
            else:
                s += '%s = %s\n' % (k,v)
    return s

