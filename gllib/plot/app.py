from gllib.application import GlApplication, GlWindow
from gllib.controller import Controller
from gllib.plot import plotter2d
from gllib.framelayout import FramelayoutController
from gllib.plot.plotter2d import DARK_COLORS, DEFAULT_COLORS, BLA_COLORS
import numpy

def plot2d(f, width=600, height=600, dark=False, **kwargs):
    window = GlWindow(width, height, 'plot')
    app = GlApplication()
    app.windows.append(window)
    if not 'color_scheme' in kwargs:
        kwargs['color_scheme']=DEFAULT_COLORS if not dark else BLA_COLORS
    plotter = plotter2d.Plotter( **kwargs)
    window.set_controller(plotter)
    app.init()
    f(plotter)
    app.run()


def plot2dRows(f, plotters, width=600, height=600, dark=False):
    window = GlWindow(width, height, '2 cool quads 4 yolo')
    app = GlApplication()
    app.windows.append(window)
    if dark:
        for plotterargs in plotters:
            plotterargs['color_scheme']=BLA_COLORS
    plotters = [plotter2d.Plotter(**args) for args in plotters]


    window.set_controller(FramelayoutController([[c] for c in plotters]))
    app.init()
    f(plotters)

    app.run()

def plot2dColumns(f, plotters, width=600, height=600, dark=False):
    window = GlWindow(width, height, '2 cool quads 4 yolo')
    app = GlApplication()
    app.windows.append(window)
    if dark:
        for plotterargs in plotters:
            plotterargs['color_scheme']=BLA_COLORS
    plotters = [plotter2d.Plotter(**args) for args in plotters]

    def bla():
        print('CYCLE')
    controller = FramelayoutController([[c for c in plotters]])
    if hasattr(f, 'pre_cycle'):
        controller.on_pre_cycle.append(f.pre_cycle)
    window.set_controller(controller)

    app.init()
    f(plotters)

    app.run()


def plot2dColumns_extended(f, n, fake=None, width=600, height=600, **kwargs):
    window = GlWindow(width, height, 'Column plot')
    app = GlApplication()
    app.windows.append(window)

    def merge(a,b):
        c = a.copy()
        c.update(b)
        return c

    plotters = None
    if isinstance(n, list):
        plotters = [plotter2d.Plotter(**merge(kwargs, args)) for args in n]
    else:
        plotters = [plotter2d.Plotter(**kwargs) for i in range(0,n)]

    def bla():
        print('CYCLE')

    views = [[c for c in plotters]]
    if fake and isinstance(fake, list):
        plotters.extend(fake)
        views.append(fake)
    elif fake:
        plotters.append(fake)
        views.append([fake])

    controller = FramelayoutController(views)
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