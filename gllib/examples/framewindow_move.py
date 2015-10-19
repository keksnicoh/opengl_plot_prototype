#-*- coding: utf-8 -*-
"""
example of connecting the SimplePrimitivesRenderer
with controller and window framework

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.application import GlApplication, GlWindow
from gllib.controller import Controller
from gllib.renderer.primitives import SimplePrimitivesRenderer
from gllib.renderer.window import Framebuffer
import numpy
from OpenGL.GL import *
from time import time

class ExampleController(Controller):
    def __init__(self, camera=None):
        Controller.__init__(self, camera)
        self.rectangle1 = None
        self.rectangle2 = None
        self.framebuffer = None 
        self.start_time = time()
    def init(self):
        self.framebuffer = Framebuffer(
            self.camera, 
            screensize=[600, 150], 
            capture_size=[150, 150], 
            screen_mode=Framebuffer.SCREEN_MODE_REPEAT,
            clear_color=[1,0,0,1])
        self.framebuffer.init(self)

        # first quad
        self.rectangle1 = SimplePrimitivesRenderer(self.framebuffer.inner_camera)
        self.rectangle1.init(self)
        self.rectangle1.set_primitives_type(GL_TRIANGLE_STRIP)
        self.rectangle1.buffer_data([50, 50, 100, 50, 50, 100, 100, 100])

        self.camera.on_change_matrix.append(self.camera_updated)
        Controller.init(self)

    def camera_updated(self, camera):
        self.framebuffer.screensize[0] = camera.screensize[0]
        self.framebuffer.update_camera(camera)
        Controller.camera_updated(self, camera)

    def run(self):
        if self.framebuffer.has_captured():
            self.framebuffer.use()
            self.rectangle1.render(self)
            self.framebuffer.unuse()
        self.framebuffer.render(self)
        self.framebuffer.screen_translation[0] = 100*(time()-self.start_time)
        self.framebuffer.screen_translation[1] = 100*numpy.sin(0.1*self.framebuffer.screen_translation[0])
window = GlWindow(600, 600, '2 cool quads 4 yolo')
window.set_controller(ExampleController())

app = GlApplication()
app.windows.append(window)



app.run()