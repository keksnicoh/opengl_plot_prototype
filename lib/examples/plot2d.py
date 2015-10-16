#-*- coding: utf-8 -*-
"""
example of connecting the SimplePrimitivesRenderer
with controller and window framework

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.plot.domain import RealAxis
from lib.plot.graph import Line2d
from lib.plot.app import plot2d
from lib.plot.plotter2d import DARK_COLORS, DEBUG_COLORS

def plot_main(plotter):
    plotter._debug=False

    domain = RealAxis(length=100)
    ydomain = RealAxis(axis=1, length=100 )
    plotter.graphs['test'] = Line2d(domain, "y=sin(x)")
    plotter.graphs['test2'] = Line2d(domain, "y=2*sin(2*x)/(2*max(0,x)+0.1);x=2*cos(2*x)/(2*max(0,x)+0.1)+2")
    plotter.graphs['test3'] = Line2d(domain, "y=0")
    plotter.graphs['test5'] = Line2d(ydomain, "x=sin(y);")
    plotter.graphs['test4'] = Line2d(ydomain, "x=1;")
    plotter.graphs['test6'] = Line2d(domain, "y=-x;x=3.14159;")

    #for g in plotter.graphs.values():
    #    g.init()
    #    g.program.use()
    #    #g.program.uniform('width', 0.05)
    #    g.program.unuse()
plot2d(plot_main, 
    axis=[4, 4], 
    origin=[0, -1], 
    axis_units=[1,1],
    color_scheme=DARK_COLORS)