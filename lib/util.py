# TODO
# clean me :)
from OpenGL.GL import (glCompileShader, glShaderSource, glCreateProgram,
    glCreateShader, glAttachShader, glLinkProgram, glGetUniformLocation,
    glGetShaderInfoLog, glGetProgramInfoLog, glGetAttribLocation, glUseProgram,
    glDeleteShader, GL_FRAGMENT_SHADER, GL_VERTEX_SHADER, GL_GEOMETRY_SHADER,
    glGenVertexArrays, glBindVertexArray, glGenBuffers, GL_ARRAY_BUFFER, glBindBuffer,
    glBufferSubData, glUniformMatrix4fv, glUniform1i, GL_FALSE,
    glTexImage2D, GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_TEXTURE_MIN_FILTER,
    GL_LINEAR, GL_RGB, glGenTextures, glBindTexture, GL_UNSIGNED_BYTE,
    glTexParameterf, glBindFramebuffer, GL_DRAW_FRAMEBUFFER, glFramebufferTexture, GL_COLOR_ATTACHMENT0,
    GL_DEPTH_ATTACHMENT, glGenRenderbuffers, glGenFramebuffers, GL_RENDERBUFFER,
    glFramebufferRenderbuffer, glRenderbufferStorage, GL_FRAMEBUFFER,
    glCheckFramebufferStatus, GL_FRAMEBUFFER_COMPLETE, glDrawBuffer,
    glBindRenderbuffer, GL_DEPTH_COMPONENT, glUniform4f)

from ctypes import c_ubyte
from OpenGL.GL import *
import numpy
from functools import partial
class CommandQueue(list):
    def __call__(self):
        for c in self: c[0](*c[1], **c[2])
        del self[:]
    def queue(self, command):
        return partial(self.push, command)
    def push(self, command, *args, **kwargs):
        self.append((command, args, kwargs))
class Event(list):
    def __call__(self, *args, **kwargs):
        for l in self:
            l(*args, **kwargs)
def gl_id(obj):
    if hasattr(obj, 'gl_id'): return obj.gl_id()
    return obj

class Framebuffer():
    """
    simple framebuffer wrapper
    """
    def __init__(self, w, h, color_texture, depth_texture):
        self._gl_id = glGenFramebuffers(1);

        self._ct = color_texture

        self._dt = depth_texture
        with self:

            glDrawBuffer(GL_COLOR_ATTACHMENT0)
            glFramebufferTexture(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, gl_id(color_texture), 0);
            glFramebufferTexture(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, gl_id(depth_texture), 0);
            rid = glGenRenderbuffers(1)

            glBindRenderbuffer(GL_RENDERBUFFER, rid)
            glRenderbufferStorage(GL_RENDERBUFFER, GL_DEPTH_COMPONENT, w, h)
            glFramebufferRenderbuffer(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_RENDERBUFFER, rid)
            glBindRenderbuffer(GL_RENDERBUFFER, 0)
            e = glCheckFramebufferStatus(GL_DRAW_FRAMEBUFFER);
            if e != GL_FRAMEBUFFER_COMPLETE:
                raise Exception('GOT PROBLEMS {}'.format(e))
    def gl_id(self):
        return self._gl_id
    def bind(self):
        #glBindTexture(GL_TEXTURE_2D, 0)
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, self._gl_id)
    def unbind(self):
        glBindFramebuffer(GL_DRAW_FRAMEBUFFER, 0)
    def __enter__(self): self.bind()
    def __exit__(self, type, value, tb): self.unbind()
class Texture2D():
    """
    simple texture wrapper
    """
    def __init__(self, w, h, format=GL_RGBA, internalFormat=None):
        self._id = glGenTextures(1);
        self._w = w
        self._h = h
        if internalFormat is None:
            internalFormat = format

        # crashes _sometimes_ when self._w * self._h > 888*888
        glBindTexture(GL_TEXTURE_2D, self._id);
        glTexImage2D(GL_TEXTURE_2D, 0, format, self._w, self._h, 0, internalFormat, GL_UNSIGNED_BYTE, None);
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D, 0);

    def gl_id(self):
        return self._id
class VAO():
    def __init__(self):
        self._gl_id = glGenVertexArrays(1)
    def __enter__(self):
        glBindVertexArray(self._gl_id)
    def __exit__(self, type, value, tb):
        glBindVertexArray(0)
class VBO():
    def __init__(self, n=1):
        vbo = glGenBuffers(n)
        if n == 1: vbo = [vbo]
        self.vbo = [Buffer(gl_buffer_id) for gl_buffer_id in vbo]
    def get(self, buffer_id=0):
        return self.vbo[buffer_id]
    def __enter__(self):
        return self.get().__enter__()
    def __exit__(self, type, value, tb):
        return self.get().__exit__(type, value, tb)

class Buffer():
    def __init__(self, gl_buffer_id):
        self._is_binded = False
        self.id = gl_buffer_id

    def glBufferSubData(self, byte_start, byte_length, data):
        with self:
            glBufferSubData(GL_ARRAY_BUFFER, byte_start, byte_length, data)
    def __enter__(self):
        if not self._is_binded:
            glBindBuffer(GL_ARRAY_BUFFER, self.id)
            self._is_binded = True
    def __exit__(self, type, value, tb):
        if self._is_binded:
            glBindBuffer(GL_ARRAY_BUFFER, 0)
            self._is_binded = False
class Shader(object):
    def __init__(self, vertex=None, geometry=None, fragment=None, link=False):
        self.program_id = glCreateProgram()
        self._shaders = []
        if not vertex is None:
            self.attachShader(GL_VERTEX_SHADER, vertex)
        if not geometry is None:
            self.attachShader(GL_GEOMETRY_SHADER, geometry)
        if not fragment is None:
            self.attachShader(GL_FRAGMENT_SHADER, fragment)
        if link: self.linkProgram()
        self._in_use = 0
    def attachShader(self,type,source):
        shader = glCreateShader(type)
        glShaderSource(shader,source)
        glCompileShader(shader)
        shader_log = glGetShaderInfoLog(shader)
        if shader_log:
            if type == GL_FRAGMENT_SHADER:
                str_type = "GL_FRAGMENT_SHADER"
            elif type == GL_VERTEX_SHADER:
                str_type = "GL_VERTEX_SHADER"
            elif type == GL_GEOMETRY_SHADER:
                str_type = "GL_GEOMETRY_SHADER"
            else:
                str_type = "unkown shader type %s" % str(type)
            raise RuntimeError("%s\n%s" % (str_type, shader_log))
        glAttachShader(self.program_id, shader)
        self._shaders.append(shader)

    def uniformLocation(self, name):
        return glGetUniformLocation(self.program_id, name)

    def attributeLocation(self, name):
        return glGetAttribLocation(self.program_id, name)

    def uniform(self, name, value):
        with self:
            if type(value) == int or type(value) == long:
                glUniform1i(self.uniformLocation(name), value)
            elif type(value) == float or type(value) == numpy.float32:
                glUniform1f(self.uniformLocation(name), value)
            elif len(value) == 4:
                value = numpy.array(value, dtype=numpy.float32)
                glUniform4f(self.uniformLocation(name), *value)
            elif len(value) == 16:
                glUniformMatrix4fv(self.uniformLocation(name), 1, GL_FALSE, value)
            elif len(value) == 9:
                glUniformMatrix3fv(self.uniformLocation(name), 1, GL_FALSE, value)
            elif len(value) == 2:
                value = numpy.array(value, dtype=numpy.float32)
                glUniform2f(self.uniformLocation(name), *value)
            else:
                print(len(value))
                raise Exception('not implemented')
    def linkProgram(self):
        glLinkProgram(self.program_id)
        program_log = glGetProgramInfoLog(self.program_id)
        if program_log:
            raise RuntimeError("shader_program\n%s" % program_log)

        for shader in self._shaders:
            glDeleteShader(shader)
        self._shaders = []
    def useProgram(self):
        glUseProgram(self.program_id)
    def unuseProgram(self):
        glUseProgram(0)
    def __enter__(self):
        self.useProgram()
        self._in_use += 1
    def __exit__(self, type, value, tb):
        if self._in_use > 0:
            self._in_use -= 1
        if self._in_use == 0:
            self.unuseProgram()

