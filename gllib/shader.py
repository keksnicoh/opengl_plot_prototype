#-*- coding: utf-8 -*-
"""
shader library

    try:
        program         = Program()
        vertex_shader   = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/id.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/id.frag.glsl'))

        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()
    except shader.Error as e:
        print('oh no, too bad..', e)

programs find out which attributes and uniforms are present in 
given shaders.

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.errors import GlError
from gllib.gltype import *

import re
from OpenGL.GL import * 
import numpy as np 
from copy import deepcopy
class ShaderError(GlError): 
    """
    error indicates problems with shaders and programs
    """
    pass

class Shader():
    """
    shader representation
    """
    def __init__(self, type, source, substitutions={}):
        """
        initializes shader by given source.
        matches all attributes and uniforms 
        by using regex
        """
        self.substitutions = {
            'VERSION': 410
        }
        self.substitutions.update(substitutions)

        self.source = source
        self.type = type
        self.gl_id = None
        
        matches = re.findall(r'uniform\s+(\w+)\s+([\w]+)\s*=?\s*(.*?);', source, flags=re.MULTILINE)
        self.uniforms = {k: (t, d) for t, k, d in matches}
        
        matches = re.findall(r'(in|out)\s+(\w+)\s+([\w]+).*?;', source, flags=re.MULTILINE)
        self.attributes = {k: (s, t) for s, t, k in matches}

    def delete(self):
        """
        deletes gl shader if exists
        """
        if self.gl_id is not None:
            glDeleteShader(self.gl_id)
            self.gl_id = None

    def compile(self):
        """
        compiles shader an returns gl id
        """
        if self.gl_id is None:
            self.gl_id = glCreateShader(self.type)
            if self.gl_id < 1:
                self.gl_id = None
                raise ShaderError('glCreateShader returns an invalid id.')

            source = self.source
            for name, code in self.substitutions.items():
                source = source.replace('/*{$%s$}*/'%name, str(code))

            glShaderSource(self.gl_id, source)
            glCompileShader(self.gl_id)

            error_log = glGetShaderInfoLog(self.gl_id)
            if error_log:
                self.delete()
                raise ShaderError('{}: {}'.format(self.type, error_log))

        return self.gl_id

class Program():
    """
    opengl render program representation 
    """
    __LAST_USE_GL_ID = None

    def __init__(self):
        """
        initialize the state 
        """
        self.shaders    = []
        self.gl_id      = None
        self.attributes = {}
        self.uniforms   = {}
        self._uniform_changes = {}
        self._uniform_values = {}

    def use(self, flush_uniforms=True):
        """
        tells opengl state to use this program 
        """
        if Program.__LAST_USE_GL_ID is not None and Program.__LAST_USE_GL_ID != self.gl_id:
            raise ShaderError('cannot use program {} since program {} is still in use'.format(
                self.gl_id, Program.__LAST_USE_GL_ID
            ))

        if self.gl_id != Program.__LAST_USE_GL_ID:
            glUseProgram(self.gl_id)
            Program.__LAST_USE_GL_ID = self.gl_id
            self.flush_uniforms()

    def unuse(self):
        """
        tells opengl state to unuse this program
        """
        if self.gl_id != Program.__LAST_USE_GL_ID:
            raise ShaderError('cannot unuse program since its not used.')

        glUseProgram(0)
        Program.__LAST_USE_GL_ID = None

    def delete(self):
        """
        deletes gl program if exists 
        """
        if self.gl_id is not None:
            glDeleteProgram(self.gl_id)
            self.gl_id = None

    def link(self):
        """
        links all shaders together
        """
        # prepare
        self.gl_id = glCreateProgram()

        if self.gl_id < 1:
            self.gl_id = None
            raise ShaderError('glCreateProgram returns an invalid id')

        for shader in self.shaders:
            shader.compile()
            glAttachShader(self.gl_id, shader.gl_id)
        glLinkProgram(self.gl_id)

        error_log = glGetProgramInfoLog(self.gl_id)
        if error_log:
            self.delete()
            raise ShaderError(error_log)

        self._configure_attributes()
        self._configure_uniforms()

        return self.gl_id

    def uniform(self, name, value, flush=False):
        if not name in self.uniforms:
            raise ShaderError('unkown uniform "{}"'.format(name))

        if flush or self.gl_id == Program.__LAST_USE_GL_ID:
            self._uniform(name, value)
        else:
            self._uniform_changes[name] = deepcopy(value)
        #
        #self.flush_uniforms()

    def flush_uniforms(self, force=False):
        for name, value in self._uniform_changes.items():
            was_changed = False
            if not force:
                if isinstance(value, np.ndarray):
                    was_changed = not np.array_equal(self._uniform_values[name], value)
                else:
                    was_changed = self._uniform_values[name] != value
            if force or was_changed:
                self._uniform(name, value)
        self._uniform_changes = {} 

    def _uniform(self, name, value):
        type = self.uniforms[name][1]
        location = self.uniforms[name][0]

        if type == 'mat4':
            glUniformMatrix4fv(location, 1, GL_FALSE, mat4(value))
        elif type == 'mat3':
            glUniformMatrix3fv(location, 1, GL_FALSE, mat3(value))
        elif type == 'mat2':
            glUniformMatrix2fv(location, 1, GL_FALSE, mat2(value))
        elif type == 'float':
            glUniform1f(location, value)
        elif type == 'int':
            glUniform1i(location, value)
        elif type == 'vec2':
            glUniform2f(location, *value)
        elif type == 'vec3':
            glUniform3f(location, value)
        elif type == 'vec4':
            glUniform4f(location, *value)
        elif type == 'sampler2D':
            glUniform1i(location, value)
        elif type == 'sampler2DMS':
            glUniform1i(location, value)
        elif type == 'bool':
            glUniform1i(location, value)
        else:
            raise NotImplementedError('oops! type "{}" not implemented by shader library.'.format(type))
        self._uniform_values[name] = value
        
    def get_vertex_shader(self):
        """
        returns vertex shader if appended
        """
        for shader in self.shaders:
            if shader.type == GL_VERTEX_SHADER:
                return shader
                      
    def _configure_attributes(self):
        """
        configures attributes cache
        """
        vertex_shader = self.get_vertex_shader()
        if vertex_shader is not None:
            input_attributes = {k: d for k, d in vertex_shader.attributes.items() if d[0] == 'in'}
            self.attributes = {k: glGetAttribLocation(self.gl_id, k) for k in input_attributes}

    def _configure_uniforms(self):
        """
        configures uniforms cache
        """
        self.uniforms = {}
        for shader in self.shaders:
            for k, u in shader.uniforms.items():
                # check whether any uniform is defined in 2 shaders with different types.
                if k in self.uniforms and self.uniforms[k][1] != u[0]:
                    raise ShaderError('uniform "{name}" appears twice with different types: {t1}, {t2}'.format(
                        name=k,
                        t1=self.uniforms[k][1],
                        t2=u[0]
                    ))

                self.uniforms[k] = (glGetUniformLocation(self.gl_id, k), u[0], u[1])
                self._uniform_values[k] = None

