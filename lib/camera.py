import numpy
class Camera():
    def get_matrix(self):
        return numpy.array([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ])

class Camera2d(Camera): pass
class Camera3d(Camera): pass