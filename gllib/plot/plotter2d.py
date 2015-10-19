#-*- coding: utf-8 -*-
"""
plot2d

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.renderer import renderer, primitives, window
from gllib.shader import Shader, Program
from gllib.helper import load_lib_file, hex_to_rgba
from gllib.camera import Camera2d
from gllib.controller import Controller
from gllib.plot import axis 
from gllib.glfw import *

import numpy 

from OpenGL.GL import *

DEFAULT_COLORS = {
    'bgcolor'              : 'ffffffff',
    'plotplane-bgcolor'    : 'ffffffff',
    'plotplane-bordercolor': '000000ff',
    'xaxis-bgcolor'        : 'ffffffff',
    'yaxis-bgcolor'        : 'ffffffff',
    'xaxis-linecolor'      : '000000ff',
    'xaxis-bgcolor'        : '00000000',
    'xaxis-fontcolor'      : '000000ff',
    'yaxis-linecolor'      : '000000ff',
    'yaxis-bgcolor'        : '00000000',
    'yaxis-fontcolor'      : '000000ff',
    'graph-colors': [
        '000000ff',
        'ff0000ff',
        '00ff00ff',
        '0000ffff',
        'ffff00ff',
        'ff00ffff',
        '00ffffff',
    ]
}

class Plotter(Controller):
    KEY_TRANSLATION_SPEED = 0.05
    KEY_ZOOM_SPEED = 0.02

    def __init__(self, 
        camera=None, 
        axis=[1,1], 
        origin=[0,-1],
        axis_units=[1,1],
        axis_subunits=[9,9],
        color_scheme=DEFAULT_COLORS
    ):
        Controller.__init__(self, camera)

        self.graphs               = {}
        self.plot_camera          = None
        self._axis_translation    = (5, 5)
        self._axis_space          = (50, 50)
        self._plot_plane_min_size = (100, 100)
        self._axis                = axis 
        self._axis_units          = axis_units 
        self._axis_subunits       = axis_subunits
        self._origin              = origin

        self.color_scheme = color_scheme

        self._plotframe   = None
        self._xaxis_frame = None
        self._yaxis_frame = None
        self._debug       = False

        # states
        self._render_graphs      = True
        self._graphs_initialized = False
        self._has_rendered       = False

        self.on_keyboard.append(self.keyboard_callback)

    def keyboard_callback(self, active, pressed):
        update_camera = False
        if GLFW_KEY_W in active:
            self._plotframe.inner_camera.move(0, +self.KEY_TRANSLATION_SPEED)
            update_camera = True
            #self.camera_updated(self._plotframe.inner_camera)
        if GLFW_KEY_A in active:
            self._plotframe.inner_camera.move(self.KEY_TRANSLATION_SPEED)
            update_camera = True
            #self.camera_updated(self._plotframe.inner_camera)
        if GLFW_KEY_S in active:
            self._plotframe.inner_camera.move(0, -self.KEY_TRANSLATION_SPEED)
            update_camera = True
            #self.camera_updated(self._plotframe.inner_camera)
        if GLFW_KEY_D in active:
            self._plotframe.inner_camera.move(-self.KEY_TRANSLATION_SPEED)
            update_camera = True
        if GLFW_KEY_SPACE in active:
            zoom = 1+(-1 if GLFW_KEY_LEFT_SHIFT in active else 1)*self.KEY_ZOOM_SPEED
            translation = self._plotframe.inner_camera.get_position()
            self._plotframe.inner_camera.zoom(zoom)
            #self._plotframe.inner_camera.move((zoom-1)*translation[0])
            update_camera = True
        if update_camera:
            self.camera_updated(self._plotframe.inner_camera)

    def get_plotframe_size(self):
        """
        returns the absolute size of the plotframe
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-2*self._axis_space[1]), 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-2*self._axis_space[0])
        ]

    def get_xaxis_size(self):
        """
        returns the absolute size of x axis
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-2*self._axis_space[1]), 
            self._axis_space[0]
        ]

    def get_yaxis_size(self):
        """
        returns the absolute size of y axis
        """
        return [
            self._axis_space[1], 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-2*self._axis_space[0]) 
        ]

    def init(self):
        """
        initializes plot2d
        """
        # setup axis

        # setup plotplane
        plotframe = window.Framebuffer(
            camera      = self.camera, 
            screensize  = self.get_plotframe_size(), 
            screen_mode = window.Framebuffer.SCREEN_MODE_STRECH,
            clear_color = hex_to_rgba(self.color_scheme['plotplane-bgcolor']),
            border      = window.PixelBorder(hex_to_rgba(self.color_scheme['plotplane-bordercolor']))
        )

        plotframe.init()
        plotframe.modelview.set_position(self._axis_space[1], self._axis_space[1])
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

        # setup axis
        if self._axis_space[0] > 0:
            self._xaxis_frame = axis.Scale(
                camera       = self.camera,
                scale_camera = self._plotframe.inner_camera,
                size         = self.get_xaxis_size(),
                unit         = self._axis_units[0],
                subunits     = self._axis_subunits[0],
                axis         = 0,
                bgcolor      = hex_to_rgba(self.color_scheme['xaxis-bgcolor']),
                linecolor    = hex_to_rgba(self.color_scheme['xaxis-linecolor']),
                fontcolor    = hex_to_rgba(self.color_scheme['xaxis-fontcolor']),
            )
            self._xaxis_frame.init()
            self._update_xaxis()

        if self._axis_space[1] > 0:
            self._yaxis_frame = axis.Scale(
                camera       = self.camera,
                scale_camera = self._plotframe.inner_camera,
                size         = self.get_yaxis_size(),
                unit         = self._axis_units[1],
                subunits     = self._axis_subunits[1],
                axis         = 1,
                bgcolor      = hex_to_rgba(self.color_scheme['yaxis-bgcolor']),
                linecolor    = hex_to_rgba(self.color_scheme['yaxis-linecolor']),
                fontcolor    = hex_to_rgba(self.color_scheme['yaxis-fontcolor']),
            )
            self._yaxis_frame.init()
            self._update_yaxis()

        # parent controller initialization
        Controller.init(self)

    def init_graphs(self):
        """
        initializes the graphs if neccessary and 
        updates graph matricies
        """
        colors = self.color_scheme['graph-colors']
        colors_length = len(colors)
        graph_color_index = 0
        for graph in [g for g in self.graphs.values() if not g.initialized]:
            graph.init()
            if graph.color is None:
                graph.program.use()
                graph.program.uniform('color', hex_to_rgba(colors[graph_color_index%colors_length]))
                graph.program.unuse()
                graph_color_index+=1

        self._update_graph_matricies()
        self._graphs_initialized = True

    def _update_xaxis(self):
        """
        updates camera and modelview of the x axis
        """
        if self._axis_space[0] > 0:
            size = self.get_xaxis_size()
            #size[1] += self._axis_translation[0]
            self._xaxis_frame.size   = size
            self._xaxis_frame.update_camera(self.camera)

            self._xaxis_frame.modelview.set_position(self._axis_space[1], self.get_plotframe_size()[1]-1*self._axis_translation[0]+self._axis_space[0])
            self._xaxis_frame.update_modelview()

    def _update_yaxis(self):
        """
        updates camera and modelview of the y axis
        """
        if self._axis_space[1] > 0:
            size = self.get_yaxis_size()
            #size[0] += self._axis_translation[1]
            #size[0] += self._plotframe.inner_camera.get_position()[0]

            translation = self._plotframe.inner_camera.get_position()[1]
            self._yaxis_frame.size   = size
            self._yaxis_frame.capture_size = self.get_yaxis_size()
            
            self._yaxis_frame.modelview.set_position(self._axis_translation[1],self._axis_space[0])
            self._yaxis_frame.update_modelview()       
            self._yaxis_frame.update_camera(self.camera)
    def _update_plotframe_camera(self):
        """
        updates plotframe camera
        """
        self._plotframe.screensize = self.get_plotframe_size()
        self._plotframe.capture_size = self.get_plotframe_size()
        self._plotframe.update_camera(self.camera)
        self._plotframe.inner_camera.set_screensize(self.get_plotframe_size())
      
    def camera_updated(self, camera):
        """
        updates cameras and modelview of axis and plotplane
        """
        self._update_xaxis()
        self._update_yaxis()

        self._update_plotframe_camera()
        self._update_graph_matricies()

        self._render_graphs = True

        Controller.camera_updated(self, camera)

    def _update_graph_matricies(self):
        for graph in self.graphs.values():
            # strech domain a little bit over plot plane boundaries
            # XXX
            # check this for static domains
            plot_camera = self._plotframe.inner_camera;
            axis        = plot_camera.get_screen_scaling()
            origin      = plot_camera.get_position()

            domain_matrix = graph.domain.get_transformation_matrix(
                #axis=(axis[0]*1.05, axis[1]*1.05),
                #origin=(origin[0]+0.025*axis[0],origin[1]+0.025*axis[1]),
                axis=(axis[0], axis[1]),
                origin=(origin[0],origin[1]),
            )

            graph.program.use()
            graph.program.uniform('mat_camera', plot_camera.get_matrix())
            graph.program.uniform('mat_domain', domain_matrix)
            graph.program.uniform('zoom', plot_camera.get_zoom())
            graph.program.unuse() 

    def run(self):

        if not self._graphs_initialized:
            self.init_graphs()


        # render axis if neccessary
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

        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glClearColor(*hex_to_rgba(self.color_scheme['bgcolor']))
        self._plotframe.render()
        self._yaxis_frame.render()
        self._xaxis_frame.render()
        self._has_rendered = True


DEBUG_COLORS = {
    'bgcolor'              : '000000ff',
    'plotplane-bgcolor'    : 'ccccccff',
    'plotplane-bordercolor': '000000ff',
    'xaxis-bgcolor'        : 'ffffffff',
    'yaxis-bgcolor'        : 'ffffffff',
    'xaxis-linecolor'      : '000000ff',
    'xaxis-bgcolor'        : 'aaaa0088',
    'xaxis-fontcolor'      : '000000ff',
    'yaxis-linecolor'      : '000000ff',
    'yaxis-bgcolor'        : '00aaaa88',
    'yaxis-fontcolor'      : '000000ff',
    'graph-colors': [
        '000000ff',
        'ff0000ff',
        '00ff00ff',
        '0000ffff',
        'ffff00ff',
        'ff00ffff',
        '00ffffff',
    ]
}


DARK_COLORS = {
    'bgcolor'              : '000000ff',
    'plotplane-bgcolor'    : '02050eff',
    'plotplane-bordercolor': 'FF9900ff',
    'xaxis-bgcolor'        : '020609ff',
    'yaxis-bgcolor'        : '020609ff',
    'xaxis-linecolor'      : '99D699ff',
    'xaxis-bgcolor'        : '00333300',
    'xaxis-fontcolor'      : '000000ff',
    'yaxis-linecolor'      : '99D699ff',
    'yaxis-bgcolor'        : '00333300',
    'yaxis-fontcolor'      : '000000ff',
    'graph-colors': [
        'FF000099',
        '00ff0099',
        '0000ff99',
    ]
}

