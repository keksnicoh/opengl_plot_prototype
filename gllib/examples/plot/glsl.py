#-*- coding: utf-8 -*-
"""
simple plot example where a user defined
glsl kernel maps x domain to y domain.

:author: Nicolas 'keksnicoh' Heimann
"""
from gllib.plot.domain import NumpyDomain
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d

import numpy as np 

def plot_main(plotter):
    xf = np.array([0.01*x for x in np.arange(1000)], dtype=np.float32)
    plotter.graphs['test1'] = Line2d(NumpyDomain(xf), 'y=sin(x)*cos(2*x)')

plot2d(plot_main, axis=[10, 2], origin=[0,-1])