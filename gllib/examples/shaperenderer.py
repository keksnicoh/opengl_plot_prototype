from gllib.renderer.shape import *
from gllib.application import *
from gllib.controller import Controller 
from gllib.renderer.window import Framebuffer
from gllib.texture import NumpyTexture 

import numpy as np 

class MyController(Controller):
    def init(self):
        Controller.init(self)
        self.shaperenderer = ShapeRenderer(self.camera)
        self.shaperenderer.gl_init()
        self.first = True 
        self.frame_buffer = Framebuffer(self.camera, self.camera.screensize, record_mode=Framebuffer.RECORD_BLIT)
        self.frame_buffer.init()
        shape = Rectangle()
        texture = NumpyTexture(np.random.random_sample(4*10000).reshape(100,100,4))
        texture.gl_init()
        self.shaperenderer.draw_instance(ShapeInstance(shape, **{
            'size': (200,200),
            'position': (100,200), 
            'color': [0,0,0,1],
            'border': {
                'size': 10,
                'color': [1,0,0,1],
            },
            'texture': self.frame_buffer
        }))
        self.shaperenderer.draw_instance(ShapeInstance(shape, (200,200),(300,100), border={
            'size': 20,
            'color': [1,1,0,0.5],


        }))
    def run(self):
        self.frame_buffer.use()
        self.shaperenderer.render()
        self.frame_buffer.unuse()
        self.frame_buffer.render()


app = GlApplication()
window = GlWindow(600, 600)
window.set_controller(MyController())
app.windows.append(window)
app.run()