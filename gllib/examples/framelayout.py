from gllib.application import GlApplication, GlWindow
from gllib.plot.plotter2d import Plotter, DEBUG_COLORS, DARK_COLORS
from gllib.framelayout import FramelayoutController, LayoutRow, LayoutColumn
from gllib.plot.domain import RealAxis
from gllib.plot.graph import Line2d

application = GlApplication()
GlApplication.DEBUG=False
window = GlWindow(900, 900)
application.windows.append(window)

domain = RealAxis()
graph = Line2d(domain, "y=sin(10*x)")

layout = FramelayoutController([
    [Plotter(graphs={'sin': graph}, color_scheme=DARK_COLORS)],
    [Plotter(graphs={'sin': graph}, color_scheme=DARK_COLORS),Plotter(graphs={'sin': graph}, color_scheme=DARK_COLORS)],
    [Plotter(graphs={'sin': graph}, color_scheme=DARK_COLORS),Plotter(graphs={'sin': graph}, color_scheme=DARK_COLORS)],
])
window.set_controller(layout)


application.run()