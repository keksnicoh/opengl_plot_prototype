#-*- coding: utf-8 -*-
"""
font rendering library.

XXX
- intelligent partioning of char buffers
- what if characters are unkown
- simple markup        <color=red>...</color>
- simple TeX parsing   $ ... $
   * fractionals
   * square roots
   * integrals
   * uppers
   * lowers
   * left and right () with correct size

@author Nicolas 'keksnicoh' Heimann <nicolas.heimann@gmail.com>
"""
from gllib.shader import Shader, Program
from gllib.helper import load_lib_file, resource_path
from gllib.vertex import BufferObject
import os
import re

from OpenGL.GL import *
import numpy as np
from ctypes import c_void_p, c_int
from scipy.ndimage.io import imread

FONT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'resources', 'fnt')
import re

class SimpleLatexLexer():
    T_CHARS = 'T_CHARS'
    T_COMMAND = 'T_COMMAND'
    T_COMMAND_ARG = 'T_COMMAND_ARG'
    T_COMMAND_END = 'T_COMMAND_END'
    T_LOWER = 'T_LOWER'
    T_LOWER_END = 'T_LOWER_END'
    T_UPPER = 'T_UPPER'
    T_UPPER_END = 'T_UPPER_END'

    def __init__(self):
        self.opcode = []
        self.ptr = 0

    def lex(self, chars):
        self.opcode = []
        self.ptr = 0
        self.chars = chars

        self._lex_chrs()

        return self.opcode

    def _lex_chrs(self):
        buf = ''
        while self.ptr < len(self.chars):
            if self.chars[self.ptr] == '$':
                if buf != '':
                    self.opcode.append((self.T_CHARS, buf))
                    buf = ''

                self.ptr += 1
                self._lex_tex()

                if self.ptr >= len(self.chars) or self.chars[self.ptr] != '$':
                    raise Exception('expected closing $')

                self.ptr += 1
            else:
                buf += self.chars[self.ptr]
                self.ptr += 1

        if buf != '':
            self.opcode.append((self.T_CHARS, buf))

    def _lex_tex(self, end_chars=['$']):
        buf = ''
        while self.ptr < len(self.chars):
            if self.chars[self.ptr] in end_chars:
                if buf != '':
                    self.opcode.append((self.T_CHARS, buf))
                return

            if self.chars[self.ptr] == '\\':
                if len(buf):
                    self.opcode.append((self.T_CHARS, buf))
                    buf = ''

                self.ptr += 1
                self._lex_cmd()

            elif self.chars[self.ptr] == '_':
                if len(buf):
                    self.opcode.append((self.T_CHARS, buf))
                    buf = ''
                self.ptr += 1
                self._lex_uplow(self.T_LOWER, self.T_LOWER_END)
            elif self.chars[self.ptr] == '^':
                if len(buf):
                    self.opcode.append((self.T_CHARS, buf))
                    buf = ''
                self.ptr += 1
                self._lex_uplow(self.T_UPPER, self.T_UPPER_END)
            else:
                buf += self.chars[self.ptr]
                self.ptr += 1

    def _lex_cmd(self):
        if self.chars[self.ptr] == '\\':
            self.opcode.append((self.T_CHARS, '\\'))
            self.ptr += 1
            return

        buf = ''
        while self.ptr < len(self.chars) and re.match(u'[a-zA-Z]$', self.chars[self.ptr]):
            buf += self.chars[self.ptr]
            self.ptr += 1

        if buf == '':
            raise Exception('unexpected char after command begin "{}"'.format(self.chars[self.ptr]))

        self.opcode.append((self.T_COMMAND, buf, self.chars[self.ptr]))

        if self.ptr >= len(self.chars):
            self.opcode.append((self.T_COMMAND_END,))

        if self.chars[self.ptr] != '{':
            self.opcode.append((self.T_COMMAND_END,))

        if self.chars[self.ptr] == '_':
            self.ptr += 1
            self._lex_uplow(self.T_LOWER, self.T_LOWER_END)

        if self.chars[self.ptr] == '^':
            self.ptr += 1
            self._lex_uplow(self.T_UPPER, self.T_UPPER_END)


    def _lex_uplow(self, opcode_begin, opcode_end):
        assert self.ptr < len(self.chars)

        self.opcode.append((opcode_begin, ))
        if self.chars[self.ptr] == '{':
            self.ptr += 1
            self._lex_tex(['}', '$'])

            assert self.ptr < len(self.chars)
            assert self.chars[self.ptr] == '}'

            self.ptr += 1

        elif self.chars[self.ptr] == '\\':
            self.ptr += 1
            self._lex_cmd()

        elif not re.match(u'\b', self.chars[self.ptr]):
            self.opcode.append((self.T_CHARS, self.chars[self.ptr]))
            self.ptr += 1

        else:
            raise Exception('unepected char in T_LOWER "{}"'.format(self.chars[self.ptr]))

        self.opcode.append((opcode_end, ))

LEXER = SimpleLatexLexer()

class TextObject(object):
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
        'Int'       : u'\u222B',
    }

    """
    represents one chunk of related chars
    within a string
    """
    def __init__(self, renderer, chars, size, position, color=[0,0,0,1], rotation=0, enable_simple_tex=False):
        self._chars = chars
        self.renderer = renderer
        self._rotation = rotation
        self._color = color
        self._size = size
        self._position = position
        self._enable_simple_tex = enable_simple_tex
        self._boxsize = None
        self._buffer = None
        self._has_changes = True

    def get_boxsize(self):
        self._create_buffer()
        return self._boxsize

    def _create_buffer(self):
        if not self._has_changes:
            pass



        font = self.renderer.font
        index = 0
        position = self.position

        colors = []
        if type(self._color[0]) in [list, tuple]:
            for charcol in self._color:
                colors.append(charcol)
            for i in range(len(colors), len(self.chars)):
                colors.append(charcol)
        else:
            colors = [self._color for i in range(len(self.chars))]

        chars = self.chars.decode('utf-8')
        def _map_latex_placeholder(match):
            if match.group(1) not in self._LATEX_CHARACTER_MAPPING:
                return match.group(0)

            return self._LATEX_CHARACTER_MAPPING[match.group(1)]
        chars = re.sub(r'\$([a-zA-Z0-9]+)\$', _map_latex_placeholder, chars)
        chardata = np.empty(len(chars), dtype=FontRenderer.CHAR_DTYPE)

        char_list = []
        position = [self.position[0], self.position[1]]

        class OpcodeToCharacters():
            def __init__(self):
                pass

            def to_characters(self, opcode, font, position, size, rotation, color):
                self.font = font
                self.color = color
                self.rotation = rotation
                self.position = position
                self.size = [size]
                self.ptr = 0
                self.offset = [[0,0]]
                self.position_stack = []
                self.max_position_stack = []
                self.opcode = opcode
                self.char_list = []
                self._main()
                return self.char_list

            def _main(self):
                while self.ptr < len(self.opcode):
                    if self.opcode[self.ptr][0] == LEXER.T_CHARS:
                        self._chars()
                        self.ptr += 1

                    elif self.opcode[self.ptr][0] == LEXER.T_COMMAND:
                        self._cmd()

                    elif self.opcode[self.ptr][0] == LEXER.T_LOWER:
                        self.position_stack.append((self.position[0], self.position[1]))
                        self.offset.append([self.offset[-1][0] - self.size[-1]*0.05, self.offset[-1][1] + self.size[-1]*0.45])
                        self.size.append(self.size[-1]*0.85)
                        self.ptr += 1

                    elif self.opcode[self.ptr][0] == LEXER.T_LOWER_END:
                        self.size.pop()
                        self.offset.pop()
                        self.ptr += 1
                        self.max_position_stack.append(self.position)

                        #self.position = self.position_stack.pop()

                    elif self.opcode[self.ptr][0] == LEXER.T_UPPER:
                        if self.opcode[self.ptr-1][0] == LEXER.T_LOWER_END:
                            self.position_stack.append((self.position[0], self.position[1]))
                        else:
                            self.max_position_stack.append(self.position)

                        self.offset.append([0, self.offset[-1][1] + -self.size[-1]*0.05])
                        self.size.append(self.size[-1]*0.6)

                        self.ptr += 1

                    elif self.opcode[self.ptr][0] == LEXER.T_UPPER_END:
                        self.size.pop()
                        self.offset.pop()
                        self.ptr += 1

                        p1 = self.max_position_stack.pop()
                        if p1[0] > self.position[0]:
                            self.position = p1


                    else:
                        raise Exception('could not work with opcode {}'.format(self.opcode[self.ptr]))

            def _cmd(self):
                cmd = self.opcode[self.ptr][1]
                if not cmd in TextObject._LATEX_CHARACTER_MAPPING:
                    raise Exception('cannot handle latex command \\{}'.format(cmd))

                self._write_char(TextObject._LATEX_CHARACTER_MAPPING[cmd])

                self.ptr += 1

                if not self.opcode[self.ptr][0] == LEXER.T_COMMAND_END:
                    raise Exception('latex error runaway. Intrnal error? ')

                self.ptr += 1

            def _chars(self):
                for c in self.opcode[self.ptr][1]:
                    self._write_char(c)

            def _write_char(self, c):
                self.char_list.append((
                    (self.position[0] + self.offset[-1][0], self.position[1] + self.offset[-1][1]),
                    self.color,
                    self.size[-1],
                    self.rotation,
                    self.font.char_glyph[c]))

                sizefactor = float(self.size[-1])/60

                fntobj = self.font.glyphs[font.char_glyph[c]]
                self.position = (self.position[0] + sizefactor*float(fntobj.xadvance-16), self.position[1])

        if self._enable_simple_tex:
            opcode = LEXER.lex(chars)
            charser = OpcodeToCharacters()
            char_list = charser.to_characters(opcode, font, (position[0], position[1]), self.size, self.rotation, colors[0])
            chardata = np.array(char_list, dtype=FontRenderer.CHAR_DTYPE)
        else:
            for char in chars:
                if not char in font.char_glyph:
                    # XXX
                    # - define me
                    print('WARNING UNKOWN CHAR renderer.py')
                    continue
                fntobj = font.glyphs[font.char_glyph[char]]

                chardata[index] = ((position[0], position[1]), colors[index], self.size, self.rotation, font.char_glyph[char])
                sizefactor = float(self.size)/60
                position = (position[0]+sizefactor*float(fntobj.xadvance-16), position[1])
                index += 1

        coords = chardata['position'] - self.position
        transformation = np.array([
            (np.cos(self.rotation), np.sin(self.rotation)),
            (-np.sin(self.rotation), np.cos(self.rotation))
        ], dtype=np.float32)
        chardata['position'] = [transformation.dot(a) for a in coords]
        chardata['position'] += self.position

        positions = chardata['position']
        self._buffer = chardata
        self._boxsize = (
            chardata['position'][-1][0]-chardata['position'][0][0]+self._size,
            chardata['position'][0][1]-chardata['position'][-1][1]+self._size)
        self._has_changes = False

    def get_data(self):
        self._create_buffer()
        return self._buffer

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = rotation
        self.renderer._has_changes = True
        self._has_changes = True

    @property
    def chars(self):
        return self._chars

    @chars.setter
    def chars(self, chars):
        self._chars = chars
        self.renderer._has_changes = True
        self._has_changes = True

    @property
    def size(self):
        return self._size

    @size.setter
    def size(self, size):
        self._size = size
        self.renderer._has_changes = True
        self._has_changes = True

    @property
    def position(self):
        return self._position

    @position.setter
    def position(self, position):
        self._position = position
        self.renderer._has_changes = True
        self._has_changes = True

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, color):
        self._color = color
        self.renderer._has_changes = True
        self._has_changes = True

    def __len__(self):
        return len(self._chars.decode('utf-8'))



class FNTFile():
    """
    *.fnt representation.
    todo: persist
    """

    class FNTGlyph():
        """
        representation of glyph
        """
        def __init__(self, *args):
            self.cid, self.x, self.y, self.width, self.height, \
            self.xoffset, self.yoffset, self.xadvance, \
            self.page, self.chnl = [int(a) for a in args]

        def dump(self):
            return ((self.x, self.y,0,0), (self.width,self.height,0,0),(self.xoffset,self.yoffset,0,0),self.page,self.xadvance,self.chnl,0)


    def __init__(self):
        self.page_paths = []
        self.glyphs = []
        self.char_glyph = {}

    @classmethod
    def load_from_file(cls, file_path):
        prog = re.compile(u'^char\s+id=(\d+)\s+x=(\d+)\s+y=(\d+)\s+width=(\d+)'
                        + u'\s+height=(\d+)\s+xoffset=(-?\d+)\s+yoffset=(-?\d+)'
                        + u'\s+xadvance=(\d+)\s+page=(\d+)\s+chnl=(\d+)')

        fnt = cls()
        page_prog = re.compile(u'^page id=(\d+)\s+file="?(.*\.png)"?')
        page_files = []
        with open(file_path) as f:
            expected_chars = None
            index = 0;
            for line in f:
                match = page_prog.match(line)
                if match is not None:
                    pid, pfile = match.groups()
                    page_path = os.path.join(os.path.dirname(file_path), pfile)
                    fnt.page_paths.append(page_path)
                    continue

                if expected_chars is None:
                    if line[0:11] == 'chars count':
                        expected_chars = int(line.split('=')[1])
                else:
                    match = prog.match(line)
                    if match is not None:
                        if len(fnt.glyphs) > expected_chars:
                            raise Exception('more characters than declared in "chars count" found in file ""'.format(file_path))

                        fntchar = FNTFile.FNTGlyph(*match.groups())
                        fnt.glyphs.append(fntchar)
                        fnt.char_glyph[unichr(fntchar.cid)] = index
                        index += 1

            if expected_chars is None:
                raise Exception('"chars count" missing in file "{}"'.format(file_path))

            if expected_chars != len(fnt.glyphs):
                raise Exception(
                    ('did not find all characters: expected {}'
                    +' characterd to be defined but found {} in file "{}"').format(
                    expected_chars, len(fnt.glyphs), file_path))

            return fnt

class FontRenderer():
    CHAR_DTYPE = np.dtype([
        ('position', np.float32, (2,)),
        ('color', np.float32, (4,)),
        ('size', np.float32),
        ('rot', np.float32),
        ('fntobj', np.int32),
    ])

    GLYPH_DTYPE = np.dtype([
        ('position', np.float32, (4,)),
        ('size', np.float32, (4,)),
        ('offset', np.float32, (4,)),
        ('xadvance', np.float32),
        ('page', np.float32),
        ('chnl', np.float32),
        ('buff', np.float32),
    ])

    def __init__(self, font=None):
        self.camera = None
        if font is None:
            font = os.path.join(FONT_FOLDER, 'arial.fnt')
        self.font_path = font
        self.texts = []
        self._has_changes = True
        self._fnt = None

    @property
    def font(self):
        return self._fnt


    def init(self):
        # load font file
        self._fnt = FNTFile.load_from_file(self.font_path)

        # upload glyph 3d atlas
        page_data         = [imread(img_path)[:,:,3] for img_path in self._fnt.page_paths]
        glypthatlas_width = page_data[0].shape[0]
        glyphatlas_height = page_data[0].shape[1]
        glyphatlas        = np.empty((len(page_data), glypthatlas_width, glyphatlas_height), dtype=np.float32)
        for i, glyphdata in enumerate(page_data):
            if glyphdata.shape[0:2] != (glypthatlas_width,glyphatlas_height):
                raise Exception((
                    'font "{}" corrupt: font page id={} file="{}" image size {}x{}'
                    + ' differs from the first page id=0 file="{}" {}x{}').format(
                        self.font, i, self._fnt.page_paths[i], glyphdata.shape[0],
                        glyphdata.shape[1], self._fnt.page_paths[0],
                        page_data[0].shape[0], page_data[0].shape[1]))

            glyphatlas[i] = glyphdata

        self.texture_id = glGenTextures(1);

        glBindTexture(GL_TEXTURE_2D_ARRAY, self.texture_id);
        glTexImage3D(GL_TEXTURE_2D_ARRAY, 0, GL_R32F, glypthatlas_width, glyphatlas_height, glyphatlas.shape[0], 0, GL_RED, GL_FLOAT, glyphatlas);
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameterf(GL_TEXTURE_2D_ARRAY, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        glBindTexture(GL_TEXTURE_2D_ARRAY, 0);

        # create shader
        self.shader_program = Program()
        self.shader_program.shaders.append(Shader(GL_VERTEX_SHADER, VERTEX_SHADER))
        self.shader_program.shaders.append(Shader(GL_GEOMETRY_SHADER, GEOMETRY_SHADER.replace('$n$', str(len(self._fnt.glyphs)))))
        self.shader_program.shaders.append(Shader(GL_FRAGMENT_SHADER, FRAGMENT_SHADER.replace('$n$', str(len(self._fnt.glyphs)))))
        self.shader_program.link()

        # create vbo/vao
        self.buffer = BufferObject.empty(1, dtype=self.CHAR_DTYPE)
        self.vao = glGenVertexArrays(1)

        # bind vao
        glBindVertexArray(self.vao)
        self.buffer.bind()

        itemsize = c_int(self.CHAR_DTYPE.itemsize)
        glVertexAttribPointer(self.shader_program.attributes['vertex_position'], 2, GL_FLOAT, GL_FALSE, itemsize, c_void_p(0))
        glEnableVertexAttribArray(0)
        glVertexAttribPointer(self.shader_program.attributes['glyph_color'], 4, GL_FLOAT, GL_FALSE, itemsize, c_void_p(8))
        glEnableVertexAttribArray(1)
        glVertexAttribPointer(self.shader_program.attributes['glyph_size'], 1, GL_FLOAT, GL_FALSE, itemsize, c_void_p(24))
        glEnableVertexAttribArray(2)
        glVertexAttribPointer(self.shader_program.attributes['glyph_rot'], 1, GL_FLOAT, GL_FALSE, itemsize, c_void_p(28))
        glEnableVertexAttribArray(3)
        glVertexAttribIPointer(self.shader_program.attributes['fntobj'], 1, GL_INT, itemsize, c_void_p(32))
        glEnableVertexAttribArray(4)

        self.buffer.unbind()
        glBindVertexArray(0)

        # upload glyph information
        glyphdata = np.empty(len(self._fnt.glyphs), dtype=self.GLYPH_DTYPE)
        glyphdata[:] = [c.dump() for c in self._fnt.glyphs]

        self.font_buffer = BufferObject.to_device(glyphdata, target=GL_UNIFORM_BUFFER)
        self.font_buffer.bind_buffer_base(0)

        block_index = glGetUniformBlockIndex(self.shader_program.gl_id, "ubo_font_objects")
        if block_index == GL_INVALID_INDEX:
            raise Exception('wo is der block was')

        glUniformBlockBinding(self.shader_program.gl_id, block_index, self.font_buffer.gl_buffer_base)

        self.shader_program.uniform('tex_scale', [1.0/glypthatlas_width, 1.0/glyphatlas_height])
        self.shader_program.uniform('fontsize_real', 60)
        self.shader_program.uniform('tex', 1)

        if self.camera:
            self.shader_program.uniform('mat_camera', self.camera.get_matrix())
            self.camera_changed = False

        for text in self.texts:
            text.font = self._fnt

    def set_camera(self, camera):
        self.camera = camera
        self.camera_changed = True

    def create_text(self, text, size=10, position=(0,0), color=[0,0,0,1], rotation=0, **kwargs):
        """
        creates a text with certain size, position and rotation.
        :text: the text to be rendered
        :size: size of the text
        :position: position on xy plane
        :rotation: angle to rotate aroung (position.x, position.y)
           in mathematical way (anti clockwise).
           np.pi/2   = 90°
           np.pi     = 180°
           np.pi*3/2 = 270°
           2*pi      = 360°
        returns a TextObject instance.
        """
        textobj = TextObject(self, text, size, position, color=color, rotation=rotation, **kwargs)
        self.texts.append(textobj)
        self._has_changes = True
        return textobj

    def clear_texts(self):
        self.texts = []
        self._has_changes = True

    def render(self):
        self._dummybufferstuff()
        if self.camera_changed:
            self.shader_program.uniform('mat_camera', self.camera.get_matrix())

        # prepare
        glClearColor(1,1,1,1)
        glActiveTexture(GL_TEXTURE1) # XXX disale texture later??
        glBindTexture (GL_TEXTURE_2D_ARRAY, int(self.texture_id))
        glEnable (GL_BLEND)
        glBlendFunc (GL_SRC_ALPHA,GL_ONE_MINUS_SRC_ALPHA)

        # render
        glBindVertexArray(self.vao)
        self.shader_program.use()
        glDrawArrays(GL_POINTS, 0, self.buffer.shape[0])
        self.shader_program.unuse()
        glBindVertexArray(0)

    def _dummybufferstuff(self):
        # XXX
        #  think about me,
        #  intelligent partitioning and bla
        if self._has_changes:
            nchars = 0
            for textobj in self.texts:
                nchars += len(textobj)

            chardata = np.empty(nchars, dtype=self.CHAR_DTYPE)
            index = 0
            for textobj in self.texts:
                data = textobj.get_data()
                chardata[index:index+len(data)] = data
                index += len(data)

            self.buffer.set(chardata)
            self._has_changes = False

VERTEX_SHADER = """
#version /*{$VERSION$}*/

uniform mat4 mat_camera;


in float glyph_rot;
out float geom_glyph_rot;

in vec4 glyph_color;
out vec4 geom_glyph_color;

in float glyph_size;
out float geom_glyph_size;

in int fntobj;
out int geom_fntobj;

in vec2 vertex_position;

void main()
{
    geom_glyph_size = glyph_size;
    geom_fntobj = fntobj;
    geom_glyph_rot = glyph_rot;
    geom_glyph_color = glyph_color;
    gl_Position = vec4(vertex_position, 0, 1);
}
"""

GEOMETRY_SHADER = """
#version /*{$VERSION$}*/

struct glyph {
  vec4 pos;
  vec4 size;
  vec4 offset;
  float page;
  float xadvance;

  float c;
};
layout (std140) uniform ubo_font_objects
{
    glyph glyphs[$n$];
};

layout (points)  in;
layout (triangle_strip)   out;
layout (max_vertices = 4) out;

in       float geom_glyph_size[1];
in       int   geom_fntobj[1];
in       float geom_glyph_rot[1];
in       vec4  geom_glyph_color[1];
out      vec2  tex_coord;
out      vec4  color;
flat out float page_id;

uniform float  fontsize_real;
uniform mat4   mat_camera;
uniform vec2   tex_scale;

float xwidth;
float ywidth;
float yfactor;
vec4 pos;
float sizefactor;
mat4 glyph_rotation;

float xo, yo;

glyph current;
void main(void)
{
    glyph_rotation[0] = vec4(cos(geom_glyph_rot[0]),-sin(geom_glyph_rot[0]),0,0);
    glyph_rotation[1] = vec4(sin(geom_glyph_rot[0]),cos(geom_glyph_rot[0]),0,0);
    glyph_rotation[2] = vec4(0,0,1,0);
    glyph_rotation[3] = vec4(0,0,0,1);

    current = glyphs[geom_fntobj[0]];
    sizefactor = geom_glyph_size[0]/fontsize_real;

    xo = sizefactor*current.offset.x;
    yo = sizefactor*current.offset.y;
    xwidth = sizefactor*current.size.x;
    ywidth = sizefactor*current.size.y;

    // lower left - to upper left
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xo, ywidth+yo,0,0));
    tex_coord = vec2(tex_scale.x*current.pos.x,tex_scale.x*(current.pos.y+current.size.y));
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    // upper left - to upper right
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xwidth+xo, ywidth+yo,0,0));
    tex_coord = vec2(tex_scale.x*(current.pos.x+current.size.x),tex_scale.x*(current.pos.y+current.size.y));
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    // upper right - to lower left
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xo, yo, 0,0));
    tex_coord = vec2(tex_scale.x*current.pos.x, tex_scale.x*current.pos.y);
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    // lower left - to lower right
    gl_Position = mat_camera*(gl_in[0].gl_Position + glyph_rotation*vec4(xwidth+xo, yo, 0,0));
    tex_coord = vec2(tex_scale.x*(current.pos.x+current.size.x), tex_scale.x*current.pos.y);
    color=geom_glyph_color[0];
    page_id=current.page;
    EmitVertex();

    EndPrimitive();
}
"""

FRAGMENT_SHADER = """
#version /*{$VERSION$}*/

in      vec2 tex_coord;
flat in float page_id;
in      vec4 color;
out     vec4 out_color;

uniform sampler2DArray tex;

float distance;
float width;
float edge;
float alpha;

void main()
{
    width = 0.38;
    edge = 0.25;
    distance = 1.0-texture(tex, vec3(tex_coord, page_id)).r/255;
    alpha = 1.0-smoothstep(width, width+edge, distance);
    out_color = vec4(color.x,color.y,color.z,color.a*alpha);
}

"""
