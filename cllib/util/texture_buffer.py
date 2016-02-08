import pystache
import numpy as np
import pyopencl as cl
from copy import copy 
class BufferToTexture():
    def __init__(self, ctx, size, arguments, map_expr="1", shape=None, blocksize=1):
        self.ctx = ctx
        self.size = size
        self.map_expr = map_expr
        self.shape = shape or size
        self.blocksize = blocksize 
        self.arguments = arguments 
        self.kernel_name = 'foo'

    def build(self):
        SOURCE = """
        #define HEIGHT {{HEIGHT}}
        __kernel void {{NAME}}({{ARGS}}, __write_only image2d_t _outtex) {
            int _x = get_global_id(0);
            int _y = get_global_id(1);

            int __in_key = _x + _y*HEIGHT;

            int2 __FIELD = (int2)(_x, _y);
            write_imagef(_outtex, __FIELD, {{MAP_EXPR}});
        }
        """
        strcts = [] 
        for i, cl_arg in enumerate(self.arguments):
            if type(cl_arg[2]) is np.dtype:
                strct_name = 'strct_{}'.format(cl_arg[0])
                _, c_decl = cl.tools.match_dtype_to_c_struct(
                    self.ctx.devices[0], 
                    strct_name, 
                    cl_arg[2],
                )
                strcts.append(c_decl)
                self.arguments[i] = (cl_arg[0], cl_arg[1], strct_name, cl_arg[3])
        cl_args = [' '.join(a[1:]) for a in self.arguments]

        src = pystache.render(SOURCE, {
            'ARGS': ', '.join(cl_args),
            'NAME': self.kernel_name,
            'HEIGHT': self.size[1],
            'MAP_EXPR': self.map_expr,
        })
        self._kernel_args = [a[0] for a in self.arguments] + ['out_texture']
        self._kernel = cl.Program(self.ctx, src.encode('ascii')).build()

    def __call__(self, queue, length, *args, **kwargs):
        self.run(queue, length, *args, **kwargs)


    def run_acquired(self, queue, length, *args, **kwargs):
        """
        run the kernel with acquired interop objects.
        all objects in argument of type cl.GL* will be acquire and released.

            cl.enqueue_acquire_gl_objects(...)
            kernel()
            cl.enqueue_release_gl_objects(...)
        """
        arguments = self._prepare_args(*args, **kwargs)
        enq = [a for a in arguments if type(a) in [cl.GLTexture, cl.GLBuffer]]

        cl.enqueue_acquire_gl_objects(queue, enq)

        getattr(self._kernel, self.kernel_name)(queue, self.size, None, *arguments)

        cl.enqueue_release_gl_objects(queue, enq) 

    def run(self, queue, length, *args, **kwargs):
        arguments = self._prepare_args(*args, **kwargs)
        getattr(self._kernel, self.kernel_name)(queue, self.size, None, *arguments)

    def _prepare_args(self, *args, **kwargs):
        """
        invoke kernel
        """
        if self._kernel is None:
            self.build()

        # collect arguments
        arguments = []
        available_args = copy(self._kernel_args)

        for arg in args:
            arguments.append(arg)
            del available_args[0]

        for name in available_args:
            if name not in kwargs:
                raise ValueError('argument "{}" missing for {}'.format(name, self))
            arguments.append(kwargs[name])
            del kwargs[name]
            
        if len(kwargs):
            for key in kwargs:
                if key in self._kernel_args:
                    raise ArgumentError((
                        'cannot use {} as keyword argument'
                        + ' since it is allready used as '
                        + 'positional argument').format(key)
                    )
            raise ArgumentError('unkown arguments: {}'.format(', '.join(kwargs.keys())))
        
        return arguments