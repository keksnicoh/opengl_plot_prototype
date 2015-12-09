#-*- coding: utf-8 -*-
"""
fieldplot example
:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.plot.app import plot2d
from gllib.plot.domain import FieldDomain
from gllib.plot.field import Field
import numpy as np 

#
# numpy array describes the texture size and format. 
# third component in shape is the length of a component
# 1 => GL_RED
# 2 => GL_RG
# 3 => GL_RGB
# 4 => GL_RGBA
#
# if third component not defined then 
# it will set it automatically to 1 so
# only GL_RED channel is used.
#
w = 1000
h = 1000
color_channels = 3
data = np.random.random_sample(w*h*color_channels).reshape(w, h, color_channels)

def plot_main(plotter): 
    domain = FieldDomain.from_numpy(data)
    plotter.graphs['my_awesome_random_field'] = Field(domain)

plot2d(plot_main, axis=data.shape, origin=[-.5, .5], 
    title  = 'random numpy array of float{} vectors'.format(color_channels),
    xlabel = 'pixel space y',
    ylabel = 'pixel space x',
)