#-*- coding: utf-8 -*-
"""
scipy fft example based on 
http://docs.scipy.org/doc/scipy/reference/tutorial/fftpack.html
:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.plot.domain import NumpyDomain
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d

import numpy as np 
from scipy.fftpack import fft

N = 1200
T = 1.0 / 800.0

def plot_main(plotter):
    x    = np.linspace(0.0, N*T, N)
    y    = np.sin(50.0 * 2.0*np.pi*x) + 0.2*np.sin(80.0 * 2.0*np.pi*x)
    yf   = 2.0/N * np.abs(fft(y)[0:0.5*N][0:N/2])
    xf   = np.linspace(0.0, 1.0/(2.0*T), N/2)
    data = np.column_stack((xf,yf))
    plotter.graphs['test1'] = Line2d([NumpyDomain(xf.astype(np.float32)), NumpyDomain(yf.astype(np.float32))], width=1)

plot2d(plot_main, axis=[200, 1])