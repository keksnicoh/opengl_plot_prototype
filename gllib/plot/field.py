#-*- coding: utf-8 -*-
"""
field plotting.

contains classes that plots 2d fields of data

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.shader import Program, Shader 
from gllib.buffer import VertexArray, VertexBuffer
from gllib.helper import load_lib_file

import pystache

import numpy as np
from OpenGL.GL import * 


class Field():
    """
    draw a 2d field by using Field Domain (OpenGL textures).

    this plot runs either with or without a given FieldDomain(texture).
    If no domain defined, the field will scale to top_left, bottom_right.
    the data_kernel can be used to calculate data where domain is [0,1] x [0,1].

    if domain is not None, that top_left, bottom_right will be the center of
    top_left and bottom_right texel. data_kernel is by default the default
    glsl 2d texture sampler.

    using a color scheme one can modify data from data_kernel. 
    (field plot color scheme...)
    """
    def __init__(self, domain=None, top_left=None, bottom_right=None, color_scheme=None, data_kernel=None):

        if domain is None and data_kernel is None:
            raise ValueError('either domain or data_kernel must be defined.')

        self.top_left            = top_left or None
        self.bottom_right        = bottom_right or None
        self.domain              = domain
        self.color_scheme        = color_scheme or ''
        self.initialized         = False
        self.program             = None
        self.data_kernel         = data_kernel or 'fragment_color = texture(tex[0], x);'
        self._np_vertex_data     = None 
        self._np_texture_data    = None
        self._coord_top_left     = None
        self._coord_bottom_right = None

    def init(self):
        if self.domain is not None:
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
        if self.domain is None:
            self._coord_top_left = top_left or (0,1)
            self._coord_bottom_right = bottom_right or (1,0)
        else:
            dimensions = (self.domain.dimensions[0]-1, self.domain.dimensions[1]-1)
            unit_size_x = 0.5*float(bottom_right[0]-top_left[0])/dimensions[0]
            unit_size_y = 0.5*float(top_left[1]-bottom_right[1])/dimensions[1]
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
        glsl_functions = ''
        if hasattr(self.color_scheme, 'glsl_functions'):
            glsl_functions += '\n/*COLOR_SCHEME FUNCTIONS*/\n'
            glsl_functions += self.color_scheme.glsl_functions
        if hasattr(self.data_kernel, 'glsl_functions'):
            glsl_functions += '\n/*DATA_KERNEL FUNCTIONS*/\n'
            glsl_functions += self.data_kernel.glsl_functions

        glsl_uniforms = []
        if hasattr(self.color_scheme, 'glsl_uniforms'):
            glsl_uniforms.append('/*COLOR_SCHEME UNIFORMS*/')
            glsl_uniforms += ['uniform {} {};'.format(t, n) for t, n in self.color_scheme.glsl_uniforms]
        if hasattr(self.data_kernel, 'glsl_uniforms'):
            glsl_uniforms.append('/*DATA_KERNEL UNIFORMS*/')
            glsl_uniforms += ['uniform {} {};'.format(t, n) for t, n in self.data_kernel.glsl_uniforms]

        frag_src = pystache.render(load_lib_file('glsl/plot2d/field.frag.glsl'), {
            'UNIFORMS'    : '\n'.join(glsl_uniforms), 
            'FUNCTIONS'   : glsl_functions,
            'DATA_KERNEL' : str(self.data_kernel),
            'COLOR_KERNEL': str(self.color_scheme)
        })

        self.program = Program()
        self.program.shaders.append(Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/field.vert.glsl')))
        self.program.shaders.append(Shader(GL_FRAGMENT_SHADER, frag_src))
        self.program.link()

        if hasattr(self.color_scheme, 'get_uniform_data'):
            for uniform in self.color_scheme.get_uniform_data().items():
                self.program.uniform(*uniform)
        if hasattr(self.data_kernel, 'get_uniform_data'):
            for uniform in self.data_kernel.get_uniform_data().items():
                self.program.uniform(*uniform)

    def render(self, plotter):
        # final rendering
        glActiveTexture(GL_TEXTURE0);
        if self.domain is not None:
            glBindTexture(GL_TEXTURE_2D, self.domain.gl_texture_id)
        else:
            glBindTexture(GL_TEXTURE_2D, 0)

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

