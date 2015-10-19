from lib.application import GlWindow, GlApplication
from lib.controller import Controller
from lib.plot.plotter2d import Plotter

from lib.plot.domain import RealAxis, RealAxisDual
from lib.plot.graph import Line2d

app = GlApplication()
window1 = GlWindow(200, 200)
window2 = GlWindow(200, 200)


def plot_main(plotter):
	
    domain = RealAxisDual(length=100)
    plotter.graphs['test'] = Line2d(domain, "y=sin(x)")

plotter = Plotter()

window1.set_controller(plotter)
window2.set_controller(Plotter())

app.windows.extend([window1, window2])
app.init()

plot_main(plotter)

app.run()