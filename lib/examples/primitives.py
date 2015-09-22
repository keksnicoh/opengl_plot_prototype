#-*- coding: utf-8 -*-
"""
example of connecting the SimplePrimitivesRenderer
with controller and window framework

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.application import GlApplication, GlWindow
from lib.controller import Controller
from lib.renderer.primitives import SimplePrimitivesRenderer

from OpenGL.GL import *

window = GlWindow(600, 600, '2 cool quads 4 yolo')
controller = Controller()
window.set_controller(controller)

app = GlApplication()
app.windows.append(window)

# first quad
rectangle = SimplePrimitivesRenderer(controller.get_camera())
rectangle.set_primitives_type(GL_TRIANGLE_STRIP)
rectangle.set_vertex_data([100, 100, 300, 100, 100, 300, 300, 300])
controller.on_init.append(rectangle.init)
controller.on_render.append(rectangle.render)

# second quad
rectangle2 = SimplePrimitivesRenderer(controller.get_camera())
rectangle2.set_primitives_type(GL_TRIANGLE_STRIP)
rectangle2.set_vertex_data([400, 400, 500, 400, 400, 500, 500, 500])
controller.on_init.append(rectangle2.init)
controller.on_render.append(rectangle2.render)

app.run()