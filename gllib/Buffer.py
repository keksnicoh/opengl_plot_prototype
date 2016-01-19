#-*- coding: utf-8 -*-
"""
buffer objects

XXX
- make me nice and clean

:author: Nicolas 'keksnicoh' Heimann 
"""
from OpenGL.GL import *
class VertexBuffer():
    """
    representation of a buffer
    """
    _FLT32 = 4
    def __init__(self, length=None, dimension=None, gl_vbo_id=None):
        self.length = length 
        self.dimension = dimension 
        self.usage = GL_STATIC_DRAW
        self.nbytes = None 

        if gl_vbo_id is not None:
            self._gl_vbo_id = gl_vbo_id
        else:
            self._gl_vbo_id = None

        self.gl_buffer_length = 0
        self.gl_initialized = False
    @classmethod
    def from_numpy(cls, np_data):
        """
        creates a corresponding vbo from 
        a given numpy array
        """
        if np_data.shape[1] is None:
            raise ValueError('numpy array must have 2d shape. given shape: {}'.format(np_data))
                
        vertex_buffer = VertexBuffer(*np_data.shape[0:2])
        vertex_buffer.buffer_data(np_data)
        return vertex_buffer

    @property
    def gl_vbo_id(self):
        if not self.gl_initialized:
            self.gl_init()

        return self._gl_vbo_id

    def gl_init(self):
        if self._gl_vbo_id is None:
            self._gl_vbo_id = glGenBuffers(1)
        self.gl_initialized = True

    def buffer_data(self, data=None):
        self.data = data
        glBindBuffer(GL_ARRAY_BUFFER, self.gl_vbo_id)
        glBufferData(GL_ARRAY_BUFFER, self.dimension*self.length*self._FLT32, data.flatten(), self.usage)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        self.gl_buffer_length = self.length

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
            glVertexAttribPointer(program_attributes[name], buffer.dimension, GL_FLOAT, GL_FALSE, 0, None)
            glEnableVertexAttribArray(i)
        glBindVertexArray(0)
    def bind(self):
        glBindVertexArray(self.gl_vao_id)
    def unbind(self):
        glBindVertexArray(0)
        