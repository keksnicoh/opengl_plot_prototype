"""
displays the difference between 2 numpy datasets as texture

:author Jesse Hinrichsen
"""
from gllib.glfw import * 
from OpenGL.GL import * 
import numpy as np 
from time import time

# input matrix
np_data = np.array([1 for x in range(25)], dtype=np.float32)

np_data_2 = np.array([1-x/25.0 for x in range(25)], dtype=np.float32)

dim = int(np.sqrt(len(np_data)))


VERT_SHADER = """
#version 410
in vec2 vertex_position;
in vec2 text_coord;
out vec2 frag_text_coord;
void main() {
    gl_Position = vec4(vertex_position.xy, 0, 1);
    frag_text_coord = text_coord;
}
"""
FRAG_SHADER = """
#version 410
out vec4 output_color;
uniform sampler2D tex1[1];
uniform sampler2D tex2[1];
uniform vec4 color1;
uniform vec4 color2;
in vec2 frag_text_coord;
void main() {
    mediump vec4 color1 = texture(tex1[0], vec2(frag_text_coord.x, frag_text_coord.y));
    mediump vec4 color2 = texture(tex2[0], vec2(frag_text_coord.x, frag_text_coord.y));

    output_color = vec4(abs(color1.rgb - color2.rgb), color1.a);

   	//output_color = texture(tex2[0], vec2(frag_text_coord.x, frag_text_coord.y));
}
"""

if not glfwInit(): 
    raise RuntimeError('glfw.Init() error')

glfwWindowHint(GLFW_CONTEXT_VERSION_MAJOR, 4);
glfwWindowHint(GLFW_CONTEXT_VERSION_MINOR, 1);
glfwWindowHint(GLFW_OPENGL_FORWARD_COMPAT, GL_TRUE);
glfwWindowHint(GLFW_OPENGL_PROFILE, GLFW_OPENGL_CORE_PROFILE);

window = glfwCreateWindow(500, 500)
if not window: raise RuntimeError('glfw.CreateWindow() error')
glfwMakeContextCurrent(window)

# SHADER
glfwMakeContextCurrent(window)
program = glCreateProgram()

vertex_shader = glCreateShader(GL_VERTEX_SHADER)
glShaderSource(vertex_shader, VERT_SHADER)
glCompileShader(vertex_shader)
glAttachShader(program, vertex_shader)
log = glGetShaderInfoLog(vertex_shader)
if log: raise Exception(log)

fragment_shader = glCreateShader(GL_FRAGMENT_SHADER)
glShaderSource(fragment_shader, FRAG_SHADER)
glCompileShader(fragment_shader)
glAttachShader(program, fragment_shader)
log = glGetShaderInfoLog(fragment_shader)
if log: raise Exception(log)
glLinkProgram(program)

# plane 
vertex_position = np.array([-1, 1, -1, -1, 1, -1, 1, -1, 1, 1, -1, 1], dtype=np.float32)
tex_position = np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.float32)

vao = glGenVertexArrays(1)
vbo = glGenBuffers(2)

glBindVertexArray(vao)
glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_position), vertex_position, GL_STATIC_DRAW)
glVertexAttribPointer(glGetAttribLocation(program, 'vertex_position'), 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(0)

glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(tex_position), tex_position, GL_STATIC_DRAW)
glVertexAttribPointer(glGetAttribLocation(program, 'text_coord'), 2, GL_FLOAT, GL_FALSE, 0, None)
glEnableVertexAttribArray(1)

glBindBuffer(GL_ARRAY_BUFFER, 0)
glBindVertexArray(0)

textures = glGenTextures (2)
glBindTexture (GL_TEXTURE_2D, textures[0])


glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, dim, dim, 0, GL_RED, GL_FLOAT, np_data)
glBindTexture(GL_TEXTURE_2D, 0);

glBindTexture (GL_TEXTURE_2D, textures[1])
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, dim, dim, 0, GL_RED, GL_FLOAT, np_data_2)
glBindTexture(GL_TEXTURE_2D, 0);

# render
while not glfwWindowShouldClose(window):
    glfwPollEvents()

    glClear(GL_COLOR_BUFFER_BIT)
    glUseProgram(program)
    glActiveTexture(GL_TEXTURE0);
    glBindTexture (GL_TEXTURE_2D, textures[0])
    myUniformLocation1 = glGetUniformLocation(program, "tex1")
    glUniform1i(myUniformLocation1, 0)

    glActiveTexture(GL_TEXTURE1);
    glBindTexture (GL_TEXTURE_2D, textures[1])

    myUniformLocation2 = glGetUniformLocation(program, "tex2")
    glUniform1i(myUniformLocation2, 1)

    glBindVertexArray(vao)
    glDrawArrays(GL_TRIANGLES, 0, 6)
    glBindVertexArray(0)
    glUseProgram(0)

    glfwSwapBuffers(window)
