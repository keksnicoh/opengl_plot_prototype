#-*- coding: utf-8 -*-
"""
:author: Nicolas 'keksnicoh' Heimann 
"""

from gllib.renderer import renderer
from gllib.shader import Program, Shader 
from gllib.camera import Camera2d
from gllib import matrix
from gllib import glutil
from gllib.helper import load_lib_file
from gllib.application import GlApplication
from gllib.errors import GlError
from gllib.matrix import ModelView
from gllib.gltype import *
from OpenGL.GL import * 
import numpy
import logging

class Framebuffer(renderer.Renderer):
    SCREEN_MODE_STRECH = 1
    SCREEN_MODE_REPEAT = 2

    RECORD_CLEAR = 1
    RECORD_TRACK = 2
    RECORD_TRACK_COMPLEX = 3

    """
    simple framebuffer which renders to a 2d plane.
    """
    def __init__(self, 
        camera, 
        screensize, 
        capture_size = None, 
        screen_mode  = SCREEN_MODE_STRECH,
        record_mode  = RECORD_CLEAR,
        inner_camera = None, 
        modelview    = None,
        clear_color  = [0,0,0,1],
        border       = None):
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
        self.modelview          = modelview or ModelView()
        self.record_mode        = record_mode 
        self.record_program     = None

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
        self._record_texture_id       = None
        self._record_vao              = None
        self._record_vbo              = None
        self._record_framebuffer_id   = None
        self._gl_clear_executed       = False
        self._record_captured         = False

    def __del__(self):
        """
        Delete opengl data 
        """
        if self._rgb_texture_id is not None:
            glDeleteTextures([self._rgb_texture_id])
        if self._framebuffer_id is not None:
            glDeleteFramebuffers([self._framebuffer_id])

    def init(self):
        """
        initializes shader program, framebuffer and plane vao/vbo
        """
        # default shader program
        if self.program is None:
            program  = Program()
            vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/framewindow.vert.glsl'))
            fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/framewindow.frag.glsl'))
            program.shaders.append(vertex_shader)
            program.shaders.append(fragment_shader)
            program.link()
            self.program = program

        # default complex record shader program
        if self.record_mode == Framebuffer.RECORD_TRACK_COMPLEX and self.record_program is None:
            program = Program()
            vertex_shader = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/framewindow_record.vert.glsl'))
            fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/framewindow_record.frag.glsl'))
            program.shaders.append(vertex_shader)
            program.shaders.append(fragment_shader)
            program.link()
            self.record_program = program

        self.init_capturing()
        self.init_screen()

        self.update_camera(self.camera)
        self.update_modelview()

    def link_program_to_vbo(self):
        """
        links vbo with current set shader attributes
        """
        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo[0])
        glVertexAttribPointer(self.program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo[1])
        glVertexAttribPointer(self.program.attributes['text_coord'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def link_record_program_to_vbo(self):
        """
        links vbo with current set shader attributes
        """
        glBindVertexArray(self._record_vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._record_vbo[0])
        glVertexAttribPointer(self.record_program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, self._record_vbo[1])
        glVertexAttribPointer(self.record_program.attributes['text_coord'], 2, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(1)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

    def init_screen(self):
        """
        init vbo and stuff from the screen plane
        """
        vertex_position = numpy.array([
            0, self.screensize[1], 0, 0, self.screensize[0], 0, self.screensize[0], 0, 
            self.screensize[0], self.screensize[1], 0, self.screensize[1], 
        ], dtype=numpy.float32)
        tex_position = numpy.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=numpy.float32)

        if self._vao is None:
            self._vao = glGenVertexArrays(1)
            self._vbo = glGenBuffers(2)
            self.link_program_to_vbo()

        glBindVertexArray(self._vao)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo[0])
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
        glBindBuffer(GL_ARRAY_BUFFER, self._vbo[1])
        glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(tex_position), tex_position, GL_STATIC_DRAW)
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
        if GlApplication.WINDOW_CURRENT.glspecs['max_texture_size']**2 > self.capture_size[0]*self.capture_size[1]:
            raise GlError('capture {} size exceeds max_texutre_size {}'.format(
                GlApplication.WINDOW_CURRENT.glspecs['max_texture_size'],
                self.capture_size
            ))

        # cleanup if there was allready a texture
        if self._rgb_texture_id is not None:
            glDeleteTextures([self._rgb_texture_id])

        self._rgb_texture_id = glutil.simple_texture(self.capture_size, parameters=[
            # those filters enable translation on 
            # texture without anyoing blur effects.
            (GL_TEXTURE_MAG_FILTER, GL_NEAREST),
            (GL_TEXTURE_MIN_FILTER, GL_NEAREST),
        ])

        if self._framebuffer_id is None:
            self._framebuffer_id = glGenFramebuffers(1);

        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._framebuffer_id)
        glDrawBuffer(GL_COLOR_ATTACHMENT0)
        glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self._rgb_texture_id, 0);
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

        self.inner_camera.set_screensize(self.capture_size)
        self._last_capture_size = self.capture_size
        self._texture_matrix_changed = True
        self._gl_clear_executed = False

        self.init_record_track_complex()

    def init_record_track_complex(self):
        """
        initializes texture and framebuffer for complex record 
        mode. the second framebuffer is required to swap old framebuffer
        content to the record_texture
        """
        if self.record_mode == Framebuffer.RECORD_TRACK_COMPLEX:
            self._record_captured = False

            if self._record_texture_id is not None:
                glDeleteTextures([self._record_texture_id])

            self._record_texture_id = glutil.simple_texture(self.capture_size)  
            if self._record_framebuffer_id is None:
                self._record_framebuffer_id = glGenFramebuffers(1);
                
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self._record_framebuffer_id)
            glReadBuffer(GL_COLOR_ATTACHMENT0)
            glFramebufferTexture(GL_READ_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, self._record_texture_id, 0);
            glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)      

            # spawn complex track record texture plane.
            # use default opengl coordinates since the vertex shader should not use and
            # camera matrix this will fill the entire screen.
            vertex_position = numpy.array([-1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1], dtype=numpy.float32)
            tex_position = numpy.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=numpy.float32)

            if self._record_vao is None:
                self._record_vao = glGenVertexArrays(1)
                self._record_vbo = glGenBuffers(2)
                self.link_record_program_to_vbo()

            glBindVertexArray(self._record_vao)
            glBindBuffer(GL_ARRAY_BUFFER, self._record_vbo[0])
            glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, self._record_vbo[1])
            glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(tex_position), tex_position, GL_STATIC_DRAW)
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            glBindVertexArray(0)

    def _screen_has_changed(self):
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

    def _get_texture_matrix(self):
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

    # --- IMPORTANT PUBLIC METHODS 

    def update_modelview(self):
        self.program.uniform('mat_modelview', self.modelview)
        if self.border is not None:
            self.border.set_matricies(self.camera.get_matrix(), self.modelview)

    def update_camera(self, camera):
        """
        camera update -> tell the shader
        """
        self.program.uniform('mat_camera', self.get_camera().get_matrix())
        if self.border is not None:
            self.border.set_matricies(self.camera.get_matrix(), self.modelview)

    def has_captured(self):
        """
        returns whether the framebuffer has allready
        been used or not. also if capture_size has changed
        this method will return True 
        """
        return self._has_captured and self._last_capture_size == self.capture_size

    def use(self):
        """
        start rendering to a framebuffer.
        keeps old opengl values and restores them 
        after finishing
        """
        #logging.debug('start using window.Framebuffer %s', self)
  
        if self._last_capture_size != self.capture_size:
            self.init_capturing()

        # fetch old state
        self._outer_viewport    = glGetIntegerv(GL_VIEWPORT)
        self._outer_clear_value = glGetFloatv(GL_COLOR_CLEAR_VALUE)

        # prepare base frame buffer.
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._framebuffer_id)
        GlApplication.GL__ACTIVE_FRAMEBUFFER.append(self._framebuffer_id)
        if not self._gl_clear_executed or self.record_mode != Framebuffer.RECORD_TRACK:
            glClearColor(*self.clear_color)
            glClear(GL_COLOR_BUFFER_BIT|GL_DEPTH_BUFFER_BIT)
            self._gl_clear_executed = True
        glViewport(0, 0, *ivec2(self.capture_size))

        # draw complex record texture to the background plane
        if self.record_mode == Framebuffer.RECORD_TRACK_COMPLEX and self._record_captured:
            self.record_program.use()
            glActiveTexture(GL_TEXTURE0);
            glBindTexture (GL_TEXTURE_2D, self._record_texture_id)
            glBindVertexArray(self._record_vao)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glBindVertexArray(0)
            self.record_program.unuse()

        
    def unuse(self):
        """
        disable framebuffer and restores old opengl state.
        if complex track record mode is active, the captures
        texture will be swapped into record_texture.
        """
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
        GlApplication.GL__ACTIVE_FRAMEBUFFER.pop()
        if len(GlApplication.GL__ACTIVE_FRAMEBUFFER):
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, GlApplication.GL__ACTIVE_FRAMEBUFFER[-1])

        glClearColor(*self._outer_clear_value)
        glViewport(*self._outer_viewport)
        self._has_captured = True

        # blit texture data from framebuffer into record texture
        if self.record_mode == Framebuffer.RECORD_TRACK_COMPLEX:
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._record_framebuffer_id)
            glBindFramebuffer(GL_READ_FRAMEBUFFER, self._framebuffer_id)
            glBlitFramebuffer(0, 0, self.capture_size[0], self.capture_size[1], 0, 0, self.capture_size[0], self.capture_size[1], GL_COLOR_BUFFER_BIT, GL_NEAREST);
            glBindFramebuffer(GL_READ_FRAMEBUFFER, 0)
            glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)

            if len(GlApplication.GL__ACTIVE_FRAMEBUFFER):
                glBindFramebuffer(GL_DRAW_FRAMEBUFFER, GlApplication.GL__ACTIVE_FRAMEBUFFER[-1])
                
            self._record_captured = True

    def render(self):
        """
        renders the plane 
        """
        if self._last_screensize != self.screensize:
            self.init_screen()
            self.program.uniform('mat_camera', self.get_camera().get_matrix())
            if self.border is not None:
                self.border.set_matricies(self.camera.get_matrix(), self.modelview)
        if self._screen_has_changed():
            self.program.uniform('mat_texture', self._get_texture_matrix())
            self._texture_matrix_changed = False

        # final rendering
        glActiveTexture(GL_TEXTURE0);
        glBindTexture (GL_TEXTURE_2D, self._rgb_texture_id)
        glBindVertexArray(self._vao)
        self.program.use()
        if GlApplication.DEBUG:
            self.program.uniform('mix_debug', 0.1)
            self.program.uniform('color_debug', [1,1,0,0.7])
            glDrawArrays(GL_TRIANGLES, 0, 6)
            self.program.uniform('mix_debug', 1)
            self.program.uniform('color_debug', [0,0,1,1])
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            glDrawArrays(GL_TRIANGLES, 0, 6)
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)
            self.program.uniform('mix_debug', 0)
            self.program.uniform('color_debug', [0,0,0,0])
        else:
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
            0, screensize[1], 0, 0, 0, 0, screensize[0], 0, screensize[0], 0, 
            screensize[0], screensize[1], screensize[0], screensize[1], 0, screensize[1],
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

