#!/usr/bin/env python
"""Formex algebra in python"""

import copy

class Formex:
    """A formex is a list of cantles; a cantle is a list of signets;
    a signets is a list of uniples.
    """

    def __init__(self,l=[[[]]]):
        self.f = l

    def order(self):
        """Return the order of the Formex

        The order is the number of elements in the Formex.
        """
        return len(self.f)

    def plexitude(self,i=0):
        """Return the plexitude of the i'th cantle in the Formex

        The plexitude is the number of number of nodes in the cantle.
        2 = bar, 3 = triangle, 4= qudrilateral, etc.
        """
        return len(self.f[i])

    def grade(self,i,j):
        """Return the grade of signet j of cantle i in the Formex.

        The grade is the number of dimensions of the signet.
        2 = 2D, 3 = 3D.
        """
        return len(self.f[i][j])

    def formex(self):
        """Return the formex as a list"""
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
    
    def __str__(self):
        """String representation of a formex"""
        s = "{"
        if len(self.f):
            s += self.cantle2str(self.f[0])
            for i in self.f:
                s += ","
                s += self.cantle2str(i)
        return s+"}"
                
    def repr(self):
        return repr(self.f)

    def copy(self):
        """Returns a deep copy of itself"""
        return Formex(copy.deepcopy(self.f))

    def append(self,F):
        """Append the members of formex F to this one

        This function changes the original one! Use __add__ if you want to
        get a copy with the sum"""
        self.f += F.f
        return self

    def __add__(self,other):
        """Return the sum of two formices"""
        return self.copy().append(other)

    def bbox(self):
        """Return the boundary box of the Formex"""
        min = copy.copy(self.f[0][0])
        max = copy.copy(min)
        for cantle in self.f:
            for signet in cantle:
                for i,sig in enumerate(signet):
                    if sig < min[i]:
                        min[i] = sig
                    if sig > max[i]:
                        max[i] = sig
        return [min, max] 
        

    def translate(self,dir,dist):
        """Returns a copy translated in direction dir over distance dist"""
        formex = copy.deepcopy(self.f)
        for cantle in formex:
            for signet in cantle:
                signet[dir] += dist
        return Formex(formex)

    def reflect(self,dir,pos):
        """Returns a formex mirrored in direction dir against plane at pos"""
        formex = copy.deepcopy(self.f)
        for cantle in formex:
            for signet in cantle:
                signet[dir] = 2*pos - signet[dir]
        return Formex(formex)

    def reflectAdd(self,dir,pos):
        """Return the sum of original plus reflection"""
        return self + self.reflect(dir,pos)

    def rindle(self,dir,n,step):
        """Returns a formex with n replications in direction dir with step.

        The original formex is the first of the n replicas."""
        F = self.copy()
        for i in range(1,n):
            Fi = self.translate(dir,i*step)
            F.append(Fi)
        return F
 
    def rosette(self,plane,point,dir,n,step):
        """Returns a formex with n rotational replications in plane around point with angular step.

        The original formex is the first of the n replicas."""
        F = self.copy()
        for i in range(1,n):
            Fi = self.rotate(dir,i*step)
            F.append(Fi)
        return F


# Compatibility functions # deprecated !

    def tran(self,dir,dist):
        return self.translate(dir-1,dist)
    
    def ref(self,dir,dist):
        return self.reflect(dir-1,dist)

    def rin(self,dir,n,dist):
        return self.rindle(dir-1,n,dist)

    def lam(self,dir,dist):
        return self.reflectAdd(dir-1,dist)


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
