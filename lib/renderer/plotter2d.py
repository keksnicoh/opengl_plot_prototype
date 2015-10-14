#-*- coding: utf-8 -*-
"""
plot2d

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.renderer import renderer, primitives, window
from lib.shader import Shader, Program
from lib.helper import load_lib_file
from lib.camera import Camera2d
from lib.plot.axis import Scale
import numpy 

from OpenGL.GL import *

class Plotter(renderer.Renderer):
    def __init__(self, camera, axis=[0,1], origin=[0,-1]):
        renderer.Renderer.__init__(self, camera)

        self.graphs = {}
        self.plot_camera = None

        self._axis_space = (70, 50)
        self._plot_plane_min_size = (100, 100)
        self._axis = axis 
        self._origin = origin

        self._plotframe = None
        self._xaxis_frame = None
        self._yaxis_frame = None
        self._debug = False

        # states
        self._render_graphs = True
        self._render_axis = True
        self._graphs_initialized = False

    def get_plotframe_size(self):
        """
        returns the absolute size of the plotframe
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._axis_space[1]), 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._axis_space[0])
        ]

    def get_xaxis_size(self):
        """
        returns the absolute size of x axis
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._axis_space[1]), 
            self._axis_space[0]
        ]

    def get_yaxis_size(self):
        """
        returns the absolute size of y axis
        """
        return [
            self._axis_space[1], 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._axis_space[0])
        ]

    def init(self, controller):
        """
        initializes plot2d
        """
        # setup axis
        if self._axis_space[0] > 0:
            x_axis = Scale(self.camera, self.get_xaxis_size())
            #xaxis_frame = window.Framebuffer(self.camera, self.get_xaxis_size(), screen_mode=window.Framebuffer.SCREEN_MODE_STRECH, clear_color=[1,0,0,1])
            #xaxis_frame.init(controller)
            #xaxis_frame.modelview.set_position(self._axis_space[1], self.get_plotframe_size()[1])
            #xaxis_frame.update_modelview()
            #self._xaxis_frame = xaxis_frame
            self._xaxis_frame = x_axis

        if self._axis_space[1] > 0:
            yaxis_frame = window.Framebuffer(self.camera, self.get_yaxis_size(), screen_mode=window.Framebuffer.SCREEN_MODE_STRECH,clear_color=[1,0,0,1])
            yaxis_frame.init(controller)
            self._yaxis_frame = yaxis_frame

        # setup plotplane
        plotframe = window.Framebuffer(self.camera, self.get_plotframe_size(), screen_mode=window.Framebuffer.SCREEN_MODE_STRECH,clear_color=[1,1,1,1])
        plotframe.init(controller)
        plotframe.modelview.set_position(self._axis_space[1], 0)
        plotframe.update_modelview()

        # setup plotplane camera
        plotframe.inner_camera.set_base_matrix(numpy.array([
            1, 0, 0, 0,
            0, -1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ], dtype=numpy.float32))
        plotframe.inner_camera.set_scaling(self._axis)
        plotframe.inner_camera.set_position(*self._origin)

        self._plotframe = plotframe

        # camera update event
        self.camera.on_change_matrix.append(self.camera_updated)

    def init_graphs(self):
        """
        initializes the graphs if neccessary and 
        updates graph matricies
        """
        for graph in [g for g in self.graphs.values() if not g.initialized]:
            graph.init()
        self._update_graph_matricies()

    def camera_updated(self, camera):
        if self._axis_space[0] > 0:
            self._xaxis_frame.screensize   = self.get_xaxis_size()
            self._xaxis_frame.capture_size = self.get_xaxis_size()
            self._xaxis_frame.update_camera(self.camera)

            self._xaxis_frame.modelview.set_position(self._axis_space[1], self.get_plotframe_size()[1])
            self._xaxis_frame.update_modelview()

        if self._axis_space[1] > 0:
            self._yaxis_frame.screensize   = self.get_yaxis_size()
            self._yaxis_frame.capture_size = self.get_yaxis_size()
            self._yaxis_frame.update_camera(camera)

        self._plotframe.screensize = self.get_plotframe_size()
        self._plotframe.capture_size = self.get_plotframe_size()
        self._plotframe.update_camera(camera)

        self._plotframe.inner_camera.set_screensize(self.get_plotframe_size())
        self._update_graph_matricies()

        self._render_graphs = True
        self._render_axis = True

    def _update_graph_matricies(self):
        for graph in self.graphs.values():
            # strech domain a little bit over plot plane boundaries
            # XXX
            # check this for static domains
            plot_camera = self._plotframe.inner_camera;
            axis        = plot_camera.get_screen_scaling()
            origin      = plot_camera.get_position()

            domain_matrix = graph.domain.get_transformation_matrix(
                axis=(axis[0]*1.05, axis[1]*1.05),
                origin=(origin[0]+0.025*axis[0],origin[1]+0.025*axis[1]),
            )

            graph.program.use()
            graph.program.uniform('mat_camera', plot_camera.get_matrix())
            graph.program.uniform('mat_domain', domain_matrix)
            graph.program.unuse() 

    def render(self, controller):
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);

        if not self._graphs_initialized:
            self.init_graphs()

        # render axis if neccessary
        if self._render_axis:
            if self._axis_space[1] > 0:
                self._yaxis_frame.use()
                self._yaxis_frame.unuse()
        
            if self._axis_space[0] > 0:
                self._xaxis_frame.use()
                self._xaxis_frame.unuse()
                
            self._render_axis = False

        if self._render_graphs:
            # only render graphs if neccessary
            self._plotframe.use()

            if self._debug:
                glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

            # graph rendering
            for id, graph in self.graphs.items():

                graph.render(self)

            if self._debug: 
                glPolygonMode(GL_FRONT_AND_BACK, GL_FILL);

            self._plotframe.unuse()
            self._render_graphs = False

        self._plotframe.render(controller)
        self._xaxis_frame.render(controller)
        self._yaxis_frame.render(controller)




