#!/usr/bin/env python
"""Formex algebra in python"""

from numarray import *
import math

class Formex:
    """A formex is a numarray of order 3. An element is a uniple. A row along the axis 2 is a signet. A plane along axes 2 and 1 is a cantle.
    """

    def __init__(self,l=[[[]]]):
        self.f = array(l,type=Float32)
        if len(self.f.shape) != 3:
            raise RuntimeError,"Invalid data in creating Formex"

    def order(self):
        """Return the order of the Formex

        The order is the number of elements in the Formex.
        """
        return self.f.shape[0]

    def plexitude(self):
        """Return the plexitude of the Formex

        The plexitude is the number of number of nodes in the cantle.
        2 = bar, 3 = triangle, 4= qudrilateral, etc.
        """
        return self.f.shape[1]

    def grade(self):
        """Return the grade of the Formex.

        The grade is the number of dimensions of the signet.
        2 = 2D, 3 = 3D.
        """
        return self.f.shape[2]

    def formex(self):
        """Return the formex as a numarray"""
        return self.f

    def cantle(self,i):
        """Return cantle i of the formex"""
        return self.f[i]

    def signet(self,i,j):
        """Return signet j of cantle i"""
        return self.f[i][j]

    def uniple(self,i,j,k):
        """Return uniple k of signet j of canlte i"""
        return self.f[i][j][k]

    def signet2str(self,sig):
        s = ""
        if len(sig):
            s +=  str(sig[0])
            for i in sig[1:]:
                s += ","
                s += str(i)
        return s

    def cantle2str(self,can):
        s = "["
        if len(can):
            s += self.signet2str(can[0])
            for i in can[1:]:
                s += ";"
                s += self.signet2str(i)
        return s+"]"
    
    def asFormex(self):
        """String representation of a formex as in Formian"""
        s = "{"
        if len(self.f):
            s += self.cantle2str(self.f[0])
            for i in self.f:
                s += ","
                s += self.cantle2str(i)
        return s+"}"
                
    def asArray(self):
        return self.f.__str__()

    __str__ = asFormex

    def copy(self):
        """Returns a deep copy of itself"""
        return Formex(self.f)

    def append(self,F):
        """Append the members of formex F to this one

        This function changes the original one! Use __add__ if you want to
        get a copy with the sum"""
        self.f = concatenate((self.f,F.f))
        return self

    def __add__(self,other):
        """Return the sum of two formices"""
        return self.copy().append(other)

    def concatenate(self,list):
        """Concatenate all formices in list.

        This is a class method, not an instance method!
        """
        return Formex( concatenate([a.f for a in list]) )


    def bbox(self):
        """Return the boundary box of the Formex"""
        min = [ self.f[:,:,i].min() for i in range(self.f.shape[2]) ]
        max = [ self.f[:,:,i].max() for i in range(self.f.shape[2]) ]
        return [min, max] 

    def center(self):
        """Return the center of the Formex"""
        min,max = self.bbox()
        return [ (min[i]+max[i])/2 for i in range(self.grade()) ]

    def translationVector(self,dir,dist):
        """Returns a translation vector in direction dir over distance dist"""
        f = zeros((self.grade()),type=Float32)
        f[dir] = dist
        return f

    def rotationMatrix(self,angle,axis=2):
        """Returns a rotation matrix over angle around axis.

        If grade=2, a 2x2 matrix is returned and axis is always 2.
        If grade is 3, a 3x3 matrix is returned, and default axis is 2.
        """
        n = self.grade()
        a = math.radians(angle)
        c = math.cos(a)
        s = math.sin(a)
        if n == 2:
            f = array([[c,s],[-s,c]],type=Float32)
        elif n == 3:
            axes = range(3)
            i,j,k = axes[axis:]+axes[:axis]
            f = zeros((n,n),type=Float32)
            f[i,i] = 1.0
            f[j,j] = c
            f[j,k] = s
            f[k,j] = -s
            f[k,k] = c
        return f

    def translate1(self,dir,dist):
        """Returns a copy translated in direction dir over distance dist"""
        f = self.f.copy()
        f[:,:,dir] += dist
        return Formex(f)

    def translate(self,dist):
        """Returns a copy translated over distance dist.

        It is acceptable to specify a dist of grade 3 for a formex of grade2.
        Only the first two values will be used"""
        if self.grade() == 2:
            dist = dist[:2]
        return Formex(self.f + dist)

    def rotate(self,angle,axis=2):
        """Returns a copy rotated over distance dist of matching grade."""
        m = self.rotationMatrix(angle,axis)
        return Formex(matrixmultiply(self.f,m))

    def scale(self,scale):
        """Returns a copy scaled with scale[i] in direction i"""
        if self.grade() == 2:
            scale = scale[:2]
        return Formex(self.f*scale)

    def reflect(self,dir,pos):
        """Returns a formex mirrored in direction dir against plane at pos"""
        f = self.f.copy()
        f[:,:,dir] = 2*pos - f[:,:,dir]
        return Formex(f)

    def reflectAdd(self,dir,pos):
        """Return the sum of original plus reflection"""
        return self + self.reflect(dir,pos)

    def rindle(self,n,dir,step):
        """Returns a formex with n replications in direction dir with step.

        The original formex is the first of the n replicas."""
        f = array( [ self.f for i in range(n) ] )
        for i in range(1,n):
            f[i,:,:,dir] += i*step
        f.shape = (f.shape[0]*f.shape[1],f.shape[2],f.shape[3])
        return Formex(f)
 
    def rosette(self,n,axis,point,angle):
        """Returns a formex with n rotational replications around axis through point with angular step angle.

        axis is the number of the axis (0,1,2).
        point must have same grade as formex.
        The original formex is the first of the n replicas."""
        f = self.f - point
        f = array( [ f for i in range(n) ] )
        for i in range(1,n):
            m = self.rotationMatrix(i*angle,axis)
            f[i] = matrixmultiply(f[i],m)
        f.shape = (f.shape[0]*f.shape[1],f.shape[2],f.shape[3])
        return Formex(f + point)
        

 
    # Compatibility functions # deprecated !
        
    def give():
        print self.toFormian()

    def tran(self,dir,dist):
        return self.translate1(dir-1,dist)
    
    def ref(self,dir,dist):
        return self.reflect(dir-1,dist)

    def rin(self,dir,n,dist):
        return self.rindle(n,dir-1,dist)

    def lam(self,dir,dist):
        return self.reflectAdd(dir-1,dist)

    def ros(self,i,j,x,y,n,angle):
        if self.grade() == 2:
            return self.rosette(n,2,[x,y],angle)
        elif (i,j) == (1,2):
            return self.rosette(n,2,[x,y,0],angle)
        elif (i,j) == (2,3):
            return self.rosette(n,0,[0,x,y],angle)
        elif (i,j) == (1,3):
            return self.rosette(n,1,[x,0,y],-angle)

    def tranid(self,t1,t2):
        return self.translate([t1,t2,0])
    def tranis(self,t1,t2):
        return self.translate([t1,0,t2])
    def tranit(self,t1,t2):
        return self.translate([0,t1,t2])
    
    def rinid(self,n1,n2,t1,t2):
        return self.rin(1,n1,t1).rin(2,n2,t2)
    def rinis(self,n1,n2,t1,t2):
        return self.rin(1,n1,t1).rin(3,n2,t2)
    def rinit(self,n1,n2,t1,t2):
        return self.rin(2,n1,t1).rin(3,n2,t2)

    def lamid(self,t1,t2):
        return self.lam(1,t1).lam(2,t2)
    def lamis(self,t1,t2):
        return self.lam(1,t1).lam(3,t2)
    def lamit(self,t1,t2):
        return self.lam(2,t1).lam(2,t2)

    def genid(self,n1,n2,t1,t2,bias,taper):
        P = [ self.translate([i*bias,i*t2,0]).rin(1,n1+i*taper,t1)
              for i in range(n2) ]
        return self.concatenate(P)

    def bb(self,b1,b2):
        return self.scale([b1,b2,0])

    def bp(self,b1,b2):
        f = copy.deepcopy(self.f)
        a = b1*f[:,:,0]
        b = math.radians(b2)*f[:,:,1]
        f[:,:,0] = a*cos(b)
        f[:,:,1] = a*sin(b)
        return Formex(f)

    def bs(self,b1,b2):
        f = copy.deepcopy(self.f)
        r = b1*f[:,:,0]
        s = math.radians(b2)*f[:,:,1]
        t = math.radians(b3)*f[:,:,2]
        rc = r*cos(t)
        f[:,:,0] = rc*cos(s)
        f[:,:,1] = rc*sin(s)
        f[:,:,2] = r*sin(t)
        return Formex(f)
    
def test():
    print "This is a test of formex algebra"
    F = Formex([[[1,0],[0,1]],[[0,1],[1,2]]])
    print "F =",F
    F1 = F.tran(1,6)
    print "F1 =",F1
    F2 = F.ref(1,2)
    print "F2 =",F2
    F3 = F.ref(1,1.5).tran(2,2)
    print "F3 =",F3
    H = F.rin(1,4,2)
    print "H =",H
    R = F.lam(1,1)
    print "R =",R
    G = F.lam(1,1).lam(2,1).rin(1,10,2).rin(2,6,2)
    print "G =",G


#### Test
if __name__ == "__main__":
    test()

#### End
