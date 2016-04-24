#-*- coding: utf-8 -*-
"""
domains specifiy data which a graph plots.

a DOMAIN is basically a object which wraps around
either a vbo or a texture. 

API methods (deprecated):
# XXX
# -remove old methods
 - get_vbo() should return opengl vbo id
 - get_length() should return number of points to plot
 - get_transformation_matrix() should return a matrix to transform
      domain data within the vertex shaders

API attributes
    int gl_vbo_id     : opengl vertex buffer object id 
    int dimension     : domain dimension
    int __len__       : if domain has vbo, this attr specifies its length
    int offset        : if domain has vbo, this attr specifies rendering offset
    int gl_texture_id : opengl texture id
    np.ndarray transformation_matrix : a transformaiton matrix allows to
      perform a linear transformation on the domain within vertex shader.
      i.e.: streching the x-component of domain over the visible x-axis
           for simple shader graphs. this enables zomm, translation, ...
           and live rendering of the visible region. 

:author: Nicolas 'keksnicoh' Heimann 
"""
from OpenGL.GL import *
import numpy 
from gllib.util import Event
from gllib import texture
from gllib.buffer import VertexBuffer
import numpy as np

def interval(a, b, steps):
    return NumpyDomain(np.arange(a, b, steps, dtype=np.float32))


class Domain():
    # XXX
    # - REFACTOR OLD API METHODS 
    # - DELETE THIS BASE CLASS
    @classmethod
    def empty(cls, shape):
        if type(shape) is not tuple:
            shape = (shape, 1)
            
        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, 4*shape[0]*shape[1], None, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return cls(vbo, length=shape[0], dimension=shape[1])
        
    def __init__(self, vbo_id, dimension=2, offset=0, length=None):
        self._vbo_id = vbo_id
        self.dimension = dimension
        self.offset = offset
        self.length = length

    @property
    def gl_vbo_id(self):
        return self._vbo_id
    def __len__(self):
        return self.get_length()
    def get_transformation_matrix(self, axis, origin):
        return numpy.identity(3).flatten()
    def get_offset(self):
        return self.offset*4*self.dimension
    def get_length(self):
        if self.length is None:
            glBindBuffer(GL_ARRAY_BUFFER, self._vbo_id)
            size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            return int(float(size)/4/self.dimension)
        return self.length

    def pull_data(self, offset=0, length=None):
        # XXX
        # - offset
        bytes_per_vertex = self.dimension*4
        max_length = len(self) - self.offset
        if length is None:
            length = max_length 
        else:
            length = min(length, max_length)
        
        size = length*bytes_per_vertex
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ARRAY_BUFFER, self.gl_vbo_id)
        data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, size)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        
        return data.view('<f4').reshape((length, self.dimension))


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
        print(self.dimensions)
        self.channels = sum([1 if a == 8 else 0 for a in (
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_RED_SIZE),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_GREEN_SIZE),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_BLUE_SIZE),
            glGetTexLevelParameteriv(GL_TEXTURE_2D, 0, GL_TEXTURE_ALPHA_SIZE)
        )])
        
        glBindTexture (GL_TEXTURE_2D, 0)

    def get_transformation_matrix(self, axis, origin):
        return numpy.identity(3).flatten()

class RealAxis(object):
    def __init__(self, axis='x', interval=(0,1)):
        self.axis = axis
        self.interval = interval
        self._data = None
        self.dimension = 1
        self.length = None
        self.offset = 0
        self._vbo = None
        self._initialized = False

    def gl_init(self):
        if not self._initialized:
            self._init_data()
            self._init_vbo()
            self._initialized = True

    def _init_data(self):
        """
        initialized numpy data
        """
        data = np.arange(0, 1, 0.001, dtype=np.float32)
        self.length = len(data)
        self._data = data.reshape((self.length,1))

    def _init_vbo(self):
        """
        initialized vbo
        """
        self._vbo = VertexBuffer.from_numpy(self._data)
    
    def get_transformation_matrix(self, axis, origin):
        """
        returns a matrix which transforms the domain 
        so that the data fit in the region currently seen
        by plotter
        """
        if self.axis == 'x':
            return numpy.array([
                axis[0], 0,
                -origin[0], 1,
            ], dtype=numpy.float32)
        elif self.axis == 'y':
           return numpy.array([
                axis[1], 0,
                origin[1], 1,
            ], dtype=numpy.float32)
        else:
            return np.identity(2)

    @property
    def data(self):
        return self._data 

    def __len__(self):
        return self.length

    @property
    def gl_vbo_id(self):
        return self._vbo.gl_vbo_id

    def pull_data(self):
        return Domain.pull_data(self)

class NumpyDomain(Domain, object):
    """
    connect numpy array with opengl vbo
    and adapts into plotting library.

    ..code:
        domain = NumpyDomain(mydata)
        # at this point no VBO was inizialized

        domain.data = other_numpy_data
        # again no VBO was inizialized

        vbo_id = domain.vbo 
        # after first access of vbo attribute, a opengl vbo
        # was generated.

        domain.data = cool_data
        # now the data was trasmitted to vbo
        # directly. 

    """
    def __init__(self, data):
        self._vbo = None
        
        if len(data.shape) < 2:
            data = data.reshape((len(data),1))

        self.data = data 
        self.length = None
        self.offset = 0

    @property
    def data(self):
        return self._data 

    def __len__(self):
        return self.length or self._data.shape[0]

    @data.setter 
    def data(self, data):
        if data.dtype != numpy.float32:
            raise Exception(
                'domain data has dtype={} but must have dtype=float32.'.format(
                    data.dtype
                )
            )
        self._data = data
        if self._vbo is not None: 
            self._vbo.buffer_data(self._data)

    @property
    def dimension(self):
        return self._data.shape[1]

    @property
    def gl_vbo_id(self):
        if self._vbo is None: 
            self._init_vbo()
        return self._vbo.gl_vbo_id

    def _init_vbo(self):
        self._vbo = VertexBuffer.from_numpy(self._data)
         

    def pull_data(self):
        return Domain.pull_data(self)




