#-*- coding: utf-8 -*-
"""
simple plot2d example

:author: Nicolas 'keksnicoh' Heimann 
"""
from lib.plot.domain import RealAxis, Interval
from lib.plot.graph import Line2d
from lib.plot.app import plot2d
from lib.plot.plotter2d import DARK_COLORS, DEBUG_COLORS
import numpy as np 

def plot_main(plotter):
    plotter._debug=False
    plotter.graphs['test1'] = Line2d(RealAxis(), "y=sin(x)")
    plotter.graphs['test2'] = Line2d(Interval([np.pi,10*np.pi]), "y=10*sin(x)*cos(x)/x;x=10*cos(x)/x")
    plotter.graphs['test3'] = Line2d(RealAxis(axis=1), "x=sin(y);")

plot2d(
    plot_main, 
    axis         = [3, 3], 
    origin       = [1, -1], 
    axis_units   = [np.pi/2,1],
    color_scheme = DARK_COLORS
)