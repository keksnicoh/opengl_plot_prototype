#-*- coding: utf-8 -*-
"""
field plot to work with 2 fielddomains
and calculates difference

:author Jesse Hinrichsen
"""
from gllib.shader import Program, Shader 
from gllib.buffer import VertexArray, VertexBuffer
from gllib.helper import load_lib_file

import numpy as np
from OpenGL.GL import * 

class FieldSubtraction():
    def __init__(self, domain1, domain2, top_left=None, bottom_right=None):

        self.top_left            = top_left 
        self.bottom_right        = bottom_right
        self.domain1             = domain1
        self.domain2             = domain2
        self.domain = domain1
        self.initialized         = False
        self.program             = None
        
        self._np_vertex_data     = None 
        self._np_texture_data    = None
        self._coord_top_left     = None
        self._coord_bottom_right = None

    def init(self):
        if not hasattr(self.domain1, 'dimensions'):
            raise ValueError('domain1 must have attribute domain1.dimensions')
        if not hasattr(self.domain1, 'gl_texture_id'):
            raise ValueError('domain1 must have attribute domain1.gl_texture_id')
        if not hasattr(self.domain2, 'dimensions'):
            raise ValueError('domain2 must have attribute domain2.dimensions')
        if not hasattr(self.domain2, 'gl_texture_id'):
            raise ValueError('domain2 must have attribute domain2.gl_texture_id')

        self.domain1.gl_init()
        self.domain2.gl_init()

        if self.top_left is None:
            top_left1 = (1,self.domain1.dimensions[1])
            top_left2 = (1,self.domain2.dimensions[1])
            if not top_left1 == top_left2:
                raise ValueError('domains must have the same dimension')
            self.top_left = top_left1
        if self.bottom_right is None:
            bottom_right1 = (self.domain1.dimensions[0], 1)
            bottom_right2 = (self.domain2.dimensions[0], 1)
            if not bottom_right1 == bottom_right2:
                raise ValueError('domains must have the same dimension')
            self.bottom_right = bottom_right1

        unit_size_x1 = 0.5*float(self.bottom_right[0]-self.top_left[0])/(self.domain1.dimensions[0]-1)
        unit_size_x2 = 0.5*float(self.bottom_right[0]-self.top_left[0])/(self.domain2.dimensions[0]-1)
        if not unit_size_x1 == unit_size_x2:
            raise ValueError('domains must have the same dimension')
        unit_size_x = unit_size_x1

        unit_size_y1 = 0.5*float(self.top_left[1]-self.bottom_right[1])/(self.domain1.dimensions[1]-1)
        unit_size_y2 = 0.5*float(self.top_left[1]-self.bottom_right[1])/(self.domain2.dimensions[1]-1)
        if not unit_size_y1 == unit_size_y2:
            raise ValueError('domains must have the same dimension')
        unit_size_y = unit_size_y1

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
        self.program.shaders.append(Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/field_sub.frag.glsl')))
        self.program.link()

        self.vertex_array = VertexArray({
            'vertex_position': VertexBuffer.from_numpy(self._np_vertex_data),
            'texture_position': VertexBuffer.from_numpy(self._np_texture_data),
        }, self.program.attributes) 


    def render(self, plotter):
        # final rendering
        self.program.use()
        glActiveTexture(GL_TEXTURE0);
        glBindTexture(GL_TEXTURE_2D, self.domain1.gl_texture_id)
        tex1 = glGetUniformLocation(self.program.gl_id, "tex1")
        glUniform1i(tex1, 0)

        glActiveTexture(GL_TEXTURE1);
        glBindTexture(GL_TEXTURE_2D, self.domain2.gl_texture_id)
        tex2 = glGetUniformLocation(self.program.gl_id, "tex2")
        glUniform1i(tex2, 1)

        self.vertex_array.bind()
        self.program.use()
        glDrawArrays(GL_TRIANGLES, 0, 6)
        self.vertex_array.unbind()
        self.program.unuse()