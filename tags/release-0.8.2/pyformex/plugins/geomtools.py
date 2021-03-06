# $Id$
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
"""Basic geometrical operations.

This module defines some basic operations on simple geometrical entities
such as lines, triangles, circles, planes.
"""

from formex import *

class Plane(object):
    def __init__(self,P,n):
        self.coords = Coords.concatenate([P,normalize(n)])


def triangleInCircle(x):
    """Compute the incircles of the triangles x

    The incircle of a triangle is the largest circle that can be inscribed
    in the triangle.

    x is a Coords array with shape (ntri,3,3) representing ntri triangles.
    
    Returns a tuple r,C,n with the radii, Center and unit normals of the
    incircles.
    """
    checkArray(x,shape=(-1,3,3))
    # Edge vectors
    v = roll(x,-1,axis=1) - x
    v = normalize(v)
    # create bisecting lines in x0 and x1
    b0 = v[:,0]-v[:,2]
    b1 = v[:,1]-v[:,0]
    # find intersection => center point of incircle
    center = lineIntersection(x[:,0],b0,x[:,1],b1)
    # find distance to any side => radius
    radius = center.distanceFromLine(x[:,0],v[:,0])
    # normals
    normal = cross(v[:,0],v[:,1])
    normal /= length(normal).reshape(-1,1)
    return radius,center,normal


def triangleCircumCircle(x,bounding=False):
    """Compute the circumcircles of the triangles x

    x is a Coords array with shape (ntri,3,3) representing ntri triangles.
    
    Returns a tuple r,C,n with the radii, Center and unit normals of the
    circles going through the vertices of each triangle.

    If bounding=True, this returns the triangle bounding circle.
    """
    checkArray(x,shape=(-1,3,3))
    # Edge vectors
    v = x - roll(x,-1,axis=1)
    vv = dotpr(v,v)
    # Edge lengths
    lv = sqrt(vv)
    n = cross(v[:,0],v[:,1])
    nn = dotpr(n,n)
    # Radius
    N = sqrt(nn)
    r = asarray(lv.prod(axis=-1) / N / 2)
    # Center
    w = -dotpr(roll(v,1,axis=1),roll(v,2,axis=1))
    a = w * vv
    C = a.reshape(-1,3,1) * roll(x,1,axis=1)
    C = C.sum(axis=1) / nn.reshape(-1,1) / 2
    # Unit normals
    n = n / N.reshape(-1,1)
    # Bounding circle
    if bounding:
        # Modify for obtuse triangles
        for i,j,k in [[0,1,2],[1,2,0],[2,0,1]]:
            obt = vv[:,i] >= vv[:,j]+vv[:,k]
            r[obt] = 0.5 * lv[obt,i]
            C[obt] = 0.5 * (x[obt,i] + x[obt,j])
    
    return r,C,n


def triangleBoundingCircle(x):
    """Compute the bounding circles of the triangles x

    The bounding circle is the smallest circle in the plane of the triangle
    such that all vertices of the triangle are on or inside the circle.
    If the triangle is acute, this is equivalent to the triangle's
    circumcircle. It the triangle is obtuse, the longest edge is the
    diameter of the bounding circle.
    
    x is a Coords array with shape (ntri,3,3) representing ntri triangles.
    
    Returns a tuple r,C,n with the radii, Center and unit normals of the
    bounding circles.
    """
    return triangleCircumCircle(x,bounding=True)


def triangleObtuse(x):
    """Checks for obtuse triangles
    
    x is a Coords array with shape (ntri,3,3) representing ntri triangles.
    
    Returns an (ntri) array of True/False values indicating whether the
    triangles are obtuse.
    """
    checkArray(x,shape=(-1,3,3))
    # Edge vectors
    v = x - roll(x,-1,axis=1)
    vv = dotpr(v,v)
    return (vv[:,0] > vv[:,1]+vv[:,2]) + (vv[:,1] > vv[:,2]+vv[:,0]) + (vv[:,2] > vv[:,0]+vv[:,1])



def lineIntersection(P1,D1,P2,D2):
    """Finds the intersection of 2 coplanar lines.

    The lines (P1,D1) and (P2,D2) are defined by a point and a direction
    vector. Let a and b be unit vectors along the lines, and c = P2-P1,
    let ld and d be the length and the unit vector of the cross product a*b,
    the intersection point X is then given by X = 0.5(P1+P2+sa*a+sb*b)
    where sa = det([c,b,d])/ld and sb = det([c,a,d])/ld
    """
    P1 = asarray(P1).reshape((-1,3)).astype(float64)
    D1 = asarray(D1).reshape((-1,3)).astype(float64)
    P2 = asarray(P2).reshape((-1,3)).astype(float64)
    D2 = asarray(D2).reshape((-1,3)).astype(float64)
    N = P1.shape[0]
    # a,b,c,d
    la,a = vectorNormalize(D1)
    lb,b = vectorNormalize(D2)
    c = (P2-P1)
    d = cross(a,b)
    ld,d = vectorNormalize(d)
    # sa,sb
    a = a.reshape((-1,1,3))
    b = b.reshape((-1,1,3))
    c = c.reshape((-1,1,3))
    d = d.reshape((-1,1,3))
    m1 = concatenate([c,b,d],axis=-2)
    m2 = concatenate([c,a,d],axis=-2)
    # This may still be optimized
    sa = zeros((N,1))
    sb = zeros((N,1))
    for i in range(P1.shape[0]):
        sa[i] = linalg.det(m1[i]) / ld[i]
        sb[i] = linalg.det(m2[i]) / ld[i]
    # X
    a = a.reshape((-1,3))
    b = b.reshape((-1,3))
    X = 0.5 * ( P1 + sa*a + P2 + sb*b )
    return Coords(X)


def displaceLines(A,N,C,d):
    """Move all lines (A,N) over a distance a in the direction of point C.

    A,N are arrays with points and directions defining the lines.
    C is a point.
    d is a scalar or a list of scalars.
    All line elements of F are translated in the plane (line,C)
    over a distance d in the direction of the point C.
    Returns a new set of lines (A,N).
    """
    l,v = vectorNormalize(N)
    w = C - A
    vw = (v*w).sum(axis=-1).reshape((-1,1))
    Y = A + vw*v
    l,v = vectorNormalize(C-Y)
    return A + d*v, N


def segmentOrientation(vertices,vertices2=None,point=None):
    """Determine the orientation of a set of line segments.

    vertices and vertices2 are matching sets of points.
    point is a single point.
    All arguments are Coords objects.

    Line segments run between corresponding points of vertices and vertices2.
    If vertices2 is None, it is obtained by rolling the vertices one position
    foreward, thus corresponding to a closed polygon through the vertices).
    If point is None, it is taken as the center of vertices.

    The orientation algorithm checks whether the line segments turn
    positively around the point.
    
    Returns an array with +1/-1 for positive/negative oriented segments.
    """
    if vertices2 is None:
        vertices2 = roll(vertices,-1,axis=0)
    if point is None:
        point = vertices.center()

    w = cross(vertices,vertices2)
    orient = sign(dotpr(point,w)).astype(Int)
    return orient


def rotationAngle(A,B,angle_spec=Deg):
    """Return rotation angles and vectors for rotations of A to B.

    A and B are (n,3) shaped arrays where each line represents a vector.
    This function computes the rotation from each vector of A to the
    corresponding vector of B.
    The return value is a tuple of an (n,) shaped array with rotation angles
    (by default in degrees) and an (n,3) shaped array with unit vectors
    along the rotation axis.
    Specify angle_spec=Rad to get the angles in radians.
    """  
    A = normalize(A)
    B = normalize(B)
    n = cross(A,B) # vectors perpendicular to A and B
    t = length(n) == 0.
    if t.any(): # some vectors A and B are parallel
        n[t] = anyPerpendicularVector(A[t])
    n = normalize(n)
    c = dotpr(A,B)
    angle = arccos(c.clip(min=-1.,max=1.)) / angle_spec
    return angle,n


def anyPerpendicularVector(A):
    """Return arbitrary vectors perpendicular to vectors of A.
    
    A is a (n,3) shaped array of vectors.
    The return value is a (n,3) shaped array of perpendicular vectors.
    """
    x,y,z = hsplit(A,[1,2])
    n = zeros(x.shape,dtype=Float)
    t = (x!=0.)+(y!=0.)
    B = where(t,column_stack([-y,x,n]),column_stack([-z,n,x]))
    return B


def projectionVOV(A,B):
    """Return the projection of vector of A on vector of B."""
    L = projection(A,B)
    B = normalize(B)
    shape = list(L.shape)
    shape.append(1)
    return L.reshape(shape)*B


def projectionVOP(A,n):
    """Return the projection of vector of A on plane of B."""
    Aperp = projectionVOV(A,n)
    return A-Aperp


################## intersection tools ###############

def intersectionPointsLWL(q1,m1,q2,m2):
    """Return the intersection points of lines (q1,m1) and lines (q2,m2)

    with the perpendiculars between them.
    
    This is equivalent to intersectionTimesLWL(q1,m1,q2,m2) but returns a
    tuple of (nq1,nq2,3) shaped arrays of intersection points instead of the
    parameter values.
    """
    t1,t2 = intersectionTimesLWL(q1,m1,q2,m2)
    t1 = t1[:,:,newaxis]
    t2 = t2[:,:,newaxis]
    q1 = q1[:,newaxis,:]
    m1 = m1[:,newaxis,:]
    return q1 + t1 * m1, q2 + t2 * m2


def intersectionTimesLWL(q1,m1,q2,m2):
    """Return the intersection of lines (q1,m1) and lines (q2,m2)

    with the perpendiculars between them.

    q1/m1 is a (nq1,3) shaped array of points/vectors.
    q2/m2 is a (nq2,3) shaped array of points/vectors.
    
    The return value is a tuple of (nq1,nq2) shaped arrays of parameter
    values t1 and t2, such that the intersection points are given by
    q1+t1*m1 and q2+t2*m2.
    """
    if q1.shape != m1.shape:
        raise RuntimeError,"Expected q1 and m1 with same shape."
    if q2.shape != m2.shape:
        raise RuntimeError,"Expected q2 and m2 with same shape."
    q1 = q1[:,newaxis]
    m1 = m1[:,newaxis]
    q2 = q2[newaxis,:]
    m2 = m2[newaxis,:]
    m1 = repeat(m1,m2.shape[1],1)
    m2 = repeat(m2,m1.shape[0],0)
    m = row_stack([m1[newaxis],m2[newaxis]]) # (2,nq1,nq2,3)
    A = dotpr(m[:,newaxis],m[newaxis,:]) # (2,2,nq1,nq2)
    A[:,1] = -A[:,1]
    b = dotpr(q2-q1,m) # (2,nq1,nq2)
    t1,t2 = solveMany(A,b)
    return t1,t2


def intersectionPointsLWP(q,m,p,n):
    """Return the intersection points of lines (q,m) with planes (p,n).

    This is equivalent to intersectionTimesLWP(q,m,p,n) but returns a (nq,np,3)
    shaped array of intersection points instead of the parameter values.
    """
    t = intersectionTimesLWP(q,m,p,n)
    t = t[:,:,newaxis]
    q = q[:,newaxis,:]
    m = m[:,newaxis,:]
    return q + t * m


def intersectionTimesLWP(q,m,p,n):
    """Return the intersection of lines (q,m) with planes (p,n).

    q/m is a (nq,3) shaped array of points/vectors.
    p/n is a (np,3) shaped array of points/normals.
    
    The return value is a (nq,np) shaped array of parameter values t,
    such that the intersection points are given by q+t*m.
    """
    if q.shape != m.shape:
        raise RuntimeError,"Expected q and m with same shape."
    if p.shape != n.shape:
        raise RuntimeError,"Expected p and n with same shape."
    I1 = dotpr(p,n)
    I2 = inner(q,n)
    I3 = inner(m,n)
    return (I1-I2)/I3


def intersectionPointsPWP(p1,n1,p2,n2,p3,n3):
    """Return the intersection points of planes (p1,n1), (p2,n2) and (p3,n3).

    p1/n1 is a (np1,3) shaped array of points/normals.
    p2/n2 is a (np2,3) shaped array of points/normals.
    p3/n3 is a (np3,3) shaped array of points/normals.

    The return value is a (np1,np2,np3,3) shaped array of intersection points.
    """
    if p1.shape != n1.shape:
        raise RuntimeError,"Expected p1 and n1 with same shape."
    if p2.shape != n2.shape:
        raise RuntimeError,"Expected p2 and n2 with same shape."
    if p3.shape != n3.shape:
        raise RuntimeError,"Expected p3 and n3 with same shape."
    p1 = p1[:,newaxis,newaxis]
    n1 = n1[:,newaxis,newaxis]
    p2 = p2[newaxis,:,newaxis]
    n2 = n2[newaxis,:,newaxis]
    p3 = p3[newaxis,newaxis,:]
    n3 = n3[newaxis,newaxis,:]
    dot1 = dotpr(p1,n1)[:,:,:,newaxis]
    dot2 = dotpr(p2,n2)[:,:,:,newaxis]
    dot3 = dotpr(p3,n3)[:,:,:,newaxis]
    cross23 = cross(n2,n3)
    cross31 = cross(n3,n1)
    cross12 = cross(n1,n2)
    denom = dotpr(n1,cross(n2,n3))[:,:,:,newaxis]
    return (dot1*cross23+dot2*cross31+dot3*cross12)/denom


def intersectionLinesPWP(p1,n1,p2,n2):
    """Return the intersection lines of planes (p1,n1) and (p2,n2).

    p1/n1 is a (np1,3) shaped array of points/normals.
    p2/n2 is a (np2,3) shaped array of points/normals.

    The return value is a tuple of (np1,np2,3) shaped arrays of intersection points q
    and vectors m, such that the intersection lines are given by q+t*m.
    """
    if p1.shape != n1.shape:
        raise RuntimeError,"Expected p1 and n1 with same shape."
    if p2.shape != n2.shape:
        raise RuntimeError,"Expected p2 and n2 with same shape."
    p1 = p1[:,newaxis]
    n1 = n1[:,newaxis]
    p2 = p2[newaxis,:]
    n2 = n2[newaxis,:]
    n3 =  cross(n1,n2)
    dot1 = dotpr(p1,n1)[:,:,newaxis]
    dot2 = dotpr(p2,n2)[:,:,newaxis]
    dot3 = dotpr(p1,n3)[:,:,newaxis]
    cross23 = cross(n2,n3)
    cross31 = cross(n3,n1)
    cross12 = cross(n1,n2)
    denom = dotpr(n1,cross(n2,n3))[:,:,newaxis]
    q = (dot1*cross23+dot2*cross31+dot3*cross12)/denom
    return q,n3


def intersectionPointsPOP(q,p,n):
    """Return the intersection points of perpendiculars from points q on planes (p,n).

    This is equivalent to intersectionTimesPWP(q,p,n) but returns a (nq,np,3)
    shaped array of intersection points instead of the parameter values.
    """
    t = intersectionTimesPOP(q,p,n)
    t = t[:,:,newaxis]
    q = q[:,newaxis,:]
    return q + t * n


def intersectionTimesPOP(q,p,n):
    """Return the intersection of perpendiculars from points q on planes (p,n).

    q is (nq,3) shaped array of points.
    p/n is a (np,3) shaped array of points/normals.
    
    The return value is a (nq,np) shaped array of parameter values t,
    such that the intersection points are given by q+t*n.
    """
    if p.shape != n.shape:
        raise RuntimeError,"Expected p and n with same shape."
    I1 = dotpr(p,n)
    I2 = inner(q,n)
    I3 = dotpr(n,n)
    return (I1-I2)/I3


def intersectionPointsPOL(p,q,m):
    """Return the intersection points of perpendiculars from points p on lines (q,m).
    
    This is equivalent to intersectionTimesPWL(p,q,m) but returns a (np,nq,3)
    shaped array of intersection points instead of the parameter values.
    """
    t = intersectionTimesPOL(p,q,m)
    t = t[:,:,newaxis]
    return q + t * m


def intersectionTimesPOL(p,q,m):
    """Return the intersection of perpendiculars from points p on lines (q,m).

    p is (np,3) shaped array of points.
    q/m is a (nq,3) shaped array of points/vectors.

    The return value is a (np,nq) shaped array of parameter values t,
    such that the intersection points are given by q+t*m.
    """
    if q.shape != m.shape:
        raise RuntimeError,"Expected q and m with same shape."
    I1 = inner(p,m)
    I2 = dotpr(q,m)
    I3 = dotpr(m,m)
    return (I1-I2)/I3


################## distance tools ###############

def facetDistance(X,Fp,return_points=False):
    """Compute the closest perpendicular distance of points X to a set of facets.

    X is a (nX,3) shaped array of points.
    Fp is a (nF,nplex,3) shaped array of facet vertices.

    Note that some points may not have a normal with footpoint inside any
    of the facets.

    The return value is a tuple OKpid,OKdist,OKpoints where:
    - OKpid is an array with the point numbers having a normal distance;
    - OKdist is an array with the shortest distances for these points;
    - OKpoints is an array with the closest footpoints for these points
    and is only returned if return_points = True.
    """
    if not Fp.shape[1] == 3:
        raise ValueError, "Currently this function only works for triangular faces."
    # Compute normals on the faces
    Fn = cross(Fp[:,1]-Fp[:,0],Fp[:,2]-Fp[:,1])
    # Compute intersection points of perpendiculars from X on facets F
    Y = intersectionPointsPOP(X,Fp[:,0,:],Fn)
    # Find intersection points Y inside the facets
    inside = insideSimplex(baryCoords(Fp,Y))
    pid = where(inside)[0]
    X = X[pid]
    Y = Y[inside]
    # Compute the distances
    dist = length(X-Y)
    # Get the shortest distances
    OKpid = unique(pid)
    OKdist = array([ dist[pid == i].min() for i in OKpid ])
    if return_points:
        # Get the closest footpoints matching OKpid
        minid = array([ dist[pid == i].argmin() for i in OKpid ])
        OKpoints = array([ Y[pid==i][j] for i,j in zip(OKpid,minid) ]).reshape(-1,3)
        return OKpid,OKdist,OKpoints
    return OKpid,OKdist


def edgeDistance(X,Ep,return_points=False):
    """Compute the closest perpendicular distance of points X to a set of edges.

    X is a (nX,3) shaped array of points.
    Ep is a (nE,2,3) shaped array of edge vertices.

    Note that some points may not have a normal with footpoint inside any
    of the edges.

    The return value is a tuple OKpid,OKdist,OKpoints where:
    - OKpid is an array with the point numbers having a normal distance;
    - OKdist is an array with the shortest distances for these points;
    - OKpoints is an array with the closest footpoints for these points
    and is only returned if return_points = True.
    """
    # Compute vectors along the edges
    En = Ep[:,1] - Ep[:,0]
    # Compute intersection points of perpendiculars from X on edges E
    t = intersectionTimesPOL(X,Ep[:,0],En)
    Y = Ep[:,0] + t[:,:,newaxis] * En
    # Find intersection points Y inside the edges
    inside = (t >= 0.) * (t <= 1.)
    pid = where(inside)[0]
    X = X[pid]
    Y = Y[inside]
    # Compute the distances
    dist = length(X-Y)
    # Get the shortest distances
    OKpid = unique(pid)
    OKdist = array([ dist[pid == i].min() for i in OKpid ])
    if return_points:
        # Get the closest footpoints matching OKpid
        minid = array([ dist[pid == i].argmin() for i in OKpid ])
        OKpoints = array([ Y[pid==i][j] for i,j in zip(OKpid,minid) ]).reshape(-1,3)
        return OKpid,OKdist,OKpoints
    return OKpid,OKdist


def vertexDistance(X,Vp,return_points=False):
    """Compute the closest distance of points X to a set of vertices.

    X is a (nX,3) shaped array of points.
    Vp is a (nV,3) shaped array of vertices.

    The return value is a tuple OKdist,OKpoints where:
    - OKdist is an array with the shortest distances for the points;
    - OKpoints is an array with the closest vertices for the points
    and is only returned if return_points = True.
    """
    # Compute the distances
    dist = length(X[:,newaxis]-Vp)
    # Get the shortest distances
    OKdist = dist.min(-1)
    if return_points:
        # Get the closest points matching X
        minid = dist.argmin(-1)
        OKpoints = Vp[minid]
        return OKdist,OKpoints
    return OKdist,


##########################################

def baryCoords(S,P):
    """Return the barycentric coordinates of points P wrt. simplexes S.
    
    S is a (nel,nplex,3) shaped array of n-simplexes (n=nplex-1) e.g.:
        - 1-simplex: line segment
        - 2-simplex: triangle
        - 3-simplex: tetrahedron
    P is a (npts,nel,3) shaped array of points.
    
    The return value is a (npts,nel,nplex) shaped array of barycentric
    coordinates BC, such that the points P are given by
    (BC[:,:,:,newaxis]*S).sum(-2).
    """
    if S.shape[0] != P.shape[1]:
        raise RuntimeError,"Expected S and P with same number of elements."
    # Make S and P arrays with the same number of dimensions
    S = S.transpose(1,0,2)[:,newaxis] # (nplex,1,nel,3)
    P = P[newaxis] # (1,npts,nel,3)
    # Compute matrices
    vs = S[1:] - S[0:1] # (dim,1,nel,3)
    vp = P - S[0:1] # (1,npts,nel,3)
    A = dotpr(vs[:,newaxis],vs[newaxis,:]) # (dim,dim,1,nel)
    A = repeat(A,P.shape[1],2) # (dim,dim,npts,nel)
    b = dotpr(vs,vp) # (dim,npts,nel)
    # Compute barycentric coordinates        
    t = solveMany(A,b) # (dim,npts,nel)
    t = asarray(t).transpose(1,2,0) # (npts,nel,dim)
    t0 = 1.-t.sum(-1)
    return dstack([t0,t])


def insideSimplex(BC,bound=True):
    """Check if points are in simplexes.
    
    BC is an array of barycentric coordinates, which sum up to one.
    If bound = True, a point lying on the boundary is considered to
    be inside the simplex.
    """
    if bound:
        return (BC >= 0.).all(-1)
    else:
        return (BC > 0.).all(-1)



# End

