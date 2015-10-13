#-*- coding: utf-8 -*-
"""
renderers for primitives.

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.renderer import renderer, primitives, window
from lib.shader import Shader, Program
from lib.helper import load_lib_file
from OpenGL.GL import *
class Plotter(renderer.Renderer):
    def __init__(self, camera):
        renderer.Renderer.__init__(self, camera)
        self._axis_space = (70, 50)
        self._plot_plane_min_size = (100, 100)
        self.graphs = {}
        self._render_graphs = True
        self._render_axis = True

    def init(self, controller):
        if self._axis_space[0] > 0:
            self.xaxis_frame = window.Framebuffer(self.camera, self.get_xaxis_size(), screen_mode=window.Framebuffer.SCREEN_MODE_STRECH, clear_color=[1,0,0,1])
            self.xaxis_frame.init(controller)
            self.xaxis_frame.modelview.set_position(self._axis_space[1], self.get_plotplane_size()[1])
            self.xaxis_frame.update_modelview()

        if self._axis_space[1] > 0:
            self.yaxis_frame = window.Framebuffer(self.camera, self.get_yaxis_size(), screen_mode=window.Framebuffer.SCREEN_MODE_STRECH,clear_color=[1,0,0,1])
            self.yaxis_frame.init(controller)

        self.plotplane = window.Framebuffer(self.camera, self.get_plotplane_size(), screen_mode=window.Framebuffer.SCREEN_MODE_STRECH,clear_color=[1,1,1,1])
        self.plotplane.init(controller)
        self.plotplane.modelview.set_position(self._axis_space[1], 0)
        self.plotplane.update_modelview()


        self.camera.on_change_matrix.append(self.camera_updated)

    def init_graphs(self):

        for graph in self.graphs.values():
            graph.init(self)

            graph.program.use()
            graph.program.uniform('mat_camera', self.plotplane.inner_camera.get_matrix())
            graph.program.unuse()

    def get_plotplane_size(self):
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._axis_space[1]), 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._axis_space[0])
        ]

    def get_xaxis_size(self):
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._axis_space[1]), 
            self._axis_space[0]
        ]

    def get_yaxis_size(self):
        return [
            self._axis_space[1], 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._axis_space[0])
        ]

    def camera_updated(self, camera):
        if self._axis_space[0] > 0:
            self.xaxis_frame.screensize = self.get_xaxis_size()
            self.xaxis_frame.capture_size = self.get_xaxis_size()
            self.xaxis_frame.init_capturing()
            self.xaxis_frame.update_camera(self.camera)
            self.xaxis_frame.modelview.set_position(self._axis_space[1], self.get_plotplane_size()[1])
            self.xaxis_frame.update_modelview()

        if self._axis_space[1] > 0:
            self.yaxis_frame.screensize = self.get_yaxis_size()
            self.yaxis_frame.capture_size = self.get_yaxis_size()
            self.yaxis_frame.init_capturing()
            self.yaxis_frame.update_modelview()
            self.yaxis_frame.update_camera(camera)

        self.plotplane.screensize = self.get_plotplane_size()
        self.plotplane.capture_size = self.get_plotplane_size()
        self.plotplane.init_screen()
        self.plotplane.init_capturing()
        self.plotplane.update_camera(camera)

        self.plotplane.inner_camera.set_screensize(self.get_plotplane_size())
        #print(self.plotplane.inner_camera.get_matrix())
        for graph in self.graphs.values():
            graph.program.use()
            graph.program.uniform('mat_camera', self.plotplane.inner_camera.get_matrix())
            graph.program.uniform('plotplane_screensize', self.get_plotplane_size())
            graph.program.unuse()

        self._render_graphs = True
        self._render_axis = True
            
    def render(self, controller):
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        
        if self._render_axis:
            if self._axis_space[1] > 0:
                self.yaxis_frame.use()
                self.yaxis_frame.unuse()
        
            if self._axis_space[0] > 0:
                self.xaxis_frame.use()
                self.xaxis_frame.unuse()
                
            self._render_axis = False

        if self._render_graphs:
            self.plotplane.use()
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            for id, graph in self.graphs.items():
                graph.render(self)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);
            self.plotplane.unuse()
            self._render_graphs = False

        self.plotplane.render(controller)
        self.xaxis_frame.render(controller)
        self.yaxis_frame.render(controller)




