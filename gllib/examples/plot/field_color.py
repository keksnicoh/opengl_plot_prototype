#-*- coding: utf-8 -*-
"""
simple field plot with custom color kernel
and custom data kernel.

:author: Nicolas 'keksnicoh' Heimann 
"""
from gllib.plot.app import plot2d
from gllib.plot.domain import FieldDomain
from gllib.plot.field import Field
from gllib.plot.color.schemes import ColorMap
import numpy as np 

color_scheme = ColorMap('IDL_Pastels', colorrange=[-0.6,2])

def plot_main(plotter): 
    plotter.graphs['my_awesome_random_field'] = Field(
        color_scheme=color_scheme,
        data_kernel='fragment_color=vec4(0.5+0.5*sin(10*sqrt(x.x*x.x+x.y+x.y)), 0, 0, 1)'
    )

plot2d(plot_main, axis=[1,1], origin=[0, 0], 
    title  = 'who is your colors?',
    xlabel = 'gravitiy divided by fuel price',
    ylabel = 'sin($pi$) times new york times',
    colorlegend = color_scheme
)