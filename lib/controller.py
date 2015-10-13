from OpenGL.GL import *
import numpy
from camera import Camera2d
from util import Event

class Controller():
    def __init__(self, camera=None):
        """
        initializes basic controller events
        """
        self.camera = camera 

        self.on_init        = Event()
        self.on_pre_cycle   = Event()
        self.on_post_cycle  = Event()
        self.on_pre_render  = Event()
        self.on_post_render = Event()
        self.on_render      = Event()
        self.on_cycle       = Event()

        self.on_pre_render.append(self.clear_gl)

    def init(self): 
        self.on_init(self)
        self.camera.on_change_matrix.append(self.camera_updated)

    def camera_updated(self, camera):
        self.cycle()

    def clear_gl(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def run(self):
        self.on_cycle()
        self.on_render(self)

    def cycle(self):
        self.on_pre_cycle()
        self.on_pre_render()
        self.run()
        self.on_post_render()
        self.on_post_cycle()
        pass
