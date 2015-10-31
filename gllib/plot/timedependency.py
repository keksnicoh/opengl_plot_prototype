#-*- coding: utf-8 -*-
"""
time dependency utilities
:author: Nicolas 'keksnicoh' Heimann 
"""
from time import time 

class PlotTicker():
    """
    simple object which can be attached to
    plotter on_pre_cycle event forcing
    the plotter to replot when time 
    changes.
    """
    def __init__(self):
        self.start_time = time();
    def __call__(self, plotter):
        time_now = time() - self.start_time
        for graph in plotter.graphs.values():
            if hasattr(graph, 'set_time'):
                graph.set_time(time_now)
        plotter.render_graphs = True