from gllib.util import Event
from gllib.buffer import * 
from gllib.shader import *
from gllib.helper import load_lib_file
from gllib.matrix import ModelView
from gllib.renderer.window import Framebuffer
from gllib.texture import Texture

import numpy as np 
from OpenGL.GL import * 

class ShapeRenderer(object):

    def __init__(self, camera):
        self._instances = {} 
        self._shape_vaos = {}
        self.on_instances_changed = Event()
        self.on_instances_changed.append(ShapeRenderer.update_shape_vaos)
        self.camera = camera
        self.shapes = {}

    def gl_init(self):
        program = Program()
        program.shaders.append(Shader(GL_VERTEX_SHADER, load_lib_file('glsl/shaperenderer/vert.glsl')))
        program.shaders.append(Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/shaperenderer/frag.glsl')))
        program.link()
        program.uniform('mat_camera', self.camera.get_matrix())
        self.program = program

        border_program = Program()
        border_program.shaders.append(Shader(GL_VERTEX_SHADER, load_lib_file('glsl/shaperenderer/vert.glsl')))
        border_program.shaders.append(Shader(GL_FRAGMENT_SHADER, load_lib_file('glsl/shaperenderer/border.frag.glsl')))
        border_program.link()
        border_program.uniform('mat_camera', self.camera.get_matrix())
        self.border_program = border_program

        self._borderframe = Framebuffer(self.camera, self.camera.screensize, clear_color=[0,0,0,0])
        self._borderframe.init()

    def update_shape_vaos(self, instance, show):
        """
        creates a vao if the instance has a shape
        where we did not create an vao yet
        """
        shape = self._shape(instance)

        shape_object_id = id(shape)
        if not shape_object_id in self._shape_vaos:
            self._shape_vaos[shape_object_id] = VertexArray({
                'vertex_position': VertexBuffer.from_numpy(shape.verticies),
                'texture_coords': VertexBuffer.from_numpy(shape.texture_coords),
            }, self.program.attributes)

    def _shape(self, instance):
        shape = instance.shape
        if type(shape) is str:
            if not instance.shape in self.shapes:
                raise NameError('invalid shape id "{}". Available ids are {}'.format(
                    instance.shape,
                    ', '.join(self.shapes.keys())
                ))
            shape = self.shapes[shape]
        return shape 

    def draw_instance(self, instance):
        shape = self._shape(instance)
        shape_object_id = id(shape)
        if not shape_object_id in self._instances:
            self._instances[shape_object_id] = []

        if not instance in self._instances[shape_object_id]:
            self._instances[shape_object_id].append(instance)
            self.on_instances_changed(self, instance, True)

    def erase_instance(self, instance):
        shape = self._shape(instance)
        shape_object_id = id(shape)
        if shape_object_id in self._instances:
            self._instances[shape_object_id].remove(instance)
            self.on_instances_changed(self, instance, False)

    def update_camera(self):
        # XXX
        # - clean me. maybe watch some events or so...
        self.program.uniform('mat_camera', self.camera.get_matrix())
        self.border_program.uniform('mat_camera', self.camera.get_matrix())
        self._borderframe.capture_size = self.camera.screensize

    def render(self):
        # Render border texture
        # XXX
        # - only do if neccessary.
        self._borderframe.use()
        self._render_borders()
        self._borderframe.unuse()

        self.program.use()
        glActiveTexture(GL_TEXTURE0);
        for shape_object_id, instances in self._instances.items():
            self._shape_vaos[shape_object_id].bind()
            for instance in instances:
                # XXX
                # - define the exact behavior of mix_texture.
                if instance.texture is not None: 
                    self.program.uniform('mix_texture', 1)
                    self.program.uniform('tex', 0)
                    glBindTexture(GL_TEXTURE_2D, instance.texture.gl_texture_id)
                else:
                    self.program.uniform('mix_texture', 0)
                    glBindTexture(GL_TEXTURE_2D, 0)

                # XXX
                # - cache the modelview matrix
                modelview = ModelView()
                modelview.set_scaling(*instance.size)
                modelview.set_position(*instance.position)
                self.program.uniform('color', instance.color)
                self.program.uniform('mat_modelview', modelview.mat4)
                glDrawArrays(GL_TRIANGLES, 0, 6)
            self._shape_vaos[shape_object_id].unbind()
        self.program.unuse()

        # render borders
        # XXX
        # - only if neccessary
        self._borderframe.render()

    def _render_borders(self):
        """
        renders a texture containing the borders
        of all shapes.
        """

        # XXX
        # - read the old glBlendFunc value and restore it if neccessary.
        glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        self.border_program.use()
        for shape_object_id, instances in self._instances.items():
            self._shape_vaos[shape_object_id].bind()
            for instance in instances:
                border_size = instance.border['size']
                if instance.border > 0:
                    glEnable(GL_BLEND)
                    # XXX
                    # - cache the modelview matrix
                    modelview = ModelView()
                    modelview.set_scaling(instance.size[0]+2*border_size, instance.size[1]+2*border_size)
                    modelview.set_position(instance.position[0]-border_size, instance.position[1]-border_size)
                    self.border_program.uniform('mat_modelview', modelview.mat4)
                    self.border_program.uniform('color', instance.border['color'])
                    glDrawArrays(GL_TRIANGLES, 0, 6)

                    glDisable(GL_BLEND)
                    # XXX
                    # - cache the modelview matrix
                    modelview = ModelView()
                    modelview.set_scaling(*instance.size)
                    modelview.set_position(*instance.position)
                    self.border_program.uniform('color', [0,0,0,0])
                    self.border_program.uniform('mat_modelview', modelview.mat4)
                    glDrawArrays(GL_TRIANGLES, 0, 6)

            self._shape_vaos[shape_object_id].unbind()
        self.border_program.unuse()   

        glEnable(GL_BLEND)

class ShapeInstance():
    def __init__(self, shape, size=(1,1), position=(0,0), color=[1,1,1,1], border=0, texture=None, mix_texture=1):
        self.shape    = shape 
        self.size     = size 
        self.texture  = texture
        self.color    = color
        self.position = position 
        self.mix_texture = mix_texture
        self.border   = border if type(border) is dict else {
            'size': border,
            'color': [0,0,0,1],
        }

    @property
    def border_size(self):
        return self.border['size']
    
class Rectangle():
    @property
    def verticies(self):
        return np.array([
            0, 1, 
            0, 0, 
            1, 0, 

            1, 0, 
            1, 1, 
            0, 1, 
        ], dtype=np.float32).reshape(6,2)

    @property
    def texture_coords(self):
        return np.array([0, 0, 0, 1, 1, 1, 1, 1, 1, 0, 0, 0], dtype=np.float32).reshape(6,2)
    
  

