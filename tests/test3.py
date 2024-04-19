import random
from re import S
import sys, os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from myfusion import myfusionApp, Nucleon
from math import pi 
import myfusion
from math import *
import glm


# tritium + deuterium = helium-4 + neutron
def action1(space):
    (x,y,z)=(500,500,500)  
    if space.t == 1:
        n1 = space.merge_from_file("examples/standard/tritium.json", 500,500,500)
        space.nucleons[n1].v = glm.vec3(1.0,0.0,0.0)
        space.nucleons[n1+1].v = glm.vec3(1.0,0.0,0.0)
        space.nucleons[n1+2].v = glm.vec3(1.0,0.0,0.0)

        n2 = space.merge_from_file("examples/standard/deuterium.json", 800,500,500)
        #space.nucleons[n2].v = glm.vec3(-1.0,0.0,0.0)
        #space.nucleons[n2+1].v = glm.vec3(-1.0,0.0,0.0)


        space.nucleons2compute() 


if __name__ == '__main__':
#


    random.seed(1)
    App = myfusionApp()
    space = App.space
    space.setSize(1500,1000,1000)

    space.action = action1 

    space.ATTRACT_KOEFF= 0.03
    space.INTERACT_KOEFF= 1.5
    space.REPULSION_KOEFF1= 1.0
    space.softbox.set(False)

    App.run()

# 4.2 fps and drop
# 3.25 fps
# 1000 delta5, 0,88 