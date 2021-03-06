import numpy

class ModelView():
    def __init__(self):
        self.position = [0,0,0]
        self.scaling = (1,1,1)
        self.mat4 = numpy.array([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ], dtype=numpy.float32)

    def set_scaling(self, scaling_x=1, scaling_y=1, scaling_z=1):
        self.scaling = (scaling_x, scaling_y, scaling_z)
        self.mat4[0] = scaling_x
        self.mat4[5] = scaling_y
        self.mat4[10] = scaling_z

    def translate(self, x=0, y=0, z=0):
        translation_matrix = numpy.array([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            x, y, z, 1,
        ], dtype=numpy.float32).reshape(4,4)
        new_matrix = numpy.dot(self.mat4.reshape(4,4), translation_matrix)
        self.mat4 = new_matrix.flatten()

        #self.mat4[12] += x
        #self.mat4[13] += y
        #self.mat4[14] += z

        return self

    def set_position(self, x=0, y=0, z=0):
        self.position = [x,y,z]
        self.mat4[12] = x
        self.mat4[13] = y
        self.mat4[14] = z
        return self


    def rotate(self, deg):
        phi = numpy.radians(deg)

        rot_matrix = numpy.array([
            numpy.cos(phi),   -numpy.sin(phi),  0, 0, 
            numpy.sin(phi),   numpy.cos(phi),   0, 0,
            0,               0            ,   1, 0,
            0,0,0, 1, 
        ], dtype=numpy.float32).reshape(4,4)

        new_matrix = numpy.dot(self.mat4.reshape(4,4), rot_matrix)
        self.mat4 = new_matrix.flatten()


     #   self.mat4[0] = numpy.cos(phi + numpy.arccos(self.mat4[0]))
     #   self.mat4[1] = -numpy.sin(phi - numpy.arcsin(self.mat4[1]))
     #   self.mat4[4] = numpy.sin(phi + numpy.arcsin(self.mat4[4]))
     #   self.mat4[5] = numpy.cos(phi + numpy.arccos(self.mat4[5]))

        return self


    def set_rotation(self, deg):
        phi = numpy.radians(deg)

        self.mat4 = numpy.array([
            numpy.cos(phi),   -numpy.sin(phi),  0, 0, 
            numpy.sin(phi),   numpy.cos(phi),   0, 0,
            0,               0            ,   1, 0,
            self.mat4[12], self.mat4[13], self.mat4[14], 1, 
        ], dtype=numpy.float32)
        return self
