#-*- coding: utf-8 -*-
"""
color schemes

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
        float scaled = range.x + fragment_color.r * (range.y - range.x);
        fragment_color = colormap(scaled);
    """
    def __init__(self, filename):
        ColorScheme.__init__(self)
        self.filename = filename
        self.uniforms = [
            ('vec2', 'range'),
        ]

        self.uniform_data = [
            ('range', [0, 1]),
        ]

    def get_fragment_shader(self):
        shader_kernel = pystache.render(load_lib_file('glsl/plot2d/field.frag.glsl'), {
            'START_UNIFORMS': "*/",
            'END_UNIFORMS': "/*",
            'UNIFORMS': self._generate_uniforms(),
        })
        return Shader(GL_FRAGMENT_SHADER, shader_kernel, {
            'COLOR_KERNEL': self.COLOR_KERNEL,
            'FUNCTIONS': load_lib_file('../vendor/glsl-colormap/shaders/%s.frag' % self.filename)
        })
        

"""
expects texture to have 1 value (fragment_color.r)
creates colors from red to violet by simple linear functions
"""
class RainbowScheme(ColorScheme):
    COLOR_KERNEL = """
        vec4 packFactors = vec4( 256.0 * 256.0 * 256.0, 256.0 * 256.0, 256.0, 1.0);
        vec4 unpackFactors = vec4( 1.0 / (256.0 * 256.0 * 256.0), 1.0 / (256.0 * 256.0), 1.0 / 256.0, 1.0 );
        vec4 bitMask = vec4(0.0, 1.0 / 256.0, 1.0 / 256.0, 1.0 / 256.0);

        vec4 packedValue = vec4(fract(packFactors*fragment_color.r));
        packedValue -= packedValue.xxyz * bitMask;


        fragment_color = packedValue;
    """
    def __init__(self):
        ColorScheme.__init__(self)
        self.uniforms = [
            ('vec2', 'range'),
            ('float', 'range_center'),
        ]

        self.uniform_data = [
            ('range', [0, 1]),
            ('range_center', 0.5)
        ]

    def get_fragment_shader(self):
        shader_kernel = pystache.render(load_lib_file('glsl/plot2d/field.frag.glsl'), {
            'START_UNIFORMS': "*/",
            'END_UNIFORMS': "/*",
            'UNIFORMS': self._generate_uniforms(),
        })
        return Shader(GL_FRAGMENT_SHADER, shader_kernel, {
            'COLOR_KERNEL': self.COLOR_KERNEL
        })

"""
expects texture to have 1 value (fragment_color.r)
creates colors from red to blue by simple linear functions
"""
class RedBlueScheme(ColorScheme):
    COLOR_KERNEL = """
        float red   = 0.0f;
        float green = 0.0f;
        float blue  = 0.0f;
        float diff = 1.0f/(abs(range.y - range.x));

        float l = range.y - range.x;
        float v = fragment_color.r - range.x;
        if (fragment_color.r < range_center) {
            red = 1-2.0f/l*v;
            green = 2.0f/l*v;
        }
        else {
            blue = 2.0f/l*v-1.0f;
            green = 2.0f-2.0f/l*v;
        }
        fragment_color = vec4(red, green, blue, fragment_color.a);
    """
    def __init__(self):
        ColorScheme.__init__(self)
        self.uniforms = [
            ('vec2', 'range'),
            ('float', 'range_center'),
        ]

        self.uniform_data = [
            ('range', [0, 1]),
            ('range_center', 0.5)
        ]

    def get_fragment_shader(self):
        shader_kernel = pystache.render(load_lib_file('glsl/plot2d/field.frag.glsl'), {
            'START_UNIFORMS': "*/",
            'END_UNIFORMS': "/*",
            'UNIFORMS': self._generate_uniforms(),
        })
        return Shader(GL_FRAGMENT_SHADER, shader_kernel, {
            'COLOR_KERNEL': self.COLOR_KERNEL
        })