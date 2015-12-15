from gllib.application import GlApplication, GlWindow
from gllib.controller import Controller
from gllib.plot import plotter2d
from gllib.framelayout import FramelayoutController
from gllib.plot.plotter2d import DARK_COLORS, DEFAULT_COLORS
import numpy 

def plot2d(f, width=600, height=600, dark=False, **kwargs):
    window = GlWindow(width, height, '2 cool quads 4 yolo')
    app = GlApplication()
    app.windows.append(window)
    kwargs['color_scheme']=DEFAULT_COLORS if not dark else DARK_COLORS
    plotter = plotter2d.Plotter( **kwargs)
    window.set_controller(plotter)
    app.init()
    f(plotter)
    app.run()


def plot2dRows(f, n, **kwargs):
    window = GlWindow(800, 500, '2 cool quads 4 yolo')
    app = GlApplication()
    app.windows.append(window)

    plotters = [plotter2d.Plotter(**kwargs) for i in range(0,n)]


    window.set_controller(FramelayoutController([[c] for c in plotters]))
    app.init()
    f(plotters)

    app.run()

def plot2dColumns(f, n, **kwargs):
    window = GlWindow(1000, 700, '2 cool quads 4 yolo')
    app = GlApplication()
    app.windows.append(window)

    plotters = [plotter2d.Plotter(**kwargs) for i in range(0,n)]

    def bla():
        print('CYCLE')
    controller = FramelayoutController([[c for c in plotters]])
    if hasattr(f, 'pre_cycle'):
        controller.on_pre_cycle.append(f.pre_cycle)
    window.set_controller(controller)

    app.init()
    f(plotters)

    app.run()




def plot2dMulti(fs, **kwargs):

    windows = []
    for x in xrange(len(fs)):
        windows.append(GlWindow(600, 600, 'Number %d' % x))

    app = GlApplication()

    plotters = []
    for window in windows:
        app.windows.append(window)
        plotter = plotter2d.Plotter(**kwargs)
        plotters.append(plotter)
        window.set_controller(plotter)

    app.init()

    for x in xrange(len(fs)):
        f = fs[x]
        plotter = plotters[x]
        f(plotter)

    app.run()