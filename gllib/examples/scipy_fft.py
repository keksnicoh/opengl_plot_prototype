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
    yf   = fft(y)[0:0.5*N]
    xf   = np.linspace(0.0, 1.0/(2.0*T), N/2)
    data = np.column_stack((xf,2.0/N * np.abs(yf[0:N/2]))).astype(np.float32)

    plotter.graphs['test1'] = Line2d(NumpyDomain(data), width=1)

plot2d(plot_main, axis=[200, 1])