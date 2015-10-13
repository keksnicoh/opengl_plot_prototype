#-*- coding: utf-8 -*-
"""
example of connecting the SimplePrimitivesRenderer
with controller and window framework

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.application import GlApplication, GlWindow
from lib.controller import Controller
from lib.renderer import plot2d
from lib.plot.domain import VBODomain
from lib.plot.graph import Line2d
from OpenGL.GL import *
import numpy 

window = GlWindow(600, 600, '2 cool quads 4 yolo')

class PlotExample(Controller):
    def init(self):
        LENGTH = 1000 
        data = numpy.zeros(LENGTH*2, dtype=numpy.float32)
        start = 0
        end = 4*numpy.pi
        for i in range(0, LENGTH):
            data[2*i] = (end-start)/LENGTH*i
            data[2*i+1] = 0

        vbo = glGenBuffers(1)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)  
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        domain = VBODomain(vbo)

        graph = Line2d(domain, "y=sin(x)*cos(5*x);", [0,0,0,1])
        self.plotter = plot2d.Plotter(self.camera)
        self.plotter.init(self)

        self.plotter.plotplane.inner_camera.set_scaling([2*numpy.pi, 2])
        self.plotter.plotplane.inner_camera.set_position(*[0, -1])
        self.plotter.graphs['test'] = graph
        
        self.plotter.init_graphs()

        self.camera.on_change_matrix.append(self.plotter.camera_updated)
        Controller.init(self)
    def run(self):
        self.plotter.render(self)

window.set_controller(PlotExample())

app = GlApplication()
app.windows.append(window)

# first quad

app.run()