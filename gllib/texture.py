#-*- coding: utf-8 -*-
"""
texture wrapping utilities

if an instance has "gl_texture_id" attribute
the library should interpret this as a 
opengl texture:

   glBindTexture(tex.gl_texture_id if hasattr(hasattr(tex, 'gl_texture_id')) else tex)

:author: Nicolas 'keksnicoh' Heimann 
"""
import numpy as np 
from OpenGL.GL import * 

def map_channels(channels):
    if self.channels == 1:
        texture_format = GL_RED
    elif self.channels == 2:
        texture_format = GL_RG
    elif self.channels == 3:
        texture_format = GL_RGB
    elif self.channels == 4:
        texture_format = GL_RGBA
    else:
        raise ValueError('channels must be in [1,2,3,4] actually is {}'.format(self.channels))
    return texture_format

def create_texture(size, texture_format, type=GL_UNSIGNED_BYTE, data=None, gl_texture_parameters=[]):
    gl_texture_id = glGenTextures(1);
    glBindTexture(GL_TEXTURE_2D, gl_texture_id);
    glTexImage2D(GL_TEXTURE_2D, 0, texture_format, size[0], size[1], 0, texture_format, type, data);
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
    glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
    for parameter in gl_texture_parameters:
        glTexParameterf(GL_TEXTURE_2D, *parameter)
    glBindTexture(GL_TEXTURE_2D, 0);

class Texture():
    def __init__(self, size, channels=4, gl_texture_parameters=[]):
        self.channels = 4 
        self.gl_texture_id = None 
        self.size = size 
        self.gl_texture_parameters = gl_texture_parameters
        self.gl_texture_data = None 
        self.gl_texture_type = None

    @classmethod
    def color(cls, color): 
        texture = NumpyTexture(np.array(color, dtype=np.float32).reshape(1,1,4))
        texture.gl_init()
        return texture
        
    @classmethod
    def zeros(cls): 
        return cls.color(np.array([0,0,0,0], dtype=np.float32).reshape(1,1,4))

    def gl_init(self):
        texture_format = map_channels(self.channels)
        self.gl_texture_id = create_texture(size, texture_format)
        


class NumpyTexture():
    def __init__(self, data, gl_texture_parameters=[]):
        self.np_data = data
        self.channels=None
        self.gl_texture_id = None 
        self.gl_texture_parameters = gl_texture_parameters

    def gl_init(self):
        self.gl_texture_id = glGenTextures(1);

        shape = self.np_data.shape
        if len(shape) == 2:
            self.channels = 1
        elif len(shape) == 3:
            self.channels = shape[2]
        else:
            raise ValueError('invalid numpy shape.')

        if self.channels == 1:
            texture_format = GL_RED
        elif self.channels == 2:
            texture_format = GL_RG
        elif self.channels == 3:
            texture_format = GL_RGB
        elif self.channels == 4:
            texture_format = GL_RGBA
        else:
            raise ValueError('channels must be in [1,2,3,4] actually is {}'.format(self.channels))

        glBindTexture(GL_TEXTURE_2D, self.gl_texture_id);
        glTexImage2D(GL_TEXTURE_2D, 0, texture_format, self.np_data.shape[1], self.np_data.shape[0], 0, texture_format, GL_FLOAT, self.np_data.flatten());
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        for parameter in self.gl_texture_parameters:
            glTexParameterf(GL_TEXTURE_2D, *parameter)
        glBindTexture(GL_TEXTURE_2D, 0);



