from cllib.algorithm.map import Blockwise

import pyopencl as cl 

import numpy as np 

def rearange_to_block(ctx, strided_data):
    """
    # XXX is this the same as transpose???
    cannot use pyopencl.array.transpose at the momoment, why???
    """
    KERNEL = """
    b[OUT_BLOCK_SIZE*__item_id.y+__id] = a[__in_offset+__item_id.y];
    """
    mapper = Blockwise(ctx, map_expr=KERNEL, arguments=[
            ('a', 'global const', strided_data.dtype, '*a'),
            ('b', 'global', strided_data.dtype, '*b')    
        ],
        in_blocksize=strided_data.shape[1],
        out_blocksize=strided_data.shape[0],
        block_shape=strided_data.shape,
        threads=(1, strided_data.shape[1],)
    )
    mapper.build()

    def _kernel(queue, length, b):
        return mapper(queue, length, strided_data.data, b)

    return _kernel