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
from gllib.plot.timedependency import PlotTicker
from gllib.plot.color.schemes import ColorMap

import numpy as np 
from time import time

def plot_main(plotter):
    plotter.graphs['test1'] = Line2d(RealAxis(), "y=sin(x)")
    plotter.graphs['test2'] = Line2d(Interval([np.pi,10*np.pi]), "y=60*sin(x)*cos(x)/x;x=60*cos(x)/x")
    plotter.graphs['test3'] = Line2d(RealAxis(length=100, axis=1), "x=sin(y);", width=10)

   # plotter.graphs['dots'] = Line2d(
   #     RealAxis(length=100),
   #     'y=30*sin(0.1*x+10*time)*cos(5*x+5*time)',
   #     draw_lines=True,
   #     draw_dots=True,
   #     dotcolor=[1,0,0,0.5]
   # )

    plotter.on_pre_cycle.append(PlotTicker())

GlApplication.DEBUG = False    
plot2d(

    plot_main, 
    axis              = [50, 50], 
    origin            = [25, -25], 
    axis_units        = [np.pi,1],
    plotmode          = 'oszi3',
    axis_unit_symbols = ['$pi$', ''] ,
    title             = 'Hello plotting',
    xlabel            = 'to cool space of $xi$',
    ylabel            = 'fancy measurement f($xi$) [$omega$^2 kg/m^2]',
    dark=False
)