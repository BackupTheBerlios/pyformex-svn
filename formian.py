#!/usr/bin/env python
"""A formian-alike python"""

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
    ("Popup","&Examples",[
        ("Action","&Dome","example0"),
        ("Action","&Double Layer","example1"), ]),
    ("Popup","&View",[
        ("Action","&Front View","frontView"),
        ("Action","&Back View","frontView"),
        ("Action","&Right View","rightView"),
        ("Action","&Left View","leftView"),
        ("Action","&Top View","topView"),
        ("Action","&Bottom View","bottomView"),
        ("Action","&Isometric View","isoView"), ]),
    ("Popup","&Camera",[
        ("Action","&Zoom In","zoomIn"), 
        ("Action","&Zoom Out","zoomOut"), 
        ("Action","Pan &Right","panRight"), 
        ("Action","Pan &Left","panLeft"), 
        ("Action","Pan &Up","panUp"),
        ("Action","Pan &Down","panDown"),
        ("Action","Rotate &Right","rotRight"),
        ("Action","Rotate &Left","rotLeft"),
        ("Action","Rotate &Up","rotUp"),
        ("Action","Rotate &Down","rotDown"),  ]),
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
def example0():
    draw(example(0))
def example1():
    draw(example(1))
def frontView():
    global canvas,bbox
    canvas.setView(bbox,'front')
    canvas.display()
def backView():
    global canvas,bbox
    canvas.setView(bbox,'back')
    canvas.display()
def rightView():
    global canvas,bbox
    canvas.setView(bbox,'right')
    canvas.display()
def leftView():
    global canvas,bbox
    canvas.setView(bbox,'left')
    canvas.display()
def topView():
    global canvas,bbox
    canvas.setView(bbox,'top')
    canvas.display()
def bottomView():
    global canvas,bbox
    canvas.setView(bbox,'bottom')
    canvas.display()
def isoView():
    global canvas,bbox
    canvas.setView(bbox,'iso')
    canvas.display()
def zoomIn():
    global canvas
    canvas.zoom(0.8)
    canvas.display()
def zoomOut():
    global canvas
    canvas.zoom(1.25)
    canvas.display()
def panRight():
    global canvas
    canvas.camera.pan(+5)
    canvas.display()   
def panLeft():
    global canvas
    canvas.camera.pan(-5)
    canvas.display()   
def panUp():
    global canvas
    canvas.camera.pan(+5,1)
    canvas.display()   
def panDown():
    global canvas
    canvas.camera.pan(-5,0)
    canvas.display()   
def rotRight():
    global canvas
    canvas.camera.rotate(+5)
    canvas.display()   
def rotLeft():
    global canvas
    canvas.camera.rotate(-5)
    canvas.display()   
def rotUp():
    global canvas
    canvas.camera.rotate(+5,1)
    canvas.display()   
def rotDown():
    global canvas
    canvas.camera.rotate(-5,1)
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
    canvas.camera.setPos(0,0,5)
    # Put the GL widget inside the frame
    w.setCentralWidget(f)
    return w

testnr=0
    
def maketest(nr=0):
    global testnr,F,G,out
    if nr == 0:
        nr = testnr
    testnr = (testnr + 1) % 5
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

def example(nr):
    """A set of examples"""
    global out
    if nr == 0:
        # Dome 1
        ny=12; nz=8; rd=100; a=2; t=50;
        e = Formex([[[1,0,a],[1,1,1+a]]])
        f1 = e.rosat(1,1+a).rinit(ny,nz,2,2).bs(rd,180/ny,t/(2*nz+a))
        f2 = Formex([[[1,0,a],[1,2,a]]]).rinit(ny,2,2,2*nz).bs(rd,180/ny,t/(2*nz+a))
        out = f1 + f2
        #; use&,vt(1),vm(2),vh(10,10,20,0,0,0,0,0,1); draw f;
    elif nr == 1: # Double Layer
        n=10; a=2./3.; d=1./n;
        e1 = Formex([[[0,0,d],[2,0,d]],[[2,0,d],[1,1,d]],[[1,1,d],[0,0,d]]])
        e2 = Formex([[[0,0,d],[1,1-a,0]],[[2,0,d],[1,1-a,0]],[[1,1,d],[1,1-a,0]]])
        e4 = e1.genid(n,n,2,1,1,-1).bb(1./(2*n),1./(2*n)/tan(radians(30)))
        e5 = e1.genid(n-1,n-1,2,1,1,-1).translate([1,1-a,-d]).bb(1./(2*n),1./(2*n)/tan(radians(30)))
        e6 = e2.genid(n,n,2,1,1,-1).bb(1./(2*n),1./(2*n)/tan(radians(30)))
        out = (e4+e5+e6).tran(3,-d)
        #use &,vm(2),vh(10,6,1000,0,0,0,0,0,1); draw e; mape=1.0;
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
