#-*- coding: utf-8 -*-
"""
glsl plot with dynamic RealAxis domain.
also colormap is used in this example by
reading out the x component.

:author: Nicolas 'keksnicoh' Heimann
"""
from gllib.plot.domain import RealAxis
from gllib.plot.graph import Line2d
from gllib.plot.app import plot2d
from gllib.plot.color.schemes import ColorMap

# colormap needs to know its range and the source of data.
# 
# more possible source in this example:
#   in_d0    raw vbo data (will be in (0,1))
#   d0       transformed vbo data (will be in (screen_left, screen_right))
#   x        same as d0
#   y        defined by kernel above
#
# one could also define another domain and pass it to the 
# Line2d to get color information from it. As a source
# one would define d1 then. (or d1.x or d1.y, ... if d1 is a vector)
color_scheme = ColorMap('IDL_CB-Paired', colorrange=(-30,60), source='x')

def plot_main(plotter):
    plotter.graphs['test1'] = Line2d(
        # RealAxis in its default settings will spawn a domain
        # on the interval (0,1). The plotter will tell the domain
        # which area is shown which allows to generate a transformation
        # on the domain so the domain will fill (screen_left, screen_right).
        #
        # This allows to fly around the plot and automatically rerender
        # the glsl function
        domains=RealAxis(),

        # in simplest way the kernel is a string passed 
        # to the glsl vertex shader. one can define  
        # wrapper methods which e.g. converts sympy
        # equations to a string.
        kernel='y=-0.005*x*x+sin(x)*cos(2*x)+exp(0.05*x)-1;',

        color_scheme=color_scheme,

        # lets make the line thick yo
        width=2
    )

plot2d(plot_main, 
    axis=[100, 7], 
    origin=[25,-3], 
    title='glsl plot with color scheme and dynamic domain',
    # XXX
    # - since we use a custom source in color_scheme
    #   one gets trouble here. Define a more stable concept here
    #   and fix this ... 

    # this will render a color legend on the right side of the plot
    #colorlegend=color_scheme  
)