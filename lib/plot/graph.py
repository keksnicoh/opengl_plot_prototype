from lib.shader import * 
from lib.helper import load_lib_file
from OpenGL.GL import * 

class Graph():
    def __init__(self, domain):
        self.program = None
        self.domain = domain

    def init(self, renderer):
        pass

    def render(self, renderer):
        pass

class Line2d(Graph):
    """
    line plotter
    """
    def __init__(self, domain, kernel, color=[0,0,0,1]):
        Graph.__init__(self, domain)
        self._color = color
        self._kernel = kernel

    def init(self, renderer):
        """
        creates shader and vao 
        """
        program         = Program()
        vertex_shader   = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/line.vert.glsl'), {
            'KERNEL': self._kernel+';'
        })
        geometry_shader = Shader(GL_GEOMETRY_SHADER, load_lib_file('glsl/plot2d/line.geom.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/line.frag.glsl'))
        
        try:
            vertex_shader.compile()

        except ShaderError as e:
            # try to compile shader without kernel to see whether
            # it is an error by user kernel oder by shader itsel
            try:
                Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/line.vert.glsl')).compile()

                raise Error('invalid syntax in user defined kernel "{}"'.format(self._kernel))
            except ShaderError as e2:
                raise e

        program.shaders.append(vertex_shader)
        program.shaders.append(geometry_shader)
        program.shaders.append(fragment_shader)
        program.link()

        self.program = program

        dimension        = self.domain.dimension
        vertex_attribute = self.program.attributes['vertex_position']
        self.vao         = glGenVertexArrays(1)

        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.domain.get_vbo())
        glVertexAttribPointer(vertex_attribute, dimension, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self.program.use()
        self.program.uniform('color', self._color)
        self.program.uniform('mat_domain', self.domain.get_transformation_matrix(
            (1,1),
            [10,10],
        ))
        self.program.unuse()

    def render(self, renderer):
        """
        renders line plot 
        """
        self.program.use()
        glBindVertexArray(self.vao)
        glDrawArrays(GL_LINE_STRIP_ADJACENCY, 0, int(self.domain.get_length()/(4.0*self.domain.dimension)))
        glBindVertexArray(0)
        self.program.unuse()