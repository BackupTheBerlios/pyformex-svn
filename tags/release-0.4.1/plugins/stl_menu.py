#!/usr/bin/env pyformex
# $Id: Stl.py 156 2006-11-06 19:14:25Z bverheg $

"""Stl.py

When executed, this script adds a specialized 'Stl' menu to the menubar
with actions defined in this script. The user can then execute these actions
through the menu. Executing this script does not produce any actions.
If you make changes to this script while running pyFormex, you can activate
these changes by closing the 'Stl' menu and running this script again.
"""

from plugins import f2abq, stl, tetgen, stl_abq
from gui import widgets
import commands, os

global project,F,nodes,elems,surf
project = F = nodes = elems = surf = None
projectLabel = None


# Define some Actions

def read_stl(fn=None):
    """Read STL model from file fn.

    If no file is given, one is asked.
    The file fn should exist and contain a valid STL model.
    The STL model is stored in the Formex F.
    The workdir and project name are set from the filename.
    The Formex is stored under the project basename.
    The model is displayed.
    """
    global project,F
    if fn is None:
        fn = askFilename(GD.cfg['workdir'],"Stl files (*.stl)")
        if fn:
            clear()
            linewidth(1)
        else:
            return
    os.chdir(os.path.dirname(fn))
    message("Your current workdir is %s" % os.getcwd())
    project = os.path.splitext(fn)[0]
    message("Reading file %s" % fn)
    F = Formex(stl.read_ascii(fn))
    name = os.path.basename(project)
    projectLabel.setText(name)
    Globals().update({name:F})
    message("STL model %s has %d triangles" % (name,F.f.shape[0]))
    message("The bounding box is\n%s" % F.bbox())
    show_stl()

def show_stl():
    """Display the .stl model."""
    global F
    if F:
        updateGUI()
        GD.gui.update()
        GD.app.processEvents()
        draw(F,color='green')

def save_stl():
    """Save the stl model."""
    global project,F
    if F is None:
        return
    fn = askFilename(GD.cfg['workdir'],"Stl files (*.stl)",exist=False)
    if fn:
        if not fn.endswith('.stl'):
            fn += '.stl'
        os.chdir(os.path.dirname(fn))
        message("Your current workdir is %s" % os.getcwd())
        project = os.path.splitext(fn)[0]
        if not os.path.exists(fn) or ack("File %s already exists. Overwrite?" % fn):
            stl.write_ascii(F.f,fn)

def center_stl():
    """Center the stl model."""
    global F,oldF
    updateGUI()
    center = array(F.center())
    print center
    clear()
    draw(F,color='yellow',wait=False)
    oldF = F
    F = F.translate(-center)
    draw(F,color='green')

def scale_stl():
    """Scale the stl model."""
    global F,oldF
    itemlist = [ [ 'X-scale',1.0], [ 'Y-scale',1.0], [ 'Z-scale',1.0] ] 
    res,accept = widgets.inputDialog(itemlist,'Scaling Parameters').process()
    if accept:
        print res
        updateGUI()
        clear()
        draw(F,color='yellow',wait=False)
        oldF = F
        F = F.scale(map(float,[r[1] for r in res]))
        draw(F,color='green')

def rotate_stl():
    """Rotate the stl model."""
    global F,oldF
    itemlist = [ [ 'axis',0], ['angle','0.0'] ] 
    res,accept = widgets.inputDialog(itemlist,'Rotation Parameters').process()
    if accept:
        print res
        updateGUI()
        clear()
        draw(F,color='yellow',wait=False)
        oldF = F
        F = F.rotate(float(res[1][1]),int(res[0][1]))
        draw(F,color='green')
        
def clip_stl():
    """Clip the stl model."""
    global F,oldF
    itemlist = [['axis',0],['begin',0.0],['end',1.0],['nodes','any']]
    res,accept = widgets.inputDialog(itemlist,'Clipping Parameters').process()
    if accept:
        updateGUI()
        clear()
        bb = F.bbox()
        message("Original bbox: %s" % bb) 
        xmi = bb[0][0]
        xma = bb[1][0]
        dx = xma-xmi
        axis = int(res[0][1])
        xc1 = xmi + float(res[1][1]) * dx
        xc2 = xmi + float(res[2][1]) * dx
        nodes = res[3][1]
        print nodes
        w = F.where(nodes='any',dir=axis,min=xc1,max=xc2)
        draw(F.cclip(w),color='yellow',wait=False)
        oldF = F
        F = F.clip(w)
        message("Clipped bbox = %s" % F.bbox())
        #linewidth(2)
        draw(F,color='green')

def undo_stl():
    """Undo the last transformation."""
    global F,oldF
    clear()
    linewidth(1)
    F = oldF
    draw(F,color='green')

def section_stl():
    """Sectionize the stl model."""
    global F,sections,ctr,diam
    clear()
    linewidth(1)
    draw(F,color='yellow')
    bb = F.bbox()
    message("Bounding box = %s" % bb)

    itemlist = [['number of sections',20],['relative thickness',0.1]]
    res,accept = widgets.inputDialog(itemlist,'Sectioning Parameters').process()
    sections = []
    ctr = []
    diam = []
    if accept:
        n = int(res[0][1])
        th = float(res[1][1])
        xmin = bb[0][0]
        xmax = bb[1][0]
        dx = (xmax-xmin) / n
        dxx = dx * th
        X = xmin + arange(n+1) * dx
        message("Sections are taken at X-values: %s" % X)

        c = zeros([n,3],float)
        d = zeros([n,1],float)
        linewidth(2)

        for i in range(n+1):
            G = F.clip(F.where(nodes='any',dir=0,min=X[i]-dxx,max=X[i]+dxx))
            draw(G,color='blue',view=None)
            GD.canvas.update()
            C = G.center()
            H = Formex(G.f-C)
            x,y,z = H.x(),H.y(),H.z()
            D = 2 * sqrt((x*x+y*y+z*z).mean())
            message("Section Center: %s; Diameter: %s" % (C,D))
            sections.append(G)
            ctr.append(C)
            diam.append(D)

def circle_stl():
    """Draw circles as approximation of the STL model."""
    global sections,ctr,diam,circles
    import simple
    circle = simple.circle().rotate(-90,1)
    cross = Formex(simple.Pattern['plus']).rotate(-90,1)
    circles = []
    n = len(sections)
    for i in range(n):
        C = cross.translate(ctr[i])
        B = circle.scale(diam[i]/2).translate(ctr[i])
        S = sections[i]
        print C.bbox()
        print B.bbox()
        print S.bbox()
        clear()
        draw(S,view='left',wait=False)
        draw(C,color='red',bbox=None,wait=False)
        draw(B,color='blue',bbox=None)
        circles.append(B)

def allcircles_stl():
    global circles
    clear()
    linewidth(1)
    draw(F,color='yellow',view='front')
    linewidth(2)
    for circ in circles:
        draw(circ,color='blue',bbox=None)
        
def fill_holes():
    global F,oldF
    fn = project + '.stl'
    fn1 = project + '-closed.stl'
    if os.path.exists(fn):
        sta,out = commands.getstatusoutput('admesh %s -f -a %s' % (fn,fn1))
        message(out)
        if sta == 0:
            clear()
            linewidth(1)
            draw(F,color='yellow',view='front')
            oldF = F
            linewidth(2)
            read_stl(fn1)


def flytru_stl():
    """Fly through the stl model."""
    global ctr
    Fc = Formex(array(ctr).reshape((-1,1,3)))
    path = connect([Fc,Fc],bias=[0,1])
    flyAlong(path)
    

def export_stl():
    """Export an stl model stored in Formex F in Abaqus .inp format."""
    global project,F
    if ack("Creating nodes and elements.\nFor a large model, this could take quite some time!"):
        GD.app.processEvents()
        message("Creating nodes and elements.")
        nodes,elems = F.feModel()
        nnodes = nodes.shape[0]
        nelems = elems.shape[0]
        message("There are %d unique nodes and %d triangle elements in the model." % (nnodes,nelems))
        stl_abq.abq_export(project+'.inp',nodes,elems,'S3',"Created by stl_examples.py")
#    menu.process()
    

def create_tetgen():
    """Generate a volume tetraeder mesh inside an stl surface."""
    fn = project + '.stl'
    if os.path.exists(fn):
        sta,out = commands.getstatusoutput('tetgen %s' % fn)
        message(out)


def read_tetgen(surface=True, volume=True):
    """Read a tetgen model from files  fn.node, fn.ele, fn.smesh."""
    global nodes,elems,surf
    fn = askFilename(GD.cfg['workdir'],"Tetgen files (*.node)")
    nodes = elems =surf = None
    if fn:
        os.chdir(os.path.dirname(fn))
        message("Your current workdir is %s" % os.getcwd())
        project = os.path.splitext(fn)[0]
        nodes = tetgen.readNodes(project+'.node')
        print "Read %d nodes" % nodes.shape[0]
        if volume:
            elems = tetgen.readElems(project+'.ele')
            print "Read %d tetraeders" % elems.shape[0]
        if surface:
            surf = tetgen.readSurface(project+'.smesh')
            print "Read %d triangles" % surf.shape[0]
    show_tetgen_surface()


def read_tetgen_surface():
    read_tetgen(volume=False)

    
def read_tetgen_volume():
    read_tetgen(surface=False)


def show_tetgen_surface():
    global nodes,surf
    updateGUI()
    if surf is not None:
        surface = Formex(nodes[surf-1])
        name = os.path.basename(project)
        Globals().update({name+'-surface':surface})
        clear()
        draw(surface,color='red')


def show_tetgen_volume():
    global nodes,elems
    updateGUI()
    if elems is not None:
        volume = Formex(nodes[elems-1])
        name = os.path.basename(project)
        Globals().update({name+'-volume':volume})
        clear()
        draw(volume,color='random',eltype='tet')


def export_tetgen_surface():
    global nodes,surf
    updateGUI()
    if surf is not None:
        print "Exporting surface model"
        stl_abq.abq_export('%s-surface.inp' % project,nodes,surf,'S3',"Abaqus model generated by tetgen from surface in STL file %s.stl" % project)



def export_tetgen_volume():
    global nodes,elems
    updateGUI()
    if elems is not None:
        print "Exporting volume model"
        stl_abq.abq_export('%s-volume.inp' % project,nodes,elems,'C3D%d' % elems.shape[1],"Abaqus model generated by tetgen from surface in STL file %s.stl" % project)


def create_menu():
    """Create the STL menu."""
    menu = widgets.Menu('STL')
    MenuData = [
        #("&New project",new_project),
        ("&Read STL file",read_stl),
        ("&Show STL model",show_stl),
        ("&Center STL model",center_stl),
        ("&Rotate STL model",rotate_stl),
        ("&Clip STL model",clip_stl),
        ("&Scale STL model",scale_stl),
        ("&Undo LAST STL transformation",undo_stl),
        ("&Save STL model",save_stl),
        ("&Sectionize STL model",section_stl),
        ("&Show individual circles",circle_stl),
        ("&Show all circles on STL model",allcircles_stl),
        ("&Fill the holes in STL model",fill_holes),
        ("&Fly STL model",flytru_stl),
        ("&Export STL model to Abaqus (SLOW!)",export_stl),
        ("&Create tetgen model",create_tetgen),
        #("&Read tetgen surface",read_tetgen_surface),
        #("&Read tetgen volume",read_tetgen_volume),
        ("&Read tetgen model",read_tetgen),
        ("&Show tetgen surface",show_tetgen_surface),
        ("&Show tetgen volume",show_tetgen_volume),
        ("&Export surface to Abaqus",export_tetgen_surface),
        ("&Export volume to Abaqus",export_tetgen_volume),
        ("&Close Menu",close_menu),
        ]
    menu.addItems(MenuData)
    return menu

def close_menu():
    """Close the STL menu."""
    # We should also remove the projectLabel widget from the statusbar
    GD.gui.statusbar.removeWidget(projectLabel)
    menu.close()
    

if __name__ == "draw": # This is executed when the script is 'play'ed

    from PyQt4 import QtGui

    message(__doc__)
    menu = create_menu()
    projectLabel = QtGui.QLabel('No Project')
    GD.gui.statusbar.addWidget(projectLabel)

# End
