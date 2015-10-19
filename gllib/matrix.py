import numpy

class ModelView():
    def __init__(self):
        self.mat4 = numpy.array([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ], dtype=numpy.float32)

    def translate(self, x=0, y=0, z=0):
        return self 
        
    def set_position(self, x=0, y=0, z=0):
        self.mat4 = numpy.array([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            x, y, z, 1,
        ], dtype=numpy.float32)
        return self

