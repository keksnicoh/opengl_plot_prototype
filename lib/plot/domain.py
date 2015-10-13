from OpenGL.GL import *
import numpy 

class VBODomain():

    def __init__(self, vbo_id, dimension=2):
        self._vbo_id = vbo_id
        self.dimension = dimension

    def set_vbo(self, vbo_id):
        self._vbo_id = vbo_id

    def get_vbo(self):
        return self._vbo_id

    def get_transformation_matrix(self, axis, origin):
        """
        default transformation does transform x and y coordinates into
        the current axis/origin configuration
        """
        return numpy.array([
            axis[0], 0,   0,
            0,   axis[1], 0,
            -origin[0], -origin[1],   1.0,
        ], dtype=numpy.float32)

    def get_length(self):
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo_id)
        size = glGetBufferParameteriv(GL_ARRAY_BUFFER, GL_BUFFER_SIZE)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        return size



