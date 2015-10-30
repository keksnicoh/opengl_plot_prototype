#-*- coding: utf-8 -*-
"""
simple plot2d example

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.plot.domain import RealAxis, Interval
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d
from gllib.plot.plotter2d import DARK_COLORS, DEBUG_COLORS
from gllib.application import GlApplication
import numpy as np 

def plot_main(plotter):
    plotter.graphs['test1'] = Line2d(RealAxis(), "y=sin(x)")
    plotter.graphs['test2'] = Line2d(Interval([np.pi,10*np.pi]), "y=10*sin(x)*cos(x)/x;x=10*cos(x)/x")
    plotter.graphs['test3'] = Line2d(RealAxis(length=100, axis=1), "x=sin(y);", width=5)
GlApplication.DEBUG = False    
plot2d(
    plot_main, 
    axis         = [100, 100], 
    origin       = [1, -1], 
    axis_units   = [np.pi,1],
    axis_unit_symbols=[u'\u03C0', ''] ,
    color_scheme = DARK_COLORS
)