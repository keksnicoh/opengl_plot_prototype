from gllib.application import GlApplication, GlWindow
from gllib.controller import Controller
from gllib.font import FontRenderer 

from OpenGL.GL import * 
import numpy as np 

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
print(''.join(_LATEX_CHARACTER_MAPPING.values()))

application = GlApplication()
GlApplication.DEBUG=False
window = GlWindow(800, 400)
application.windows.append(window)
from time import time 

class TestController(Controller):
    def __init__(self):
        Controller.__init__(self)
        self._rendered = False

    def init(self):
        print('INIT')
        self.ftrenderer = FontRenderer()
        self.ftrenderer.set_camera(self.camera)
        self.ftrenderer.init()
        self._texts = []
        h = 20#
        sizes = [5,10,15,25,35,80]

        self._sizes = sizes
        self._text = 'Hallo ijkl ∫dΩf(λ)'
        for i in sizes:
            jojo_text = self.ftrenderer.create_text(self._text, size=i, position=(50,50+h), rotation=0)
            h+=i
            self._texts.append(jojo_text)

        for i in sizes:
            jojo_text = self.ftrenderer.create_text(self._text, size=i, position=(200+h,300), rotation=np.pi/2)
            h+=i

    def run(self):
        self.ftrenderer.render()
        self._rendered = True
        for i, text in enumerate(self._texts):
            text.rotation += 0.05
        self.ftrenderer._has_changes = True

window.set_controller(TestController())


application.run()