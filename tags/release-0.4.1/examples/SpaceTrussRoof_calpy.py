#!/usr/bin/env pyformex
# $Id: SpaceTrussRoof_calpy.py 154 2006-11-03 19:08:25Z bverheg $
##
## This file is part of pyFormex 0.3 Release Mon Feb 20 21:04:03 2006
## pyFormex is a python implementation of Formex algebra
## Homepage: http://pyformex.berlios.de/
## Distributed under the GNU General Public License, see file COPYING
## Copyright (C) Benedict Verhegghe except where stated otherwise 
##

"""Double Layer Flat Space Truss Roof"""

#######################################################################
# Setting this path correctly is required to import the analysis module
# You need calpy >= 0.3.4
# It can be downloaded from ftp://bumps.ugent.be/calpy/
calpy_path = '/usr/local/lib/calpy-0.3.4'
#######################################################################

####
#Data
###################

dx = 1800 # Modular size [mm]
ht = 1500  # Deck height [mm]
nx = 5     # number of bottom deck modules in x direction 
ny = 4   # number of bottom deck modules in y direction 

q = -0.005 #distributed load [N/mm^2]


#############
#Creating the model
###################

top = (Formex("1").replic2(nx-1,ny,1,1) + Formex("2").replic2(nx,ny-1,1,1)).scale(dx)
top.setProp(3)
bottom = (Formex("1").replic2(nx,ny+1,1,1) + Formex("2").replic2(nx+1,ny,1,1)).scale(dx).translate([-dx/2,-dx/2,-ht])
bottom.setProp(0)
T0 = Formex(4*[[[0,0,0]]]) 	   # 4 times the corner of the top deck
T4 = bottom.select([0,1,nx,nx+1])  # 4 nodes of corner module of bottom deck
dia = connect([T0,T4]).replic2(nx,ny,dx,dx)
dia.setProp(1)

F = (top+bottom+dia)

clear();linewidth(1);draw(F)


############
#Creating FE-model
###################

nodes,elems=F.feModel()
nnod=nodes.shape[0]


###############
#Creating nodeprops-list
###################

nlist=arange(nnod)
count = zeros(nnod)
for n in elems.flat:
    count[n] += 1
field = nlist[count==8]
topedge = nlist[count==7]
topcorner = nlist[count==6]
bottomedge = nlist[count==5]
bottomcorner = nlist[count==3]

nodeprops=zeros(nnod)
nodeprops[field]=1
nodeprops[bottomedge]=0
nodeprops[bottomcorner]=0
nodeprops[topedge]=3
nodeprops[topcorner]=3


########################
#Defining and assigning the properties
#############################

from plugins.properties import *

Q = 0.5*q*dx*dx
support = NodeProperty(0, bound = 'pinned')
edge = NodeProperty(3,cload = [0,0,Q/2,0,0,0])
loaded = NodeProperty(1,cload = [0,0,Q,0,0,0])

circ20 = ElemSection(section={'name':'circ20','radius':10, 'cross_section':314.159}, material={'name':'S500', 'young_modulus':210000, 'shear_modulus':81000, 'poisson_ratio':0.3, 'yield_stress' : 500,'density':0.000007850}, sectiontype='Circ')
diabar = ElemProperty(1,elemsection = circ20, elemtype='T3D2')
bottombar = ElemProperty(0,elemsection = circ20, elemtype='T3D2')
topbar = ElemProperty(3,elemsection = circ20, elemtype='T3D2')


######### 
#calpy analysis
###################

def getmat(key):
    """Return the 'truss material' with key (str or int)."""
    p = elemproperties[key]
    if p:
        return [ p.young_modulus, p.density, p.cross_section ]
    else:
	return [ 0.0 ] * 3

model = F
props = model.prop()
propset = model.propSet()
nelems = elems.shape[0]

##### NOW load the analysis code #####

# Check if we have calpy:
import sys
sys.path.append(calpy_path)
try:
    from fe_util import *
    from truss3d import *
except ImportError:
    import globaldata as GD
    warning("You need calpy-0.3.4 or higher to perform the analysis.\nIt can be obtained from ftp://bumps.ugent.be/calpy/\nYou should also set the correct calpy installation path\n in this example's source file\n(%s).\nThe calpy_path variable is set near the top of that file.\nIts current value is: %s" % (GD.cfg['curfile'],calpy_path))
    exit()

# boundary conditions
bcon = zeros([nnod,3],dtype=int)
bcon[nodeprops == 0] = [ 1,1,1 ]
NumberEquations(bcon)
#materials
mats=array([ getmat(i) for i in range(max(propset)+1) ])
matnod = concatenate([reshape(props+1,(nelems,1)),elems+1],1)
ndof=bcon.max()
# loads
nlc=1
loads=zeros((ndof,nlc),Float)
for n in arange(nnod).compress(nodeprops == 1):
    loads[:,0] = AssembleVector(loads[:,0],[ 0.0, 0.0, Q ],bcon[n,:])
for n in arange(nnod).compress(nodeprops == 3):
    loads[:,0] = AssembleVector(loads[:,0],[ 0.0, 0.0, Q/2 ],bcon[n,:])
message("Performing analysis: this may take some time")
displ,frc = static(nodes,bcon,mats,matnod,loads,Echo=False)

################################
#Using pyFormex as postprocessor
################################

if GD.options.gui:

    from gui.colorscale import *
    import gui.decors

    # Creating a formex for displaying results is fairly easy
    results = Formex(nodes[elems],range(nelems))
    # Now give the formex some meaningful colors.
    # The frc array returns element forces and has shape
    #  (nelems,nforcevalues,nloadcases)
    # In this case there is only one resultant force per element (the
    # normal force), and only load case; we still need to select the
    # scalar element result values from the array into a onedimensional
    # vector val. 
    val = frc[:,0,0]
    # create a colorscale
    CS = ColorScale([blue,yellow,red],val.min(),val.max(),0.,2.,2.)
    cval = array(map(CS.color,val))
    #aprint(cval,header=['Red','Green','Blue'])
    clear()
    linewidth(3)
    draw(results,color=cval)
    drawtext('Normal force in the truss members',150,20,'tr24')
    CL = ColorLegend(CS,100)
    CLA = decors.ColorLegend(CL,10,10,30,200) 
    GD.canvas.addDecoration(CLA)
    GD.canvas.update()

    # Show upright
    setview('myview1',(0.,-90.,0.))
    view('myview1',True)

    clear()
    linewidth(1)
    draw(F,view='myview1',color=black)
    linewidth(3)

    siz0 = F.sizes()
    dF = Formex(displ[:,:,0][elems])
    #clear(); draw(dF,color=black)
    siz1 = dF.sizes()

    def niceNumber(f,approx=floor):
        """Returns a nice number close to but not smaller than f."""
        n = int(approx(log10(f)))
        m = int(str(f)[0])
        return m*10**n

    optscale = niceNumber(1./(siz1/siz0).max())


    # Show a deformed plot
    def deformed_plot(dscale=100.):
        """Shows a deformed plot with deformations scaled with a factor scale."""
        dnodes = nodes + dscale * displ[:,:,0]
        deformed = Formex(dnodes[elems],F.p)
        # deformed structure
        FA = draw(deformed,view='myview1',bbox=None)
        TA = decors.Text('Deformed geometry (scale %.2f)' % dscale,400,100,'tr24')
        decorate(TA)
        GD.canvas.removeActor(FA)
        GD.canvas.removeDecoration(TA)


    for s in optscale/10. * arange(11):
        deformed_plot(s)

    linewidth(1)

    ### Rotate the model

    ##drawtimeout = 0
    ##for i in range(19):
    ##    setview('myview2',(90.,i*10.,90))
    ##    view('myview2',True)
