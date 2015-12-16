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
from gllib.util import Event
from gllib import texture


class Domain():
    def __init__(self, vbo_id, dimension=2, offset=0, length=None):
        self._vbo_id = vbo_id
        self.dimension = dimension
        self.offset = offset
        self.length = length

    def set_vbo(self, vbo_id):
        self._vbo_id = vbo_id
    def get_vbo(self):
        return self._vbo_id
    def get_transformation_matrix(self, axis, origin):
        return numpy.identity(3).flatten()
    def get_offset(self):
        return self.offset*4*self.dimension
    def get_length(self):
        if self.length is None:
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo_id)
            size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            return float(size)
        return self.length*4*self.dimension

class FieldDomain():
    """
    texture based domain
    """
    def __init__(self, texture):
        self.texture       = texture
        self.gl_texture_id = None
        self.channels      = None 
        self.dimensions    = None

    # helper methods to spawn a FieldDomain
    @classmethod
    def from_numpy(cls, np_data, discrete=True):
        return cls(texture.NumpyTexture(np_data, gl_texture_parameters=[
            (GL_TEXTURE_MAG_FILTER, GL_NEAREST if discrete else GL_LINEAR),
            (GL_TEXTURE_MIN_FILTER, GL_NEAREST if discrete else GL_LINEAR),
        ]))
        
    @classmethod
    def empty(cls, dimensions=(1,1)):
        return EmptyFieldDomain(dimensions)

    # XXX
    # - spawn methods for image files (png, bmp, ...)
    # - spawn methods for text files
    # - spawn methods for external languages (fortran, c, cython, ...)
    # - spawn methods for opencl textures ??
    # - future: spawn methods for other domains / plotting results

    def gl_init(self):
        """ 
        initializes texture and fetches properties
        """
        if hasattr(self.texture, 'gl_texture_id'):
            if hasattr(self.texture, 'gl_init'):
                self.texture.gl_init()
            self.gl_texture_id = self.texture.gl_texture_id
        else:
            self.gl_texture_id = self.texture

        glBindTexture(GL_TEXTURE_2D, self.gl_texture_id)
        self.dimensions = (
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_WIDTH),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_HEIGHT)
        )

        self.channels = sum([1 if a == 8 else 0 for a in (
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_RED_SIZE),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_GREEN_SIZE),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_BLUE_SIZE),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_ALPHA_SIZE)
        )])
        
        glBindTexture (GL_TEXTURE_2D, 0)

    def get_transformation_matrix(self, axis, origin):
        return numpy.identity(3).flatten()

class EmptyFieldDomain():
    def __init__(self, dimensions):
        self.dimensions = dimensions



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
                0,              1,              0,
                -origin[0],     0,              1,
            ], dtype=numpy.float32)
        elif self.mode == DynamicContinousDomain.MODE_DYNAMIC_Y:
           return numpy.array([
                1,              0,              0,
                0,              axis[1],        0,
                0,              origin[1],     1,
            ], dtype=numpy.float32)
        elif self.mode == DynamicContinousDomain.MODE_DYNAMIC_XY:
            return numpy.array([
                axis[0],        0,              0,
                0,              axis[1],        0,
                -origin[0],  origin[1],     1,
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

    def __init__(self, interval=[0,1], dynamic=True, axis=0, length=1000):
        """
        initializes the RealAxis Domain
        :param interval: the interval where data should spawned on
        :param dynamic: specify whether the interval will be automatically
                  fitted to plotspace. if True the interval
                  should be [0,1]
        :param axis: specifies the axis to build vertex data (0=X-Axis, 1=Y-Axis)
        :param length: number of points 
        """
        
        self._interval = interval
        self._dynamic = dynamic
        self._axis = axis 
        self.length = length
        self.offset = 0
        self._vbo_id = None
        self.dimension = 2

        dynamic_matrix = lambda: DynamicContinousDomain.MODE_DYNAMIC_X if self._axis == 0 else DynamicContinousDomain.MODE_DYNAMIC_Y
        self.mode = dynamic_matrix() if self._dynamic else DynamicContinousDomain.MODE_STATIC

    def _init_vbo(self):
        data = numpy.zeros(self.length*2, dtype=numpy.float32)
        for i in range(0, self.length):
            data[2*i+self._axis]   = self._interval[0]+self._interval[1]*float(i)/self.length
            data[2*i+self._axis^1] = 0

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)  
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        domain = Domain(vbo)

        self._vbo_id = vbo

    def get_vbo(self):
        if self._vbo_id is None:
            self._init_vbo()

        return Domain.get_vbo(self)

class Interval(RealAxis):
    # XXX
    # - remove me and create a small alias helper
    #   function for this
    def __init__(self, interval=[0,1]):
        RealAxis.__init__(self, interval=interval, axis=0, dynamic=False, length=10000)


class NumpyDomain(Domain):
    def __init__(self, data):
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)  
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        Domain.__init__(self, vbo)
         






