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

from OpenGL.GL import *

class ExampleController(Controller):
    def __init__(self, camera=None):
        Controller.__init__(self, camera)
        self.rectangle1 = None
        self.rectangle2 = None
        self.framebuffer = None 

    def init(self):
        self.framebuffer = Framebuffer(self.camera, [300, 300], clear_color=[1,0,0,1])
        self.framebuffer.init(self)

        # first quad
        self.rectangle1 = SimplePrimitivesRenderer(self.framebuffer.inner_camera)
        self.rectangle1.init(self)
        self.rectangle1.set_primitives_type(GL_TRIANGLE_STRIP)
        self.rectangle1.buffer_data([100, 100, 200, 100, 100, 200, 200, 200])

        # second quad
        self.rectangle2 = SimplePrimitivesRenderer(self.camera)
        self.rectangle2.init(self)
        self.rectangle2.set_primitives_type(GL_TRIANGLE_STRIP)
        self.rectangle2.buffer_data([400, 400, 500, 400, 400, 500, 500, 500])

        self.camera.on_change_matrix.append(self.rectangle2.update_camera)
        self.camera.on_change_matrix.append(self.framebuffer.update_camera)
        self.camera.on_change_matrix.append(self.buffer_rect2_data)
        Controller.init(self)

    def buffer_rect2_data(self, camera):
        delta_x = self.camera.screensize[0] - self.camera.initial_screensize[0]
        self.rectangle2.buffer_data([400+delta_x, 400, 500+delta_x, 400, 400+delta_x, 500, 500+delta_x, 500])

    def run(self):
        self.framebuffer.use()
        self.rectangle1.render(self)
        self.framebuffer.unuse()

        self.rectangle2.render(self)
        self.framebuffer.render(self)

window = GlWindow(600, 600, '2 cool quads 4 yolo')
window.set_controller(ExampleController())

app = GlApplication()
app.windows.append(window)






app.run()