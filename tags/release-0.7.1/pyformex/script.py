#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.7.1 Release Sat May 24 13:26:21 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""Functions for executing pyFormex scripts."""

import globaldata as GD
import threading,os,commands,copy,re,time

import formex
import utils
    

######################### Exceptions #########################################

class Exit(Exception):
    """Exception raised to exit from a running script."""
    pass    

class ExitAll(Exception):
    """Exception raised to exit pyFormex from a script."""
    pass    

class ExitSeq(Exception):
    """Exception raised to exit from a sequence of scripts."""
    pass    

class TimeOut(Exception):
    """Exception raised to timeout from a dialog widget."""
    pass    


############################# Globals for scripts ############################


def Globals():
    """Return the globals that are passed to the scripts on execution.

    This basically contains the globals defined in draw.py, colors.py,
    and formex.py, as well as the globals from numpy.
    It also contains the definitions put into the globaldata.PF, by
    preference using the export() function.
    During execution of the script, the global variable __name__ will be
    set to either 'draw' or 'script' depending on whether the script
    was executed in the 'draw' module (--gui option) or the 'script'
    module (--nogui option).
    """
    g = copy.copy(GD.PF)
    g.update(globals())
    if GD.gui:
        from gui import colors,draw
        g.update(colors.__dict__)
        g.update(draw.__dict__)
    g.update(formex.__dict__)
    return g


def export(dic):
    """Export the variables in the given dictionary."""
    GD.PF.update(dic)


def export2(names,values):
    """Export a list of names and values."""
    export(dict(zip(names,values)))


def forget(names):
    """Remove the global variables specified in list."""
    g = GD.PF
    for name in names:
        if g.has_key(name):
            del g[name]
        

def rename(oldnames,newnames):
    """Rename the global variables in oldnames to newnames."""
    g = GD.PF
    for oldname,newname in zip(oldnames,newnames):
        if g.has_key(oldname):
            g[newname] = g[oldname]
            del g[oldname]


def listAll(clas=None,dic=None):
    """Return a list of all objects in dic that are of given clas.

    If no class is given, Formex objects are sought.
    If no dict is given, the objects from both GD.PF and locals()
    are returned.
    """
    if dic is None:
        dic = GD.PF

    if clas is None:
        return dic.keys()
    else:
        return [ k for k in dic.keys() if isinstance(dic[k],clas) ]


def named(name):
    """Returns the global object named name."""
    #GD.debug("name %s" % name)
    if GD.PF.has_key(name):
        #GD.debug("Found %s in GD.PF" % name)
        dic = GD.PF
    elif globals().has_key(name):
        GD.debug("Found %s in globals()" % name)
        dic = globals()
    else:
        raise NameError,"Name %s is in neither GD.PF nor globals()" % name
    return dic[name]


#################### Interacting with the user ###############################

def ask(question,choices=None,default=''):
    """Ask a question and present possible answers.

    If no choices are presented, anything will be accepted.
    Else, the question is repeated until one of the choices is selected.
    If a default is given and the value entered is empty, the default is
    substituted.
    Case is not significant, but choices are presented unchanged.
    If no choices are presented, the string typed by the user is returned.
    Else the return value is the lowest matching index of the users answer
    in the choices list. Thus, ask('Do you agree',['Y','n']) will return
    0 on either 'y' or 'Y' and 1 on either 'n' or 'N'.
    """
    if choices:
        question += " (%s) " % ', '.join(choices)
        choices = [ c.lower() for c in choices ]
    while 1:
        res = raw_input(question)
        if res == '' and default:
            res = default
        if not choices:
            return res
        try:
            return choices.index(res.lower())
        except ValueError:
            pass

def ack(question):
    """Show a Yes/No question and return True/False depending on answer."""
    return ask(question,['Y','N']) == 0


def error(message):
    print "pyFormex Error: "+message
    if not ack("Do you want to continue?"):
        exit()
    
def warning(message):
    print "pyFormex Warning: "+message
    if not ack("Do you want to continue?"):
        exit()

def showInfo(message):
    print "pyFormex Info: "+message

##def log(s):
##    """Display a message in the terminal."""
##    print s

# message is the preferred function to send text info to the user.
# The default message handler is set here.
# Best candidates are log/info
message = GD.message

def system(cmdline,result='output'):
    """Run a command and return its output.

    If result == 'status', the exit status of the command is returned.
    If result == 'output', the output of the command is returned.
    If result == 'both', a tuple of status and output is returned.
    """
    if result == 'status':
        return os.system(cmdline)
    elif result == 'output':
        return commands.getoutput(cmdline)
    elif result == 'both':
        return commands.getstatusoutput(cmdline)


########################### PLAYING SCRIPTS ##############################

scriptDisabled = False
scriptRunning = False
exitrequested = False
starttime = 0.0

 
def playScript(scr,name=None,argv=[]):
    """Play a pyformex script scr. scr should be a valid Python text.

    There is a lock to prevent multiple scripts from being executed at the
    same time.
    If a name is specified, sets the global variable GD.scriptName if and
    when the script is started.
    """
    global scriptDisabled,scriptRunning,exitrequested
    GD.debug('SCRIPT MODE %s,%s,%s'% (scriptDisabled,scriptRunning,exitrequested))
    # (We only allow one script executing at a time!)
    # and scripts are non-reentrant
    if scriptRunning or scriptDisabled :
        return
    scriptRunning = True
    exitrequested = False
    
    # Get the globals
    g = Globals()
    if GD.gui:
        modname = 'draw'
    else:
        modname = 'script'
    g.update({'__name__':modname})
    g.update({'argv':argv})

    # Now we can execute the script using these collected globals
    exportNames = []
    GD.scriptName = name
    exitall = False

    starttime = time.clock()
    GD.debug('STARTING SCRIPT (%s)' % starttime)
    try:
        try:
            if GD.gui and stepmode:
                step_script(scr,g,True)
            else:
                exec scr in g
            if GD.cfg['autoglobals']:
                exportNames.extend(listAll(clas=formex.Formex,dic=g))
            GD.PF.update([(k,g[k]) for k in exportNames])
        except Exit:
            pass
        except ExitAll:
            exitall = True
            
    finally:
        scriptRunning = False # release the lock in case of an error
        elapsed = time.clock() - starttime
        GD.debug('SCRIPT RUNTIME : %s seconds' % elapsed)
        if GD.gui:
            stepmode = False
            drawrelease() # release the lock
            GD.gui.actions['Play'].setEnabled(True)
            #GD.gui.actions['Step'].setEnabled(False)
            GD.gui.actions['Continue'].setEnabled(False)
            GD.gui.actions['Stop'].setEnabled(False)

    if exitall:
        GD.debug("Calling exit() from playscript")
        exit()


def breakpt(msg=None):
    """Set a breakpoint where the script can be halted on a signal.

    If an argument is specified, it will be written to the message board.

    The exitrequested signal is usually emitted by pressing a button in the GUI.
    In nongui mode the stopatbreakpt function can be called from another thread.
    """
    global exitrequested
    if exitrequested:
        if msg is not None:
            GD.message(msg)
        exitrequested = False # reset for next time
        raise Exit


def stopatbreakpt():
    """Set the exitrequested flag."""
    global exitrequested
    exitrequested = True


def play(fn,argv=[]):
    """Play a formex script from file fn.

    A list of arguments can be passed. They will be available
    under the name argv.
    """
    message("Running script (%s)" % fn)
    playScript(file(fn,'r'),fn,argv)
    message("Finished script %s" % fn)
    return argv


def exit(all=False):
    if scriptRunning:
        if all:
            raise ExitAll # exit from pyformex
        else:
            raise Exit # exit from script only
    else:
        sys.exit(0) # exit from pyformex

###########################  app  ################################


def runApp(args):
    """Run the application without gui."""
    # remaining args are interpreted as scripts, possibly interspersed
    # with arguments for the scripts.
    # each script should pop the required arguments from the list,
    # and return the remainder
##    GD.message = message

    while len(args) > 0:
        scr = args.pop(0) 
        if os.path.exists(scr) and utils.isPyFormex(scr):
            play(scr,args)
        else:
            raise RuntimeError,"No such pyFormex script found: %s" % scr


########################## print information ################################
    
def formatInfo(F):
    """Return formatted information about a Formex."""
    bb = F.bbox()
    return """shape    = %s
bbox[lo] = %s
bbox[hi] = %s
center   = %s
maxprop  = %s
""" % (F.shape(),bb[0],bb[1],F.center(),F.maxprop())
    

def printall():
    """Print all Formices in globals()"""
    print "Formices currently in globals():\n%s" % listAll(clas=formex.Formex)


def printglobals():
    print globals()

def printglobalnames():
    a = globals().keys()
    a.sort()
    print a

    
def printconfig():
    print "Reference Configuration: " + str(GD.refcfg)
    print "User Configuration: " + str(GD.cfg)
        

def printdetected():
    print "%s (%s)\n" % (GD.Version,GD.__revision__)
    print "Detected Python Modules:"
    for k,v in GD.version.items():
        if v:
            print "%s (%s)" % ( k,v)
    print "\nDetected External Programs:"
    for k,v in GD.external.items():
        if v:
            print "%s (%s)" % ( k,v)

### Utilities

def chdir(fn):
    """Change the current working directory.

    If fn is a directory name, the current directory is set to fn.
    If fn is a file name, the current directory is set to the directory
    holding fn.
    In either case, the current dirctory is stored in GD.cfg['workdir']
    for persistence between pyFormex invocations.
    
    If fn does not exist, nothing is done.
    """
    if os.path.exists:
        if not os.path.isdir(fn):
            fn = os.path.dirname(fn)
        os.chdir(fn)
        GD.cfg['workdir'] = fn
        GD.message("Your current workdir is %s" % os.getcwd())


def workHere():
    """Change the current working directory to the script's location."""
    os.chdir(os.path.dirname(GD.cfg['curfile']))


def runtime():
    """Return the time elapsed since start of execution of the script."""
    return time.clock() - starttime


#### End
