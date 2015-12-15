#-*- coding: utf-8 -*-

from gllib.plot.app import plot2d
from gllib.plot.domain import FieldDomain
from gllib.plot.color.schemes import ColorMap
from gllib.plot.field import Field
from gllib.application import GlApplication

import numpy as np 


w = 2
h = 500
color_channels = 1

data = np.array([x/float(w*h) for x in range(w*h)]).reshape(w, h, color_channels)

def plot_main(plotter): 
    domain = FieldDomain.from_numpy(data)
    plotter.graphs['field'] = Field(
        domain,
        color_scheme=ColorMap('transform_rainbow')
    )
#    plotter._axis_measures = [1,2,3,4]

GlApplication.DEBUG = False   
plot2d(plot_main, axis=data.shape, origin=[0, 0], 
    title  = 'colors',
    xlabel = 'pixel space y',
    ylabel = 'pixel space x',
)