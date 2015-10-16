from lib.renderer import window
from lib.matrix import ModelView
from lib.shader import *
from lib.helper import load_lib_file
from OpenGL.GL import * 
import numpy
class Scale():

    def __init__(self, 
        camera, 
        scale_camera, 
        size, 
        axis=0, 
        unit=3.14/2, 
        subunits=10,
        bgcolor=[1,1,1,1],
        linecolor=[1,1,1,1],
        fontcolor=[1,1,1,1]):
        self.unit = unit
        self.subunits = subunits 
        self.size = size
        self.initialized = False 
        self._initial_size = [size[0],size[1]]
        print('INIFNWEINFEWI')
        self._scale_camera = scale_camera
        self.modelview = ModelView()
        self._axis = axis
        self.camera = camera 
        self._frame = None
        self.linecolor = linecolor
        self.fontcolor = fontcolor
        self.bgcolor = bgcolor
        

    def init(self):

        unit_size = float(self.unit)/self._scale_camera.get_scaling()[self._axis]
        capture_size = [0,0]
        capture_size[self._axis] = int(round(unit_size*float(self._initial_size[self._axis]), 0))
        capture_size[self._axis^1] = self.size[self._axis^1]

        print('INIT', capture_size)
        frame = window.Framebuffer(
            camera=self.camera,
            screensize=self.size,  
            capture_size=capture_size,
            screen_mode=window.Framebuffer.SCREEN_MODE_REPEAT, 
            clear_color=self.bgcolor,
        )
        frame.init()
        scaling = [0,0]
        scaling[self._axis] = self.unit
        scaling[self._axis^1] = frame.inner_camera.get_scaling()[self._axis^1]

        frame.inner_camera.set_scaling(scaling)
        frame.inner_camera.set_position(*[self._scale_camera.get_position()[0], 0])

        frame.modelview = self.modelview
        frame.update_modelview()
        self._frame = frame

        program = Program()
        vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/id.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/id.frag.glsl'))
        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()
        self.program = program
        data = numpy.zeros(self.subunits*10, dtype=numpy.float32)
        if self._axis == 0:
            data[0] = .0001
            data[1] = 0
            data[2] = .0001
            data[3] = 11

            subunit = float(self.unit)/self.subunits
            for i in range(1, self.subunits):
                data[4*i+0] = subunit*i
                data[4*i+1] = 5
                data[4*i+2] = subunit*i
                data[4*i+3] = 9    
        else:
            data[0+0] = 39
            data[1-0] = .999
            data[2+0] = 50
            data[3-0] = .999
            subunit = float(self.unit)/self.subunits
            for i in range(1, self.subunits):
                data[4*i+0] = 41
                data[4*i+1] = subunit*i
                data[4*i+2] = 45
                data[4*i+3] = subunit*i   

        self.vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)  
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glVertexAttribPointer(program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        program.use()
        program.uniform('mat_camera', self._frame.inner_camera.get_matrix())
        program.uniform('mat_modelview', numpy.array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], dtype=numpy.float32))
        program.uniform('color', self.linecolor)
        program.unuse()

        self.initialized = True
        self._last_size = self.size[:]

    def update_camera(self, camera):
        self._frame.update_camera(camera)

        position = self._scale_camera.get_position()
        if self._axis == 1:
            camera = self._frame.camera
            size = camera.screensize 
            initial = camera.initial_screensize
            diff = initial[1]-size[1]
            translation = 0.5*self.size[1]*position[1]
            self._frame.screen_translation = [0,+0.5*diff+translation]
        if self._axis == 0:
            self._frame.screen_translation[0] = -(0.5*self.size[0]*position[0])%self._frame.capture_size[0]
    def update_modelview(self):
        self._frame.modelview = self.modelview
        self._frame.update_modelview()

    def render(self):
        if not self._last_size == self.size:
            self._frame.screensize = self.size
            self._frame.init_screen()
            self._last_size = self.size 
            print(self.size)

        if not self.initialized:
            self.init()
        if not self._frame.has_captured():
            self._frame.use()
            self._render_scale_element()
            self._frame.unuse()
        self._frame.render()

    def _render_scale_element(self):
        self.program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINES, 0, self.subunits*2)
        glBindVertexArray(0)
        self.program.unuse()