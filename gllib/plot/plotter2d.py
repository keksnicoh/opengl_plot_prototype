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
from gllib.plot import axis 
from gllib.glfw import *
from gllib.renderer.font import FontRenderer, RelativeLayout, Text

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
    KEY_ZOOM_SPEED        = 0.02
    FONT_ENCODING         = 'unic'

    def __init__(self, 
        camera            = None, 
        axis              = [2,2], 
        origin            = [1,-1],
        axis_units        = [1,1],
        xlabel            = None,
        ylabel            = None,
        title             = None,
        plotmode          = None,
        axis_unit_symbols = [None,None],
        axis_subunits     = [9,9],
        color_scheme      = DEFAULT_COLORS,
        graphs            = {}
    ):
        Controller.__init__(self, camera)

        if GlApplication.DEBUG:
            color_scheme = DEBUG_COLORS
        
        self.graphs               = graphs or OrderedDict()
        self.plot_camera          = None
        self.color_scheme         = color_scheme
        self.plotmode = plotmode

        if type(plotmode) is str:
            if plotmode not in _PLOTMODE_ALIASES:
                raise ValueError('unkown plotmode "{}". Available aliases are: {}'.format(
                    plotmode, ', '.join(_PLOTMODE_ALIASES.keys())
                ))
            self.plotmode = _PLOTMODE_ALIASES[plotmode][0](
                *_PLOTMODE_ALIASES[plotmode][1], 
                **_PLOTMODE_ALIASES[plotmode][2]
            )

        self._axis_translation    = (5, 5)
        self._plotplane_margin    = (5, 5, 40, 45)
        self._plot_plane_min_size = (100, 100)
        self._axis                = axis 
        self._axis_units          = axis_units 
        
        self._xlabel              = xlabel
        self._ylabel              = ylabel
        self._title               = title
        self._title_font          = None
        self._xlabel_font         = None 
        self._ylabel_font         = None
        
        self._axis_subunits       = axis_subunits
        self._axis_unit_symbols   = axis_unit_symbols
        self._origin              = origin
        
        self._plotframe           = None
        self._xaxis               = None
        self._yaxis               = None
        self._debug               = False

        self._axis_font = ImageFont.truetype(
            resource_path(color_scheme['axis-font']), 
            color_scheme['axis-fontsize'], 
            encoding=Plotter.FONT_ENCODING
        )

        self._fontrenderer = None
        # states
        self.render_graphs      = True
        self._graphs_initialized = False
        self._has_rendered       = False

        self.on_keyboard.append(self.keyboard_callback)
        self.on_pre_render.insert(0, self.pre_render)
        self.on_pre_cycle.append(Plotter.check_graphs)
        self.on_post_render.append(self.post_render)
        self.on_render.append(self.render)

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
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._plotplane_margin[1]-self._plotplane_margin[3]), 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._plotplane_margin[0]-self._plotplane_margin[2])
        ]

    def get_xaxis_size(self):
        """
        returns the absolute size of x axis
        """
        return [
            max(self._plot_plane_min_size[0], self.camera.screensize[0]-self._plotplane_margin[1]-self._plotplane_margin[3]), 
            10
        ]

    def get_yaxis_size(self):
        """
        returns the absolute size of y axis
        """
        return [
            10, 
            max(self._plot_plane_min_size[1], self.camera.screensize[1]-self._plotplane_margin[0]-self._plotplane_margin[2]) 
        ]

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
        # setup axis
        self._fontrenderer = FontRenderer(self.camera)
        self._fontrenderer.layouts['labels'] = RelativeLayout(boxsize=self.camera.screensize)
        self._fontrenderer.init()
        self._fontrenderer.set_color(hex_to_rgba(self.color_scheme['font-color']))
        self.init_labels()

        # setup plotplane
        plotframe = window.Framebuffer(
            camera      = self.camera, 
            screensize  = self.get_plotframe_size(), 
            screen_mode = window.Framebuffer.SCREEN_MODE_STRECH,
            record_mode = self.plotmode.record_mode if self.plotmode is not None else window.Framebuffer.RECORD_CLEAR,
            clear_color = hex_to_rgba(self.color_scheme['plotplane-bgcolor']),
            multisampling = 8,
            border      = window.PixelBorder(hex_to_rgba(self.color_scheme['plotplane-bordercolor']))
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
            if hasattr(graph, 'program'):
                if 'initial_scaling' in graph.program.uniforms:
                    graph.program.uniform('initial_scaling', initial_scaling)
                if 'initial_plane_scaling' in graph.program.uniforms:
                    graph.program.uniform('initial_plane_scaling', initial_plane_scaling)

            if hasattr(graph, 'dot_program'):
                graph.dot_program.uniform('initial_scaling', initial_scaling)
                graph.dot_program.uniform('initial_plane_scaling', initial_plane_scaling)
            
        self._update_graph_matricies()
        self._graphs_initialized = True

    def _update_xaxis(self):
        """
        updates camera and modelview of the x axis
        """
        if self._plotplane_margin[0] > 0:
            self._xaxis.size = self.get_xaxis_size()
            self._xaxis.update_camera(self.camera)

            self._xaxis.modelview.set_position(self._plotplane_margin[3], self.get_plotframe_size()[1]-self._axis_translation[0]+self._plotplane_margin[0])
            self._xaxis.update_modelview()

    def _update_yaxis(self):
        """
        updates camera and modelview of the y axis
        """
        if self._plotplane_margin[1] > 0:
            translation = self._plotframe.inner_camera.get_position()[1]
            self._yaxis.size = self.get_yaxis_size()
            self._yaxis.capture_size = self.get_yaxis_size()
            
            self._yaxis.modelview.set_position(self._plotplane_margin[3]-self._axis_translation[1],self._plotplane_margin[0])
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

        self.render_graphs = True
        self._fontrenderer.layouts['labels'].boxsize = self.camera.screensize
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

            graph.program.uniform('mat_camera', plot_camera.get_matrix())
            graph.program.uniform('mat_domain', domain_matrix)
            graph.program.uniform('zoom', plot_camera.get_zoom())

            if hasattr(graph, 'dot_program'):
                graph.dot_program.uniform('mat_camera', plot_camera.get_matrix())
                graph.dot_program.uniform('mat_domain', domain_matrix)
                graph.dot_program.uniform('zoom', plot_camera.get_zoom())
 


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
            
        self._plotframe.render()
        self._yaxis.render()
        self._xaxis.render()
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
        'f0ff0fbb',
        '00ffffbb',
        'f0f0f0bb',
        'aaff66bb',
    ]
})

