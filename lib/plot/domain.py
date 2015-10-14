#-*- coding: utf-8 -*-
"""
domains specifiy data which a graph plots.
all domains are basically VBO's. any domain must provide the following
API methods:
 - get_vbo() should return opengl vbo id
 - get_length() should return number of points to plot
 - get_transformation_matrix() should return a matrix to transform
      domain data within the vertex shaders

:author: Nicolas 'keksnicoh' Heimann 
"""
from OpenGL.GL import *
import numpy 

class Domain():
    def __init__(self, vbo_id, dimension=2):
        self._vbo_id = vbo_id
        self.dimension = dimension
    def set_vbo(self, vbo_id):
        self._vbo_id = vbo_id
    def get_vbo(self):
        return self._vbo_id
    def get_transformation_matrix(self, axis, origin):
        return numpy.identity(4).flatten()
    def get_length(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo_id)
        size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return size

class DynamicContinousDomain(Domain):
    """
    domain for continuous data sets. 
    this domain provides several transformation modes MODE_*. 

    MODE_STATIC:
      the domain is static and wont be fitted to plot plane 
    MODE_DYNAMIC_X:
      the x components of this domain will be fitted to plotplane.
      this means that you are able to plot any interval on the
      x axis by the same domain.
    MODE_DYNAMIC_Y:
      the y components of this domain will be fitted to the plotplane.
      see: MODE_DYNAMIC_X
    MODE_DYNAMIC_XY:
      both MODE_DYNAMIC_X and MODE_DYNAMIC_Y are active. 

    """
    MODE_STATIC     = 1
    MODE_DYNAMIC_X  = 2
    MODE_DYNAMIC_Y  = 3
    MODE_DYNAMIC_XY = 4

    def __init__(self, vbo_id, mode=MODE_STATIC, dimension=2):
        """
        allowes to configure the mode
        :param vbo_id: opengl vbo id
        :param mode: MODE_*
        :param dimension: dimension of this domain
        """
        self.mode = mode
        Domain.__init__(self, vbo_id, dimension)

    def get_transformation_matrix(self, axis, origin):
        """
        returns a matrix to transform domain data
        with respect to plontplane space.
        :param axis: length of each axis
        :param origin: position of origin 
        :raises: ValueError 
        """
        if self.mode == DynamicContinousDomain.MODE_STATIC:
            return numpy.identity(4).flatten()
        elif self.mode == DynamicContinousDomain.MODE_DYNAMIC_X:
            return numpy.array([
                axis[0],        0,              0,
                0,              0,              0,
                -origin[0],     0,              1,
            ], dtype=numpy.float32)
        elif self.mode == DynamicContinousDomain.MODE_DYNAMIC_Y:
            return numpy.array([
                0,              0,              0,
                0,              axis[1],        0,
                0,              -origin[1],     1,
            ], dtype=numpy.float32)
        elif self.mode == DynamicContinousDomain.MODE_DYNAMIC_XY:
            return numpy.array([
                axis[0],        0,              0,
                0,              axis[1],        0,
                -origin[0],     -origin[1],     1,
            ], dtype=numpy.float32)
        else:
            raise ValueError('mode must be either {}'.format(' or '.join([
                'DynamicContinousDomain.MODE_STATIC',
                'DynamicContinousDomain.MODE_DYNAMIC_X',
                'DynamicContinousDomain.MODE_DYNAMIC_Y',
                'DynamicContinousDomain.MODE_DYNAMIC_XY',
            ])))

class RealAxis(DynamicContinousDomain):
    """
    real axis domain.

    usage:
      1) plot sin(x) for whole x axis
      domain = RealAxis()
      graph = Line2d(domain, "y=sin(x)")

      2) plot sin(x) for a fixed interval.
      domain = RealAxis([0,2], dynamic=False)
      graph = Line2d(domain, "y=sin(x)")

    if dynamic=True then this method will transform
    its data to the shown plot plane, the boundaries does
    not matter at all. this is why in dynamic mode an interval
    [0,1] is chosen.

    for static mode you need to specify the interval explicit.
    """
    def __init__(self, interval=[0,1], dynamic=True, length=1000):
        """
        initializes the RealAxis Domain
        :param interval: the interval where data should spawned on
        :param dynamic: specify whether the interval will be automatically
                  fitted to plotspace. if True the interval
                  should be [0,1]
        :param length: number of points 
        """
        data = numpy.zeros(length*2, dtype=numpy.float32)
        for i in range(0, length):
            data[2*i] = interval[0]+interval[1]*float(i)/length
            data[2*i+1] = 0

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)  
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        domain = Domain(vbo)

        mode = DynamicContinousDomain.MODE_DYNAMIC_X if dynamic else DynamicContinousDomain.MODE_STATIC
        DynamicContinousDomain.__init__(self, vbo, mode=mode)
