.. $Id$  -*- rst -*-
.. pyformex reference manual --- draw
.. CREATED WITH py2rst.py: DO NOT EDIT

.. include:: ../defines.inc
.. include:: ../links.inc

.. _sec:ref-draw:

:mod:`draw` --- Create 3D graphical representations.
====================================================

.. automodule:: draw
   :synopsis: Create 3D graphical representations.


   .. autofunction:: closeGui()
   .. autofunction:: showMessage(text,actions=['OK'],level='info',modal=True)
   .. autofunction:: showInfo(text,actions=['OK'],modal=True)
   .. autofunction:: warning(text,actions=['OK'])
   .. autofunction:: error(text,actions=['OK'])
   .. autofunction:: ask(question,choices=None)
   .. autofunction:: ack(question)
   .. autofunction:: showText(text,type=None,actions=[(!!(319, (303, (304, (305, (306, (307, (309, (310, (311, (312, (313, (314, (315, (316, (317, (3, "'OK'"))))))))))))))), (12, ','), (303, (304, (305, (306, (307, (309, (310, (311, (312, (313, (314, (315, (316, (317, (1, 'None'))))))))))))))))!!)],modal=True,mono=False)
   .. autofunction:: showFile(filename,mono=False)
   .. autofunction:: askItems(items,caption=None,timeout=None,legacy=True)
   .. autofunction:: currentDialog()
   .. autofunction:: dialogAccepted()
   .. autofunction:: dialogRejected()
   .. autofunction:: dialogTimedOut()
   .. autofunction:: askFilename(cur=None,filter="All files (*.*)",exist=True,multi=False,change=True)
   .. autofunction:: askNewFilename(cur=None,filter="All files (*.*)")
   .. autofunction:: askDirname(cur=None,change=True)
   .. autofunction:: checkWorkdir()
   .. autofunction:: printMessage(s)
   .. autofunction:: draw(F,view=None,bbox=None,color='prop',colormap=None,alpha=None,mode=None,linewidth=None,shrink=None,marksize=None,wait=True,clear=None,allviews=False,highlight=False,flat=False)
   .. autofunction:: focus(object)
   .. autofunction:: setDrawOptions(d)
   .. autofunction:: showDrawOptions()
   .. autofunction:: askDrawOptions(d={})
   .. autofunction:: reset()
   .. autofunction:: resetAll()
   .. autofunction:: shrink(v)
   .. autofunction:: setView(name,angles=None)
   .. autofunction:: drawVectors(P,v,d=1.0,color='red')
   .. autofunction:: drawPlane(P,N,size)
   .. autofunction:: drawMarks(X,M,color='black',leader='')
   .. autofunction:: drawNumbers(F,color='black',trl=None,offset=0,leader='')
   .. autofunction:: drawVertexNumbers(F,color='black',trl=None)
   .. autofunction:: drawNormals(N,P,size=5)
   .. autofunction:: drawText3D(P,text,color=None,font='sans',size=18)
   .. autofunction:: drawViewportAxes3D(pos,color=None)
   .. autofunction:: drawBbox(A)
   .. autofunction:: drawActor(A)
   .. autofunction:: undraw(itemlist)
   .. autofunction:: view(v,wait=False)
   .. autofunction:: setTriade(on=None,pos='lb',siz=100)
   .. autofunction:: drawText(text,x,y,gravity='E',font='helvetica',size=14,color=None,zoom=None)
   .. autofunction:: annotate(annot)
   .. autofunction:: unannotate(annot)
   .. autofunction:: decorate(decor)
   .. autofunction:: undecorate(decor)
   .. autofunction:: frontView()
   .. autofunction:: backView()
   .. autofunction:: leftView()
   .. autofunction:: rightView()
   .. autofunction:: topView()
   .. autofunction:: bottomView()
   .. autofunction:: isoView()
   .. autofunction:: createView(name,angles)
   .. autofunction:: zoomBbox(bb)
   .. autofunction:: zoomRectangle()
   .. autofunction:: zoomAll()
   .. autofunction:: zoom(f)
   .. autofunction:: bgcolor(color,color2=None)
   .. autofunction:: fgcolor(color)
   .. autofunction:: renderMode(mode,avg=False)
   .. autofunction:: wireframe()
   .. autofunction:: smooth()
   .. autofunction:: smoothwire()
   .. autofunction:: flat()
   .. autofunction:: flatwire()
   .. autofunction:: smooth_avg()
   .. autofunction:: lights(onoff)
   .. autofunction:: transparent(state=True)
   .. autofunction:: perspective(state=True)
   .. autofunction:: timeout(state=None)
   .. autofunction:: set_material_value(typ,val)
   .. autofunction:: set_light(light)
   .. autofunction:: set_light_value(light,key,val)
   .. autofunction:: linewidth(wid)
   .. autofunction:: pointsize(siz)
   .. autofunction:: canvasSize(width,height)
   .. autofunction:: clear_canvas()
   .. autofunction:: clear()
   .. autofunction:: redraw()
   .. autofunction:: pause(msg="Use the Step or Continue button to proceed",timeout=None)
   .. autofunction:: step()
   .. autofunction:: fforward()
   .. autofunction:: delay(i)
   .. autofunction:: sleep(timeout=None)
   .. autofunction:: wakeup(mode=0)
   .. autofunction:: printbbox()
   .. autofunction:: printviewportsettings()
   .. autofunction:: layout(nvps=None,ncols=None,nrows=None)
   .. autofunction:: addViewport()
   .. autofunction:: removeViewport()
   .. autofunction:: linkViewport(vp,tovp)
   .. autofunction:: viewport(n)
   .. autofunction:: updateGUI()
   .. autofunction:: flyAlong(path='flypath',upvector=[0.,1.,0.],sleeptime=None)
   .. autofunction:: highlightActors(K)
   .. autofunction:: highlightElements(K)
   .. autofunction:: highlightEdges(K)
   .. autofunction:: highlightPoints(K)
   .. autofunction:: highlightPartitions(K)
   .. autofunction:: removeHighlights()
   .. autofunction:: set_selection_filter(i)
   .. autofunction:: pick(mode='actor',filtr=None,oneshot=False,func=None)
   .. autofunction:: pickActors(filtr=None,oneshot=False,func=None)
   .. autofunction:: pickElements(filtr=None,oneshot=False,func=None)
   .. autofunction:: pickPoints(filtr=None,oneshot=False,func=None)
   .. autofunction:: pickEdges(filtr=None,oneshot=False,func=None)
   .. autofunction:: highlight(K,mode)
   .. autofunction:: pickNumbers(marks=None)
   .. autofunction:: set_edit_mode(i)
   .. autofunction:: drawLinesInter(mode='line',single=False,func=None)
   .. autofunction:: showLineDrawing(L)
   .. autofunction:: setLocalAxes(mode=True)
   .. autofunction:: setGlobalAxes(mode=True)

   
.. moduleauthor:: pyFormex project (http://pyformex.org)

.. End

