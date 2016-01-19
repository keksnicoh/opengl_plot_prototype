from gllib.buffer import VertexBuffer

from OpenGL.GL import * 
import numpy as np 

def map_domain(domain, mapper):
    """
    shortcut for a python domain configured with domain_mapper
    """
    return PythonDomain(domain, domain_mapper(mapper))

def domain_mapper(mapper):
    def _mapper(data):
        new_data = np.zeros_like(data)
        for i, row in enumerate(data):
            new_data[i] = mapper(row)
        return new_data
    return _mapper

class PythonDomain(object):
    """
    domain which enables to define a python
    transformation for a given domain. This domain
    enables to quickly use existing transformations
    like FFT from the scipy library and so on.
    """
    def __init__(self, domain, transformation):
        self.domain = domain 
        self.transformation = transformation
        self.offset = 0
        self._vbo = None
        self._transformed = False 
        self._transformed_data = None 

        self.dimension = 2

    def __len__(self):
        if self._transformed_data is None:
            raise Exception('FOO')
        return self._transformed_data.shape[0]
    
    @property 
    def gl_vbo_id(self):
        if self._vbo is None:
            return None
        
        return self._vbo.gl_vbo_id

    def transform(self):
        bytes_per_vertex = self.domain.dimension*4
        size = self.domain.get_length() - self.domain.offset 
        length = size/bytes_per_vertex

        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindBuffer(GL_ARRAY_BUFFER, self.domain.gl_vbo_id)
        data = glGetBufferSubData(GL_ARRAY_BUFFER, 0, 800)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        domain_data = data.view('<f4').reshape((length, self.domain.dimension))
        self._transformed = True
        self._transformed_data = self.transformation(domain_data)

        self._vbo = VertexBuffer.from_numpy(self._transformed_data)