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
from lib.errors import GlError

import re
from OpenGL.GL import * 

class Error(GlError): 
    """
    error indicates problems with shaders and programs
    """
    pass

class Shader():
    """
    shader representation
    """
    def __init__(self, type, source):
        """
        initializes shader by given source.
        matches all attributes and uniforms 
        by using regex
        """
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
        self.gl_id = glCreateShader(self.type)
        if self.gl_id < 1:
            self.gl_id = None
            raise Error('glCreateShader returns an invalid id.')

        glShaderSource(self.gl_id, self.source)
        glCompileShader(self.gl_id)

        error_log = glGetShaderInfoLog(self.gl_id)
        if error_log:
            self.delete()
            raise Error(error_log)

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


    def use(self):
        """
        tells opengl state to use this program 
        """
        if Program.__LAST_USE_GL_ID is not None and Program.__LAST_USE_GL_ID != self.gl_id:
            raise Error('cannot use program {} since program {} is still in use'.format(
                self.gl_id, Program.__LAST_USE_GL_ID
            ))

        if self.gl_id != Program.__LAST_USE_GL_ID:
            glUseProgram(self.gl_id)
            Program.__LAST_USE_GL_ID = self.gl_id

    def unuse(self):
        """
        tells opengl state to unuse this program
        """
        if self.gl_id != Program.__LAST_USE_GL_ID:
            raise Error('cannot unuse program since its not used.')

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
            raise Error('glCreateProgram returns an invalid id')

        for shader in self.shaders:
            shader.compile()
            glAttachShader(self.gl_id, shader.gl_id)
        glLinkProgram(self.gl_id)

        error_log = glGetProgramInfoLog(self.gl_id)
        if error_log:
            self.delete()
            raise Error(error_log)

        self._configure_attributes()
        self._configure_uniforms()

        return self.gl_id

    def uniform(self, name, value):
        if not name in self.uniforms:
            raise Error('unkown uniform "{}"'.format(name))

        type = self.uniforms[name][1]
        location = self.uniforms[name][0]
        
        if type == 'mat4':
            glUniformMatrix4fv(location, 1, GL_FALSE, value)
        elif type == 'mat3':
            glUniformMatrix3fv(location, 1, GL_FALSE, value)
        elif type == 'mat2':
            glUniformMatrix2fv(location, 1, GL_FALSE, value)
        elif type == 'float':
            glUniform1f(location, value)
        elif type == 'int':
            glUniform1f(location, value)
        elif type == 'vec2':
            glUniform2f(location, value)
        elif type == 'vec3':
            glUniform2f(location, value)
        elif type == 'vec4':
            glUniform2f(location, value)
        else:
            raise NotImplementedError('oops! type "{}" not implemented by shader library.'.format(type))

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
                if k in self.uniforms and self.uniforms[k][0] != u[0]:
                    raise Error('uniform "{name}" appears twice with different types: {t1}, {t2}'.format(
                        name=k,
                        t1=self.uniforms[k][0],
                        t2=u[0]
                    ))

                self.uniforms[k] = (glGetUniformLocation(self.gl_id, k), u[0], u[1])

