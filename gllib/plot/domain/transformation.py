from gllib.buffer import VertexBuffer
from gllib.plot.domain import util
from OpenGL.GL import * 
import numpy as np 
from functools import partial
from gllib.plot import get_opencl_queue, plot_warn

# registred transfromations
total_mean = lambda d: _find_transformation('total_mean')(d)
fft1d = lambda d: _find_transformation('fft1d')(d)
psd = lambda d: _find_transformation('psd')(d)
moving_avarage = lambda d: _find_transformation('moving_avarage')(d)

def _find_transformation(transformation):
    """
    finds a transformation domain by checking
    if there are gpu devices available and if so 
    then check if there is an implementation on the gpu.
    otherwise use PythonDomain
    """
    had_gpu_device = False
    cl_queue = get_opencl_queue()
    if cl_queue is not None and hasattr(OpenCLDomain, transformation):
        return partial(getattr(OpenCLDomain, transformation), opencl_device)

    had_gpu_device = cl_queue is not None 
    if not had_gpu_device:
        plot_warn('PERFORMANCE', 'No GPU device condigured for transformations. Continue with PythonDomain fallback.')
    
    if hasattr(PythonDomain, transformation):
        if had_gpu_device:
            plot_warn('PERFORMANCE', 'no "{}" domain gpu transformation found -> fallback PythonDomain'.format(transformation))
        return partial(getattr(PythonDomain, transformation))

    raise NameError('unkown transformation "{}"'.format(transformation))

class PythonDomain(object):
    """
    domain which enables to define a python
    transformation for a given domain. This domain
    enables to quickly use existing transformations
    like FFT from the scipy library and so on.
    """
    def __init__(self, domain, transformation):
        self.domain = domain 
        self.transformation = transformation
        self.offset = 0
        self._vbo = None
        self._transformed = False 
        self._transformed_data = None 

        self.dimension = domain.dimension

    def __len__(self):
        if self._transformed_data is None:
            raise Exception('FOO')
        return self._transformed_data.shape[0]
    
    @property 
    def gl_vbo_id(self):
        if self._vbo is None:
            return None
        
        return self._vbo.gl_vbo_id

    def transform(self, offset=0, length=None):
        domain_data = self.domain.pull_data(offset, length)
        self._transformed = True
        self._transformed_data = self.transformation(domain_data)

        if self._vbo is None:
            self._vbo = VertexBuffer.from_numpy(self._transformed_data)

        self._vbo.buffer_data(self._transformed_data)

    @classmethod
    def total_mean(cls, domain):
        return cls(domain, util.total_mean()) 

    @classmethod
    def fft1d(cls, domain):
        return cls(domain, util.fft1d()) 

    @classmethod
    def psd(cls, domain):
        return cls(domain, util.psd()) 

    @classmethod
    def moving_avarage(cls, domain):
        return cls(domain, util.moving_avarage()) 



    @classmethod
    def map_domain(cls, domain, mapper):
        return cls(domain, util.map_domain(mapper))

class OpenCLDomain():
    def __init__(self, queue, transformation):
        pass