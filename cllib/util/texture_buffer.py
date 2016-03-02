#-*- coding: utf-8 -*-
"""
texture buffer utilities

:author: Nicolas 'keksnicoh' Heimann 
"""
from cllib.common import kernel_helpers

import pystache
import numpy as np
import pyopencl as cl

class BufferToTexture():
    """
    converts opencl buffer to an opengl texture 
    by a given mapping expression

    :arg ctx:
    :arg size: texture size
    :arg arguments: list of arguments
    :arg map_expr: mapping expression for each pixel
    """
    def __init__(self, ctx, size, arguments, map_expr="1", shape=None):
        self.ctx = ctx
        self.size = size
        self.map_expr = map_expr
        self.shape = shape or size
        self.arguments = arguments 
        self.kernel_name = 'foo'
        self._kernel = None 
        self._kernel_args = None 
        
    def build(self):
        SOURCE = """
        #define HEIGHT {{HEIGHT}}
        #define WIDTH {{WIDTH}}
        {{{LIBS}}}
        {{{STRUCTS}}}        
        __kernel void {{NAME}}({{ARGS}}, __write_only image2d_t _outtex) {
            int _x = get_global_id(0);
            int _y = get_global_id(1);

            int __in_key = _x + _y*HEIGHT;

            int2 __FIELD = (int2)(_x, _y);
            write_imagef(_outtex, __FIELD, {{MAP_EXPR}});
        }
        """
        arguments, strcts, cl_arg_declr, includes = kernel_helpers.process_arguments_declaration(self.ctx.devices[0], self.arguments)
        src = pystache.render(SOURCE, {
            'ARGS'    : ', '.join(cl_arg_declr),
            'NAME'    : self.kernel_name,
            'WIDTH'  : self.size[0],
            'HEIGHT'  : self.size[1],
            'LIBS': '\n'.join('#include <{}>'.format(i) for i in includes),
            'STRUCTS' : '\n'.join(strcts),
            'MAP_EXPR': self.map_expr,
        })

        self._kernel_args = [a[0] for a in arguments] + ['out_texture']
        self._kernel = cl.Program(self.ctx, src.encode('ascii')).build()

    def __call__(self, queue, length, *args, **kwargs):
        """
        perform BufferToTexture.run
        """
        self.run(queue, length, *args, **kwargs)

    def run_acquired(self, queue, length, *args, **kwargs):
        """
        run the kernel with acquired interop objects.
        all objects in argument of type cl.GL* will be acquire and released.

            cl.enqueue_acquire_gl_objects(...)
            kernel()
            cl.enqueue_release_gl_objects(...)
        """
        if self._kernel is None:
            self.build()

        arguments = kernel_helpers.create_knl_args_ordered(self._kernel_args, args, kwargs)
        enq = [a for a in arguments if type(a) in [cl.GLTexture, cl.GLBuffer]]

        cl.enqueue_acquire_gl_objects(queue, enq)
        getattr(self._kernel, self.kernel_name)(queue, self.size, None, *arguments)
        cl.enqueue_release_gl_objects(queue, enq) 

    def run(self, queue, length, *args, **kwargs):
        """
        run the kernel without acquiring interop objects.
        """
        if self._kernel is None:
            self.build()
            
        arguments = kernel_helpers.create_knl_args_ordered(self._kernel_args, args, kwargs)
        getattr(self._kernel, self.kernel_name)(queue, self.size, None, *arguments)
