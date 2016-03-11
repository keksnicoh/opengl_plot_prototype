import pyopencl as cl 

from cllib.task import ClTask 

class OneDeviceHostController():
    def __init__(platform, device):
        self.cl_platform = platform 
        self.cl_device = device     
        self.cl_ctx = cl.Context(devices=[device])
        self.cl_queue = cl.CommandQueue(context)
        self.queue = []

    def run_queue(self):
        for item in self.queue:
            if type(item) is tuple:
                task, on_finish = item 
            elif isinstance(item, ClTask):
                task = item 
            else:
                raise ValueError('invalid item in queue')


