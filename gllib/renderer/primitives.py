#-*- coding: utf-8 -*-
"""
renderers for primitives.

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.renderer.renderer import Renderer 
from lib.shader import Shader, Program
from lib.helper import load_lib_file
from OpenGL.GL import * 
import numpy

class SimplePrimitivesRenderer(Renderer):

    def __init__(self, camera):
        Renderer.__init__(self, camera)
        self._initial_vertex_data = None

    """
    easy to use primites renderer for simple use cases.
    note that this renderer might not be effective if 
    you use it in many instances
    """
    def configure(self, type, vertex_data):
        """
        requires type and vertex_data
        """
        self.set_primitives_type(type)
        self.set_vertex_data(vertex_data)

    def set_primitives_type(self, type):
        """
        sets primitives type
        """
        self.primitives_type = type

    def set_vertex_data(self, vertex_data):
        """
        sets vertex data 
        """
        self._initial_vertex_data = vertex_data

    def buffer_data(self, vertex_data):
        data = numpy.array(vertex_data, dtype=numpy.float32)

        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)  
        glBindBuffer(GL_ARRAY_BUFFER, 0)

    def init(self, controller):

        program         = Program()
        vertex_shader   = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/id.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/id.frag.glsl'))

        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()
        
        # XXX
        # - replace vao/vbo utils by new library components
        self.vao = glGenVertexArrays(1)
        self.vbo = vbo = glGenBuffers(1)

        if self._initial_vertex_data is not None:
            self.buffer_data(self._initial_vertex_data)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.vbo)
        glVertexAttribPointer(program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)
        program.use()
        program.uniform('mat_camera', self.camera.get_matrix())
        program.uniform('mat_modelview', numpy.array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], dtype=numpy.float32))
        program.unuse()

        self.program = program

    def update_camera(self, camera):
        self.program.use()
        self.program.uniform('mat_camera', self.camera.get_matrix())
        self.program.unuse()

    def render(self, controller):
        self.program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(self.primitives_type, 0, 4)
        glBindVertexArray(0)
        self.program.unuse()

