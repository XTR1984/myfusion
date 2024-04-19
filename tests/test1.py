import random
from re import S
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from myfusion import myfusionApp, Nucleon
from math import pi 
import myfusion
from math import *
import glm

if __name__ == '__main__':
#
    random.seed(1)
    App = myfusionApp()
    space = App.space
    space.setSize(2000,2000,2000)

    for i in range(0,10000):
        x = random.randint(0,space.WIDTH)
        y = random.randint(0,space.HEIGHT)
        z = random.randint(0,space.DEPTH)           
        n = Nucleon(x,y,z)
        vx = random.random()-0.5
        vy = random.random()-0.5
        vz = random.random()-0.5
        n.v = glm.vec3(vx,vy,vz)
        space.appendnucleon(n)
        x = random.randint(0,space.WIDTH)
        y = random.randint(0,space.HEIGHT)
        z = random.randint(0,space.DEPTH)           
        vx = random.random()-0.5
        vy = random.random()-0.5
        vz = random.random()-0.5
        n = Nucleon(x,y,z,2)
        n.v = glm.vec3(vx,vy,vz)
        space.appendnucleon(n)

    space.ATTRACT_KOEFF= 2.0
    space.INTERACT_KOEFF= 1.0
    space.REPULSION_KOEFF1= 30.0
    space.MASS_KOEFF = 5

    App.run()

# 4.2 fps and drop
# 3.25 fps
# 1000 delta5, 0,88 