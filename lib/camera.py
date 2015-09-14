import numpy
from util import Event

class Camera():
    def __init__(self, initial_screensize, scaling=1.0):
        self.initial_screensize = initial_screensize
        self.screensize = initial_screensize
        self.scaling = float(scaling)
        self.on_change_matrix = Event()

    def set_screensize(self, screensize):
        self.screensize = screensize

    def get_matrix(self):
        return numpy.array([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ])

class Camera2d(Camera): 
    SCALING_GL = 2.0
    def set_screensize(self, screensize):
        Camera.set_screensize(self, screensize)
        self.on_change_matrix()

    def _screen_factor(self):
        return (
            Camera2d.SCALING_GL*float(self.initial_screensize[0])/(self.screensize[0]*self.scaling), 
            Camera2d.SCALING_GL*float(self.initial_screensize[1])/(self.screensize[1]*self.scaling)
        )

    def get_matrix(self):
        screen_factor = self._screen_factor()

        delta_screensize = (
            self.screensize[0]-self.initial_screensize[0],
            self.screensize[1]-self.initial_screensize[1]
        )

        translation = (
            screen_factor[0]*float(delta_screensize[0])/(Camera2d.SCALING_GL*self.initial_screensize[0]),
            screen_factor[1]*float(delta_screensize[1])/(Camera2d.SCALING_GL*self.initial_screensize[1])
        )

        return numpy.array([
            screen_factor[0], 0, 0, 0,
            0, screen_factor[1], 0, 0,
            0, 0, 1, 0,
            -translation[0], translation[1], 0, 1,
        ])
class Camera3d(Camera): pass