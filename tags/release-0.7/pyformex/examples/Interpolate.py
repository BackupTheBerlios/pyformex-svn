#!/usr/bin/env python pyformex.py
# $Id$
   

def demo_interpolate():
    clear()
    a = Formex([[[0,0,0],[1,0,0]],[[1,0,0],[2,0,0]]])
    b = Formex([[[0,1,0],[1,1,0]],[[1,1,0],[2,1,0]]])
    message("Two lines")
    draw(a+b)

    n = 10
    v = 1./n * arange(n+1)
    p = arange(n)
    
    c = interpolate(a,b,v)
    c.setProp(p)
    message("Interpolate between the two")
    draw(c)
    drawNumbers(c)

    sleep(2)
    d = interpolate(a,b,v,swap=True)
    d.setProp(p)
    clear()
    message("Interpolate again with swapped order")
    draw(d)
    drawNumbers(d)
    exit()

    sleep(2)
    f = c.divide(v)
    f.setProp((1,2))
    clear()
    message("Divide the set of lines")
    draw(f)

if __name__ == "draw":
    wireframe()
    demo_interpolate()
    
