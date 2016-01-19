#-*- coding: utf-8 -*-
"""
scipy fft example based on 
http://docs.scipy.org/doc/scipy/reference/tutorial/fftpack.html
:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.plot.domain import NumpyDomain, transformation
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d

import numpy as np 
from scipy.fftpack import fft

def plot_main(plotter):
    xf = [0.1*x for x in np.arange(100)]
    yf = [np.sin(x) for x in xf]
    data = np.column_stack((xf,yf)).astype(np.float32)

    np_domain = NumpyDomain(data)
    mapped_domain = transformation.map_domain(np_domain, lambda x: (x[0],x[1]*x[1]))
    plotter.graphs['test1'] = Line2d(mapped_domain, width=1)

plot2d(plot_main, axis=[10, 2], origin=[0,-1])