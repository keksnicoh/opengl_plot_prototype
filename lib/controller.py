from OpenGL.GL import *
import numpy
from camera import Camera2d
import util

class Controller():
    def __init__(self, camera=None, cycle_function=lambda c: None):
        self.cycle_function = cycle_function
        self.camera = camera or Camera2d()
    def on_init(self): pass
    def on_destroy(self): pass
    def set_cycle_function(self, func):
        self.cycle_function = func
    def cycle(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.cycle_function(self)
        pass

class DebugController(Controller): 
    def on_init(self):
        camera = self.camera

        vertex_position = numpy.array(
            [-.5, .5, .5, .5, .5, -.5, -.5, -.5, -.5, .5,
             -.1, .1, .1, .1, .1, -.1, -.1, -.1, -.1, .1,
             -10, 10, 10, 10, 10, -10, -10, -10, -10, 10]
        , dtype=numpy.float32)
      
        self._vao = util.VAO()
        vbo = util.VBO(2)
        self.shader = util.Shader(
            vertex="""
#version 410
in vec2 vertex_in;
uniform mat4 mat_camera;
void main() {
    gl_Position = mat_camera * vec4(vertex_in, 0, 1);

}
            """,

            fragment="""
#version 410
out vec4 output_color;
void main()
{
    output_color = vec4(1, 0, 0, 1);
}

            """,
            link=True
        )
        with self._vao:
            with vbo:
                glBufferData(
                    GL_ARRAY_BUFFER,
                    ArrayDatatype.arrayByteCount(vertex_position),
                    vertex_position,
                    GL_STATIC_DRAW)

        with self._vao:
            with vbo.get(0):
                glVertexAttribPointer(self.shader.attributeLocation('vertex_in'), 2, GL_FLOAT, GL_FALSE, 0, None)
                glEnableVertexAttribArray(0)

    def cycle(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        self.shader.uniform('mat_camera', self.camera.get_matrix())
        with self.shader:
            with self._vao:
                glDrawArrays(GL_LINE_STRIP, 0, 15)