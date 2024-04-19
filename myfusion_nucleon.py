from math import pi,sin,cos
from ctypes import Structure,c_float,c_bool
import glm


class NucleonC(Structure):
    _fields_ = [
        ("pos", c_float*4),
        ("v", c_float*4),
        ("type", c_float),
        ("r", c_float),
        ("m", c_float),
        ("_pad1", c_float),
        ("rot", c_float*4),
        ("rotv", c_float*4),
        ("animate", c_float),
        ("q",  c_float),
        ("_pad2", c_float*2),
        ("color", c_float*4),
        ]
    def to_ctypes(self, a):
        self.pos[0:3]= a.pos.to_list()
        self.pos[3]= 0
        self.v[0:3]= a.v.to_list()
        self.v[3]= 0
        self.type = a.type
        self.r = a.r
        self.m = a.m
        self.rot[0]= a.rot.x
        self.rot[1]= a.rot.y
        self.rot[2]= a.rot.z
        self.rot[3]= a.rot.w
        self.rotv[0]= a.rotv.x
        self.rotv[1]= a.rotv.y
        self.rotv[2]= a.rotv.z
        self.rotv[3]= a.rotv.w
        self.animate = 0.0
        self.q = a.q
        self.color[0:3]= a.color
        self.color[3]= 1.0

    def from_ctypes(self,a):
        a.pos = glm.vec3(self.pos[0:3])
        a.v = glm.vec3(self.v[0:3])
        a.rot.x = self.rot[0]
        a.rot.y = self.rot[1]
        a.rot.z = self.rot[2]
        a.rot.w = self.rot[3]
        a.rotv.x = self.rotv[0]
        a.rotv.y = self.rotv[1]
        a.rotv.z = self.rotv[2]
        a.rotv.w = self.rotv[3]


class Nucleon():
    id = 0
    def __init__(self,x,y,z, type=1,fixed=False):
        Nucleon.id += 1
        self.id = Nucleon.id
        self.YSHIFT = 0
        self.pos = glm.vec3(x,y,z)
        self.v = glm.vec3(0,0,0)
        self.a = glm.vec3(0,0,0)
        self.vf = 0.0
        self.vf2 = 0.0
        self.type = type
        self.fixed = fixed
        self.near = []
        self.rot = glm.quat()
        self.rotv = glm.quat()
        if self.type==1:
            self.color = (1.0,0.0,0.0)
            self.r=10
            self.m=1
            self.q=1.0
        if self.type==2 :
            self.color = (0.0,0.0,1.0)
            self.r=10
            self.m=1
            self.q=0.0
        if self.type==100 :
            self.color = (1.0,0.0,1.0)
            self.q = 0.0
            self.m = 100
            self.r = 30



            
