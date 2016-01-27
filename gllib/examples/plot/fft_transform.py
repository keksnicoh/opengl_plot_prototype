#-*- coding: utf-8 -*-
"""
like scipy_fft example this example performs a 
fft but uses transformation domains instead
of explicit scipy commands.

:author: Nicolas 'keksnicoh' Heimann
"""
from gllib.plot.domain import NumpyDomain
from gllib.plot.domain.transformation import fft1d
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d

import numpy as np 

def plot_main(plotter):
    xf = np.array([0.01*x for x in np.arange(10000)], dtype=np.float32)
    yf = np.array([
        np.sin(3*2*np.pi*x)
        + .5*np.sin(8*2*np.pi*x)
        + 2*np.sin(5*2*np.pi*x) 
        for x in xf], dtype=np.float32)

    data = np.column_stack((xf,yf))
    plotter.graphs['test1'] = Line2d(fft1d(NumpyDomain(data)))

plot2d(plot_main, axis=[10, 2], origin=[0,0])