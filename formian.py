#!/usr/bin/env python
"""Een formian-alike python"""

Version="Forming 0.1"
import sys,time

from Formex import *
from Menu import *
from Canvas import *

       
def AddMenuItems(menu, items=[]):
    """Add a list of items to a menu.

    Each item is a tuple of three strings : Type, Text, Value.
    Type is one of 'Sep', 'Popup', 'Action'.
    'Sep' is a separator item. Its Text and Value fields are not used.
    For the other types, Text is the text that will be displayed in the
    menu. It can include a '&' character to flag the hotkey.
    
    'Popup' is a popup submenu item. Its value should be an item list.
    'Action' is an active item. Its value is an instruction that is to be
    executed when the item is activated. It will be executed by calling
    python's eval(Value) instruction.
    'QAction' signals that value is a qt QAction. Text may be None if it
    was already set in constructuting the QAction.
    """
    for key,txt,val in items:
        if key == "Sep":
            menu.insertSeparator()
        elif key == "Popup":
            pop = QPopupMenu(menu,txt)
            AddMenuItems(pop,val)
            menu.insertItem(txt,pop)
        elif key == "Action":
            menu.insertItem(txt,eval(val))
        elif key == "QAction":
            if txt:
                val.setProperty("menuText",QVariant(txt))
            val.addTo(menu)
        else:
            raise RuntimeError, "Invalid key %s in menu item"%key
        

MenuData = [
    ("Popup","&File",[
        ("Action","&Save","save"),
        ("Action","Save &As","saveAs"),
        ("Sep",None,None),
        ("Action","&Play","play"),
        ("Action","&Record","record"),
        ("Sep",None,None),
        ("Action","E&xit","exit"), ]),
    ("Popup","&Display",[
        ("Action","&Test","test"), 
        ("Action","&Print","printit"), 
        ("Action","&Bbox","bbox"), 
        ("Action","&Clear","clear"),
        ("Action","&Redraw","redraw"), ]),
    ("Popup","&View",[
        ("Action","&Zoom In","zoomIn"), 
        ("Action","&Zoom Out","zoomOut"), 
        ("Action","&Front View","frontView"),
        ("Action","&Right View","rightView"),
        ("Action","&Top View","topView"),
        ("Action","&Rotate Y","rotateY"), ]),
    ("Popup","&Help",[
        ("Action","&Help","Help"),
        ("Action","&About","About"), ])]


def NotImplemented():
    print "This option has not been implemented yet!"

Help = NotImplemented
About = NotImplemented
save = NotImplemented
saveAs = NotImplemented
play = NotImplemented
record = NotImplemented
out=None
def test():
    draw(maketest(0))
def printit():
    global out
    print out
def bbox():
    global out
    print "bbox ",out.bbox()
def clear():
    global canvas
    canvas.clear()
def redraw():
    global canvas
    canvas.display()
def zoomIn():
    global canvas
    canvas.zoom(2)
    canvas.display()
def zoomOut():
    global canvas
    canvas.zoom(0.5)
    canvas.display()
def frontView():
    global canvas,bbox
    canvas.setView(bbox,'front')
    canvas.display()
def rightView():
    global canvas,bbox
    canvas.setView(bbox,'right')
    canvas.display()
def topView():
    global canvas,bbox
    canvas.setView(bbox,'top')
    canvas.display()
def rotateY():
    global canvas,bbox
    canvas.camera.setAngles(0,canvas.camera.roty+15,0)
    canvas.display()


    
def draw(F,camera=1):
    """Draw a Formex on the canvas"""
    global canvas,bbox
    canvas.removeAllActors()
    canvas.addActor(FormexActor(F))
    bbox = F.bbox()
    print "bbox = ",bbox
    if camera:
        canvas.setView(bbox)
    canvas.display()


def exit():
    global app
    if app:
        app.quit()
    else:
        sys.exit(0)

def GUI():
    global canvas
    w = QMainWindow()
    w.setCaption(Version)
    w.resize(640,480)
    # add widgets to the main window
    s = w.statusBar()
    s.message(Version+" (c) B. Verhegghe")
    m = w.menuBar()
    AddMenuItems(m,MenuData)
    # Create a nice frame to put around the OpenGL widget
    # Create our display widget
    f = QHBox(w, "frame")
    f.setFrameStyle(QFrame.Sunken | QFrame.Panel)
    f.setLineWidth(2)
    f.resize(640,480)
    from qtgl import QGLFormat
    fmt = QGLFormat.defaultFormat()
    fmt.setDirectRendering(options.dri)
    canvas = Canvas(640,480,fmt,f)
    canvas.clear()
    canvas.camera.setPosition(0,0,5)
    # Put the GL widget inside the frame
    w.setCentralWidget(f)
    return w

testnr=0
    
def maketest(nr=0):
    global testnr,F,G,out
    if nr == 0:
        nr = testnr
        testnr += 1
    print "Test nr. %d"%nr 
    if nr == 0:
        F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]])
        out = F.lam(1,1).lam(2,1).rin(1,10,2).rin(2,6,2)
    elif nr == 1:
        E = Formex([[[1,1.5],[1,1]],[[1,1],[2,1]]])
        out = E.ros(1,2,3,1,5,-45)
    elif nr == 2:
        N = Formex([[[0,0],[2,0]],[[0,0],[1,1]],[[2,0],[1,1]]])
        out = N.genid(4,3,2,1,1,-1)
    elif nr == 3:
        G = F.lamid(1,1).rinid(10,6,2,2)
        out = G.bb(1.5,0.8)
    elif nr == 3:
        out = G.bp(0.75,15)
    elif nr == 4:
        out = Formex([[[5,1,1],[5,2,1]]]).rinit(6,5,1,1) + Formex([[[5,1,1],[5,1,2]]]).rinit(7,4,1,1)
    return out

     
def runApp(args):
    global app,canvas
    app = QApplication(sys.argv)
    QObject.connect(app,SIGNAL("lastWindowClosed()"),app,SLOT("quit()"))
    # create GUI
    gui = GUI()
    app.setMainWidget(gui)
    gui.show()
    canvas.show()
    canvas.clear()
    app.exec_loop()
   
def main(argv=None):
    """This is a fairly generic main() function"""
    global options
    # this allows us to call main from the interpreter
    if argv is None:
        argv = sys.argv
    #process options
    from optparse import OptionParser,make_option
    parser = OptionParser(
        usage = "usage: %prog [<options>] [ --  <Qapp-options> ]",
        version = Version,
        option_list=[
        make_option("--nodri", help="do not use Direct Rendering",
                    action="store_false", dest="dri", default=True),
        make_option("--debug", help="display logging info to sys.stdout",
                    action="store_true", dest="debug", default=False)
        ])
    (options, args) = parser.parse_args()
    # Run the application
    return runApp(args)

#### Go
if __name__ == "__main__":
    sys.exit(main())

#### End
