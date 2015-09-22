#-*- coding: utf-8 -*-
"""
opengl compatible types
:author: Nicolas 'keksnicoh' Heimann 
"""

import numpy

mat4 = lambda *x: numpy.array(x[0:16], dtype=numpy.float32)
mat3 = lambda *x: numpy.array(x[0:9], dtype=numpy.float32)
mat2 = lambda *x: numpy.array(x[0:4], dtype=numpy.float32)
vec2 = lambda *x: numpy.array(x[0:2], dtype=numpy.float32)
vec3 = lambda *x: numpy.array(x[0:3], dtype=numpy.float32)
vec4 = lambda *x: numpy.array(x[0:4], dtype=numpy.float32)
