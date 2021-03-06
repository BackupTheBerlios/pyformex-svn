#!/usr/bin/env python
# $Id $

import globaldata as GD
from gui import *
from utils import *
import draw

from widgets import *

import sys,time,os.path,string
import qt
import qtgl

def askPreferences(list):
    items = [ [ it,GD.config.setdefault(it,"") ] for it in list ]
    #items = [ [ it,val,type(val) ] for it,val in items ]
    print "Asking Prefs ",items
    res = ConfigDialog(items).process()
    for r in res:
        GD.config[r[0]] = r[1]
    print GD.config

def prefDrawtimeout():
    askPreferences(['drawtimeout'])

def prefBGcolor():
    askPreferences(['bgcolor'])
    draw.bgcolor(GD.config['bgcolor'])

def preferences():
    test = [["item1","value1"],
            ["item2",""],
            ["an item with a long name","and a very long value for this item, just to test the scrolling"]]
    d = ConfigDialog(test)
    res = d.process()
    print res

def AddMenuItems(menu, items=[]):
    """Add a list of items to a menu.

    Each item is a tuple of three strings : Type, Text, Value.
    Type specifies the menu item type and must be one of
    'Sep', 'Popup', 'Action', 'VAction', 'QAction'.
    
    'Sep' is a separator item. Its Text and Value fields are not used.
    
    For the other types, Text is the string that will be displayed in the
    menu. It can include a '&' character to flag the hotkey.
    
    'Popup' is a popup submenu item. Its value should be an item list,
    defining the menu to pop up when activated.
    
    'Action' is an active item. Its value is a python function that will be
    executed when the item is activated. It should be a global function
    without arguments.
    
    'VAction' is an active item where the value is a tuple of an function
    and an integer argument. When activated, the function will be executed
    with the specified argument. With 'Vaction', you can bind multiple
    menu items to the same function.

    'QAction' signals that the value is a qt QAction. It is advisable to
    construct a QAction if you have to use the sameaction in more than one
    place of your program. With this type Text may be None, if it was already
    set in the QAction itself.
    """
    for key,txt,val in items:
        if key == "Sep":
            menu.insertSeparator()
        elif key == "Popup":
            pop = qt.QPopupMenu(menu,txt)
            AddMenuItems(pop,val)
            menu.insertItem(txt,pop)
        elif key == "Action":
            menu.insertItem(txt,eval(val))
        elif key == "VAction":
            id = menu.insertItem(txt,eval(val[0]))
            menu.setItemParameter(id,val[1])
        elif key == "SAction":
            menu.insertItem(txt,val)
        elif key == "QAction":
            if txt:
                val.setProperty("menuText",qt.QVariant(txt))
            val.addTo(menu)
        else:
            raise RuntimeError, "Invalid key %s in menu item"%key
#
# Using ("SAction","text",foo) is almost equivalent to
# using ("Action","text","foo"), but the latter allows for function
# that have not been defined yet in this scope!
#
MenuData = [
    ("Popup","&File",[
        ("Action","&Save","save"),
        ("Action","Save &As","saveAs"),
        ("Action","Save &Image","saveImage"),
        ("Action","Toggle &MultiSave","multiSave"),
        ("Sep",None,None),
        ("Action","&Play","play"),
        ("Action","&Record","record"),
        ("Sep",None,None),
        ("Action","E&xit","draw.exit"), ]),
    ("Popup","&Settings",[
#        ("Action","&Preferences","preferences"), 
        ("Action","&Drawwait Timeout","prefDrawtimeout"), 
        ("Action","&Background Color","prefBGcolor"), 
        ("Action","&LocalAxes","localAxes"),
        ("Action","&GlobalAxes","globalAxes"),
        ("Action","&Wireframe","draw.wireframe"),
        ("Action","&Smooth","draw.smooth"), ]),
    ("Popup","&Camera",[
        ("Action","&Zoom In","zoomIn"), 
        ("Action","&Zoom Out","zoomOut"), 
        ("Action","&Dolly In","dollyIn"), 
        ("Action","&Dolly Out","dollyOut"), 
        ("Action","Pan &Right","transRight"), 
        ("Action","Pan &Left","transLeft"), 
        ("Action","Pan &Up","transUp"),
        ("Action","Pan &Down","transDown"),
        ("Action","Rotate &Right","rotRight"),
        ("Action","Rotate &Left","rotLeft"),
        ("Action","Rotate &Up","rotUp"),
        ("Action","Rotate &Down","rotDown"),  ]),
    ("Popup","&Actions",[
        ("Action","&Step","draw.step"),
        ("Action","&Continue","draw.fforward"), 
        ("Action","&Clear","draw.clear"),
        ("Action","&Redraw","draw.redraw"),
        ("Action","&ListAll","draw.listall"),
#        ("Action","&Print","printit"),
#        ("Action","&Bbox","printbbox"),
        ("Action","&Globals","draw.printglobals"),  ]),
    ("Popup","&Help",[
        ("Action","&Help","showHelp"),
        ("Action","&About","about"), 
        ("Action","&Warning","testwarning"), ]) ]

# Examples Menu
def insertExampleMenu():
    """Insert the examples menu in the menudata."""
    global example
    dir = os.path.join(GD.config['pyformexdir'],"examples")
    if not os.path.isdir(dir):
        return
    example = filter(lambda s:s[-3:]==".py" and s[0]!='.' and s[0]!='_',os.listdir(dir))
    example = filter(lambda s:file(os.path.join(GD.config['pyformexdir'],"examples",s)).readlines()[0].strip().endswith('pyformex'),example)
    example.sort()
    vm = ("Popup","&Examples",[
        ("VAction","&%s"%os.path.splitext(t)[0],("runExample",i)) for i,t in enumerate(example)
        ])
    nEx = len(vm[2])
    vm[2].append(("VAction","Run All Examples",("runExamples",nEx)))
    MenuData.insert(4,vm)

def addDefaultMenu(menu):
    """Add the default menu structure to the GUI."""
    AddMenuItems(menu,MenuData)

def runExample(i):
    """Run example i from the list of found examples."""
    global example
    draw.playFile(os.path.join(GD.config['pyformexdir'],"examples",example[i]))

def runExamples(n):
    """Run the first n examples."""
    for i in range(n):
        runExample(i)

# add action buttons to toolbar
def addActionButtons(toolbar):
    global action
    action = {}
    dir = GD.config['icondir']
    buttons = [ [ "Step", "next.xbm", draw.step, False ],
                [ "Continue", "ff.xbm", draw.fforward, False ],
              ]
    for b in buttons:
        a = qt.QAction(b[0],qt.QIconSet(qt.QPixmap(os.path.join(dir,b[1]))),b[1],0,toolbar)
        qt.QObject.connect(a,qt.SIGNAL("activated()"),b[2])
        a.addTo(toolbar)
        a.setEnabled(b[3])
        action[b[0]] = a
    return action

# add camera buttons to toolbar (repeating)
def addCameraButtons(toolbar):
    dir = GD.config['icondir']
    buttons = [ [ "Rotate left", "rotleft.xbm", rotLeft ],
                [ "Rotate right", "rotright.xbm", rotRight ],
                [ "Rotate up", "rotup.xbm", rotUp ],
                [ "Rotate down", "rotdown.xbm", rotDown ],
                [ "Twist left", "twistleft.xbm", twistLeft ],
                [ "Twist right", "twistright.xbm", twistRight ],
                [ "Translate left", "left.xbm", transLeft ],
                [ "Translate right", "right.xbm", transRight ],
                [ "Translate down", "down.xbm", transDown ],
                [ "Translate up", "up.xbm", transUp ],
                [ "Zoom In", "zoomin.xbm", zoomIn ],
                [ "Zoom Out", "zoomout.xbm", zoomOut ],  ]
    for b in buttons:
        w = qt.QToolButton(qt.QIconSet(qt.QPixmap(os.path.join(dir,b[1]))),b[0],"",b[2],toolbar)
        w.setAutoRepeat(True)



###################### Actions #############################################
# Actions are just python functions, preferably without arguments
# Actions are often used as slots, which are triggered by signals,
#   e.g. by clicking a menu item or a tool button.
# Since signals have no arguments:
# Can we use python functions with arguments as actions ???
# - In menus we can have the menuitems send an integer id.
# - For other cases (like toolbuttons), we can subclass QAction and let it send
#   a signal with appropriate arguments 


def NotImplemented():
    draw.warning("This option has not been implemented yet!")
    
save = NotImplemented
saveAs = NotImplemented
record = NotImplemented

global help
help = None
def showHelp():
    """Start up the help browser"""
    global help
    from helpviewer import HelpViewer
    print "help = ",help
    if help == None:
        dir = os.path.join(GD.config['docdir'],"html")
        home = os.path.join(dir,"formex.html")
        print "Help file = ",home
        help = HelpViewer(home, dir,bookfile=GD.config['helpbookmarks'])
        help.setCaption("pyFormex - Helpviewer")
        help.setAbout("pyFormex Help", \
                  "This is the pyFormex HelpViewer.<p>It was modeled after the HelpViewer example " \
                  "from the Qt documentation.</p>")
        #help.resize(800,600)
        help.connect(help,qt.SIGNAL("destroyed()"),closeHelp)
    help.show()

def closeHelp():
    """Close the help browser"""
    global help
    help = None
        

def about():
    about = qt.QMessageBox()
    about.about(about,"About pyFormex",
        GD.Version+"\n\n"
        "pyFormex is a python implementation of Formex algebra\n\n"
        "http://pyformex.berlios.de\n\n"
        "Copyright 2004 Benedict Verhegghe\n"
        "Distributed under the GNU General Public License.\n\n"
        "For help or information, mailto benedict.verhegghe@ugent.be\n" )

def testwarning():
    draw.warning("Smoking may be hazardous to your health!\nWindows is a virus!")

    
def saveImage():
    """Save the current rendering in image format."""
    global canvas
    fs = FileSelectionDialog(pattern="Images (*.png *.jpg)",mode=qt.QFileDialog.AnyFile)
    fn = fs.getFilename()
    if fn:
        ext = os.path.splitext(fn)[1]
        fmt = imageFormatFromExt(ext)
        if fmt in qt.QImage.outputFormats():
            if len(ext) == 0:
                fn += '.%s' % fmt.lower()
            GD.canvas.save(fn,fmt)
        else:
            draw.warning("Sorry, can not save in %s format!\n"
                    "Suggest you use PNG format ;)"%fmt)

multisave = None

def saveNext():
    global multisave
    name,nr,fmt = multisave
    nr += 1
    multisave = [ name,nr,fmt ]
    GD.canvas.save(name % nr,fmt)


def multiSave():
    """Save a sequence of images.

    If the filename supplied has a trailing numeric part, subsequent images
    will be numbered continuing from this number. Otherwise a numeric part
    -000, -001, will be added to the filename.
    """
    global canvas,multisave
    if multisave:
        print "Stop auto mode"
        qt.QObject.disconnect(GD.canvas,qt.PYSIGNAL("save"),saveNext)
        multisave = None
        return
    
    fs = FileSelectionDialog(pattern="Images (*.png *.jpg)",mode=qt.QFileDialog.AnyFile)
    fn = fs.getFilename()
    if fn:
        print "Start auto mode"
        name,ext = os.path.splitext(fn)
        fmt = imageFormatFromExt(ext)
        print name,ext,fmt
        if fmt in qt.QImage.outputFormats():
            name,number = splitEndDigits(name)
            if len(number) > 0:
                nr = int(number)
                name += "%%0%dd" % len(number)
            else:
                nr = 0
                name += "-%03d"
            if len(ext) == 0:
                ext = '.%s' % fmt.lower()
            name += ext
            draw.warning("Each time you hit the 'S' key,\nthe image will be saved to the next number.")
            qt.QObject.connect(GD.canvas,qt.PYSIGNAL("save"),saveNext)
            multisave = [ name,nr,fmt ]
        else:
            draw.warning("Sorry, can not save in %s format!\n"
                    "Suggest you use PNG format ;)"%fmt)

#
def play():
    dir = GD.config.get('workdir',".")
    fs = FileSelectionDialog(dir,"pyformex scripts (*.frm *.py)")
    fn = fs.getFilename()
    if fn:
        GD.config['workdir'] = os.path.dirname(fn)
        playFile(fn)
        

def zoomIn():
    global canvas
    GD.canvas.zoom(1./GD.config['zoomfactor'])
    GD.canvas.update()
def zoomOut():
    global canvas
    GD.canvas.zoom(GD.config['zoomfactor'])
    GD.canvas.update()
##def panRight():
##    global canvas,config
##    canvas.camera.pan(+5)
##    canvas.update()   
##def panLeft():
##    global canvas,config
##    canvas.camera.pan(-5)
##    canvas.update()   
##def panUp():
##    global canvas,config
##    canvas.camera.pan(+5,0)
##    canvas.update()   
##def panDown():
##    global canvas,config
##    canvas.camera.pan(-5,0)
##    canvas.update()   
def rotRight():
    global canvas
    GD.canvas.camera.rotate(+GD.config['rotfactor'],0,1,0)
    GD.canvas.update()   
def rotLeft():
    global canvas
    GD.canvas.camera.rotate(-GD.config['rotfactor'],0,1,0)
    GD.canvas.update()   
def rotUp():
    global canvas
    GD.canvas.camera.rotate(-GD.config['rotfactor'],1,0,0)
    GD.canvas.update()   
def rotDown():
    global canvas
    GD.canvas.camera.rotate(+GD.config['rotfactor'],1,0,0)
    GD.canvas.update()   
def twistLeft():
    global canvas
    GD.canvas.camera.rotate(+GD.config['rotfactor'],0,0,1)
    GD.canvas.update()   
def twistRight():
    global canvas
    GD.canvas.camera.rotate(-GD.config['rotfactor'],0,0,1)
    GD.canvas.update()   
def transLeft():
    global canvas
    GD.canvas.camera.translate(-GD.config['panfactor'],0,0,GD.config['localaxes'])
    GD.canvas.update()   
def transRight():
    global canvas
    GD.canvas.camera.translate(GD.config['panfactor'],0,0,GD.config['localaxes'])
    GD.canvas.update()   
def transDown():
    global canvas
    GD.canvas.camera.translate(0,-GD.config['panfactor'],0,GD.config['localaxes'])
    GD.canvas.update()   
def transUp():
    global canvas
    GD.canvas.camera.translate(0,GD.config['panfactor'],0,GD.config['localaxes'])
    GD.canvas.update()   
def dollyIn():
    global canvas
    GD.canvas.camera.dolly(1./GD.config['zoomfactor'])
    GD.canvas.update()   
def dollyOut():
    global canvas
    GD.canvas.camera.dolly(GD.config['zoomfactor'])
    GD.canvas.update()   

def frontView():
    view("front");
def backView():
    view("back");
def leftView():
    view("left");
def rightView():
    view("right");
def topView():
    view("top");
def bottomView():
    view("bottom");
def isoView():
    view("iso");
# JUST TESTING:
def userView(i=1):
    if i==1:
        frontView()
    else:
        isoView()

     

def localAxes():
    GD.config['localaxes'] = True 
def globalAxes():
    GD.config['localaxes'] = False 



#### End
