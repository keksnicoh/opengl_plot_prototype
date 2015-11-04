#-*- coding: utf-8 -*-
"""
font rendering utilities.
XXX optimize texture rendering...
@author Nicolas 'keksnicoh' Heimann <keksnicoh@googlemail.com>
"""
from gllib.renderer import renderer
from gllib.shader import Shader, Program
from gllib.helper import load_lib_file
from gllib.application import GlApplication
from gllib.matrix import ModelView
from gllib.util import Event

from OpenGL.GL import *
from PIL import ImageFont
import numpy, os, uuid
DEFAULT_FONT = os.path.dirname(os.path.abspath(__file__))+'/../resources/fonts/arial.ttf'
from copy import deepcopy
import re


class Text():
    """
    global texture cache. keys are tuples of
    (id(image_font_instance), character)
    """
    _TEXTURE_CACHE = {}

    _LATEX_CHARACTER_MAPPING = {
        'pi'        : u'\u03C0',
        'alpha'     : u'\u03b1',
        'beta'      : u'\u03b2',
        'gamma'     : u'\u03b3',
        'delta'     : u'\u03b4',
        'epsilon'   : u'\u03b5',
        'zeta'      : u'\u03b6',
        'eta'       : u'\u03b7',
        'Gamma'     : u'\u0393',
        'Delta'     : u'\u0394',
        'Theta'     : u'\u0398',
        'theta'     : u'\u03b8',
        'vartheta'  : u'\u03d1',
        'kappa'     : u'\u03ba',
        'lambda'    : u'\u03bb',
        'mu'        : u'\u03bc',
        'nu'        : u'\u03bd',
        'xi'        : u'\u03be',
        'Lambda'    : u'\u039b',
        'Xi'        : u'\u039e',
        'Pi'        : u'\u03a0',
        'rho'       : u'\u03c1',
        'varrho'    : u'\u03f1',
        'sigma'     : u'\u03c3',
        'varsigma'  : u'\u03c2',
        'Sigma'     : u'\u03a3',
        'Upsilon'   : u'\u03a5',
        'Phi'       : u'\u03d5',
        'tau'       : u'\u03c4',
        'phi'       : u'\u03d5',
        'varphi'    : u'\u03a6',
        'chi'       : u'\u03a7',
        'psi'       : u'\u03c8',
        'omega'     : u'\u03c9',
        'Psi'       : u'\u03a8',
        'Omega'     : u'\u03a9',

    }

    def __init__(self, text, font, line_spacing=5):
        self._text          = text
        self.font           = font
        self.line_spacing   = line_spacing
        self.on_update = Event()

        # font renderer api attributes
        self.is_prepared    = False
        self.unique_id      = None
        self.font_renderer = None
        self.in_use_layouts = set()
        self.render_data    = None
        self.vertex_data    = numpy.zeros(len(self._text)*2*6, dtype=numpy.float32)
        self.txt_data       = numpy.zeros(len(self._text)*2*6, dtype=numpy.float32)

        # layout api attributes
        self.boxsize        = [0.0,0.0] 
    
    def set_text(self, text):
        self._text = text
        self.prepare()
        self.on_update(self)

    def _map_latex_placeholder(self, match):
        if match.group(1) not in Text._LATEX_CHARACTER_MAPPING:
            return match.group(0)

        return Text._LATEX_CHARACTER_MAPPING[match.group(1)]

    def _text_process(self):
        latex_replaced = re.sub(r'\$([a-zA-Z0-9]+)\$', self._map_latex_placeholder, self._text)
        return unicode(latex_replaced)

    def prepare(self):
        relpos          = [0.0,.0]
        max_line_height = 0.0
        processed_text = self._text_process()
        self.render_data = list([None for j in range(0,len(processed_text))])
        for n, char in enumerate(processed_text):
            glyph                          = self.font.getmask(char)
            glyph_width, glyph_height      = glyph.size
            glyph_offset_x, glyph_offset_y = self.font.getoffset(char)

            # special characters
            if char == FontRenderer.NEWLINE:
                self.render_data[n] = FontRenderer.NEWLINE
                relpos[1] += max_line_height+self.line_spacing
                relpos[0] = .0
                continue

            # vertex data. note that opengl interpret this
            # data counter clockwise...
            #    5   6
            #  1 +---+        -
            #    |\  |        |
            #    | \ |        | (offset_y - size_y)
            #    |  \|        |
            #  2 +---+ 3,4    -
            #    |   |
            #   (offset_x + size_x)
            vert_size = (glyph_width, glyph_height-1)
            vert_offset = (-glyph_offset_x, glyph_offset_y)
            self.vertex_data[n*12:(n+1)*12] = numpy.array([
                relpos[0]+vert_offset[0],              relpos[1]+vert_offset[1],              #1 #left triangle
                relpos[0]+vert_offset[0],              relpos[1]+vert_offset[1]+vert_size[1], #2
                relpos[0]+vert_offset[0]+vert_size[0], relpos[1]+vert_offset[1]+vert_size[1], #3
                relpos[0]+vert_offset[0]+vert_size[0], relpos[1]+vert_offset[1]+vert_size[1], #4 #right triangle
                relpos[0]+vert_offset[0]+vert_size[0], relpos[1]+vert_offset[1],              #5
                relpos[0]+vert_offset[0],              relpos[1]+vert_offset[1]               #6
            ], dtype=numpy.float32)
            relpos[0] += glyph_width

            # text coord data implies the coords in fragment shader
            # for the texture. note that this must be inverse to the
            # vertex_data since opengl vertex_data is interpreted counter
            # clockwise, and text_data is clockwise.
            frag_size = (1, 1)
            self.txt_data[n*12:(n+1)*12] = numpy.array([
                0,0, 0,frag_size[1], frag_size[0],frag_size[1],
                frag_size[0], frag_size[1], frag_size[0],0, 0,0,
            ], dtype=numpy.float32)

            # create final render data
            ID = self._create_texture(char, glyph, glyph_width, glyph_height)
            self.render_data[n] = [ID, None]
            max_line_height = max(max_line_height, vert_size[1])

        self.boxsize = [relpos[0], relpos[1]+max_line_height]
        self.is_prepared = True

    def _create_texture(self, char, glyph, width, height):
        """
        creates an opengl 2d texture from a TTF font object.
        XXX optimize this, we only need a 2 channel i guess...
        """
        if (id(self.font), char) not in Text._TEXTURE_CACHE:
            ID = glGenTextures (1)
            glBindTexture (GL_TEXTURE_2D, ID)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
            glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
            tex2d = []
            for j in xrange (height):
                for i in xrange (width):
                    value = glyph.getpixel ((i, j))
                    tex2d.append(float(value)/255)
            tex2d = numpy.array(tex2d, dtype=numpy.float32)
            glTexImage2D(GL_TEXTURE_2D, 0, GL_RED, width, height, 0, GL_RED, GL_FLOAT, tex2d)
            Text._TEXTURE_CACHE[(id(self.font), char)] = ID
        return Text._TEXTURE_CACHE[(id(self.font), char)]

class Layout():
    def __init__(self):
        self._texts = []
        self.has_changed = True

    def get_render_protocol(self):
        raise NotImplementedError('abstract method must not be empty')

    def get_unique_texts(self):
        self.has_changed = False
        return set(text[0] for text in self._texts)

class RelativeLayout(Layout):
    """
    layout can handle basic relative operations like
    top/center/bottom alignment. to provide more power
    there is a simple box model implemented which allows to
    define 2 alignments per text. 
    """

    VTOP    = 1
    VCENTER = 2
    VBOTTOM = 4
    HLEFT   = 8
    HCENTER = 16
    HRIGHT  = 32

    def __init__(self, boxsize, modelview=None):
        self.boxsize = boxsize
        self._texts = [] 
        self.has_changed = True
        self.modelview = ModelView()

    def clear_texts(self):
        for text in self._texts:
            text[0].in_use_layouts.remove(self)
        self._texts = []

    def add_text(self, text, alignment=VTOP|HLEFT, boxalignment=None, margin=[0,0,0,0], boxsize=(None, None), rotation=None):
        self._texts.append((text, alignment, boxalignment or alignment, margin, boxsize, rotation))
        text.in_use_layouts.add(self)
        self.has_changed = True

    def get_render_protocol(self):
        protocol = []
        for i, (text, alignment, boxalignment, margin, boxsize, rotation) in enumerate(self._texts):
            translation = [0,0]
            text_size = [text.boxsize[0]+margin[1]+margin[3], text.boxsize[1]+margin[0]+margin[2]]
            text_boxsize = (boxsize[0] or self.boxsize[0], boxsize[1] or self.boxsize[1])

            if alignment & RelativeLayout.HCENTER:
                translation[0] += float(text_boxsize[0])/2 - float(text_size[0])/2
            elif alignment & RelativeLayout.HRIGHT:
                translation[0] += text_boxsize[0] - text_size[0]
            else:
                translation[0] += 0
            if alignment & RelativeLayout.VCENTER:
                translation[1] += float(text_boxsize[1])/2 - float(text_size[1])/2
            elif alignment & RelativeLayout.VBOTTOM:
                translation[1] += text_boxsize[1] - text_size[1]
            else:
                translation[1] += margin[0]


            #modelview.translate(*translation)
            

            if boxalignment & RelativeLayout.HCENTER:
                translation[0] += float(self.boxsize[0])/2 - float(text_boxsize[0])/2
            elif boxalignment & RelativeLayout.HRIGHT:
                translation[0] += self.boxsize[0] - text_boxsize[0]
            else:
                translation[0] += 0
            if boxalignment & RelativeLayout.VCENTER:
                translation[1] += float(self.boxsize[1])/2 - float(text_boxsize[1])/2
            elif boxalignment & RelativeLayout.VBOTTOM:
                translation[1] += self.boxsize[1] - text_boxsize[1]
            else:
                translation[1] += 0
            modelview = deepcopy(self.modelview)
            
            if rotation is not None:
                modelview.translate(-float(text_size[0])/2,-float(text_size[1])/2)
                modelview.rotate(rotation)
                modelview.translate(+float(text_size[0])/2,+float(text_size[1])/2)
            modelview.translate(*translation)

            protocol.append((text, modelview))

        return protocol

class AbsoluteLayout(Layout):
    # XXX
    # - implement missing transformations
    LEFT_UPPER    = 1
    LEFT_CENTER   = 2
    LEFT_BOTTOM   = 3
    CENTER_UPPER  = 4
    CENTER_CENTER = 5
    CENTER_BOTTOM = 6
    RIGHT_UPPER   = 7
    RIGHT_CENTER  = 8
    RIGHT_BOTTOM  = 9
    UPPER_CENTER  = 10
    LEFT_CENTER   = 11
    RIGHT_CENTER  = 12

    def __init__(self, modelview=None, coord_system=LEFT_UPPER):
        self.coord_system = coord_system
        self._position = [0,0] 
        self.has_changed = True
        self._texts = [] 
        self.modelview = ModelView()
    def clear_texts(self):
        for text in self._texts:
            text[0].in_use_layouts.remove(self)
        self._texts = []

    def add_text(self, text, pos=(0.0,0.0)):
        self._texts.append((text, pos))
        text.in_use_layouts.add(self)
        self.has_changed = True

    def get_render_protocol(self):
        protocol = []
        for i, (text, pos) in enumerate(self._texts):
            modelview = deepcopy(self.modelview)
            if self.coord_system == AbsoluteLayout.LEFT_UPPER:
                translation = pos
            elif self.coord_system == AbsoluteLayout.UPPER_CENTER:
                translation = (pos[0]-float(text.boxsize[0])/2, pos[1])
            elif self.coord_system == AbsoluteLayout.LEFT_CENTER:
                translation = (pos[0], pos[1]+float(text.boxsize[1])/2)
            elif self.coord_system == AbsoluteLayout.RIGHT_CENTER:
                translation = (pos[0]-text.boxsize[0], pos[1]-float(text.boxsize[1])/2)
            else:
                raise ValueError('invalid coord system')
            modelview.translate(*translation)
            protocol.append((text, modelview))
        return protocol

class FontRenderer(renderer.Renderer):
    NEWLINE = '\n'
    SCALING = 1.0
    def __init__(self, camera, modelview=None):
        self.camera = camera
        self.color = [0.0, 0.0, 0.0, 1.0]
        self.program = None
        self.length = None
        self.xy = (0,0)
        self.render_data = []
        self._texture_cache = {}
        #self.init()
        self._texts_prepared = False
        self._is_camera_updated = False
        self.modelview = modelview or ModelView()
        """ local modelview matrix. """

        """
        stores all active text objects
        """
        self._texts = {}

        self.layouts = {}

        # Has to be more specifierd later
        #self.camera.on_change_matrix.append(self.screen_resized)

    #def screen_resized(self, *args, **kwargs):
    #    self._is_camera_updated = True
    #    self._texts_prepared = False

    def set_color(self, color):
        self.color = color


    def init(self):
        """
        prepares shaders and vao/vbo
        """
        # init gl
        program         = Program()
        vertex_shader   = Shader(GL_VERTEX_SHADER, load_lib_file('glsl/font/font.vert.glsl'))
        fragment_shader = Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/font/font.frag.glsl'))
        program.shaders.append(vertex_shader)
        program.shaders.append(fragment_shader)
        program.link()

        self.program = program

        self.camera.on_change_matrix.append(self.camera_updated)

    def _find_text_tuple(self, text):
        return self._texts[text.unique_id]


    def _update_texts(self, texts):
        existing_texts = set(x[0] for x in self._texts if x in texts)
        new_texts = texts - existing_texts
        for text in new_texts:
            text.unique_id = uuid.uuid4()
            self._texts[text.unique_id] = (text, None, None)

            text.on_update.append(self.text_updated)

    def text_updated(self, text):
        raise NotImplementedError('implement my behavior')

    def prepare_texts(self):
        """
        prepares all registred texts.
        """
        for unique_id, (text, vao, length) in self._texts.items():
            # text is not used by any layouts => remove text and cleanup buffers
            if len(text.in_use_layouts) < 1:
                text.unique_id = None
                glDeleteVertexArrays(1, (vao,))
                text.on_update.remove(self.text_updated)
                del self._texts[unique_id]

            # text is used by layouts but there is no vao
            # or text was not prepared yet.
            elif vao is None or not text.is_prepared:
                text.prepare()
                vertex_data = text.vertex_data
                text_coord_data = text.txt_data

                length = len(vertex_data)
                vao = vao or glGenVertexArrays(1)
                vbo = glGenBuffers(2)
                glBindVertexArray(vao)

                glBindBuffer(GL_ARRAY_BUFFER, vbo[0])
                glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(vertex_data), vertex_data, GL_STATIC_DRAW)
                glVertexAttribPointer(self.program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, 0, None)
                glEnableVertexAttribArray(0)
                glBindBuffer(GL_ARRAY_BUFFER, 0)

                glBindBuffer(GL_ARRAY_BUFFER, vbo[1])
                glBufferData(GL_ARRAY_BUFFER, ArrayDatatype.arrayByteCount(text_coord_data), text_coord_data, GL_STATIC_DRAW)
                glVertexAttribPointer(self.program.attributes['vertex_texcoord'], 2, GL_FLOAT, GL_FALSE, 0, None)
                glEnableVertexAttribArray(1)
                glBindBuffer(GL_ARRAY_BUFFER, 0)

                self._texts[unique_id] = (text, vao, length)

        self.camera_updated()
        self.modelview_updated()
        self._texts_prepared = True    

    def camera_updated(self, *args, **kwargs):
        self.program.use()
        self.program.uniform('mat_camera', self.camera.get_matrix())
        self.program.unuse()    

    def modelview_updated(self, *args, **kwargs):
        self.program.use()
        self.program.uniform('mat_modelview', self.modelview)
        self.program.unuse()    

    def set_render_length(self, length=None):
        self.length = length

    def render(self):
        for name, layout in self.layouts.items():
            if layout.has_changed:
                self._update_texts(layout.get_unique_texts())
                self._texts_prepared = False

        if not self._texts_prepared:
            self.prepare_texts()

        self.program.use()
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        if GlApplication.DEBUG == True:
            self.program.uniform('debug', True)
        glActiveTexture(GL_TEXTURE1) # XXX disale texture later??
        self.program.uniform('tex', 1)
        self.program.uniform('color', self.color)

        # Too many looops!!!!!!
        for name, layout in self.layouts.items():
            for (text, modelview) in layout.get_render_protocol():
                (_, vao, length) = self._find_text_tuple(text)
                self.program.uniform('mat_modelview', modelview)
                glBindVertexArray(vao)
                
                render_data = text.render_data
                for n, data in enumerate(render_data[0:length]):
                    if data == FontRenderer.NEWLINE: continue
                    (gl_tex_id, _) = data
    
                    glBindTexture (GL_TEXTURE_2D, gl_tex_id)
                    glDrawArrays(GL_TRIANGLES, n*6, 6)
    
                glBindVertexArray(0)
        
        if GlApplication.DEBUG == True:
            self.program.uniform('debug', False)
        self.program.unuse()

def next_p2 (num):
    """ If num isn't a power of 2, will return the next higher power of two """
    rval = 1
    while rval<num:
        rval <<= 1
    return rval
