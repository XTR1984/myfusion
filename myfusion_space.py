import os
import json
from math import sqrt,sin,cos,pi,acos
import numpy as np
import random
from myfusion_nucleon import Nucleon
import glm
import tkinter as tk
import time

class Space:
    def __init__(self,width=1500,height=1000,depth=1000):
        self.gpu_compute =tk.BooleanVar()
        self.gpu_compute.set(True)
        self.pause = False
        self.ucounter = 0
        self.setSize(width,height,depth)
        self.debug = False
        self.nucleonRADIUS = 10
        self.BOND_KOEFF = 0.2
        self.BONDR = 4.0
        self.INTERACT_KOEFF= 1.0
        self.ROTA_KOEFF = 10
        self.REPULSION1 = -3
        self.REPULSION_KOEFF1 = 7
        self.ATTRACTIOND = 1
        self.ATTRACT_KOEFF= 1.0
        self.MASS_KOEFF = 5.0
        self.MAXVELOCITY = 1.0
        self.NEARDIST = 200.0   # near nucleons buffering
        self.heat = 0.0
        self.atype=1
        self.t = -1
        self.stoptime = -1
        self.recordtime = 0
        self.recording = tk.BooleanVar()
        self.recording.set(False)
        self.nucleons = []	
        self.g = 0.001
        self.newnucleon = None
        self.createtype=4
        self.createf = 0
        self.standard = True
        self.merge_nucleons = []
        self.merge_rot = glm.quat()
        self.merge_center = glm.vec3(0,0,0)
        self.select_mode = 0
        self.selected_nucleons = [] 
        self.gravity = tk.BooleanVar()
        self.gravity.set(False)
        self.shake= tk.BooleanVar()
        self.shake.set(False)
        self.softbox = tk.BooleanVar()
        self.softbox.set(False)
        self.SHAKE_KOEFF = 0.5
        self.competitive = True
        self.linear_field = False
        self.update_delta= 5
        self.show_q = False
        self.action = None
        self.fdata = open('data.txt',"w")

    def setSize(self, width,height,depth):
        self.WIDTH=width
        self.HEIGHT=height
        self.DEPTH=depth
        self.box = glm.vec3(self.WIDTH, self.HEIGHT, self.DEPTH)
        print("box size =  ",self.box)
        self.merge_pos = self.box/2


    def appendnucleon(self,a):
        a.space = self
        self.nucleons.append(a)

    def appendmixer(self,n=1):
        for i in range(0,n):
            m = Nucleon(random.randint(1,self.WIDTH),random.randint(1,self.HEIGHT),random.randint(1,self.DEPTH),100)
            m.space = self
            m.v = glm.vec3(random.random(),random.random(),random.random())
            self.nucleons.append(m)
    


    def get_mergeobject_center(self):
         sum = glm.vec3(0,0,0)
         N = len(self.merge_nucleons)
         for a in self.merge_nucleons:
              sum += a.pos
         center = sum/N
         #print("center=",center)
         return center


    def get_nucleons_center(self, nucleons=None):
         if nucleons==None:
            nucleons = self.nucleons
         sum = glm.vec3(0,0,0)
         N = len(nucleons)
         for a in nucleons:
              sum += a.pos
         center = sum/N
         return center


    def selected2merge(self):
        for i in self.selected_nucleons:
                a = self.nucleons[i]
                self.merge_nucleons.append(a)
                #a.unbond()  
        for m in self.merge_nucleons:
            self.nucleons.remove(m)
        self.selected_nucleons = []
        self.merge_rot = glm.quat()
        self.merge_center = self.get_mergeobject_center()
        self.merge_pos = glm.vec3(self.merge_center)


    def get_nucleons_distant(self,nucleons=None):
         if nucleons==None:
              nucleons = self.nucleons
         center = self.get_nucleons_center(nucleons)
         distant = glm.vec3(0,0,0)
         N = len(nucleons)
         for a in nucleons:
              if abs(a.pos.x-center.x) > distant.x:
                   distant.x = a.pos.x-center.x
              if abs(a.pos.y-center.y) > distant.y:
                   distant.y = a.pos.y-center.y
              if abs(a.pos.z-center.z) > distant.z:
                   distant.z = a.pos.z-center.z
         return (center,distant)

        

    def nucleons2compute(self):
        t = time.time()
        print("nucleons2compute gpu")
        self.glframe.nucleons2ssbo()
        delta = time.time() - t
        print("  delta=", delta)            

    
    def compute2nucleons(self):
        t = time.time()
        print("compute2nucleons gpu")
        self.glframe.ssbo2nucleons()
        delta = time.time() - t
        print("  delta=", delta)     

    def merge2nucleons(self):
        #self.compute2nucleons()
        N = len(self.nucleons)
        self.merge_center = self.get_mergeobject_center()
        for a in self.merge_nucleons:
            pos = a.pos.xyz
            pos -= self.merge_center
            pos = self.merge_rot * pos
            pos += self.merge_pos
            a.pos = pos.xyz
            a.rot = glm.normalize(self.merge_rot * a.rot)
            self.appendnucleon(a)
        self.merge_nucleons = []
        return N
        #self.nucleons2compute()


    def merge_from_file(self, filename, x=0,y=0,z=0, merge_rot=glm.quat()):
        f =  open(filename,"r")		
        self.merge_nucleons = []
        mergedata = json.loads(f.read())
        self.load_data(mergedata, merge=True)
        self.merge_pos = glm.vec3(x,y,z)
        self.merge_rot = merge_rot
        first = self.merge2nucleons()
        self.merge_pos = self.box/2
        self.merge_rot = glm.quat()
        return first
    
    
   

    def make_export(self, nucleons=None):
        if nucleons==None:
            nucleons=self.nucleons
        frame = {}
        frame["vers"] = "1.0"
        frame["time"] = self.t
        frame["nucleons"] = []
        N = len(nucleons)
        for i in range(0,N):
            if nucleons[i].color == (0,0,0): continue    #spec color for remove nucleons on save
            nucleon = {}
            nucleon["id"] = nucleons[i].id
            nucleon["type"] = nucleons[i].type
            nucleon["x"] = round(nucleons[i].pos.x,4)
            nucleon["y"] = round(nucleons[i].pos.y,4)
            nucleon["z"] = round(nucleons[i].pos.z,4)
            #nucleon["f"] = round(self.nucleons[i].f,4)
            #nucleon["f2"] = round(self.nucleons[i].f2,4)
            nucleon["rot"] = nucleons[i].rot.to_tuple()
            nucleon["vx"] = round(nucleons[i].v.x,4)
            nucleon["vy"] = round(nucleons[i].v.y,4)
            nucleon["vz"] = round(nucleons[i].v.z,4)
            nucleon["q"] = nucleons[i].q
            nucleon["m"] = nucleons[i].m
            nucleon["r"] = nucleons[i].r
            frame["nucleons"].append(nucleon)
        return frame

    def load_data(self, j, merge=False, zerospeed=True):
        if not merge: 
            self.nucleons = []
        for a in j["nucleons"]:
            type = a["type"]
            #if type==100: continue
            if "z" in a:
                z = a["z"]
                vz = a["vz"]
                rot = glm.quat(a["rot"])
            else:
                z = 500
                vz = 0
                if type==4: type=400
                if type==2: type=200
                if type==5: type=500
                if type==6: type=600
                rot = glm.quat(glm.vec3(0,0,-a["f"]))
            aa = Nucleon(a["x"],a["y"],z, type=type )
            aa.r=a["r"]
            if zerospeed and type!=100:
                aa.v= glm.vec3(0,0,0) 
            else:
                aa.v = glm.vec3(a["vx"],a["vy"],vz)
            aa.rot = rot
            aa.q=a["q"]
            aa.m=a["m"]
#            if not "version" in j:
#                 aa.f= 2*pi - aa.f
            ni = 0
            if merge:
                aa.space = self
                self.merge_nucleons.append(aa)
            else:
                self.appendnucleon(aa)



