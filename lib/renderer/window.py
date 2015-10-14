#-*- coding: utf-8 -*-
"""
:author: Nicolas 'keksnicoh' Heimann 
"""

from lib.renderer import renderer
from lib.shader import Program, Shader 
from lib.camera import Camera2d
from lib import matrix
from lib import glutil
from lib.helper import load_lib_file

from OpenGL.GL import * 
import numpy
import logging

class Framebuffer(renderer.Renderer):
    SCREEN_MODE_STRECH = 1
    SCREEN_MODE_REPEAT = 2

    """
    simple framebuffer which renders to a 2d plane.
    """
    def __init__(self, 
        camera, 
        screensize, 
        capture_size=None, 
        screen_mode=SCREEN_MODE_STRECH,
        inner_camera=None, 
        clear_color=[0,0,0,1],
        border=None):
        """
        initializes attributes
        :param camera: camera instance 
        :param screensize: inner screensize
        :param inner_camera: inner camera
        :param clear_color: inner clear color
        """
        renderer.Renderer.__init__(self, camera)

        self.screensize         = screensize
        self.clear_color        = clear_color
        self.capture_size       = capture_size or screensize
        self.inner_camera       = inner_camera or Camera2d(self.capture_size)
        self.screen_mode        = screen_mode
        self.program            = None
        self.screen_translation = [0,0]
        self.border             = border

        self._rgb_texture_id          = None 
        self._framebuffer_id          = None 
        self._outer_viewport          = None
        self._outer_clear_value       = None
        self._last_capture_size       = None
        self._last_screensize         = None
        self._vao                     = None
        self._texture_matrix_changed  = True
        self._has_captured            = False
        self._last_screen_translation = None

    def init(self):
        """
        initializes shader program, framebuffer and plane vao/vbo
        """
        program = Program()
        vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/framewindow.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/framewindow.frag.glsl'))
        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()

        self.program = program
        self.init_capturing()
        self.init_screen()

        self.update_camera(self.camera)
        self.modelview = matrix.ModelView()
        self.update_modelview()

    def init_screen(self):
        """
        init vbo and stuff from the screen plane
        """
        logging.debug('initialite window.Framebuffer screen %s', self)

        vertex_position = numpy.array([
            0,                  self.screensize[1], 
            0,                  0, 
            self.screensize[0], 0, 
            self.screensize[0], 0, 
            self.screensize[0], self.screensize[1],
            0,                  self.screensize[1], 
        ], dtype=numpy.float32)

        tex_position = numpy.array([
            0, 0, 
            0, 1, 
            1, 1, 
            1, 1, 
            1, 0, 
            0, 0
        ], dtype=numpy.float32)

        self._vao = glGenVertexArrays(1)
        vbo_frame = glGenBuffers(2)
        
        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_frame[0])
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
        glVertexAttribPointer(self.program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindBuffer(GL_ARRAY_BUFFER, vbo_frame[1])
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(tex_position), tex_position, GL_STATIC_DRAW)
        glVertexAttribPointer(self.program.attributes['text_coord'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self._last_screensize = self.screensize[:]
        self._texture_matrix_changed = True
        if self.border is not None:
            self.border.init(self.screensize)

    def init_capturing(self):
        """
        initialized framebuffer & texture
        """
        self._rgb_texture_id = glutil.simple_texture(self.capture_size, parameters=[
            # those filters enable translation on 
            # texture without anyoing blur effects.
            (GL_TEXTURE_MAG_FILTER, GL_NEAREST),
            (GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        ])

        self._framebuffer_id = glGenFramebuffers(1);
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._framebuffer_id)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self._rgb_texture_id, 0);
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

        self.inner_camera.set_screensize(self.capture_size)
        self._last_capture_size = self.capture_size
        self._texture_matrix_changed = True

    def use(self):
        """
        start rendering to a framebuffer.
        keeps old opengl values and restores them 
        after finishing
        """
        logging.debug('start using window.Framebuffer %s', self)
  
        if self._last_capture_size != self.capture_size:
            self.init_capturing()

        self._outer_viewport    = glGetIntegerv(GL_VIEWPORT)
        self._outer_clear_value = glGetFloatv(GL_COLOR_CLEAR_VALUE)

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._framebuffer_id)
        glClearColor(*self.clear_color)
        glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
        glViewport(0, 0, *self.capture_size)

    def unuse(self):
        """
        disable framebuffer and restore old opengl state
        """
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        glClearColor(*self._outer_clear_value)
        glViewport(*self._outer_viewport)

        self._has_captured = True
        logging.debug('stop using window.Framebuffer %s', self)

    def update_modelview(self):
        self.program.use()
        self.program.uniform('mat_modelview', self.modelview)
        self.program.unuse()

    def update_camera(self, camera):
        """
        camera update -> tell the shader
        """
        self.program.use()
        self.program.uniform('mat_camera', self.get_camera().get_matrix())
        self.program.unuse()

    def screen_has_changed(self):
        """
        when anything on the screen/capturing has
        changed this method will return true
        """
        return (
            self._last_screensize != self.screensize 
            or self._last_capture_size != self.capture_size
            or self._texture_matrix_changed
            or self._last_screen_translation != self.screen_translation
        )

    def has_captured(self):
        """
        returns whether the framebuffer has allready
        been used or not. also if capture_size has changed
        this method will return True 
        """
        return self._has_captured and self._last_capture_size == self.capture_size

    def get_texture_matrix(self):
        """
        returns a texture matrix 
        """
        self._last_screen_translation = self.screen_translation[:]

        if self.screen_mode == Framebuffer.SCREEN_MODE_STRECH:
            return numpy.identity(3).flatten()
        elif self.screen_mode == Framebuffer.SCREEN_MODE_REPEAT:
            return numpy.array([
                float(self.screensize[0])/self.capture_size[0],0,0,
                0,float(self.screensize[1])/self.capture_size[1],0,
                float(self.screen_translation[0])/self.capture_size[0],float(self.screen_translation[1])/self.capture_size[1],1,
            ], dtype=numpy.float32)
        else:
            raise ValueError('screenmode must be either {}'.format(' or '.join([
                'Framebuffer.SCREEN_MODE_STRECH',
                'Framebuffer.SCREEN_MODE_REPEAT'
            ])))

    def render(self):
        """
        renders the plane 
        """
        self.program.use()
        if self._last_screensize != self.screensize:
            self.init_screen()

            self.program.uniform('mat_camera', self.get_camera().get_matrix())
            if self.border is not None:
                self.program.unuse()
                self.border.set_matricies(self.camera.get_matrix(), self.modelview)
                self.program.use()
        if self.screen_has_changed():
            self.program.uniform('mat_texture', self.get_texture_matrix())
            self._texture_matrix_changed = False

        glActiveTexture(GL_TEXTURE0);
        glBindTexture (GL_TEXTURE_2D, self._rgb_texture_id)
        
        glBindVertexArray(self._vao)
        glDrawArrays(GL_TRIANGLES, 0, 6)
        glBindVertexArray(0)
        self.program.unuse()

        if self.border is not None:
            self.border.render()

class PixelBorder():
    def __init__(self, color):
        self.color = color
    def init(self, screensize):
        """
        initializes shader program, framebuffer and plane vao/vbo
        """
        program = Program()
        vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/id.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/id.frag.glsl'))
        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()

        self.program = program
        self.init_border(screensize)

    def init_border(self, screensize):
        """
        init vbo and stuff from the screen plane
        """
        vertex_position = numpy.array([
            0,            screensize[1], 
            0,            0, 
            screensize[0], 0, 
            screensize[0], 0, 
            screensize[0], screensize[1],
            0,            screensize[1], 
        ], dtype=numpy.float32)

        self._vao = glGenVertexArrays(1)
        vbo_frame = glGenBuffers(1)
        
        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, vbo_frame)
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
        glVertexAttribPointer(self.program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)

        glBindVertexArray(0)  
    def set_matricies(self, camera, modelview):
        self.program.use()
        self.program.uniform('mat_camera', camera)
        self.program.uniform('mat_modelview', modelview)
        self.program.uniform('color', self.color)
        self.program.unuse()
    def render(self):
        """
        renders the plane 
        """
        self.program.use()
        glBindVertexArray(self._vao)
        glDrawArrays(GL_LINES, 0, 45)
        glBindVertexArray(0)
        self.program.unuse()

