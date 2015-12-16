#-*- coding: utf-8 -*-
"""
color schemes. integration of glsl-colomap
vendor.

:author: Jesse Hinrichsen
"""
from gllib.shader import Shader
from gllib.helper import load_lib_file
from OpenGL.GL import *
import pystache

class ColorScheme():
    def __init__(self):
        self.uniforms     = []
        self.uniform_data = []

    def get_fragment_shader(self):
        raise NotImplementedError('abstract method')

    def _generate_uniforms(self):
        uniforms = ""
        for (type, name) in self.uniforms:
            uniforms += "uniform " + type + " " + name + ";\n"

        return uniforms

class ColorMap(ColorScheme):
    COLOR_KERNEL = """
        float scaled = (-range.x + (fragment_color.r)) / abs(range.y - range.x);
        fragment_color = colormap(scaled);
    """
    def __init__(self, filename, colorrange=[0,1], center=None):
        ColorScheme.__init__(self)
        self.filename = filename
        self.colorrange = colorrange
        self.center = center or 0.5*(colorrange[1]-colorrange[0])+colorrange[0]
        self.uniform_data = [
            ('range', colorrange),
        ]

    @property
    def range(self):
        return [self.colorrange[0], self.center, self.colorrange[1]]
    

    def get_uniform_data(self):
        return {
            'range': self.colorrange
        }
        

    @property
    def glsl_functions(self): return load_lib_file('../vendor/glsl-colormap/shaders/{}.frag'.format(self.filename))

    def __str__(self): return ColorMap.COLOR_KERNEL

    @property
    def glsl_uniforms(self):
        return [('vec2', 'range')]
     