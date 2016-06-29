from gllib.renderer import window
from gllib.matrix import ModelView
from gllib.shader import *
from gllib.helper import load_lib_file, resource_path
from OpenGL.GL import *
from gllib.renderer.font import FontRenderer, AbsoluteLayout, Text
from gllib.buffer import VertexArray, VertexBuffer

from PIL import ImageFont
import numpy
import numpy as np

XAXIS = 0
YAXIS = 1
ZAXIS = 2

class Fixed():
    def __init__(self,
        camera,
        scale_camera,
        measurements,
        bgcolor,
        size,
        modelview=None,
        linecolor=[1,1,1,1]):

        self.size = size
        self.measurements = numpy.array([(x,10) for x in measurements], dtype=numpy.float32).reshape(len(measurements),2)
        self.bgcolor = bgcolor
        self.camera = camera
        self.scale_camera = scale_camera
        self.modelview = modelview
        self.linecolor = linecolor

    def init(self):
        self._frame = window.Framebuffer(
            camera       = self.camera,
            screensize   = self.size,
            clear_color  = self.bgcolor,
            multisampling= 4,
            modelview    = self.modelview,
        )

        scaling      = [0,0]
        scaling[0]   = self.size[0]
        scaling[1]   = self.scale_camera.get_scaling()[1]
        self._frame.inner_camera.set_scaling(scaling)

        self._frame.inner_camera.set_base_matrix(np.array([
            1, 0, 0, 0,
            0, -1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1,
        ], dtype=np.float32))

        self._frame.init()
        self.init_shader()

    def init_shader(self):
        self.program = Program()
        self.program.shaders.append(Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/axis/marker_y.vert.glsl')))
        self.program.shaders.append(Shader(GL_GEOMETRY_SHADER, load_lib_file('glsl/plot2d/axis/marker_y.geom.glsl')))
        self.program.shaders.append(Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/axis/marker.frag.glsl')))
        self.program.link()

        self.program.uniform('color', self.linecolor)

        self.vao = VertexArray({
            'vertex_position': VertexBuffer.from_numpy(self.measurements)
        }, self.program.attributes)

    def update_modelview(self):
        self._frame.update_modelview()

    def update_camera(self, camera):

        scaling      = [0,0]
        scaling[0]   = self.size[0]
        scaling[1]   = self.scale_camera.get_scaling()[1]

        self.size = (self.size[0], self.scale_camera.screensize[1])

        self._frame.screensize = self.size
        self._frame.capture_size = self.size

        self._frame.inner_camera.set_position(y=self.scale_camera.position[1])
        self._frame.inner_camera.set_screensize(self.size)
        self._frame.inner_camera.set_scaling(scaling)

        self._frame.update_camera(camera)

    @property
    def labels(self):
        screen_scale = self._frame.inner_camera.screensize[1] / float(self._frame.inner_camera.initial_screensize[1])
        y_range = (self._frame.inner_camera.position[1], self._frame.inner_camera.position[1] + screen_scale*self._frame.inner_camera.scaling[1])
        return [(float(y), '{:.3f}'.format(float(y))) for y,_ in self.measurements if y > y_range[0] and y < y_range[1]]

    def render(self):
        """
        renders the axis.
        also checks whether there is a change in screensize or whether the
        object was ininzialized.
        """
        self._frame.use()
        self.program.use()

        self.vao.bind()

        self.program.uniform('mat_camera', self._frame.inner_camera.get_matrix())
        self.program.uniform('mat_outer_camera', self._frame.camera.get_matrix())
        glDrawArrays(GL_POINTS, 0, len(self.measurements))
        self.vao.unbind()

        self.program.unuse()
        self._frame.unuse()

        self._frame.render()


class Scale():
    def __init__(self,
        camera,
        scale_camera,
        size,
        axis=0,
        unit=1,
        subunits=9,
        unit_symbol=u'',
        bgcolor=[1,1,1,1],
        linecolor=[1,1,1,1],
        fontcolor=[1,1,1,1],
        font=None):

        self._font_renderer       = None

        self.unit                 = unit
        self.subunits             = subunits
        self.size                 = size
        self.initialized          = False
        self.modelview            = ModelView()
        self.camera               = camera
        self.linecolor            = linecolor
        self.fontcolor            = fontcolor
        self.density = 80
        self.unit_symbol = unit_symbol or ''
        self.bgcolor              = bgcolor
        self._last_screen_scaling = None
        self._frame               = None
        self._axis                = axis
        self._translation = 0
        self._font_size = 14
        self._font = font or ImageFont.truetype(resource_path("fonts/arialbd.ttf"), 14, encoding='unic')
        self._unit_f = 1
        self._scale_camera        = scale_camera
        self._initial_size        = [size[0],size[1]]
        self.vao = None
        self._labels =  []

    def unit_density_factor(self, capture_size):
        density = self.density
        size = capture_size
        f = 1.0
        last_diff = density - size
        while True:
            if last_diff < 0:
                if size*f < 2*density:
                    f *= 0.5
                    break
                f *= 0.5
            else:
                if 2*size*f > density:
                    break
                f *= 2
        return f

    def init(self):
        """
        initialize the whole object
        """
        self._font_renderer = FontRenderer(self.camera)

        self._font_renderer.layouts['axis'] = AbsoluteLayout(
            coord_system = AbsoluteLayout.UPPER_CENTER if self._axis == 0 \
                      else AbsoluteLayout.RIGHT_CENTER
        )
        self._font_renderer.init()
        self._font_renderer.set_color(self.fontcolor)

        self.init_shader()
        self.init_capturing()
        self.initialized = True

    def init_shader(self):
        """
        initializes shader
        """
        axis_program = Program()
        vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/axis/marker_{}.vert.glsl'.format('x' if self._axis == 0 else 'y')))
        geometry_shader = Shader(GL_GEOMETRY_SHADER, load_lib_file('glsl/plot2d/axis/marker_{}.geom.glsl'.format('x' if self._axis == 0 else 'y')))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/axis/marker.frag.glsl'))
        axis_program.shaders.append(vertex_shader)
        axis_program.shaders.append(geometry_shader)
        axis_program.shaders.append(fragment_shader)
        axis_program.link()
        self.axis_program = axis_program

        self.axis_program.use()
        #self.axis_program.uniform('mat_modelview', numpy.array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], dtype=numpy.float32))
        self.axis_program.uniform('color', self.linecolor)
        self.axis_program.unuse()

    def init_capturing(self):
        """
        initializes capturing of a unit
        """

        # create framebuffer for one scale unit.
        unit_size    = float(self.unit)/self._scale_camera.get_scaling()[self._axis]
        capture_size = [0,0]
        capture_size[self._axis]   = float(unit_size)*float(self._initial_size[self._axis])
        capture_size[self._axis^1] = self.size[self._axis^1]
        self._unit_f = self.unit_density_factor(capture_size[self._axis])
        capture_size[self._axis]   *= self.unit_density_factor(capture_size[self._axis])
        #if self._frame is None:
        frame = window.Framebuffer(
            camera       = self.camera,
            screensize   = self.size,
            capture_size = capture_size,
            screen_mode  = window.Framebuffer.SCREEN_MODE_REPEAT,
            clear_color  = self.bgcolor,
            multisampling= 1,
            modelview    = self.modelview,
        )

        frame.inner_camera.set_scaling(self.size)

        self._frame = frame

        self._frame.init()

        # create a special scaling.
        # in self._axis direction the scaling should be like unit scaling,
        # on the perpendicular axis the scaling should be like the scaling
        # from frame space.
        scaling               = [0,0]
        scaling[self._axis]   = self.unit
        scaling[self._axis^1] = self._frame.inner_camera.get_scaling()[self._axis^1]

        #scaling = capture_size
        self._frame.inner_camera.set_scaling(scaling)
        self._frame.inner_camera.set_screensize(capture_size)

        if self._axis == 0:
            self._frame.inner_camera.set_base_matrix(np.array([
                1, 0, 0, 0,
                0, -1, 0, 0,
                0, 0, 1, 0,
                0, 0, 0, 1,
            ], dtype=np.float32))
        # update shader
        self.axis_program.use()
        self.axis_program.uniform('mat_camera', self._frame.inner_camera.get_matrix())
        self.axis_program.uniform('mat_outer_camera', self.camera.get_matrix())
        self.axis_program.unuse()
        self.axis_program.uniform('border', 1.5*float(self.camera.screensize[self._axis])/capture_size[self._axis])
        # create vao
        if self.vao is None:
            self._init_capturing_vbo()

        # set init state
        self._last_size = self.size[:]
        self._last_screen_scaling = self._scale_camera.get_screen_scaling()

    @property
    def labels(self):
        return self._labels


    def _init_capturing_vbo(self):
        data = numpy.zeros(self.subunits*2+2, dtype=numpy.float32)
        if self._axis == 0:
            subunit = float(self.unit)/self.subunits
            data[0] = subunit/2
            data[1] = 10
            for i in range(1, self.subunits):
                data[2*i+2] = subunit*i+subunit/2
                data[2*i+3] = 3
        else:
            subunit = float(self.unit)/self.subunits
            data[0] = subunit/2
            data[1] = 10
            for i in range(1, self.subunits):
                data[2*i+2] = subunit*i+subunit/2
                data[2*i+3] = 3

        self.vao = glGenVertexArrays(1)
        vbo = glGenBuffers(1)

        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(data), data, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo)
        glVertexAttribPointer(self.axis_program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def prepare_fonts(self):
        """
        prepares axis fonts
        """
        self._labels = []
        capture_size = self._frame.capture_size[self._axis]
        translation  = self._translation%self._frame.capture_size[self._axis]
        size         = self._last_size[self._axis] + translation
        unit_count   = int(numpy.floor(size/capture_size))
        start_unit   = numpy.floor(self._translation/capture_size)

        axis_flayout = self._font_renderer.layouts['axis']
        axis_flayout.clear_texts()
        axis_flayout.modelview.set_position(*self._frame.modelview.position)

        if self._axis == 0:
            position = [translation,20]
            for i in range(0, unit_count):
                label = self.format_number(self._unit_f*(i-start_unit), self.unit_symbol)
                self._labels.append((position[0], label))
                position[self._axis] += capture_size
        else:
            position = [self.size[0]-15,size-capture_size]
            for i in range(0, unit_count):
                label = self.format_number(self._unit_f*(start_unit+i+1), self.unit_symbol)
              #  text = Text(label, self._font)
              #  axis_flayout.add_text(text, (position[0], position[1]))
                self._labels.append((position[1], label))
                position[self._axis] -= capture_size

    def format_number(self, number, symbol):
        if number == 0:
            return '0'
        if number == 1 and len(symbol):
            return symbol
        if number == -1 and len(symbol):
            return '-' + symbol
        if np.ceil(number) == number:
            return '{:d}'.format(int(number))+symbol
        return '{:.4g}'.format(number)+symbol

    def update_camera(self, camera):
        """
        updates the frame and capture camare to
        adjust zooming and translation of the axis units and
        position of the axis
        """
        # scale the axis size to window size.
        # no translation is done here. do translation (e.g. bottom fixed)
        # from outside.
        self._frame.update_camera(camera)
        self.axis_program.use()
        self.axis_program.uniform('mat_camera', self._frame.inner_camera.get_matrix())
        self.axis_program.uniform('mat_outer_camera', self._frame.camera.get_matrix())
        self.axis_program.unuse()
        # if screen-scaling of the scale_camera has changed
        # we need to initialize capturing of the axis for this size.
        # this happens for example when the zoom changed.
        if self._last_screen_scaling != self._scale_camera.get_screen_scaling():
            self.init_capturing()

        # translate the axis texture so it follows the scale_camera position.
        position = self._scale_camera.get_position()
        subunit = float(self.unit)/self.subunits
        if self._axis == 1:
            fix_translation = 0.5*self._frame.capture_size[1]/self.subunits
            translation = self.size[1]*position[1]/self._last_screen_scaling[1]
            self._translation = translation
            self._frame.screen_translation[1] = self._translation%self._frame.capture_size[1] - fix_translation

            self.prepare_fonts()
        if self._axis == 0:
            fix_translation = 0.5*self._frame.capture_size[0]/self.subunits
            translation = self.size[0]*position[0]/self._last_screen_scaling[0]
            self._translation = translation
            self._frame.screen_translation[0] = -self._translation%self._frame.capture_size[0] + fix_translation
            self.prepare_fonts()

    def update_modelview(self):
        """
        updates model view
        """
        self._frame.update_modelview()

    def render(self):
        """
        renders the axis.
        also checks whether there is a change in screensize or whether the
        object was ininzialized.
        """
        if not self.initialized:
            self.init()

        elif not self._last_size == self.size:
            self._frame.screensize = self.size
            self._frame.init_screen()
            self._last_size = self.size

        if not self._frame.has_captured():
            self.prepare_fonts()
            self._frame.use()
            self._render_scale_element()
            self._frame.unuse()

        # render the object
        self._frame.render()
        self._font_renderer.render()
    def _render_scale_element(self):
        """
        renders one scale unit
        """
        self.axis_program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_POINTS, 0, 2*self.subunits)
        glBindVertexArray(0)
        self.axis_program.unuse()