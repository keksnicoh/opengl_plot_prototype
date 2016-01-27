from pyopencl.tools import get_gl_sharing_context_properties
import pyopencl as cl 
from termcolor import colored

from pkgutil import extend_path
__path__ = extend_path(__path__, __name__)

_DRIVER = {
    'opencl': None,
    'cuda': None,
}

class OpenCLQueue():
    def __init__(self, queue):
        self.queue = queue

    @classmethod
    def create_gpu_driver(cls):
        platform = cl.get_platforms()[0]
        devices = platform.get_devices()
        gpu_device = devices[1]
        properties = get_gl_sharing_context_properties()

        context = cl.Context( devices=[gpu_device])
        return cls(cl.CommandQueue(context))

def enable_opencl(queue=True):
    if queue == True:
        queue = OpenCLQueue.create_gpu_driver()
    else:
        queue = OpenCLQueue(queue)
    _DRIVER['opencl'] = queue

def get_opencl_queue():
    return _DRIVER['opencl']

def plot_warn(category, message):
    print('[{}] {}: {}'.format(colored('WARN', 'red'), colored(category, attrs=['bold']), message))

def plot_info(category, message):
    print('[{}] {}: {}'.format(colored('INFO', 'cyan'), colored(category, attrs=['bold']), message))
