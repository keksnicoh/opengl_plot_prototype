from gllib.shader import * 
from gllib.helper import load_lib_file
from OpenGL.GL import * 
from gllib.application import GlApplication
class Graph():
    def __init__(self, domain):
        self.program = None
        self.domain = domain

    def init(self, renderer):
        pass

    def render(self, renderer):
        pass



class Line2d(Graph):
    GEOMETRY_SHADER_WIDTH = .5
    """
    line plotter
    """
    def __init__(self, domain, kernel='', draw_dots=False, draw_lines=True, color=None, dotcolor=None, width=1, dotsize=None, shift=(0.0,0.0)):
        Graph.__init__(self, domain)
        self.color       = color
        self._kernel     = kernel
        self.color_index = None
        self.dotcolor = dotcolor or color
        self.draw_lines  = draw_lines
        self.draw_dots   = draw_dots 
        self.dotsize = dotsize or width*5
        self.initialized = False 
        self._width      = width
        self.shift       = shift

    def init(self):
        """
        creates shader and vao 
        """
        
        vertex_shader   = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/plot2d/line.vert.glsl'), {
            'KERNEL': self._kernel+';' #user friendly semicolon :)
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

        program = Program()
        program.shaders.append(vertex_shader)
        program.shaders.append(geometry_shader)
        program.shaders.append(fragment_shader)
        program.link()

        self.program = program

        geometry_shader = Shader(GL_GEOMETRY_SHADER, load_lib_file('glsl/plot2d/dot.geom.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/dot.frag.glsl'))
        program = Program()
        program.shaders.append(vertex_shader)
        program.shaders.append(geometry_shader)
        program.shaders.append(fragment_shader)
        program.link()

        self.dot_program = program

        dimension        = self.domain.dimension
        vertex_attribute = self.program.attributes['vertex_position']
        self.vao         = glGenVertexArrays(1)


        #self.vao = VertexAttayObject(self.program, attributes={
        #    'vertex_position': VertexBufferObject(self.length),
        #    'vertex_text': VertexBufferObject(self.length),
        #})
    
        glBindVertexArray(self.vao)
        glBindBuffer(GL_ARRAY_BUFFER, self.domain.get_vbo())
        glVertexAttribPointer(vertex_attribute, dimension, GL_FLOAT, GL_FALSE, 0, None)
        glEnableVertexAttribArray(0)
        glBindBuffer(GL_ARRAY_BUFFER, 0)
        glBindVertexArray(0)

        self.program.uniform('color', self.color or [0,0,0,1])
        self.program.uniform('mat_domain', numpy.identity(4).flatten())
        self.program.uniform('width', Line2d.GEOMETRY_SHADER_WIDTH*self._width)
        self.dot_program.uniform('color', self.dotcolor or self.color or [0,0,0,1])
        self.dot_program.uniform('mat_domain', numpy.identity(4).flatten())
        self.dot_program.uniform('width', Line2d.GEOMETRY_SHADER_WIDTH*self.dotsize)

        self.initialized = True

    def set_time(self, time):
        self.program.uniform('time', time)
        self.dot_program.uniform('time', time)

    def render(self, plotter):
        """
        renders line plot 
        """
        if not self.initialized:
            self.init()

        if GlApplication.DEBUG == True:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)
            
        if self.draw_lines:
            self.program.use()
            self.program.uniform('shift', self.shift)
            glBindVertexArray(self.vao)
            glDrawArrays(
                GL_LINE_STRIP_ADJACENCY, 
                int(self.domain.get_offset()/(4.0*self.domain.dimension)), 
                int(self.domain.get_length()/(4.0*self.domain.dimension))
            )
            glBindVertexArray(0)
            self.program.unuse()


        if self.draw_dots:
            self.dot_program.use()
            self.dot_program.uniform('shift', self.shift)
            glBindVertexArray(self.vao)
            glDrawArrays(
                GL_POINTS, 
                int(self.domain.get_offset()/(4.0*self.domain.dimension)), 
                int(self.domain.get_length()/(4.0*self.domain.dimension))
            )
            glBindVertexArray(0)
            self.dot_program.unuse()

        if GlApplication.DEBUG == True:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)







