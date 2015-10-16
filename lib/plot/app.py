from lib.application import GlApplication, GlWindow
from lib.controller import Controller
from lib.plot import plotter2d

import numpy 

def plot2d(f, **kwargs):
    window = GlWindow(600, 600, '2 cool quads 4 yolo')
    app = GlApplication()
    app.windows.append(window)
    plotter = plotter2d.Plotter(**kwargs)
    window.set_controller(plotter)
    app.init()
    f(plotter)
    app.run()