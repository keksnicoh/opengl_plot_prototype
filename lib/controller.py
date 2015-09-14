from OpenGL.GL import *
import numpy
from camera import Camera2d
import util
from util import Event

class Controller():
    def __init__(self, camera=None):
        self.camera = camera 
        
        self.on_init        = Event()
        self.on_pre_cycle   = Event()
        self.on_post_cycle  = Event()
        self.on_pre_render  = Event()
        self.on_post_render = Event()
        self.on_render      = Event()
        self.on_cycle       = Event()
        self.on_destroy     = Event()

        self.on_init.append(self.init)
        self.on_pre_render.append(self.clear_gl)
        

    def init(self): pass

    def camera_updated(self):
        self.cycle()
    
    def clear_gl(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    def set_cycle_function(self, func):
        self.cycle_function = func
    def cycle(self):
        self.on_pre_cycle()
        self.on_pre_render()
        self.on_cycle()
        self.on_render()
        self.on_post_render()
        self.on_post_cycle()
        pass

class DebugController(Controller): 
    def init(self):
        camera = self.camera
        vertex_position = numpy.array(
            [-.5, .5, .5, .5, .5, -.5, -.5, -.5, -.5, .5,
             -.1, .1, .1, .1, .1, -.1, -.1, -.1, -.1, .1,
             -10, 10, 10, 10, 10, -10, -10, -10, -10, 10]
        , dtype=numpy.float32)
      
        self._vao = util.VAO()
        self.vbo = util.VBO(1)
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
            with self.vbo.get(0):
                glBufferData(
                    GL_ARRAY_BUFFER,
                    ArrayDatatype.arrayByteCount(vertex_position),
                    vertex_position,
                    GL_STATIC_DRAW)

        with self._vao:
            with self.vbo.get(0):
                glVertexAttribPointer(self.shader.attributeLocation('vertex_in'), 2, GL_FLOAT, GL_FALSE, 0, None)
                glEnableVertexAttribArray(0)

    def cycle(self):
        self.on_pre_cycle()
        self.on_pre_render()

        self.shader.uniform('mat_camera', self.camera.get_matrix())
        with self.shader:
            with self._vao:
                glDrawArrays(GL_LINE_STRIP, 0, 15)

        self.on_post_render()
        self.on_post_cycle()