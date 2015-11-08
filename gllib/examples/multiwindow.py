from gllib.application import GlWindow, GlApplication
from gllib.controller import Controller
from gllib.plot.plotter2d import Plotter

from gllib.plot.domain import RealAxis
from gllib.plot.graph import Line2d

app = GlApplication()
window1 = GlWindow(200, 200, x=0, y=0)
window2 = GlWindow(200, 200, x=0, y=210)


def plot_main(plotter):
	
    domain = RealAxis(length=100)
    plotter.graphs['test'] = Line2d(domain, "y=sin(x)")

plotter = Plotter()

window1.set_controller(plotter)
window2.set_controller(Plotter())

app.windows.extend([window1, window2])
app.init()

plot_main(plotter)

app.run()