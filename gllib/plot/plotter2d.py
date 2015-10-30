#-*- coding: utf-8 -*-
"""
plot2d

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.renderer import renderer, primitives, window
from gllib.shader import Shader, Program
from gllib.helper import load_lib_file, hex_to_rgba, resource_path
from gllib.camera import Camera2d
from gllib.application import GlApplication
from gllib.controller import Controller
from gllib.plot import axis 
from gllib.renderer.primitives import SimplePrimitivesRenderer
from gllib.glfw import *
from PIL import ImageFont

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
        'aa0000ff',
        '00aa00ff',
        '0000aaff',
        'aaaa00ff',
        'aa00aaff',
        '00aaaaff',
    ]
}

class Plotter(Controller):
    KEY_TRANSLATION_SPEED = 0.05
    KEY_ZOOM_SPEED = 0.02

    def __init__(self, 
        camera=None, 
        axis=[2,2], 
        origin=[1,-1],
        axis_units=[1,1],
        axis_unit_symbols=[None,None],
        axis_subunits=[9,9],
        color_scheme=DEFAULT_COLORS,
        graphs={}
    ):
        Controller.__init__(self, camera)

        if GlApplication.DEBUG:
            color_scheme = DEBUG_COLORS

        self.graphs               = graphs or {}
        self.plot_camera          = None
        self._axis_translation    = (5, 5)
        self._axis_space          = (75, 75, 10, 10)
        self._plot_plane_min_size = (100, 100)
        self._axis                = axis 
        self._axis_units          = axis_units 
        self._axis_subunits       = axis_subunits
        self._axis_unit_symbols = axis_unit_symbols
        self._origin              = origin
        self.color_scheme = color_scheme

        self._plotframe = None
        self._xaxis     = None
        self._yaxis     = None
        self._debug     = False

        self._axis_font = ImageFont.truetype(resource_path("fonts/arialbd.ttf"), 14, encoding='unic')

        # states
        self._render_graphs      = True
        self._graphs_initialized = False
        self._has_rendered       = False

        self.on_keyboard.append(self.keyboard_callback)
        self.on_pre_render.insert(0, self.pre_render)
        self.on_cycle.append(self.check_graphs)
        self.on_post_render.append(self.post_render)
        self.on_render.append(self.render)
    def keyboard_callback(self, active, pressed):
        update_camera = False
        if GLFW_KEY_W in active:
            self._plotframe.inner_camera.move(0, +self.KEY_TRANSLATION_SPEED)
            update_camera = True
        if GLFW_KEY_A in active:
            self._plotframe.inner_camera.move(self.KEY_TRANSLATION_SPEED)
            update_camera = True
        if GLFW_KEY_S in active:
            self._plotframe.inner_camera.move(0, -self.KEY_TRANSLATION_SPEED)
            update_camera = True
        if GLFW_KEY_D in active:
            self._plotframe.inner_camera.move(-self.KEY_TRANSLATION_SPEED)
            update_camera = True
        if GLFW_KEY_SPACE in active:
            zoom = 1+(-1 if GLFW_KEY_LEFT_SHIFT in active else 1)*self.KEY_ZOOM_SPEED
            translation = self._plotframe.inner_camera.get_position()
            self._plotframe.inner_camera.zoom(zoom)
            update_camera = True
        if update_camera:
            self.camera_updated(self._plotframe.inner_camera)

    def get_plotframe_size(self):
        """
        returns the absolute size of the plotframe
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._axis_space[1]-self._axis_space[3]), 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._axis_space[0]-self._axis_space[2])
        ]

    def get_xaxis_size(self):
        """
        returns the absolute size of x axis
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._axis_space[1]-self._axis_space[3]), 
            self._axis_space[0]
        ]

    def get_yaxis_size(self):
        """
        returns the absolute size of y axis
        """
        return [
            self._axis_space[1], 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._axis_space[0]-self._axis_space[2]) 
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
        plotframe.modelview.set_position(self._axis_space[0], self._axis_space[2])
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
            self._xaxis = axis.Scale(
                camera       = self.camera,
                scale_camera = self._plotframe.inner_camera,
                size         = self.get_xaxis_size(),
                unit         = self._axis_units[0],
                subunits     = self._axis_subunits[0],
                font         = self._axis_font,
                axis         = axis.XAXIS,
                unit_symbol  = self._axis_unit_symbols[0],
                bgcolor      = hex_to_rgba(self.color_scheme['xaxis-bgcolor']),
                linecolor    = hex_to_rgba(self.color_scheme['xaxis-linecolor']),
                fontcolor    = hex_to_rgba(self.color_scheme['xaxis-fontcolor']),
            )
            self._xaxis.init()
            self._update_xaxis()

        if self._axis_space[1] > 0:
            self._yaxis = axis.Scale(
                camera       = self.camera,
                scale_camera = self._plotframe.inner_camera,
                size         = self.get_yaxis_size(),
                unit         = self._axis_units[1],
                subunits     = self._axis_subunits[1],
                font         = self._axis_font,
                axis         = axis.YAXIS,
                unit_symbol  = self._axis_unit_symbols[1],
                bgcolor      = hex_to_rgba(self.color_scheme['yaxis-bgcolor']),
                linecolor    = hex_to_rgba(self.color_scheme['yaxis-linecolor']),
                fontcolor    = hex_to_rgba(self.color_scheme['yaxis-fontcolor']),
            )
            self._yaxis.init()
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
        initial_scaling = [self._plotframe.inner_camera.get_matrix()[0], self._plotframe.inner_camera.get_matrix()[5]]
        for graph in [g for g in self.graphs.values() if not g.initialized]:
            graph.init()
            if graph.color is None:
                graph.program.use()
                graph.program.uniform('color', hex_to_rgba(colors[graph_color_index%colors_length]))
                graph.program.uniform('initial_scaling', initial_scaling)
                graph.program.unuse()
                graph_color_index+=1

        self._update_graph_matricies()
        self._graphs_initialized = True

    def _update_xaxis(self):
        """
        updates camera and modelview of the x axis
        """
        if self._axis_space[0] > 0:
            self._xaxis.size = self.get_xaxis_size()
            self._xaxis.update_camera(self.camera)

            self._xaxis.modelview.set_position(self._axis_space[1], self.get_plotframe_size()[1]-1*self._axis_translation[0]+self._axis_space[2])
            self._xaxis.update_modelview()

    def _update_yaxis(self):
        """
        updates camera and modelview of the y axis
        """
        if self._axis_space[1] > 0:
            translation = self._plotframe.inner_camera.get_position()[1]
            self._yaxis.size = self.get_yaxis_size()
            self._yaxis.capture_size = self.get_yaxis_size()
            
            self._yaxis.modelview.set_position(self._axis_translation[1],self._axis_space[2])
            self._yaxis.update_modelview()       
            self._yaxis.update_camera(self.camera)

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

    # controller action events

    def pre_render(self):
        glEnable(GL_BLEND);
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA);
        glClearColor(*hex_to_rgba(self.color_scheme['bgcolor']))

    def post_render(self):
        self._has_rendered = True

    def check_graphs(self):
        if not self._graphs_initialized:
            self.init_graphs()  

    def render(self):

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

        self._plotframe.render()
        self._yaxis.render()
        self._xaxis.render()
        

        


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
    'xaxis-fontcolor'      : 'ffffffff',
    'yaxis-linecolor'      : '99D699ff',
    'yaxis-bgcolor'        : '00333300',
    'yaxis-fontcolor'      : 'ffffffff',
    'graph-colors': [
        'FF0000bb',
        '00ff00bb',
        '0000ffbb',
        'ff00ffbb',
        '00ffffbb',
    ]
}

