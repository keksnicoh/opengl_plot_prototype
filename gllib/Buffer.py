#-*- coding: utf-8 -*-
"""
buffer objects

XXX
- make me nice and clean

:author: Nicolas 'keksnicoh' Heimann 
"""
from OpenGL.GL import *
class VertexBuffer():
    _FLT32 = 4
    def __init__(self, length, dimension=2):
        self.length = length 
        self.dimension = dimension 
        self.gl_vbo_id = None
        self.init_gl()
        self.gl_buffer_length = 0

    @classmethod
    def from_numpy(cls, np_data):

        if np_data.shape[1] is None:
            raise ValueError('numpy array must have 2d shape. given shape: {}'.format(np_data))
                

        vertex_buffer = VertexBuffer(*np_data.shape)
        vertex_buffer.buffer_data(np_data)
        return vertex_buffer

    def init_gl(self):
        self.gl_vbo_id = glGenBuffers(1)

    def buffer_data(self, data=None):
        glBindBuffer(GL_ARRAY_BUFFER, self.gl_vbo_id)
        glBufferData(GL_ARRAY_BUFFER, self.dimension*self.length*self._FLT32, data.flatten(), GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        self.gl_buffer_length = self.length
        print(self.length)

    def bind(self):
        glBindBuffer(GL_ARRAY_BUFFER, self.gl_vbo_id)
    def unbind(self):
        glBindBuffer(GL_ARRAY_BUFFER, 0)

class VertexArray():
    def __init__(self, attributes, enable_attributes=None):
        self.attributes = attributes
        self.init_gl()
        if enable_attributes is not None:
            self.enable_attributes(enable_attributes)
    def init_gl(self):
        self.gl_vao_id = glGenVertexArrays(1)
    def enable_attributes(self, program_attributes):
        glBindVertexArray(self.gl_vao_id)
        for i, (name, buffer) in enumerate(self.attributes.items()):
            buffer.bind()
            print(i, name, buffer.dimension)
            glVertexAttribPointer(program_attributes[name], buffer.dimension, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(i)
        glBindVertexArray(0)
    def bind(self):
        glBindVertexArray(self.gl_vao_id)
    def unbind(self):
        glBindVertexArray(0)
        