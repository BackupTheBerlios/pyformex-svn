#/usr/bin/env python
	
from qt import *
import sys
        
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
        

        
if __name__ == "__main__":

    from qtgl import *
    
    def testing():
        print "testing QAction"

    qa = QAction(None,"Te&sting")
    qa.setProperty("text",QVariant("T&esting"))
    qa.connect(qa,SIGNAL("activated()"),testing)

    MenuData = [
        ("Popup","&File",[
            ("Action","&Save","Save"),
            ("Action","Save &As","SaveAs"),
            ("Sep",None,None),
            ("Action","E&xit","a.quit")]),
        ("Popup","&Settings",[]),
        ("Popup","&Qactions",[
            ("QAction",None,qa),
            ("QAction","QA",qa)]),
        ("Sep",None,None),
        ("Popup","&Help",[
            ("Action","&Help","Help"),
            ("Action","&About","About")])]

    def NotImplemented():
        print "This has not been implemented yet!"

    def Save():
        NotImplemented()

    SaveAs = NotImplemented
    Help = NotImplemented
    About = NotImplemented
    
    # Create application and main window
    a = QApplication(sys.argv)
    QObject.connect(a,SIGNAL("lastWindowClosed()"),a,SLOT("quit()"))
    w = QMainWindow()
    w.setCaption("Tracker 0.1")
    # add widgets to the main window
    s = w.statusBar()
    #r = QLabel("Ready",s)
    #s.addWidget(r)
    s.message("Tracker 0.1 (c) B. Verhegghe")
    m = w.menuBar()
    AddMenuItems(m,MenuData)
    o = QGLWidget()
    o.setFixedSize(640,480)
    w.setCentralWidget(o)
    # show main widget and go
    a.setMainWidget(w)
    w.show()
    a.exec_loop()
