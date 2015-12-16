#-*- coding: utf-8 -*-
"""
time dependency utilities
:author: Nicolas 'keksnicoh' Heimann 
"""
from time import time 

from gllib.util import Event 

class PlotTicker():
    TPS_COUNT = 20
    """
    simple object which can be attached to
    plotter on_pre_cycle event forcing
    the plotter to replot when time 
    changes.
    """
    def __init__(self, *tick_events):
        self.on_tick = Event()

        for tick_event in tick_events:
            self.on_tick.append(tick_event)

        self.pause = False
        self.start_time = time()
        self.tick_count = 0
        self.ticks_per_second = 0

        self._ticks_per_second_time = self.start_time
        self._ticks_per_second_ticks = 0

    def __call__(self, plotter):
        if self.pause:
            return 

        time_now = time() - self.start_time

        self.on_tick(time_now, self.tick_count, self.ticks_per_second)

        for graph in plotter.graphs.values():
            if hasattr(graph, 'set_time'):
                graph.set_time(time_now)
                
        plotter.render_graphs = True
        
        if self.tick_count % self.TPS_COUNT == 0:
            self.ticks_per_second = (self.tick_count-self._ticks_per_second_ticks)/(time() - self._ticks_per_second_time)
            self._ticks_per_second_time = time()
            self._ticks_per_second_ticks = self.tick_count

        self.tick_count += 1