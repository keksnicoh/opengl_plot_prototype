#-*- coding: utf-8 -*-
"""
task utilities

:author: Nicolas 'keksnicoh' Heimann 
"""
import pyopencl as cl
import pyopencl.array

import numpy as np 

from collections import OrderedDict
from copy import deepcopy

def cl_array():
    """
    creates a cl.array.Array buffer. No initial create
    possible since nobody knows at this point how big
    the buffer should be.
    """
    def validate(task): 
        pass

    def transform(ctx, queue, data):
        if not isinstance(data, cl.array.Array):
            if isinstance(data, np.ndarray):
                return cl.array.to_device(queue, data)
            elif isinstance(data, np.generic):
                return cl.array.to_device(queue, np.array([data], dtype=data))
            else:
                raise ValueError('must be cl.array.Array or np.generic')
        return data

    def create(ctx, queue, task):
        pass

    return (validate, transform, create)

def like(reference, shape=None, dtype=None, complex=None, real=None):
    """
    declares a buffer to be similar to another buffer.
    This is possible if other buffer is allready created 
    and is a cl.array.Array or numpy.ndarray instance. 
    """

    def validate(task):
        if not reference in task:
            raise ValueError('unkown reference {}'.format(reference))

    def transform(ctx, queue, data):
        raise RuntimeError('VLLALA')

    def create(ctx, queue, task):
        ref_buffer = task[reference]
        if isinstance(ref_buffer, cl.array.Array):
            new_shape = [ref_buffer.shape[s] for s in shape]
            empty_buffer = cl.array.empty(queue, new_shape, dtype=dtype or ref_buffer.dtype)
            return empty_buffer
        else:
            raise NotImplemented('this is not supported (yet?).')

    return (validate, transform, create)

def py_value(value):
    def validate(task): pass 
    def transform(task): pass
    def create(task): return deepcopy(value)
    return (validate, transform, create)

class Task():
    """
    A task represents one computation on either opencl
    device or on cpu usung numpy arrays.

    Changing buffer is possible but there are some important
    notes one should know:
     - if the kernel depends on shape of some buffers
       it may not possible to replace a buffer by another
       buffer with a different shape after prepare()
       method was invoked.

    Buffers can be declared by using static members.
    Those declarations consists of three methods which will 
    validate, transform or create the buffer.
    """
    def __init__(self, ctx, queue, data={}, parameters=None):
        self.cl_ctx = ctx 
        self.cl_queue = queue
        self.parameters = parameters

        # initialize buffer declarations and 
        # validate each buffer.
        self._declr = self._init_declr()
        for name, methods in self._declr.items():  
            validate, _, _ = methods
            try:
                validate(self)
            except Exception as e:
                raise RuntimeError('buffer declaration for "{}" invalid: {}'.format(name, str(e)))

        # initialize buffers
        self._data = {}
        for name in [n for n in self._declr if n in data]:
            self[name] = data[name]

    @classmethod 
    def _init_declr(cls):
        """
        prepare buffer declaration and returns 
        key, methods OrderedDict
        """
        is_attr = lambda a: (
            not callable(getattr(cls, a)) 
            and not a.startswith("_")
        )
        attributes = OrderedDict()
        is_declaration = lambda x: type(x) is tuple and len(x) == 3
        readable_declr = lambda x: x if is_declaration(x) else py_value(x)
        attributes.update((a, readable_declr(getattr(cls, a))) for a in dir(cls) if is_attr(a))

        return attributes

    def prepare(self):
        return self 

    def keys(self):
        return self._declr.keys() 

    def __contains__(self, key):
        """
        checks whether a buffer id is 
        in the declaration of the task
        """
        return key in self._declr

    def __setitem__(self, key, data):
        """
        sets buffer. if there declaration transformation
        does return anything else then None we use that value.

        e.g.:
           consider a task which uses a gpu buffer (cl.array.Array)
           and the value given to this function is a numpy ndarray.
           The transformation will send the data to GPU device
           and return corresponding cl.array.Array instance with 
           same shape and same dtype as incoming numpy ndarray.

        """
        assert key in self, key
        transformed = self._declr[key][1](self.cl_ctx, self.cl_queue, data)
        self._data[key] = transformed if transformed is not None else data

    def __getitem__(self, key):
        """
        returns buffer. if there is no buffer defined this 
        method will try to create default buffer by using 
        declraration create method. 

        e.g.:
           consider a task with a buffer A. if buffer B is defined to 
           be like A we can create an empty instance of same size/dtype.

        """
        if not key in self:
            raise KeyError('unkown data {}'.format(key))

        if not key in self._data:
            empty_buffer = self._declr[key][2](self.cl_ctx, self.cl_queue, self)
            if empty_buffer is None:
                raise RuntimeError('could not create default buffer "{}"'.format(key))
            self._data[key] = empty_buffer

        return self._data[key]


