#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.7.1 Release Fri May  9 08:39:30 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
#
"""Numerical data reader"""

__all__ = ['splitFloat','readData']

import re

Float = re.compile('[-+]?(\d+(\.\d*)?|\d*\.\d+)([eE]\d+)?')
FloatString = re.compile('(?P<float>[-+]?(\d+(\.\d*)?|\d*\.\d+)([eE]\d+)?)(?P<string>.*)')
        

def splitFloat(s):
    """Match a floating point number at the beginning of a string

    If the beginning of the string matches a floating point number,
    a list is returned with the float and the remainder of the string;
    if not, None is returned.
    Example: splitFloat('123e4rt345e6') returns [1230000.0, 'rt345e6']
    """
    m = FloatString.match(s)
    if m:
        return [float(m.group('float')), m.group('string')]
    return None


def readData(s,type,strict=False):
    """Read data from a line matching the 'type' specification.

    This is a powerful function for reading, interpreting and converting
    numerical data from a string. Fields in the string s are separated by
    commas. The 'type' argument is a list where each element specifies how
    the corresponding field should be interpreted. Available values are
    'int', 'float' or some unit ('kg', 'm', etc.).
    If the type field is 'int' or 'float', the data field is converted to
    the matching type.
    If the type field is a unit, the data field should be a number and a
    unit separated by space or not, or just a number. If it is just a number,
    its value is returned unchanged (as float). If the data contains a unit,
    the number is converted to the requested unit. It is an error if the
    datafield holds a non-conformable unit.
    The function returns a list of ints and/or floats (without the units).
    If the number of data fields is not equal to the number of type specifiers,
    the returned list will correspond to the shortest of both and the surplus
    data or types are ignored, UNLESS the strict flag has been set, in which
    case a RuntimError is raised.
    Example:
      readData('12, 13, 14.5e3, 12 inch, 1hr, 31kg ', ['int','float','kg','cm','s'])
    returns
     [12, 13.0, 14500.0, 30.48, 3600.0]
    Prerequisites:
    You need to have GNU 'units' installed for the unit conversion to work. 
    """
    import units,string
    out = []
    data = string.split(s,',')
    if strict and len(data) != len(type):
        raise RuntimeError, "Data do not match type specifier %s\nData: '%s'" % (type,s)
    for t,d in zip(type,data):
        #print t,d
        if len(d) == 0:
            break
        v = string.strip(d)
        if t == 'int':
            val = int(v)
        elif t == 'float':
            val = float(v)
        else:
            m = Float.match(v)
            #print m.start(),m.end(),len(v)
            if m and m.end() == len(v):
                val = float(v)
            else:
                val = float(units.ConvertUnits(v,t))
        out.append(val)
    return out


if __name__ == "__main__":
    print readData('12, 13, 14.5e3, 12 inch, 1hr, 5MPa', ['int','float','kg','cm','s'])
