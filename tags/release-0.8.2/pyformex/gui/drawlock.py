## $Id$
##
##  This file is part of pyFormex 0.8.2 Release Sat Jun  5 10:49:53 2010
##  pyFormex is a tool for generating, manipulating and transforming 3D
##  geometrical models by sequences of mathematical operations.
##  Homepage: http://pyformex.org   (http://pyformex.berlios.de)
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
"""A locking mechanism for the4 drawing functions."""

import pyformex as GD

import threading


class DrawLock(object):
    """A timed lock to slow down drawing processes"""

    def __init__(self):
        self.allowed = True
        self.locked = False
        self.timer = None


    def wait(self):
        """Wait for the drawing lock to be released.
        
        This method can be called to wait until the lock is released,
        while still processing GUI events.
        """
        if self.allowed:
            while self.locked:
                GD.canvas.update()
                GD.app.processEvents()


    def lock(self,time=None):
        """Lock the drawing function for the next time seconds.

        If a no time is specified, a global value is used.
        """
        #print self.allowed,self.locked
        if self.allowed and not self.locked:
            if time is None:
                time = GD.GUI.drawwait
            if time > 0:
                GD.debug('STARTING TIMER')
                self.locked = True
                self.timer = threading.Timer(time,self.release)
                self.timer.start()


    # ?? SHOULD block and release only be activated if self.allowed ??
    def block(self):
        """Lock the drawing function indefinitely."""
        if self.timer:
            self.timer.cancel()
        self.locked = True


    def release(self):
        """Release the lock on the drawing function.

        If a timer is running, cancel it.
        """
        #print "RELEASING LOCK"
        self.locked = False
        if self.timer:
            self.timer.cancel()


    def free(self):
        """Release the lock and prevent waits until allow() is called."""
        self.allowed = False
        self.release()


    def allow(self):
        """Allow draw waits.

        This is called after a free() to reinstall the draw locking.
        """
        self.allowed = True


def repeat(func,duration=-1,maxcount=-1,*args,**kargs):
    """Repeatedly execute a function.

    func(*args,**kargs) is repeatedly executed until one of the following
    conditions is met:
    - the function returns a value that evaluates to False
    - duration >= 0 and duration seconds have elapsed
    - maxcount >=0 and maxcount executions have been reached
    The default will indefinitely execute the function until it returns False.
    This may cause the system to freeze if it never does so!
    """
    GD.debug("REPEAT: %s, %s" % (duration,maxcount))
    global _repeat_timed_out
    _repeat_timed_out = False
    _repeat_count_reached = False
    
    def timeOut():
        global _repeat_timed_out
        _repeat_timed_out = True
        
    if duration >= 0:
        timer = threading.Timer(duration,timeOut)
        timer.start()
    
    count = 0

    while True:
        GD.app.processEvents()
        res = func(*args,**kargs)
        _exit_requested = not(res)
        count += 1
        if maxcount >= 0:
             _repeat_count_reached = count >= maxcount
        if _exit_requested or _repeat_timed_out or _repeat_count_reached:
            GD.debug("Count: %s, TimeOut: %s" % (count,_repeat_timed_out))
            break
            

#### End
