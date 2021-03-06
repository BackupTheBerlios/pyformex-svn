#!/usr/bin/env python
# $Id$
##
## This file is part of pyFormex 0.7 Release Fri Apr  4 18:41:11 2008
## pyFormex is a Python implementation of Formex algebra
## Website: http://pyformex.berlios.de/
## Copyright (C) Benedict Verhegghe (benedict.verhegghe@ugent.be) 
##
## This program is distributed under the GNU General Public License
## version 2 or later (see file COPYING for details)
##
"""Functions for executing pyFormex scripts."""

import globaldata as GD
import threading,os,commands,copy,re

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
    g = copy.copy(GD.PF)
    g.update(globals())
    g.update(formex.__dict__) 
    g.update({'__name__':'script'})
    return g


def export(dic):
    GD.PF.update(dic)


def export2(names,values=None):
    if values is None:
        values = [ Globals().get(n,None) for n in names ]
    export(dict(zip(names,values)))


def forget(names):
    g = GD.PF
    for name in names:
        if g.has_key(name):
            del g[name]
        

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
 
def playScript(scr,name=None,argv=[]):
    """Play a pyformex script scr. scr should be a valid Python text.

    There is a lock to prevent multiple scripts from being executed at the
    same time.
    If a name is specified, sets the global variable GD.scriptName if and
    when the script is started.
    """
    global scriptRunning, scriptDisabled, allowwait
    # (We only allow one script executing at a time!)
    # and scripts are non-reentrant
    if scriptRunning or scriptDisabled :
        return
    scriptRunning = True
    allowwait = True
    if GD.canvas:
        GD.canvas.update()
    if GD.gui:
        GD.gui.actions['Step'].setEnabled(True)
        GD.gui.actions['Continue'].setEnabled(True)
        GD.app.processEvents()
    # We need to pass formex globals to the script
    # This would be done automatically if we put this function
    # in the formex.py file. But then we need to pass other globals
    # from this file (like draw,...)
    # We might create a module with all operations accepted in
    # scripts.

    # Our solution is to take a copy of the globals in this module,
    # and add the globals from the 'colors' and 'formex' modules
    # !! Taking a copy is needed to avoid changing this module's globals !!
    g = copy.copy(globals())
    if GD.gui:
        g.update(colors.__dict__)
    g.update(formex.__dict__) # this also imports everything from numpy
    # Finally, we set the name to 'script' or 'draw', so that the user can
    # verify that the script is the main script being excuted (and not merely
    # an import) and also whether the script is executed under the GUI or not.
    if GD.gui:
        modname = 'draw'
    else:
        modname = 'script'
    g.update({'__name__':modname})
    g.update({'argv':argv})
    # Now we can execute the script using these collected globals

    GD.scriptName = name
    exitall = False
    try:
        try:
            exec scr in g
        except Exit:
            pass
        except ExitAll:
            exitall = True
    finally:
        scriptRunning = False # release the lock in case of an error
        if GD.gui:
            GD.gui.actions['Step'].setEnabled(False)
            GD.gui.actions['Continue'].setEnabled(False)
    if exitall:
        exit()

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
