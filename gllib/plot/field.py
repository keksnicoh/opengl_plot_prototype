#-*- coding: utf-8 -*-
"""
field plotting.

contains classes that plots 2d fields of data

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.shader import Program, Shader 
from gllib.buffer import VertexArray, VertexBuffer
from gllib.helper import load_lib_file

import numpy as np
from OpenGL.GL import * 

class Field():
    """
    draw a 2d field by using Field Domain (OpenGL textures).
    """
    def __init__(self, domain, top_left=None, bottom_right=None, color_scheme=None):

        self.top_left            = top_left 
        self.bottom_right        = bottom_right
        self.domain              = domain
        self.color_scheme        = color_scheme
        self.initialized         = False
        self.program             = None
        
        self._np_vertex_data     = None 
        self._np_texture_data    = None
        self._coord_top_left     = None
        self._coord_bottom_right = None

    def init(self):
        if not hasattr(self.domain, 'dimensions'):
            raise ValueError('domain must have attribute domain.dimensions')
        if not hasattr(self.domain, 'gl_texture_id'):
            raise ValueError('domain must have attribute domain.gl_texture_id')

        self.domain.gl_init()
        if self.top_left is None:
            self.top_left = (1,self.domain.dimensions[1])
        if self.bottom_right is None:
            self.bottom_right = (self.domain.dimensions[0], 1)

        self.gl_init()   

        self._np_texture_data = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.float32).reshape(6,2)
        self.scale(self.top_left, self.bottom_right)

        self.initialized = True

    def scale(self, top_left, bottom_right):
        """
        scales to field to a rectangle with top_left
        and bottom_right corner
        """
        unit_size_x = 0.5*float(bottom_right[0]-top_left[0])/(self.domain.dimensions[0]-1)
        unit_size_y = 0.5*float(top_left[1]-bottom_right[1])/(self.domain.dimensions[1]-1)
        self._coord_top_left = (top_left[0]-unit_size_x, top_left[1]+unit_size_y)
        self._coord_bottom_right = (bottom_right[0]+unit_size_x, bottom_right[1]-unit_size_y)

        self._np_vertex_data = np.array([
            self._coord_top_left[0], self._coord_top_left [1], 
            self._coord_top_left [0], self._coord_bottom_right[1], 
            self._coord_bottom_right[0], self._coord_bottom_right[1], 
            self._coord_bottom_right[0], self._coord_bottom_right[1], 
            self._coord_bottom_right[0], self._coord_top_left [1], 
            self._coord_top_left [0], self._coord_top_left [1]
        ], dtype=np.float32).reshape(6,2)

        self.vertex_array = VertexArray({
            'vertex_position': VertexBuffer.from_numpy(self._np_vertex_data),
            'texture_position': VertexBuffer.from_numpy(self._np_texture_data),
        }, self.program.attributes)

        self.top_left            = top_left 
        self.bottom_right        = bottom_right

    def gl_init(self):
        """
        initializes shader program and plane vao
        """
        self.program = Program()
        self.program.shaders.append(Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/field.vert.glsl')))
        if self.color_scheme:
            self.program.shaders.append(self.color_scheme.get_fragment_shader())
        else:
            self.program.shaders.append(Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/field.frag.glsl')))
        self.program.link()

        if self.color_scheme:
            for uniform in self.color_scheme.uniform_data:
                self.program.uniform(*uniform)


    def render(self, plotter):
        # final rendering
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, self.domain.gl_texture_id)
        self.vertex_array.bind()
        self.program.use()
        glDrawArrays(GL_TRIANGLES, 0, 6)
        self.vertex_array.unbind()
        self.program.unuse()

    @classmethod
    def create_texture1f(cls, size):
        texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, texture);
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, size[0], size[1], 0, GL_RED, GL_FLOAT, np.zeros(size[0]*size[1], dtype=np.float32))
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glBindTexture(GL_TEXTURE_2D, 0);
        return texture

