from OpenGL.GL import *
import numpy
from gllib.camera import Camera2d
from gllib.util import Event
#
# XXX
# remove me asap
class Controller():
    def __init__(self, camera=None):
        """
        initializes basic controller events
        """
        self.camera = camera

        self.on_init          = Event()
        self.on_pre_cycle     = Event()
        self.on_post_cycle    = Event()
        self.on_request_cycle = Event()
        self.on_pre_render    = Event()
        self.on_post_render   = Event()
        self.on_render        = Event()
        self.on_cycle         = Event()
        self.on_mouse = Event()
        self.on_cursor = Event()
        self.on_destroy         = Event()
        self.on_keyboard      = Event()
        self.initialized      = False
        self.host_controller  = None
        self.cursor = (0,0)
        self.on_pre_render.append(self.clear_gl)

    def init(self):
        self.on_init(self)
        self.camera.on_change_matrix.append(self.camera_updated)
        self.initialized = True
    def camera_updated(self, camera):
        if self.host_controller is None:
            self.cycle()

    def clear_gl(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    def run(self):
        self.on_cycle()
        self.on_render()

    def cycle(self,
        keyboard_active=set(),
        keyboard_pressed=set(),
        cursor=(0,0)):

        self.on_pre_cycle(self)
        if len(keyboard_pressed) or len(keyboard_active):
            self.on_keyboard(keyboard_active, keyboard_pressed)

        if self.cursor != cursor:
            self.on_cursor(cursor)
            self.cursor = cursor


        self.on_pre_render()
        self.run()
        self.on_post_render()
        self.on_post_cycle()

