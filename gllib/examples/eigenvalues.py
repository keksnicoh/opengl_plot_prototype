#-*- coding: utf-8 -*-

from gllib.plot.domain import RealAxisData
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2dMulti, plot2d
from gllib.plot.plotter2d import DARK_COLORS

import numpy as np
from numpy import linalg as LA

interval=[0,10]
length=1000
eigenvalue_count = 5


data = []
for c in xrange(eigenvalue_count):
    data.append(np.zeros(length*2, dtype=np.float32))


for x in range(0, length):
    a = interval[0]+interval[1]*float(x)/length
    b = 0

    w, v = LA.eig([
    [4+2*b, -a, 0, 0, 0],
    [-a, 1+b, -a, 0, 0],
    [0, -a, 0, -a, 0],
    [0, 0, -a, 1+b, -a],
    [0, 0, 0, -a, 4+2*b]])

    for c in xrange(eigenvalue_count):
        data[c][2*x] = a
        data[c][2*x+1] = w[c]


def plot_eigenvalues(plotter):
    for c in xrange(eigenvalue_count):
        domain = RealAxisData(data[c])
        plotter.graphs['eigen %s' % c] = Line2d(domain, "y=y")

def plot_variance(plotter):
    for c in xrange(eigenvalue_count):
        domain = RealAxisData(data[c])
        plotter.graphs['eigen %s' % c] = Line2d(domain, "y=y")


plot2d(plot_eigenvalues, 
    axis=[4, 8], 
    origin=[0, -1], 
    axis_units=[1,1],
    color_scheme=DARK_COLORS)

#plot2dMulti([plot_eigenvalues], 
#    axis=[4, 8], 
#    origin=[0, -1], 
#    axis_units=[1,1],
#    color_scheme=DARK_COLORS)


