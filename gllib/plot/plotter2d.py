#-*- coding: utf-8 -*-
"""
plot2d

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.renderer import window
from gllib.shader import Shader, Program
from gllib.helper import hex_to_rgba, resource_path, load_lib_file
from gllib.application import GlApplication
from gllib.controller import Controller
from gllib.matrix import ModelView
from gllib.plot import axis 
from gllib.util import Event
from gllib.glfw import *
from gllib.renderer.font import FontRenderer, RelativeLayout, Text, AbsoluteLayout
from gllib.buffer import VertexBuffer, VertexArray
from gllib.plot.field import Field
from gllib.renderer.shape import ShapeInstance, ShapeRenderer, Rectangle 
import numpy as np 
from collections import OrderedDict

from PIL import ImageFont
from OpenGL.GL import *

DEFAULT_COLORS = {
    'bgcolor'              : 'ffffffff',
    'plotplane-bgcolor'    : 'ffffffff',
    'plotplane-bordercolor': '000000ff',

    'axis-fontsize'        : 15,
    'axis-font'            : 'fonts/arialbd.ttf',
    
    'title-fontsize'       : 25,
    'title-boxheight'      : 40,
    'title-font'           : 'fonts/arialbd.ttf',
    
    'xlabel-fontsize'      : 18,
    'xlabel-boxheight'     : 35,
    'xlabel-font'          : 'fonts/arialbd.ttf',
    
    'ylabel-fontsize'      : 18,
    'ylabel-boxheight'     : 35,
    'ylabel-font'          : 'fonts/arialbd.ttf',

    'font-color': '000000ff',

    'xaxis-bgcolor'        : 'ffffffff',
    'xaxis-linecolor'      : '000000ff',
    'xaxis-bgcolor'        : '00000000',
    'xaxis-fontcolor'      : '000000ff',

    'yaxis-linecolor'      : '000000ff',
    'yaxis-bgcolor'        : '00000000',
    'yaxis-fontcolor'      : '000000ff',
    'yaxis-bgcolor'        : 'ffffff00',

    'select-area-bgcolor'  : 'dddddd66',
    'select-area-pending-bgcolor'  : '6666ffbb',
    'select-area-border-color': '000000ff',
    'select-area-border-size': 1,

    'plotframe-border-size': 2,
    'plotframe-border-color': '000000ff',
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

class Plotter(object, Controller):
    KEY_TRANSLATION_SPEED = 0.05
    KEY_ZOOM_SPEED        = 0.02
    FONT_ENCODING         = 'unic'

    STATE_SELECT_AREA         = 'STATE_SELECT_AREA'
    STATE_IDLE                = 'STATE_IDLE'
    STATE_SELECT_AREA_PENDING = 'STATE_SELECT_AREA_PENDING'

    def __init__(self, 
        camera            = None, 
        axis              = [2,2], 
        origin            = [0,0],
        axis_units        = [1,1],
        xlabel            = None,
        ylabel            = None,
        title             = None,
        plotmode          = None,
        colorlegend      = None,
        axis_unit_symbols = [None,None],
        axis_subunits     = [4,4],
        color_scheme      = DEFAULT_COLORS,
        graphs            = {},
        axis_measures     = [] 
    ):
        Controller.__init__(self, camera)

        if GlApplication.DEBUG:
            color_scheme = DEBUG_COLORS
        
        self.graphs               = graphs or OrderedDict()
        self.plot_camera          = None
        self.color_scheme         = color_scheme
        self.plotmode = plotmode
        self.colorlegend = colorlegend

        if type(plotmode) is str:
            if plotmode not in _PLOTMODE_ALIASES:
                raise ValueError('unkown plotmode "{}". Available aliases are: {}'.format(
                    plotmode, ', '.join(_PLOTMODE_ALIASES.keys())
                ))
            self.plotmode = _PLOTMODE_ALIASES[plotmode][0](
                *_PLOTMODE_ALIASES[plotmode][1], 
                **_PLOTMODE_ALIASES[plotmode][2]
            )

        self._axis_measures = axis_measures

        self.on_state = Event()

        self._axis_translation     = (10, 0)
        self._plotplane_margin     = [5, 10, 40, 45]
        self._plot_plane_min_size  = (100, 100)
        self._axis                 = axis 
        self._axis_units           = axis_units 
        
        self._xlabel               = xlabel
        self._ylabel               = ylabel
        self._title                = title
        self._title_font           = None
        self._xlabel_font          = None 
        self._ylabel_font          = None

        self._axis_subunits        = axis_subunits
        self._axis_unit_symbols    = axis_unit_symbols
        self._origin               = origin
        
        self._plotframe            = None
        self._xaxis                = None
        self._yaxis                = None
        self._colorlegend_axis              = None
        self._debug                = False
        self._fontrenderer         = None

        # dstates
        self.render_graphs         = True
        self._graphs_initialized   = False
        self._has_rendered         = False
        self._state = 0 
        self._select_area          = [0,0,0,0]
        self._select_area_rectangle = None
        self._colorlegend_frame = None 
        self._colorlegend = None
        self._colorlegend_graph = None
        self._axis_font = ImageFont.truetype(
            resource_path(color_scheme['axis-font']), 
            color_scheme['axis-fontsize'], 
            encoding=Plotter.FONT_ENCODING
        )


        self.on_keyboard.append(self.keyboard_callback)
        self.on_mouse.append(self.mouse_callback)
        self.on_pre_render.insert(0, self.pre_render)
        self.on_pre_cycle.append(Plotter.check_graphs)
        self.on_post_render.append(self.post_render)
        self.on_render.append(self.render)

    # -- HELPER UTILITIES -----------------------------------------------------------
    
    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value
        self.on_state(self._state)
    

    def coord_in_plotframe(self, pos):
        """
        checks whether a given 
        coordinate is inside plotspace frame.
        """
        frame_pos = self.plotframe_position
        frame_size = self.plotframe_size

        return pos[0] > frame_pos[0] and pos[0] < frame_pos[0] + frame_size[0] \
           and pos[1] > frame_pos[1] and pos[1] < frame_pos[1] + frame_size[1]

    def coord_to_plotframe(self, coord):
        """
        transforms a given window space coordinate into
        plotspace coordinates. 
        """
        plotcam = self._plotframe.inner_camera
        frame_size = self.plotframe_size

        relative = (
            coord[0]-self.plotframe_position[0],
            frame_size[1]-coord[1]+ self.plotframe_position[1]
        )
        scaled = (
            float(plotcam.scaling[0])/plotcam.get_zoom()/frame_size[0]*relative[0], 
            float(plotcam.scaling[1])/plotcam.get_zoom()/frame_size[1]*relative[1]
        )
        return (
            scaled[0]-plotcam.position[0],
            scaled[1]+plotcam.position[1]
        )

    # -- EVENTS -------------------------------------------------------------------

    def keyboard_callback(self, active, pressed):
        update_camera = False
        if GLFW_KEY_W in active:
            self._plotframe.inner_camera.move(
                0, 
                self.KEY_TRANSLATION_SPEED
                *self._plotframe.inner_camera.scaling[1]
                /self._plotframe.inner_camera.get_zoom()
            )
            update_camera = True
        if GLFW_KEY_A in active:
            self._plotframe.inner_camera.move(
                self.KEY_TRANSLATION_SPEED
                *self._plotframe.inner_camera.scaling[0]
                /self._plotframe.inner_camera.get_zoom()
            )
            update_camera = True
        if GLFW_KEY_S in active:
            self._plotframe.inner_camera.move(
                0, 
                -self.KEY_TRANSLATION_SPEED
                *self._plotframe.inner_camera.scaling[1]
                /self._plotframe.inner_camera.get_zoom()
            )
            update_camera = True
        if GLFW_KEY_D in active:
            self._plotframe.inner_camera.move(
                -self.KEY_TRANSLATION_SPEED
                *self._plotframe.inner_camera.scaling[0]
                /self._plotframe.inner_camera.get_zoom()
            )
            update_camera = True
        if GLFW_KEY_SPACE in active:
            self.zoom(1+(+1 if GLFW_KEY_LEFT_SHIFT in active else -1)*self.KEY_ZOOM_SPEED)
        if update_camera:
            self.camera_updated(self._plotframe.inner_camera)

    def mouse_callback(self, win, button, action, mod):
        # STATE SELECT AREA 
        def area_selecting():
            self.state = self.STATE_SELECT_AREA
            self._select_area_rectangle.color = hex_to_rgba(self.color_scheme['select-area-bgcolor'])

            self._select_area = list(self.cursor) + [0,0]
            self.shaperenderer.draw_instance(self._select_area_rectangle)

        def area_selected():
            pos = self.cursor 

            # only if mouse is in the selected area with a 
            # tolerance of 20.
            if pos[0] > self._select_area[0]-20 and pos[0] < self._select_area[2]+20 \
               and pos[1] > self._select_area[1]-20 and pos[1] < self._select_area[3]+20:
                coord_a = self.coord_to_plotframe(self._select_area[0:2])
                coord_b = self.coord_to_plotframe(self._select_area[2:4])
                self.show_area(coord_a+coord_b)
                self._select_area = [0,0,0,0]

            self.state = self.STATE_IDLE
            self.shaperenderer.erase_instance(self._select_area_rectangle)
        def area_pending():
            self.state = self.STATE_SELECT_AREA_PENDING
            self._select_area_rectangle.color = hex_to_rgba(self.color_scheme['select-area-pending-bgcolor'])
            self._select_area = self._select_area[0:2] + list(self.cursor)

            # if user opens the box in the wrong direction
            # we need to fix the coordinates so that the upper
            # left corner stays in upper left corner and so 
            # for the lower right corner...
            if self._select_area[0] > self._select_area[2]:
                tmp = self._select_area[2]
                self._select_area[2] = self._select_area[0]
                self._select_area[0] = tmp
            if self._select_area[1] > self._select_area[3]:
                tmp = self._select_area[3]
                self._select_area[3] = self._select_area[1]
                self._select_area[1] = tmp

        if button == GLFW_MOUSE_BUTTON_2:
            if action == 1:
                if self.state == self.STATE_IDLE:
                    if self.coord_in_plotframe(self.cursor):
                        area_selecting()
                elif self.state == self.STATE_SELECT_AREA:
                    area_pending()
                    area_selected()
        elif button == GLFW_MOUSE_BUTTON_1:
            if self.state == self.STATE_SELECT_AREA and action == 0:
                area_pending()
            elif self.state == self.STATE_SELECT_AREA_PENDING and action == 0:
                area_selected()

    # -- PLOTTER INTERACTION --------------------------------------------------------------
    def zoom(self, factor):
        #self._plotframe.inner_camera.zoom(factor)
        plotcam = self._plotframe.inner_camera
        scaling = plotcam.scaling
        plotcam.set_scaling((scaling[0]*factor, scaling[1]*factor))
        self.camera_updated(self._plotframe.inner_camera)

    def show_area(self, area):
        plotcam = self._plotframe.inner_camera
        old_scaling = plotcam.scaling
        axis = (abs(area[2]-area[0]), abs(area[3]-area[1]))
        plotcam.set_scaling(axis)
        plotcam.set_position(-area[0], area[3])
        self.camera_updated(self._plotframe.inner_camera)

    # -- PROPERTIES -------------------------------------------------------------------

    @property 
    def plotframe_position(self): return self._plotplane_margin[3], self._plotplane_margin[0]
    @property
    def plotframe_size(self): return [
        max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._plotplane_margin[1]-self._plotplane_margin[3])-self.colorlegend_boxsize[0], 
        max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._plotplane_margin[0]-self._plotplane_margin[2])
    ]
    @property 
    def colorlegend_size(self):
        if self.colorlegend is None:
            return (0,0)

        return (100-self.colorlegend_margin[1]-self.colorlegend_margin[3], self.camera.screensize[1]-self.colorlegend_margin[0]-self.colorlegend_margin[2])
    
    @property 
    def colorlegend_boxsize(self):
        if self.colorlegend is None:
            return (0,0)
        return (100, self.camera.screensize[1]-self.colorlegend_margin[0]-self.colorlegend_margin[2])

    @property 
    def colorlegend_margin(self):
        if self.colorlegend is None:
            return (0,0,0,0)
        return (self._plotplane_margin[0], 60, self._plotplane_margin[2], 10)

    @property 
    def colorlegend_position(self):
        if self.colorlegend is None:
            return (0,0)

        return (self.plotframe_position[0]+self.plotframe_size[0]+self.colorlegend_margin[3], self.plotframe_position[1])

    def get_xaxis_size(self):
        """
        returns the absolute size of x axis
        DEPRECATED (need to implement multi axis stuff REMOVE THIS STATIC STUFF HERE)
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._plotplane_margin[1]-self._plotplane_margin[3])-self.colorlegend_boxsize[0], 
            10
        ]

    def get_yaxis_size(self):
        """
        returns the absolute size of y axis
        DEPRECATED (need to implement multi axis stuff REMOVE THIS STATIC STUFF HERE)
        """
        return [
            10, 
            self.plotframe_size[1]
        ]

    # -- BUSINESS -------------------------------------------------------------------

    def init_labels(self):
        """
        initializes plot labels.
        """
        axis_space = list(self._plotplane_margin)

        if self._xlabel is not None:
            axis_space[2] += self.color_scheme['xlabel-boxheight']
            self._fontrenderer.layouts['labels'].add_text(
                Text(self._xlabel, ImageFont.truetype(
                    resource_path(self.color_scheme['xlabel-font']), 
                    self.color_scheme['xlabel-fontsize'], 
                    encoding=Plotter.FONT_ENCODING
                )), 
                alignment=RelativeLayout.HCENTER|RelativeLayout.VTOP,
                boxalignment=RelativeLayout.VBOTTOM,
                boxsize=(None, self.color_scheme['xlabel-boxheight'])
            )
        if self._ylabel is not None:
            axis_space[3] += self.color_scheme['ylabel-boxheight']
            self._fontrenderer.layouts['labels'].add_text(
                Text(self._ylabel, ImageFont.truetype(
                    resource_path(self.color_scheme['ylabel-font']), 
                    self.color_scheme['ylabel-fontsize'], 
                    encoding=Plotter.FONT_ENCODING
                )), 
                alignment=RelativeLayout.HCENTER|RelativeLayout.VCENTER,
                boxalignment=RelativeLayout.HLEFT,
                boxsize=(self.color_scheme['ylabel-boxheight'], None),
                rotation=90
            )
        if self._title is not None:
            axis_space[0] += self.color_scheme['title-boxheight']
            self._fontrenderer.layouts['labels'].add_text(
                Text(self._title, ImageFont.truetype(
                    resource_path(self.color_scheme['title-font']), 
                    self.color_scheme['title-fontsize'], 
                    encoding=Plotter.FONT_ENCODING
                )), 
                alignment=RelativeLayout.HCENTER|RelativeLayout.VCENTER,
                boxalignment=RelativeLayout.VTOP,
                boxsize=(None, self.color_scheme['title-boxheight'])
            )
        self._plotplane_margin = axis_space

    def init(self):
        """
        initializes plot2d
        """
        self.shaperenderer = ShapeRenderer(self.camera)
        self.shaperenderer.shapes['default_rectangle'] = Rectangle()
        self.shaperenderer.gl_init()

        # setup axis
        self._fontrenderer = FontRenderer(self.camera)
        self._fontrenderer.layouts['labels'] = RelativeLayout(boxsize=self.camera.screensize)
        self._fontrenderer.layouts['axis'] = AbsoluteLayout()

        self._fontrenderer.init()
        self._fontrenderer.set_color(hex_to_rgba(self.color_scheme['font-color']))
        self.init_labels()

        # setup plotplane
        plotframe = window.Framebuffer(
            camera      = self.camera, 
            screensize  = self.plotframe_size, 
            screen_mode = window.Framebuffer.SCREEN_MODE_STRECH,
            record_mode = self.plotmode.record_mode if self.plotmode is not None else window.Framebuffer.RECORD_CLEAR,
            clear_color = hex_to_rgba(self.color_scheme['plotplane-bgcolor']),
            multisampling = 8,
            blit_texture=True,
        )

        if self.plotmode is not None:
            plotframe.record_program = self.plotmode.get_shader()

        plotframe.init()
        plotframe.modelview.set_position(self._plotplane_margin[3], self._plotplane_margin[0])
        plotframe.update_modelview()

        # setup plotplane camera
        plotframe.inner_camera.set_base_matrix(np.array([
            1, 0, 0, 0,
            0, -1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ], dtype=np.float32))
        plotframe.inner_camera.set_scaling(self._axis)
        plotframe.inner_camera.set_position(*self._origin)
        self._plotframe = plotframe
        self.init_colorlegend()


        # setup axis
        if self._plotplane_margin[0] > 0:
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

        if self._plotplane_margin[1] > 0:
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
        self.state = self.STATE_IDLE

        self._select_area_rectangle = ShapeInstance('default_rectangle', **{
            'size': (0,0),
            'position': (0,0),
            'border': {
                'size': self.color_scheme['select-area-border-size'],
                'color': hex_to_rgba(self.color_scheme['select-area-border-color']),
            },
            'color': hex_to_rgba(self.color_scheme['select-area-bgcolor']),
        })

        self._plotplane = ShapeInstance('default_rectangle', **{
            'size': self.plotframe_size,
            'position': self.plotframe_position,
            'border': {
                'size': self.color_scheme['plotframe-border-size'],
                'color': hex_to_rgba(self.color_scheme['plotframe-border-color']),
            },
            'color': [0,0,0,0],
            'texture': self._plotframe
        })
        self.shaperenderer.draw_instance(self._plotplane)

    def init_colorlegend(self):
        """
        initializes color legend. 
        XXX
        - Refactor me as a kind of widget or so ...
        """
        if self.colorlegend is not None:
            self._colorlegend_frame = window.Framebuffer(
                self.camera, 
                screensize = self.colorlegend_size,
                blit_texture=True,
                clear_color = hex_to_rgba(self.color_scheme['plotplane-bgcolor']),
                multisampling=6
            )  
            self._colorlegend_frame.init()

            colorrange = self.colorlegend.colorrange
            colorrange_length = colorrange[1]-colorrange[0]

            factor = 0.1
            self._colorlegend_frame.inner_camera.set_scaling([1,colorrange_length*(1+2*factor)])
            self._colorlegend_frame.inner_camera.set_position(0,-colorrange_length*factor+colorrange[0])
            self._colorlegend_frame.update_camera(self.camera)

            if self._colorlegend is None:
                self._colorlegend = ShapeInstance('default_rectangle', **{
                    'size': self.colorlegend_size,
                    'position': self.colorlegend_position,
                    'border': {
                        'size': self.color_scheme['plotframe-border-size'],
                        'color': hex_to_rgba(self.color_scheme['plotframe-border-color']),
                    },
                    'color': [0,0,0,0],
                    'texture': self._colorlegend_frame
                })

                self.shaperenderer.draw_instance(self._colorlegend)
            else:
                self._colorlegend.position = self.colorlegend_position
                self._colorlegend.size = self.colorlegend_size
                


            self._colorlegend_graph = Field(
                top_left=(0,colorrange_length*(1+factor)+colorrange[0]),
                bottom_right=(1,colorrange[0]-colorrange_length*factor),
                color_scheme=self.colorlegend,
                data_kernel='fragment_color = vec4({a}+{l}*(1+2*{f})*x.y-{l}*{f},0,0,1)'.format(
                    a=colorrange[0],
                    l=colorrange_length,
                    f=factor)
            )
            self._colorlegend_graph.init()
            plot_camera = self._colorlegend_frame.inner_camera;
            self._colorlegend_graph.program.uniform('mat_camera', plot_camera.get_matrix())
            self._colorlegend_graph.program.uniform('mat_outer_camera', self._plotframe.camera.get_matrix())
            self._colorlegend_graph.program.uniform('mat_domain', np.identity(3))

            self._colorlegend_axis = axis.Fixed(
                camera       = self.camera,
                measurements = self.colorlegend.range,
                bgcolor      = hex_to_rgba(self.color_scheme['yaxis-bgcolor']),
                size         = (self.get_yaxis_size()[0], self.get_yaxis_size()[1]),
                scale_camera = self._colorlegend_frame.inner_camera,
                linecolor    = hex_to_rgba(self.color_scheme['yaxis-linecolor']),
                modelview    = ModelView()
            )
            self._colorlegend_axis.init()
            self._update_measure_axis()
            self._colorlegend_frame.use()
            self._colorlegend_graph.render(self)
            self._colorlegend_frame.unuse()
            font = ImageFont.truetype(
                resource_path(self.color_scheme['ylabel-font']), 
                self.color_scheme['ylabel-fontsize'], 
                encoding=Plotter.FONT_ENCODING
            )
            length = colorrange_length*(1+2*factor)
            shift = colorrange_length*factor
            y_viewspace = lambda y: (1-(float(y-colorrange[0]+shift)/length))*self.colorlegend_size[1]+self.colorlegend_margin[0]
            x_viewspace = self.colorlegend_position[0]+self.colorlegend_size[0]+5
            axis_labels = self._fontrenderer.layouts['axis']
            axis_labels.clear_texts()
            for yplot, label in self._colorlegend_axis.labels:
                axis_labels.add_text(Text(label,font), (x_viewspace, y_viewspace(yplot)-10))



    def init_graphs(self):
        """
        initializes the graphs if neccessary and 
        updates graph matricies
        """
        colors = self.color_scheme['graph-colors']
        colors_length = len(colors)
        graph_color_index = 0
        initial_scaling = [
            self._plotframe.inner_camera.get_matrix()[0], 
            self._plotframe.inner_camera.get_matrix()[5]
        ]
        initial_plane_scaling = [
            self._plotframe.camera.get_matrix()[0], 
            self._plotframe.camera.get_matrix()[5]
        ]
        for graph in [g for g in self.graphs.values() if not g.initialized]:
            if hasattr(graph, 'color') and graph.color is None:
                graph.color = hex_to_rgba(colors[graph_color_index%colors_length])
                graph_color_index+=1

            graph.init()

        self._update_graph_matricies()
        self._graphs_initialized = True

    def _update_xaxis(self):
        """
        updates camera and modelview of the x axis
        """
        if self._plotplane_margin[0] > 0:
            self._xaxis.size = self.get_xaxis_size()
            self._xaxis.update_camera(self.camera)

            self._xaxis.modelview.set_position(self._plotplane_margin[3], self.plotframe_size[1]-self._axis_translation[0]+self._plotplane_margin[0])
            self._xaxis.update_modelview()

    def _update_yaxis(self):
        """
        updates camera and modelview of the y axis
        """
        if self._plotplane_margin[1] > 0:
            #translation = self._plotframe.inner_camera.get_position()[1]
            self._yaxis.size = self.get_yaxis_size()
            self._yaxis.capture_size = self.get_yaxis_size()
            
            self._yaxis.modelview.set_position(self._plotplane_margin[3]-self._axis_translation[1],self._plotplane_margin[0])
            self._yaxis.update_modelview()       
            self._yaxis.update_camera(self.camera)

    def _update_measure_axis(self):
        if self._colorlegend_axis:
            #self._colorlegend_axis.size = self.get_yaxis_size()
            #self._colorlegend_axis.capture_size = self.get_yaxis_size()

            self._colorlegend_axis.modelview.set_position(self._plotplane_margin[3] + self.plotframe_size[0] + self.colorlegend_size[0], self._plotplane_margin[0])
            self._colorlegend_axis.update_modelview()    

            self._colorlegend_axis.update_camera(self.camera)

    def _update_plotframe_camera(self):
        """
        updates plotframe camera
        """
        self._plotframe.screensize = self.plotframe_size
        self._plotframe.capture_size = self.plotframe_size
        self._plotframe.update_camera(self.camera)
        self._plotframe.inner_camera.set_screensize(self.plotframe_size)

    def _update_colorlegend(self): 
        if self.colorlegend is not None:
            self.init_colorlegend()

    def camera_updated(self, camera):
        """
        updates cameras and modelview of axis and plotplane
        """
        self._update_xaxis()
        self._update_yaxis()

        self._update_measure_axis()

        self._update_plotframe_camera()
        self._update_graph_matricies()
        self._update_colorlegend()

        self.render_graphs = True
        self._fontrenderer.layouts['labels'].boxsize = self.camera.screensize
        self.shaperenderer.update_camera()
        self._plotplane.size = self.plotframe_size
        Controller.camera_updated(self, camera)

    def _update_graph_matricies(self):
        for graph in self.graphs.values():
            if hasattr(graph, 'update_plotmeta'):
                # strech domain a little bit over plot plane boundaries
                # XXX
                # check this for static domains
                plot_camera = self._plotframe.inner_camera;
                axis        = plot_camera.get_screen_scaling()
                origin      = plot_camera.get_position()

                graph.update_plotmeta(
                    plot_camera.get_matrix(), 
                    self._plotframe.camera.get_matrix(), 
                    axis, 
                    origin
                )



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
        
        if self.render_graphs:
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

            self.render_graphs = False
        if self.state == self.STATE_SELECT_AREA:
            cursor = list(self.cursor) 
            frame_pos = self.plotframe_position
            frame_size = self.plotframe_size
            cursor[0] = min(frame_pos[0]+frame_size[0], max(frame_pos[0], cursor[0]))
            cursor[1] = min(frame_pos[1]+frame_size[1], max(frame_pos[1], cursor[1]))
            
            self._select_area_rectangle.size = (
                cursor[0]-self._select_area[0],
                cursor[1]-self._select_area[1],
            )
            self._select_area_rectangle.position = self._select_area[0:2]

        self.shaperenderer.render()
        self._yaxis.render()
        self._xaxis.render()
        if self._colorlegend_axis:
            self._colorlegend_axis.render()
        self._fontrenderer.render()
        
    
class Plotter2dMode_Blur():
    def __init__(self, w=0.8):
        self.record_mode = window.Framebuffer.RECORD_TRACK_COMPLEX
        self.w = w
    def get_shader(self):
        record_program = Program()
        record_program.shaders.append(Shader(GL_VERTEX_SHADER, """
#version 410
in  vec2 vertex_position;
in  vec2 text_coord;
out vec2 frag_tex_coord;
mat3 transformation;
void main() {
    transformation = mat3(
        vec3(1,0,0),
        vec3(0,-1,0),
        vec3(0,0,1)
    );
    frag_tex_coord = text_coord;
    gl_Position = vec4((transformation*vec3(vertex_position,1)).xy, 0, 1); 
}"""))
        record_program.shaders.append(Shader(GL_FRAGMENT_SHADER, """
#version 410
in  vec2 frag_tex_coord;
out vec4 output_color;
uniform sampler2D tex[1];
mat2 derp;
void main() {
    derp[0].x = 1; derp[0].y = 0;
    derp[1].x = 0; derp[1].y = 1;
    output_color = texture(tex[0], derp*frag_tex_coord);
    output_color.w = %f;
}
        """%self.w))
        record_program.link()
        return record_program

_PLOTMODE_ALIASES = {
    'oszi' : (Plotter2dMode_Blur, [], {}),
    'oszi0': (Plotter2dMode_Blur, [], {'w':0.05}),
    'oszi1': (Plotter2dMode_Blur, [], {'w':0.15}),
    'oszi2': (Plotter2dMode_Blur, [], {'w':0.25}),
    'oszi3': (Plotter2dMode_Blur, [], {'w':0.35}),
    'oszi4': (Plotter2dMode_Blur, [], {'w':0.45}),
    'oszi5': (Plotter2dMode_Blur, [], {'w':0.55}),
    'oszi6': (Plotter2dMode_Blur, [], {'w':0.65}),
    'oszi7': (Plotter2dMode_Blur, [], {'w':0.75}),
    'oszi8': (Plotter2dMode_Blur, [], {'w':0.85}),
    'oszi9': (Plotter2dMode_Blur, [], {'w':0.95}),
    'oszi95': (Plotter2dMode_Blur, [], {'w':0.995}),
    'oszi100': (Plotter2dMode_Blur, [], {'w':1}),
}  

DEBUG_COLORS = DEFAULT_COLORS.copy()
DEBUG_COLORS.update({
    'bgcolor'              : '000000ff',
    'font-color'           : 'ffffffff',
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
    ]
})


DARK_COLORS = DEFAULT_COLORS.copy()
DARK_COLORS.update({
    'bgcolor'              : '000000ff',
    'plotplane-bgcolor'    : '02050eff',
    'plotplane-bordercolor': 'FF9900ff',
    'font-color'           : 'ffffffff',

    'select-area-bgcolor'  : 'aaaaaa66',
    'select-area-pending-bgcolor'  : 'FF990066',
    'select-area-border-color': 'FF9900ff',
    'select-area-border-size': 1,


    'xaxis-bgcolor'        : '020609ff',
    'yaxis-bgcolor'        : '020609ff',
    'xaxis-linecolor'      : '99D699ff',
    'xaxis-bgcolor'        : '00333300',
    'xaxis-fontcolor'      : 'ffffffff',
    'yaxis-linecolor'      : '99D699ff',
    'yaxis-bgcolor'        : '00333300',
    'yaxis-fontcolor'      : 'ffffffff',

    'plotframe-border-size': 2,
    'plotframe-border-color': 'FF9900ff',
    'graph-colors': [
        'FF0000bb',
        '00ff00bb',
        '0000ffbb',
        'ff00ffbb',
        'f0ff0fbb',
        '00ffffbb',
        'f0f0f0bb',
        'aaff66bb',
    ]
})

BLA_COLORS = DEFAULT_COLORS.copy()
BLA_COLORS.update({
    'bgcolor'              : '142638ff',
    'plotplane-bgcolor'    : '000000aa',
    'plotplane-bordercolor': '9ABAD9ff',
    'font-color'           : 'ffffffff',

    'select-area-bgcolor'  : 'aaaaaa66',
    'select-area-pending-bgcolor'  : 'FF990066',
    'select-area-border-color': 'FF9900ff',
    'select-area-border-size': 1,


    'xaxis-bgcolor'        : '020609ff',
    'yaxis-bgcolor'        : '020609ff',
    'xaxis-linecolor'      : 'aaaaaaff',
    'xaxis-bgcolor'        : '00333300',
    'xaxis-fontcolor'      : 'ffffffff',
    'yaxis-linecolor'      : 'aaaaaaff',
    'yaxis-bgcolor'        : '00333300',
    'yaxis-fontcolor'      : 'ffffffff',

    'plotframe-border-size': 2,
    'plotframe-border-color': '9ABAD9ff',
    'graph-colors': [
        'FC82C3ff',
        '2FB5F3ff',
        'E1C829ff',
        '18DD00ff',
        '00ffffff',
        'f0f0f0ff',
        'aaff66ff',
    ]
})

