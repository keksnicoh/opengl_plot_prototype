#-*- coding: utf-8 -*-
"""
Basic example to show multidomain support.
Reason for this is that other plot libs like matplotlib
uses seperate buffers as domains, e.g.
   plot(x_data, y_data, x_data, y2_data)
which can be quiet usefull if one have lot of y*_data
for the same x_data. 

Note that Line2d automatically decides to change the
data_layout to (d0.x, d1.x) since the user defined 
two one dimensional domains.

:author: Nicolas 'keksnicoh' Heimann
"""
from gllib.plot.domain import NumpyDomain
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d

import numpy as np 

def plot_main(plotter):
    xf = np.array([0.1*x for x in np.arange(100)], dtype=np.float32)
    yf = np.array([np.sin(x) for x in xf], dtype=np.float32)

    plotter.graphs['test1'] = Line2d([NumpyDomain(xf), NumpyDomain(yf)])

plot2d(plot_main, axis=[10, 2], origin=[0,-1])