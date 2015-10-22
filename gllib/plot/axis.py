from gllib.renderer import window
from gllib.matrix import ModelView
from gllib.shader import *
from gllib.helper import load_lib_file
from OpenGL.GL import * 
import numpy
class Scale():

    def __init__(self, 
        camera, 
        scale_camera, 
        size, 
        axis=0, 
        unit=1, 
        subunits=9,
        bgcolor=[1,1,1,1],
        linecolor=[1,1,1,1],
        fontcolor=[1,1,1,1]):

        self.unit                 = unit
        self.subunits             = subunits 
        self.size                 = size
        self.initialized          = False 
        self.modelview            = ModelView()
        self.camera               = camera 
        self.linecolor            = linecolor
        self.fontcolor            = fontcolor
        self.bgcolor              = bgcolor
        self._last_screen_scaling = None
        self._frame               = None
        self._axis                = axis
        self._scale_camera        = scale_camera
        self._initial_size        = [size[0],size[1]]
        self.vao = None
    def unit_density_factor(self, capture_size):
        density = 100
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
        self.init_shader()
        self.init_capturing()
        self.initialized = True

    def init_shader(self):
        """
        initializes shader
        """
        axis_program = Program()
        vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/id.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/id.frag.glsl'))
        axis_program.shaders.append(vertex_shader)
        axis_program.shaders.append(fragment_shader)
        axis_program.link()
        self.axis_program = axis_program   

        self.axis_program.use()
        self.axis_program.uniform('mat_modelview', numpy.array([1,0,0,0, 0,1,0,0, 0,0,1,0, 0,0,0,1], dtype=numpy.float32))
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
        capture_size[self._axis]   *= self.unit_density_factor(capture_size[self._axis])

        #if self._frame is None:
        frame = window.Framebuffer(
            camera       = self.camera,
            screensize   = self.size,  
            capture_size = capture_size,
            screen_mode  = window.Framebuffer.SCREEN_MODE_REPEAT, 
            clear_color  = self.bgcolor,
            modelview    = self.modelview,
        )
        
        self._frame = frame

        self._frame.init()
        # create a special scaling. 
        # in self._axis direction the scaling should be like unit scaling,
        # on the perpendicular axis the scaling should be like the scaling 
        # from frame space. 
        scaling               = [0,0]
        scaling[self._axis]   = self.unit
        scaling[self._axis^1] = self._frame.inner_camera.get_scaling()[self._axis^1]

        self._frame.inner_camera.set_scaling(scaling)
        
        # update shader
        self.axis_program.use()
        self.axis_program.uniform('mat_camera', self._frame.inner_camera.get_matrix())
        self.axis_program.unuse()

        # create vao
        if self.vao is None:
            self._init_capturing_vbo()

        # set init state
        self._last_size = self.size[:]
        self._last_screen_scaling = self._scale_camera.get_screen_scaling()


    def _init_capturing_vbo(self):
        """
        XXX
        - wiggling of units?! maybe shader problem
        - make this nice ...
        """
        data = numpy.zeros(self.subunits*10, dtype=numpy.float32)
        if self._axis == 0:
            data[0] = .001
            data[1] = 0
            data[2] = .001
            data[3] = 11

            subunit = float(self.unit)/self.subunits
            for i in range(1, self.subunits+1):
                data[4*i+0] = subunit*i
                data[4*i+1] = 5
                data[4*i+2] = subunit*i
                data[4*i+3] = 9    
        else:
            data[0+0] = 39
            data[1-0] = .999
            data[2+0] = 50
            data[3-0] = .999
            subunit = float(self.unit)/self.subunits
            for i in range(1, self.subunits+1):
                data[4*i+0] = 41
                data[4*i+1] = subunit*i
                data[4*i+2] = 45
                data[4*i+3] = subunit*i   

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

        # if screen-scaling of the scale_camera has changed
        # we need to initialize capturing of the axis for this size. 
        # this happens for example when the zoom changed.
        if self._last_screen_scaling != self._scale_camera.get_screen_scaling():
            self.init_capturing()

        # translate the axis texture so it follows the scale_camera position.
        position = self._scale_camera.get_position()
        if self._axis == 1:
            translation = 0.5*self.size[1]*position[1]
            self._frame.screen_translation[1] = translation%self._frame.capture_size[1]
        if self._axis == 0:
            translation = 0.5*self.size[0]*position[0]
            self._frame.screen_translation[0] = -translation%self._frame.capture_size[0]


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
            self._frame.use()
            self._render_scale_element()
            self._frame.unuse()

        # render the object
        self._frame.render()

    def _render_scale_element(self):
        """
        renders one scale unit
        """
        self.axis_program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINES, 0, self.subunits*2)
        glBindVertexArray(0)
        self.axis_program.unuse()