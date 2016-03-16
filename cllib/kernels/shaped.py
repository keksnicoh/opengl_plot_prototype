#-*- coding: utf-8 -*-
"""
algorithms to map data

:author: Nicolas 'keksnicoh' Heimann 
"""
from cllib.common import kernel_helpers

import pystache
from copy import copy
import pyopencl as cl
import pyopencl.tools 

from operator import mul
import numpy as np 

thread_layouts = {
    

}
class ShapedKernel():
    """
    Kernel maps structured chunks to structured chunks. 

    XXX
    - test me 
    - fix redundancy, 
    - examples.  
    """
    _SOURCE = """
#pragma OPENCL EXTENSION cl_khr_fp64 : enable
{{{INCLUDES}}}
{{{IN_LAYOUT}}}
{{CONSTANTS}}

{{STRUCTS}}

{{{PROCEDURE_FUNCTIONS}}}

__kernel 
void {{{KERNEL_NAME}}}(
    {{{PROCEDURE_ARGUMENTS}}}) 
{
    {{{IDS}}}
    {{{PROCEDURE}}}
    {{{POSTPROCESS}}}
}
    """

    def __init__(self, 
        ctx, 
        kernel_code=None,
        arguments=None, 
        in_blocksize=1, 
        out_blocksize=None,
        shape=None,
        libraries='',
        threads=None,
        name='_map_kernel', 
    ):
        if type(kernel_code) is not str \
           and kernel_helpers.get_attribute_or_item(kernel_code, 'kernel_code') is None:
           raise ValueError('arg kernel_code must be either string or an object with kernel_code attribute or and dict with kernel_code key.')

        self.kernel_code       = kernel_code
        self.name           = name
        self.ctx            = ctx
        self.in_blocksize   = in_blocksize
        self.out_blocksize  = out_blocksize or in_blocksize
        self.shape    = shape
        self.arguments      = arguments

        self.libraries      = libraries
        self.includes       = None 
        self.threads        = threads
        self._kernel_layout = None
        self._arguments     = []
        self._kernel_args   = None
        self._kernel        = None
        self._kernel_local  = None 

    def build(self, caardinality=1, dimension=1):
        if hasattr(self.kernel_code, 'build'):
            self.kernel_code.build()

        if type(self.kernel_code) is str:
            kernel_code = self.kernel_code
        else:
            kernel_code = kernel_helpers.get_attribute_or_item(self.kernel_code, 'kernel_code')
            if self.kernel_code is None:
                raise ValueError('invalid kernel_code')

        libraries = self.libraries or ''
        kernel_code_libs = kernel_helpers.get_attribute_or_item(self.kernel_code, 'libraries')
        if kernel_code_libs is not None:
            libraries += '\n'+kernel_code_libs

        arguments = self.arguments or []
        kernel_code_args = kernel_helpers.get_attribute_or_item(self.kernel_code, 'arguments')
        if kernel_code_args is not None:
            arguments += kernel_code_args

        includes = self.includes or []
        kernel_code_args = kernel_helpers.get_attribute_or_item(self.kernel_code, 'includes')
        if kernel_code_args is not None:
            includes += kernel_code_args

        # find structures.
        # XXX
        # - helper function
        arguments, strcts, cl_arg_declr, arg_includes = kernel_helpers.process_arguments_declaration(self.ctx.devices[0], arguments)
        includes += arg_includes

        cl_includes = ['#include <{}>'.format(path) for path in set(includes)]

        shape = self.shape or [self.in_blocksize]
        shape_def = ['#define DIM{} {}'.format(*a) for a in enumerate(shape)] # deprecated backward compatibility
        shape_def += ['#define SHAPE{} {}'.format(*a) for a in enumerate(shape)]

        cl_constants = [
            ('IN_BLOCK_SIZE', self.in_blocksize),
            ('OUT_BLOCK_SIZE', self.out_blocksize)
        ]

        cl_item_var = '\n'.join([
            'int __id = get_{}_id(0);'.format('global' if self.threads is None else 'group'),
            'int __in_offset = __id*IN_BLOCK_SIZE;',
            'int __out_offset = __id*OUT_BLOCK_SIZE;',
        ])


        if self.threads is not None:
            # XXX
            # - check for bool (get shape)
            # - and so on ...
            if hasattr(self.threads, '__call__'):
                self._kernel_local, thread_constants, itemsrc = self.threads(self)
                nthreads = len(thread_constants)
                cl_item_var += itemsrc

            else:
                # default thread layout
                self._kernel_local = self.threads
                thread_constants = self._kernel_local
                nthreads = len(self._kernel_local)

                get_local_id = lambda i: 'get_local_id({})'.format(i)                
                itemid = 'int{n} __item_id = (int{n})({ids});'.format(
                    n='' if nthreads == 1 else nthreads, 
                    ids=','.join([get_local_id(i) for i in range(0, len(thread_constants))]))
                if nthreads == 1:
                    cl_item_var += itemid+"""
                        int __item = __item_id;
                        int __itemT = __item_id;
                    """
                elif nthreads == 2:
                    cl_item_var += itemid+"""
                        int __item = THREAD_X*__item_id.x+__item_id.y;
                        int __itemT = THREAD_X*__item_id.y+__item_id.x;
                    """
                elif nthreads == 3:
                    cl_item_var += itemid+"""
                        int __item = THREAD_X*__item_id.x+__item_id.y;;
                        int __itemT = THREAD_X*__item_id.y+__item_id.x;
                    """
  
            if nthreads == 1:
                cl_constants.append(('THREAD_X', thread_constants[0]))
            elif nthreads == 2:
                cl_constants.append(('THREAD_X', thread_constants[0]))
                cl_constants.append(('THREAD_Y', thread_constants[1]))
            elif nthreads == 3:
                cl_constants.append(('THREAD_X', thread_constants[0]))
                cl_constants.append(('THREAD_Y', thread_constants[1]))
                cl_constants.append(('THREAD_Z', thread_constants[2]))
            else:   
                # XXX
                # - does a n>3 case make sense? check opencl specs...
                raise NotImplemented('not implemented yet')
            
        src = pystache.render(ShapedKernel._SOURCE, {
            'INCLUDES'           : '\n'.join(cl_includes),
            'STRUCTS'            : '\n'.join(strcts),
            'PROCEDURE'          :  kernel_code,
            'IDS'                : cl_item_var,           
            'CONSTANTS'          : '\n'.join(['#define {} {}'.format(*x) for x in cl_constants])     ,      
            'PROCEDURE_ARGUMENTS': ', \n    '.join(cl_arg_declr),
            'PROCEDURE_FUNCTIONS': libraries,
            'KERNEL_NAME'        : self.name,
            'IN_LAYOUT'          : '\n'.join(shape_def),
        })

        self._kernel = cl.Program(self.ctx, src.encode('ascii')).build()
        self._kernel_args = [a[0] for a in arguments]
        return src

    def __call__(self, queue, length, *args, **kwargs):
        """
        invoke kernel
        """
        if self._kernel is None:
            self.build()

        if self._kernel_local is None:
            length = (length, )
        elif len(self._kernel_local) == 1:
            length = (length*self._kernel_local[0], )
        elif len(self._kernel_local) == 2:
            length = (length*self._kernel_local[0], self._kernel_local[1])
        elif len(self._kernel_local) == 3:
            length = (length*self._kernel_local[0], self._kernel_local[1], self._kernel_local[2])

        knl_args = kernel_helpers.create_knl_args_ordered(self._kernel_args, args, kwargs)
        return getattr(self._kernel, self.name)(queue, length, self._kernel_local, *knl_args)

    def __str__(self):
        """
        readable representation of kernel delcaration 
        """
        return '{}({})'.format(self.name, ', '.join(self._kernel_args))


