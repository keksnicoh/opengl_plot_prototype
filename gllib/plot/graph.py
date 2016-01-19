#-*- coding: utf-8 -*-
"""
graph plotting module

:author: Nicolas 'keksnicoh' Heimann
"""
from gllib.shader import * 
from gllib.helper import load_lib_file
from gllib.buffer import * 
from gllib.application import GlApplication

from OpenGL.GL import * 


import pystache
import re

# XXX
# - print out a warning if domains have different lengths?
# - print out a warning if domains have different offsets?
# - should we extract draw_dots out of here? 
#   + cleaner api
#   - more abstract usage, not so easy in real life ...

class Line2d():
    GEOMETRY_SHADER_WIDTH = .5
    """
    line plotter
    """
    def __init__(self, domains, kernel='', 
        draw_dots=False, 
        draw_lines=True, 
        color=None, 
        dotcolor=None, 
        data_layout=None,
        width=1, 
        dotsize=None, 
        shift=(0.0,0.0),
        color_scheme='fragment_color=point_color;'):

        self.domains = domains 
        self.program = None 
        self.dot_program = None
        self.color        = color
        self._kernel      = kernel
        self.color_index  = None
        self.dotcolor     = dotcolor or color
        self.draw_lines   = draw_lines
        self._data_layout = data_layout
        self.draw_dots    = draw_dots 
        self.color_scheme = color_scheme
        self.dotsize      = dotsize or width*5
        self.initialized  = False 
        self._width       = width
        self.shift        = shift
        
        # plot from the max offset to min length of 
        # all defined domains. 
        self._max_offset  = 0
        self._min_length  = 0

    def update_plotmeta(self, plot_cam, outer_cam, axis, origin):
        # not so nice ... but later refactoring ...
        for i, domain in enumerate(self.domains):
            if hasattr(domain, 'get_transformation_matrix'):
                self.program.uniform('trans_d{}'.format(i), domain.get_transformation_matrix(
                    axis=(axis[0], axis[1]),
                    origin=(origin[0],origin[1]),
                ))

        self.program.uniform('mat_camera', plot_cam)
        self.program.uniform('mat_outer_camera', outer_cam)
        

        if hasattr(self, 'dot_program'):
            self.dot_program.uniform('mat_camera', plot_cam)
            self.dot_program.uniform('mat_outer_camera', outer_cam)
      #      dot_program.uniform('mat_domain', domain_matrix)


    def set_time(self, time):
        # urgh ... we need a uniform manager :(
        self.program.uniform('time', time)
        self.dot_program.uniform('time', time)

    def init(self):
        """
        creates shader and vao 
        """
        if not type(self.domains) is list:
            self.domains = [self.domains]

        vertex_array = {}
        shader_pre_compile_vbo = ''
        shader_pre_compile_transformations = ''
        shader_pre_compile_uniforms = ''
        uniforms_transformation_matricies = {}

        lengths = [] 

        # loop thru all domains to prepare vertex array buffers
        # and glsl pre compiled code
        for i, domain in enumerate(self.domains):
            if hasattr(domain, 'gl_init'):
                domain.gl_init()
            if hasattr(domain, 'transform'):
                domain.transform()

            if not hasattr(domain, 'gl_vbo_id'):
                raise TypeError('any domain passed to graph must have gl_vbo_id attribute')

            vec_d = ('vec'+str(domain.dimension)) if domain.dimension > 1 else 'float'
            vertex_array['in_d{}'.format(i)] = VertexBuffer(dimension=domain.dimension, gl_vbo_id=domain.gl_vbo_id)
            shader_pre_compile_vbo += 'in {} in_d{};\n'.format(vec_d, i)

            if hasattr(domain, 'get_transformation_matrix'):
                shader_pre_compile_uniforms += 'uniform mat{} trans_d{};\n'.format(domain.dimension+1, i)

                shader_pre_compile_transformations += '{vec} d{i} = (trans_d{i} * vec{d1}(in_d{i},1)).{coords};\n'.format(
                    coords = 'x' if domain.dimension == 1 else ('xy' if domain.dimension==2 else 'xyz'),
                    vec=vec_d,
                    i=i, 
                    d1=domain.dimension+1
                )
                uniforms_transformation_matricies['trans_d{}'.format(i)] = 'mat{}'.format(domain.dimension+1)
            else:
                shader_pre_compile_transformations = '{vec} d{i} = in_d{i};\n'.format(vec=vec_d, i=i)

            self._max_offset = max(self._max_offset, domain.offset)
            lengths.append(len(domain))

        self._min_length = min(lengths)

        # get glsl_functions if there are some available.
        color_functions = ''
        if hasattr(self.color_scheme, 'glsl_functions'):
            color_functions = self.color_scheme.glsl_functions

        vertex_source = pystache.render(load_lib_file('glsl/plot2d/line.vert.glsl'),{
            'VBO_IN'         : shader_pre_compile_vbo,
            'UNIFORMS'       : shader_pre_compile_uniforms,
            'TRANSFORMATIONS': shader_pre_compile_transformations,
            'DATA_LAYOUT'    : self._pre_compile_data_layout(),
            'COLOR_SCHEME'   : self.color_scheme,
            'COLOR_FUNCTIONS': color_functions
        })

        self._compile_glsl_programs(vertex_source)
        self._init_program_uniforms()

        self.vao = VertexArray(vertex_array, self.program.attributes)
        self.initialized = True

    def render(self, plotter):
        """
        renders line plot 
        """
        if not self.initialized:
            self.init()

        if GlApplication.DEBUG == True:
            glPolygonMode(GL_FRONT_AND_BACK, GL_LINE)

        self.vao.bind()

        if self.draw_lines:
            self.program.use()
            self.program.uniform('shift', self.shift)
            glDrawArrays(GL_LINE_STRIP_ADJACENCY, self._max_offset, self._min_length)
            self.program.unuse()


        if self.draw_dots:
            self.dot_program.use()
            self.dot_program.uniform('shift', self.shift)
            glDrawArrays(GL_POINTS, self._max_offset, self._min_length)
            self.dot_program.unuse()

        self.vao.unbind()

        if GlApplication.DEBUG == True:
            glPolygonMode(GL_FRONT_AND_BACK, GL_FILL)


    def _pre_compile_data_layout(self):
        """
        validates datalayout and returns
        glsl code snippet
        """

        # try to find a good configuration if no specific 
        # layout was set by user 
        if self._data_layout is None:

            # XXX
            # - think more about this. It could be confusing
            #   that the layout is default set to this value.
            #   if one uses bad domain configuration and does not
            #   know it, he would need lot of try error to find out...
            #
            #   eg:
            #     x_data = RealAxis()
            #     y_data = NumpyDomain(...)
            #   --> here d0.x and d0.y would be used for plot.
            #       user could expext that x_data is an interval 
            #       and y_data is corresponding y_data ... who knowz??
            #
            self._data_layout = ('d0.x', 'd0.y')

            if len(self.domains) == 1:
                if self.domains[0].dimension == 1:
                    self._data_layout = ('d0.x', )
                else: 
                    self._data_layout = ('d0.x', 'd0.y')
            else:
                if self.domains[0].dimension == 1:
                    self._data_layout = ('d0.x', 'd1.x')

        if not type(self._data_layout) == tuple or len(self._data_layout) > 2:
            raise ValueError('Line2d.data_layout "{}" must be tuple of size 1 or 2'.format(
                self._data_layout
            ))

        pre_compiled_code = ''
        data_layout_match = re.compile('^d(\d)\.([xyzw]{0,1})$')
        for i, source in enumerate(self._data_layout):
            match = data_layout_match.match(source)
            if match is None:
                raise ValueError(
                    ('Line2d.data_layout {}-component "{}" bad format.'
                    + ' Must be d<number>.<xyzw>').format(
                    ['x','y'][i], source
                ))

            domain_id = int(match.group(1))
            if domain_id > len(self.domains)-1:
                print(', '.join(str(i) for i in range(0, len(self.domains))))
                raise ValueError(
                    ('Line2d.data_layout {}-component "{}" reffer to unkown domain d{}.'
                    + ' available domains: {}').format(
                    ['x','y'][i], 
                    source, 
                    domain_id, 
                    ', '.join('d'+str(i) for i in range(0, len(self.domains)))
                ))

            domain_dim = self.domains[domain_id].dimension
            glsl_component = match.group(2)
            if glsl_component == '':
                glsl_component = 'x'

            component_dim = {'x':1,'y':2,'w':3,'z':4}
            source_component = component_dim[glsl_component]
            
            if source_component > domain_dim:
                raise ValueError(
                    ('Line2d.data_layout {}-component "{}": cannot use d{}.{} '
                    + 'since domain d{} with dimension {} has only "{}" available.').format(
                    ['x','y'][i], 
                    source, 
                    domain_id, 
                    glsl_component,
                    domain_id,
                    domain_dim, 
                    ''.join(['x','y','z','w'][0:domain_dim])
                ))

            # float back mapping 
            if domain_dim == 1:
                source = 'd{}'.format(domain_id)

            pre_compiled_code += '{} = {};\n'.format(['x','y'][i], source)

        return pre_compiled_code

    def _init_program_uniforms(self):
        """
        set program uniforms to its default values
        """
        self.program.uniform('color', self.color or [0,0,0,1])
        self.program.uniform('mat_domain', numpy.identity(4).flatten())
        self.program.uniform('width', Line2d.GEOMETRY_SHADER_WIDTH*self._width)
        self.dot_program.uniform('color', self.dotcolor or self.color or [0,0,0,1])
        self.dot_program.uniform('mat_domain', numpy.identity(4).flatten())
        self.dot_program.uniform('width', Line2d.GEOMETRY_SHADER_WIDTH*self.dotsize)


        if hasattr(self.color_scheme, 'get_uniform_data'):
            for uniform in self.color_scheme.get_uniform_data().items():
                self.program.uniform(*uniform)

    def _compile_glsl_programs(self, vertex_source):
        """
        compiles glsl programs 
        """
        vertex_shader = Shader(GL_VERTEX_SHADER, vertex_source, substitutions={
            'KERNEL' : self._kernel+';', #user friendly semicolon :)
        })
        geometry_shader = Shader(GL_GEOMETRY_SHADER, load_lib_file('glsl/plot2d/line.geom.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/plot2d/line.frag.glsl'))
        
        try:
            vertex_shader.compile()

        except ShaderError as e:
            # try to compile shader without kernel to see whether
            # it is an error by user kernel oder by shader itsel
            try:
                Shader(GL_VERTEX_SHADER, vertex_source).compile()

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

