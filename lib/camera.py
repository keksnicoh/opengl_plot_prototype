import numpy
from util import Event

class Camera():
    def __init__(self, initial_screensize, scaling=None):
        self.initial_screensize = initial_screensize
        self.screensize = initial_screensize
        self.position = [0,0,0]
        self.scaling = None
        self.set_scaling(scaling)
        self.on_change_matrix = Event()

    def set_scaling(self, scaling):
        if scaling is None:
            scaling = (float(self.initial_screensize[1]), float(self.initial_screensize[0]))

        self.scaling = scaling

    def set_screensize_unit(self, screensize_unit):
        self.screensize_unit = screensize_unit

    def set_position(self, x=0, y=0, z=0):
        self.position = [x,y,z]
        self.on_change_matrix(self)

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
    """
    camera to project the x-y-plane by a given
    scaling. by default the camera transforms 
    the viewspace so a change of screensize wont
    affect viewspace coordinates.
    """
    SCALING_GL = 2.0
    
    def set_screensize(self, screensize):
        Camera.set_screensize(self, screensize)
        self.on_change_matrix(self)


    def _screen_factor(self):
        return (
            Camera2d.SCALING_GL*float(self.initial_screensize[0])/(self.screensize[0]), 
            Camera2d.SCALING_GL*float(self.initial_screensize[1])/(self.screensize[1])
        )

    def get_matrix(self):
        screen_factor = self._screen_factor()
        return numpy.array([
            screen_factor[0]/self.scaling[0], 0, 0, 0,
            0, -screen_factor[1]/self.scaling[1], 0, 0,
            0, 0, 1, 0,
            -1.0 + self.position[0], 1.0 + self.position[1], self.position[2], 1,
        ])
