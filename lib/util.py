# TODO
# clean me :)
# - remove all the deprecated stuff in here
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


from functools import partial
from OpenGL.GL import *
import numpy

signal = lambda ssx, *args, **kwargs: lambda *x, **y: ssx(*args, **kwargs)

class CommandQueue(list):
    """
    simple command queue structure.
    usage:

      q = CommandQueue()
      q.push(a_command)
      q.push(a_nother_command)
      q()

    """
    def __call__(self):
        """
        invokes the whole queue
        """
        for c in self: c[0](*c[1], **c[2])
        del self[:]

    def queue(self, command):
        """
        returns an callback which will push 
        the given command with arguments into queue
        :param command: callback
        """
        return partial(self.push, command)

    def push(self, command, *args, **kwargs):
        """
        pushed a command with args into the queue
        """
        self.append((command, args, kwargs))

class Event(list):
    """
    event listener stack

    my_event = Event()
    my_event.append(blurp)
    my_event.append(blurp2)
    my_event('first arg', 'and so on...')

    """
    def __call__(self, *args, **kwargs):
        """
        invokes all listeners with given arguments
        """
        for l in self:
            l(*args, **kwargs)

#
#
#
#      DEPRECATED AREA. REFACTOR ME PLEASE!!!!
#
#
#


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

