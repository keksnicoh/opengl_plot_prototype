from gllib.application import GlApplication, GlWindow
from gllib.controller import Controller
from gllib.plot import plotter2d
from gllib.framelayout import FramelayoutController
from gllib.plot.plotter2d import DARK_COLORS, DEFAULT_COLORS, BLA_COLORS
import pyscreenshot as ImageGrab
import numpy

class ScreenshotKeyboardHandler():
    def __init__(self, window, file_name=None):
        validate_filename = lambda x: x if '.' in x else x+'.png'

        self.window    = window
        self.file_name = validate_filename(file_name) if file_name else '__screen_capture.png'

    def __call__(self, active, pressed=[]):
        if (74, 0) in pressed: # J
            pos, size = self.window.get_frame()
            x_offset = 10
            y_offset = 40
            im = ImageGrab.grab(bbox=(pos[0] + x_offset, pos[1] + y_offset, size[0] + pos[0] + x_offset, size[1] + pos[1] + y_offset - 4))
            im.save(self.file_name)

def plot2d(f, width=600, height=600, dark=False, screenshot_file_name=None, **kwargs):
    window = GlWindow(width, height, 'plot')
    app = GlApplication()
    app.windows.append(window)
    if not 'color_scheme' in kwargs:
        kwargs['color_scheme']=DEFAULT_COLORS if not dark else BLA_COLORS
    plotter = plotter2d.Plotter( **kwargs)
    plotter.on_keyboard.append(ScreenshotKeyboardHandler(window, screenshot_file_name))
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

def plot2dCustom(f, plotters, fake=None, width=600, height=600, window_title='', **kwargs):
    window = GlWindow(width, height, window_title)
    app = GlApplication()
    app.windows.append(window)

    controller = FramelayoutController(plotters)
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