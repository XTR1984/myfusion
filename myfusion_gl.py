import OpenGL.GL as gl
import OpenGL.GL.shaders
#import glfw
import ctypes
from pyopengltk import OpenGLFrame
import numpy as np
import glm
import random
from PIL import Image
from math import sin,cos,sqrt,pi
import time
from myfusion_functions import make_sphere_vert,make_cube2
from myfusion_data import cube_vertices
from myfusion_nucleon import NucleonC
from array import array
from mesh import Mesh

class AppOgl(OpenGLFrame):
    def set_space(self,space):
        self.space = space
    def initgl(self):
        """Initalize gl states when the frame is created"""
        print("init gl")
        gl.glViewport(0, 0, self.width, self.height)
        gl.glClearColor(0.3, 0.3, 0.3, 0.0)
        gl.glEnable(gl.GL_DEPTH_TEST)
        #gl.glEnable(gl.GL_CULL_FACE);
        #gl.glCullFace(gl.GL_FRONT); 
        #gl.glFrontFace(gl.GL_CW) 
        #gl.glEnable(gl.GL_DEBUG_OUTPUT)
        #gl.glEnable(gl.GL_CULL_FACE); 
        #gl.glEnable(gl.GL_FRAMEBUFFER_SRGB);
        #gl.glEnable(gl.GL_DEPTH_TEST)
        #gl.glEnable (gl.GL_LINE_SMOOTH);    
        #gl.glfwWindowHint(gl.GLFW_SAMPLES, 4);
        #gl.glEnable(gl.GL_MULTISAMPLE); 
        self.nearnucleonsmax = 5000
        self.LOCALSIZEX = 64
        self.nearflag = False

        vertex_shader = open("shaders/nucleon_vertex1.glsl","r").read()
        fragment_shader = open("shaders/nucleon_frag1.glsl","r").read()
        compute_shader = open("shaders/compute.glsl","r").read()
        compute_shader = compute_shader.replace("NEARnucleonSMAX",str(self.nearnucleonsmax))
        compute_shader = compute_shader.replace("LOCALSIZEX",str(self.LOCALSIZEX))
        compute_shader = compute_shader.replace("MAXVEL",str(self.space.MAXVELOCITY))
#        geom_shader = open("shaders/nucleon_geom1.glsl","r").read()

        self.shader = OpenGL.GL.shaders.compileProgram(
            OpenGL.GL.shaders.compileShader(vertex_shader, gl.GL_VERTEX_SHADER),
#            OpenGL.GL.shaders.compileShader(geom_shader, gl.GL_GEOMETRY_SHADER),
            OpenGL.GL.shaders.compileShader(fragment_shader, gl.GL_FRAGMENT_SHADER),validate=False
        )
        
        OpenGL.GL.shaders.compileShader(compute_shader, gl.GL_COMPUTE_SHADER)
        self.compute_shader = gl.glCreateShader(gl.GL_COMPUTE_SHADER)
        gl.glShaderSource(self.compute_shader, compute_shader)
        gl.glCompileShader(self.compute_shader)
        
        self.gpu_code = gl.glCreateProgram()
        gl.glAttachShader(self.gpu_code, self.compute_shader)
        gl.glLinkProgram(self.gpu_code)
   
        self.cameraUp = glm.vec3(0,1,0)
        self.cameraFront = glm.vec3(0.5,0.5,-1)
        self.cameraPos = glm.vec3(0.5,0.5,2)
        #self.cameraPos = glm.vec3(0.5,0.5,0.5)
        self.cameraTarget = glm.vec3(0.5,0.5,0.5)

        #self.cameraDirection = glm.normalize(self.cameraPos - self.cameraTarget)
        self.keypressed = []
        self.lastframe_time= time.time()
        self.lastX = 500
        self.lastY = 300
        self.yaw = -90
        self.pitch = 0 
        self.fov = 45
        self.light_pos = glm.vec3(1.2,1.0,2.0)

        self.factor = 0.001
        self.curpos = glm.vec3(0.,0.,0.)
        self.sphere_vertices = np.array(make_sphere_vert(1,20), dtype=np.float32)
        self.sphere_vertices2 = np.array(make_sphere_vert(1,5), dtype=np.float32)
        self.cube_vertices = np.array(make_cube2(), dtype=np.float32)
        #np.array(make_cube2(), dtype=np.float32)
        #cameraRight = glm.normalize(glm.cross(up, cameraDirection))
        #cameraUp = glm.cross(cameraDirection, cameraRight)
        self.create_objects()
        print("objects created")
        #self.space.nucleons2compute()
        self.start = time.time()
        self.nframes = 0          
        self.rframes = 0
        self.initok = True
        
    

    def nucleons2ssbo(self):
        self.N = len(self.space.nucleons)
        print(f"  nucleons2ssbo N={self.N}")
        ac = NucleonC()
        if self.N>0:
            a_data = bytearray()
            for a in self.space.nucleons:
                ac.to_ctypes(a)
                abytearray =  bytearray(ac)               
                a_data += abytearray
        else:
            a_data = bytearray()
        datasize = len(a_data)
        a_data = np.array(a_data,dtype=np.byte)
        print(f"  buffer size={datasize}")
        self.nucleons_buffer = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.nucleons_buffer)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, self.nucleons_buffer);
       
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, datasize, a_data , gl.GL_DYNAMIC_DRAW);
        self.nucleons_buffer2 = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.nucleons_buffer2)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, self.nucleons_buffer2);
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, datasize, None , gl.GL_DYNAMIC_DRAW);
    
        #nearbuffer
        self.near_buffer = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.near_buffer)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 2, self.near_buffer);
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, self.N*4*(self.nearnucleonsmax+1), None , gl.GL_DYNAMIC_DRAW);
        self.nearflag = True    

        #far field buffer
        self.far_buffer = gl.glGenBuffers(1)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.far_buffer)
        gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 3, self.far_buffer);
        gl.glBufferData(gl.GL_SHADER_STORAGE_BUFFER, self.N*4, None , gl.GL_DYNAMIC_DRAW);


    def ssbo2nucleons(self):
        self.N = len(self.space.nucleons)
        print(f"  ssbo2nucleons N={self.N}")
        asize = ctypes.sizeof(NucleonC)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, self.nucleons_buffer)
        a_data8 = gl.glGetBufferSubData(gl.GL_SHADER_STORAGE_BUFFER, 0, self.N*asize)
        print("  getbuffersubdata size=", self.N*asize)
        gl.glBindBuffer(gl.GL_SHADER_STORAGE_BUFFER, 0)
        offset = 0
        for i in range(0,self.N):
            a = self.space.nucleons[i]
            abytearray = a_data8[offset:offset+ctypes.sizeof(NucleonC)]
            ac = NucleonC.from_buffer(abytearray)
            ac.from_ctypes(a)
            offset+= ctypes.sizeof(NucleonC)




    def init_loc(self):
            self.loc = {}
            self.loc.update( {"stage": gl.glGetUniformLocation(self.gpu_code, "stage")})
            self.loc.update( {"box": gl.glGetUniformLocation(self.gpu_code, "box")})
            self.loc.update( {"iTime": gl.glGetUniformLocation(self.gpu_code, "iTime")})
            self.loc.update( {"gravity": gl.glGetUniformLocation(self.gpu_code, "gravity") })
            self.loc.update( {"shake": gl.glGetUniformLocation(self.gpu_code, "shake") })
            self.loc.update( {"atype": gl.glGetUniformLocation(self.gpu_code, "atype") })
            self.loc.update( {"softbox": gl.glGetUniformLocation(self.gpu_code, "softbox") })
            self.loc.update( {"BOND_KOEFF": gl.glGetUniformLocation(self.gpu_code, "BOND_KOEFF") })
            self.loc.update( {"INTERACT_KOEFF": gl.glGetUniformLocation(self.gpu_code, "INTERACT_KOEFF") })
            self.loc.update( {"REPULSION_KOEFF1": gl.glGetUniformLocation(self.gpu_code, "REPULSION_KOEFF1") })
            self.loc.update( {"ATTRACT_KOEFF": gl.glGetUniformLocation(self.gpu_code, "ATTRACT_KOEFF") })
            self.loc.update( {"ROTA_KOEFF": gl.glGetUniformLocation(self.gpu_code, "ROTA_KOEFF") })
            self.loc.update( {"MASS_KOEFF": gl.glGetUniformLocation(self.gpu_code, "MASS_KOEFF") })
            self.loc.update( {"NEARDIST": gl.glGetUniformLocation(self.gpu_code, "NEARDIST") })
            self.loc.update( {"HEAT": gl.glGetUniformLocation(self.gpu_code, "HEAT") })
            #view_loc = gl.glGetUniformLocation(self.shader, "view")
            #proj_loc = gl.glGetUniformLocation(self.shader, "projection")
            #mode_loc = gl.glGetUniformLocation(self.shader, "mode")
            self.loc.update( {"view": gl.glGetUniformLocation(self.shader, "view") })
            self.loc.update( {"projection": gl.glGetUniformLocation(self.shader, "projection") })
            self.loc.update( {"mode": gl.glGetUniformLocation(self.shader, "mode") })
            self.loc.update( {"lightPos": gl.glGetUniformLocation(self.shader, "lightPos") })
            


    def create_objects(self):
        print("create objects start")
        self.nucleonMesh = Mesh(self.sphere_vertices)
        self.nucleonMesh.setup()
        self.containerMesh = Mesh(self.cube_vertices)
        self.containerMesh.setup()
        model =  glm.mat4()
        model =  glm.scale(model,self.space.box/glm.vec3(1/self.factor))
        model =  glm.scale(model, glm.vec3(0.5,0.5,0.5))
        model =  glm.translate(model, glm.vec3(1, 1, 1))

        self.containerMesh.color = (1,1,1)
        self.containerMesh.modelmatrix = model

        self.init_loc()

    def updateContainerSize(self):
        if not self.containerMesh: return
        model =  glm.mat4()
        model =  glm.scale(model,self.space.box/glm.vec3(1/self.factor))
        model =  glm.scale(model, glm.vec3(0.5,0.5,0.5))
        model =  glm.translate(model, glm.vec3(1, 1, 1))
        self.containerMesh.modelmatrix = model

    def render(self):
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT )
       
        gl.glUseProgram(self.shader)
        front = ( cos(glm.radians(self.pitch))*cos(glm.radians(self.yaw)),
                 sin(glm.radians(self.pitch)),
                 cos(glm.radians(self.pitch))*sin(glm.radians(self.yaw)),
                )
        self.cameraFront = glm.normalize(front)
        self.view = glm.lookAt(self.cameraPos, self.cameraPos + self.cameraFront, self.cameraUp)
        self.projection = glm.perspective(glm.radians(self.fov), self.width/self.height, 0.01,20.0)
        gl.glUniformMatrix4fv(self.loc["view"],1, gl.GL_FALSE, glm.value_ptr(self.view))
        gl.glUniformMatrix4fv(self.loc["projection"],1, gl.GL_FALSE, glm.value_ptr(self.projection))
        gl.glUniform3f(self.loc["lightPos"],self.cameraPos.x+self.view[0,0]+self.view[0,1],
                                            self.cameraPos.y+self.view[1,0]+self.view[1,1],
                                            self.cameraPos.z+self.view[2,0]+self.view[2,1])


        #render merge_nucleon
        if len(self.space.merge_nucleons)>0:
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE)
            for a in self.space.merge_nucleons:
                pos = glm.vec3(a.pos)
                pos -= self.space.merge_center
                pos = self.space.merge_rot * pos
                pos += self.space.merge_pos
                pos *= self.factor
                model =  glm.translate(pos)
                model =  glm.scale(model,glm.vec3(1)*self.factor*a.r)
                self.nucleonMesh.modelmatrix = model
                self.nucleonMesh.color = a.color
                self.nucleonMesh.draw(self.shader)
            gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL)

        #if self.space.gpu_compute.get():
        gl.glBindVertexArray(self.nucleonMesh.VAO )
        # render computed nucleons
        gl.glUniform1i(self.loc["mode"],1)
        gl.glDrawArraysInstanced(gl.GL_TRIANGLES, 0, int(self.sphere_vertices.size/6), len(self.space.nucleons))

        gl.glUniform1i(self.loc["mode"],0)
        gl.glBindVertexArray( 0 )

        # draw container            
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE );
        self.containerMesh.drawQuads(self.shader)
        gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL );

        #render selection
        if self.space.select_mode==1:
            for i in self.space.selected_nucleons:
                a = self.space.nucleons[i]
                model =  glm.mat4()
                model =  glm.translate(model, a.pos * self.factor  )
                model =  glm.scale(model, glm.vec3(a.r * self.factor*1.1))
                self.nucleonMesh.color = (1,0,0)
                self.nucleonMesh.modelmatrix = model
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_LINE );
                self.nucleonMesh.draw(self.shader)
                gl.glPolygonMode(gl.GL_FRONT_AND_BACK, gl.GL_FILL );
        gl.glUseProgram(0)

        # gpu compute nucleons
        gl.glBindVertexArray(self.nucleonMesh.VAO )
        if not self.space.pause and self.space.gpu_compute.get():
            gl.glUseProgram(self.gpu_code)
            gl.glUniform3fv(self.loc["box"], 1, glm.value_ptr(self.space.box))
            gl.glUniform1i(self.loc["iTime"],self.space.t)
            gl.glUniform1i(self.loc["gravity"],self.space.gravity.get())
            gl.glUniform1i(self.loc["shake"],self.space.shake.get())
            gl.glUniform1i(self.loc["atype"],int(self.space.atype))
            gl.glUniform1i(self.loc["softbox"],self.space.softbox.get())
            gl.glUniform1f(self.loc["BOND_KOEFF"],self.space.BOND_KOEFF)
            gl.glUniform1f(self.loc["INTERACT_KOEFF"],self.space.INTERACT_KOEFF)
            gl.glUniform1f(self.loc["REPULSION_KOEFF1"],self.space.REPULSION_KOEFF1)
            gl.glUniform1f(self.loc["ATTRACT_KOEFF"],self.space.ATTRACT_KOEFF)
            gl.glUniform1f(self.loc["ROTA_KOEFF"],self.space.ROTA_KOEFF)
            gl.glUniform1f(self.loc["MASS_KOEFF"],self.space.MASS_KOEFF)
            gl.glUniform1f(self.loc["NEARDIST"],self.space.NEARDIST)
            gl.glUniform1f(self.loc["HEAT"],self.space.heat)

            for i in range(0,self.space.update_delta):
                self.space.t+=1
                if not self.space.pause:
                    if self.space.t%(int(self.space.NEARDIST/2.0))==0 or self.nearflag==True:  #near field calc
                        self.nearflag = False
                        gl.glUniform1i(self.loc["stage"],1)
                        gl.glDispatchCompute(int(len(self.space.nucleons)/self.LOCALSIZEX)+1,1,1)        
                        gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT)

                    gl.glUniform1i(self.loc["stage"],2)  #main
                    gl.glDispatchCompute(int(len(self.space.nucleons)/self.LOCALSIZEX)+1,1,1)        
                    gl.glMemoryBarrier(gl.GL_SHADER_STORAGE_BARRIER_BIT)
                    self.nucleons_buffer,self.nucleons_buffer2 = self.nucleons_buffer2,self.nucleons_buffer
                    gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 0, self.nucleons_buffer)
                    gl.glBindBufferBase(gl.GL_SHADER_STORAGE_BUFFER, 1, self.nucleons_buffer2)
                    if self.space.action:
                        self.space.action(self.space)   
            gl.glUseProgram(0)


    def do_movement(self):
        cameraSpeed = 5 * self.framedelta
        if 'w' in self.keypressed:
              self.cameraPos += cameraSpeed * self.cameraFront
        if 's' in self.keypressed:
              self.cameraPos -= cameraSpeed * self.cameraFront
        if 'a' in self.keypressed:
              self.cameraPos -= glm.normalize(glm.cross(self.cameraFront, self.cameraUp)) * cameraSpeed
        if 'd' in self.keypressed:
              self.cameraPos += glm.normalize(glm.cross(self.cameraFront, self.cameraUp)) * cameraSpeed


    def redraw(self):
        """Render a single frame"""
        
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        self.render()
        if self.space.recording.get() and not self.space.pause:
            pix = gl.glReadPixels(0,0,self.width, self.height,gl.GL_RGB,gl.GL_UNSIGNED_BYTE)
            img = Image.frombytes("RGB", (self.width,self.height), pix)
            img2 = img.transpose(method=Image.FLIP_TOP_BOTTOM)
            img2.save("output/frame"+str(self.rframes)+".png")
            self.rframes+=1

                            
        self.curframe_time = time.time()
        self.framedelta = self.curframe_time - self.lastframe_time 
   #     self.do_movement()
        #time.sleep(0.1)
        self.lastframe_time = self.curframe_time
        throttle = 1/40 - self.framedelta
        if throttle>0:
            time.sleep(throttle)
        self.nframes += 1
                
#        print("fps",self.nframes / tm, end="\r" )
        if self.nframes%50 == 0:
            if self.framedelta!=0:
                tm = time.time() - self.start
                self.status_bar.setFPS(self.nframes/tm)
