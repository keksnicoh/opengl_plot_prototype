from cllib.algorithm.map import Blockwise

import pyopencl as cl 
import pyopencl.array 

import numpy as np 

from operator import mul 

def duplicate(ctx, data):
    """
    # XXX is this the same as transpose???
    cannot use pyopencl.array.transpose at the momoment, why???
    """
    KERNEL = """
        for (int j = 0; j < IN_BLOCK_SIZE; ++j) {
            b[OUT_BLOCK_SIZE*__id+j] = a[j];
        }  
    """
    mapper = Blockwise(ctx, map_expr=KERNEL, arguments=[
            ('a', 'global const', data.dtype, '*a'),
            ('b', 'global', data.dtype, '*b')    
        ],
        in_blocksize=reduce(mul, data.shape),
        out_blocksize=reduce(mul, data.shape)
    )
    mapper.build()

    def _kernel(queue, length, b=None):
        if b is None:
            shape = [length*data.shape[0]] + list(data.shape[1:])
            b = cl.array.empty(queue, tuple(shape), data.dtype)

        mapper(queue, length, data.data, b.data)
        return b 

    return _kernel