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
    def __init__(self, domain, top_left=None, bottom_right=None):

        self.top_left            = top_left 
        self.bottom_right        = bottom_right
        self.domain              = domain
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

        unit_size_x = 0.5*float(self.bottom_right[0]-self.top_left[0])/(self.domain.dimensions[0]-1)
        unit_size_y = 0.5*float(self.top_left[1]-self.bottom_right[1])/(self.domain.dimensions[1]-1)
        self._coord_top_left = (self.top_left[0]-unit_size_x, self.top_left[1]+unit_size_y)
        self._coord_bottom_right = (self.bottom_right[0]+unit_size_x, self.bottom_right[1]-unit_size_y)

        self._np_vertex_data = np.array([
            self._coord_top_left[0], self._coord_top_left [1], 
            self._coord_top_left [0], self._coord_bottom_right[1], 
            self._coord_bottom_right[0], self._coord_bottom_right[1], 
            self._coord_bottom_right[0], self._coord_bottom_right[1], 
            self._coord_bottom_right[0], self._coord_top_left [1], 
            self._coord_top_left [0], self._coord_top_left [1]
        ], dtype=np.float32).reshape(6,2)

        self._np_texture_data = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.float32).reshape(6,2)

        self.gl_init()   
        self.initialized = True

    def gl_init(self):
        """
        initializes shader program and plane vao
        """
        self.program = Program()
        self.program.shaders.append(Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/field.vert.glsl')))
        self.program.shaders.append(Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/field.frag.glsl')))
        self.program.link()

        self.vertex_array = VertexArray({
            'vertex_position': VertexBuffer.from_numpy(self._np_vertex_data),
            'texture_position': VertexBuffer.from_numpy(self._np_texture_data),
        }, self.program.attributes) 


    def render(self, plotter):
        # final rendering
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, self.domain.gl_texture_id)
        self.vertex_array.bind()
        self.program.use()
        glDrawArrays(GL_TRIANGLES, 0, 6)
        self.vertex_array.unbind()
        self.program.unuse()

