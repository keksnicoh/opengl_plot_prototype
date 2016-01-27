#-*- coding: utf-8 -*-
"""
algorithms to map data

:author: Nicolas 'keksnicoh' Heimann 
"""
import pystache
from copy import copy
import pyopencl as cl
from operator import mul

class Blockwise():
    """
    mapper for matrix structures.    
    """
    _SOURCE = """
{{IN_LAYOUT}}
#define IN_BLOCK_SIZE {{{IN_BLOCK_SIZE}}}
#define OUT_BLOCK_SIZE {{{OUT_BLOCK_SIZE}}}
{{{PROCEDURE_FUNCTIONS}}}

__kernel 
void {{{KERNEL_NAME}}}(
    {{{PROCEDURE_ARGUMENTS}}}) 
{
    int __id = get_global_id(0);
    int __in_offset = __id*IN_BLOCK_SIZE;
    int __out_offset = __id*OUT_BLOCK_SIZE;
    {{{PROCEDURE}}}
    {{{POSTPROCESS}}}
}
    """

    def __init__(self, 
        ctx, 
        map_expr=None,
        arguments=None, 
        in_blocksize=1, 
        out_blocksize=1,
        block_shape=None,
        libraries='',
        name='_map_kernel', 
    ):
        self.map_expr = map_expr
        self.name = name
        self.ctx = ctx
        self.in_blocksize = in_blocksize
        self.block_shape = block_shape
        self.out_blocksize = out_blocksize
        self.arguments = arguments
        self._kernel_layout = None
        self.libraries = ''
        self._arguments = []
        self._kernel_args = None
        self._build = False

    def build(self, caardinality=1, dimension=1):
        if hasattr(self.map_expr, 'build'):
            self.map_expr.build()

        if type(self.map_expr) is str:
            map_expr = self.map_expr
        elif hasattr(self.map_expr, 'map_expr'):
            map_expr = self.map_expr.map_expr
        elif (hasattr(self.map_expr, '__contains__')
            and 'map_expr' in self.map_expr 
            and hasattr(self.map_expr, '__getitem__')):
            map_expr = map_expr['map_expr']
        else:
            raise ValueError('map expr is invalid')

        arguments = self.arguments or []
        if hasattr(self.map_expr, 'arguments'):
            arguments += self.map_expr.arguments
        elif (hasattr(self.map_expr, '__contains__')
            and 'arguments' in self.map_expr 
            and hasattr(self.map_expr, '__getitem__')):
            arguments += map_expr['arguments']
        
        cl_args = [' '.join(a[1:]) for a in arguments]

        libraries = self.libraries or ''
        if hasattr(self.map_expr, 'libraries'):
            libraries += '\n'+self.map_expr.libraries
        elif (hasattr(self.map_expr, '__contains__')
            and 'libraries' in self.map_expr 
            and hasattr(self.map_expr, '__getitem__')):
            libraries += '\n'+map_expr['libraries']


        shape_def = []
        for a in enumerate(self.block_shape or [self.in_blocksize]):
            shape_def.append('#define DIM{} {}'.format(*a))

        src = pystache.render(Blockwise._SOURCE, {
            'PROCEDURE'          :  map_expr,
            'PROCEDURE_ARGUMENTS': ', \n    '.join(cl_args),
            'PROCEDURE_FUNCTIONS': libraries,
            'KERNEL_NAME'        : self.name,
            'IN_LAYOUT': '\n'.join(shape_def),

            'IN_BLOCK_SIZE': self.in_blocksize,
            'OUT_BLOCK_SIZE': self.out_blocksize,
        })
        print(src)
        self._kernel = cl.Program(self.ctx, src).build()
        self._kernel_args = [a[0] for a in arguments]
        self._build = True

    def __call__(self, queue, length, *args, **kwargs):
        if not self._build:
            self.build()
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

        getattr(self._kernel, self.name)(queue, (length,), None, *arguments)

    def __str__(self):
        return '{}({})'.format(self.name, ', '.join(self._kernel_args))

class MatrixElementWise():
    """
    mapper for matrix structures.    
    """
    _SOURCE = """
#define DIM {{{DIM}}}
#define CAARD {{{CAARD}}}
#define OUT_DIM {{{OUT_DIM}}}

{{{PROCEDURE_FUNCTIONS}}}

__kernel 
void {{{KERNEL_NAME}}}(
    {{{PROCEDURE_ARGUMENTS}}}) 
{
    int2 _FIELD  = (int2)(get_global_id(0), get_global_id(1));
    int _ITEMID = (get_global_size(0)*_FIELD.y + _FIELD.x);
    int _ITEMKEY = {{DIM_FACTOR}}{{CAARD_FACTOR}}(get_global_size(0)*_FIELD.y + _FIELD.x);
    int _ELEMENTID  = {{CAARD_FACTOR}}(get_global_size(0)*_FIELD.y + _FIELD.x);
    int _ELEMENTKEY = {{DIM_FACTOR}}_ITEMID;
    int _OUTELEMENTKEY = OUT_DIM*_ITEMID;
    {{{PROCEDURE}}}
    {{{POSTPROCESS}}}
}
    """

    def __init__(self, 
        ctx, 
        operation, 
        layout=(1,1), 
        name='_map_kernel', 
        map_expr=None,
        arguments=None, 
        postprocess='float*'
    ):
        self.map_expr = map_expr
        self.operation = operation
        self.postprocess = postprocess
        self.name = name
        self.ctx = ctx
        self.layout = layout
        self.arguments = arguments
        self._kernel_layout = None
        self._arguments = []
        self._kernel_args = None
        self._build = False

    def build(self, caardinality=1, dimension=1):
        if hasattr(self.operation, 'build'):
            self.operation.build()

        map_expr = None
        if hasattr(self.operation, 'map_expr'):
            map_expr = self.operation.map_expr
        elif self.map_expr is not None :
            map_expr = self.map_expr

        argument_list = self.operation.arguments

        layout = self.operation.mapping_declaration 
        domain, out_domain = [s.strip() for s in layout.split('->')]
        domain_split = [_read_factors(d.strip()) for d in domain.split(',')]
        kernel_layout = [_evaluate_factor(d.strip(), *self.layout[0:2]) for d in domain.split(',')]
        out_domain_split = [_read_factors(d.strip(), '') for d in out_domain.split(',')]
        out_domain_shape = [_evaluate_factor(d.strip(), *self.layout[0:2]) for d in out_domain.split(',')]


        pp_args = []
        pp_code = ''
        pp_lib = ''
        pp_layout = (int(float(self.layout[0])/kernel_layout[0]),1)

        if type(self.postprocess) is str and map_expr is not None:
            # XXX
            # wtf is this... does it make sense???
            pp_args = [('__out', '__global', self.postprocess, '__out')]
            pp_code = '__out[_ELEMENTID] = {{{MAP_EXPR}}};'

        elif self.postprocess is not None:
            pp = self.postprocess
            if hasattr(pp, 'build'):
                pp.build()

            if hasattr(pp, '__contains__') and hasattr(pp, '__getitem__'):
                if 'arguments' in pp:
                    pp_args = pp['arguments']
                if 'code' in pp:
                    pp_code = pp['code']
                if 'library' in pp:
                    pp_lib = pp['library']
                if 'layout' in pp:
                    pp_layout = pp['layout']

            if hasattr(pp, 'arguments'):
                pp_args = pp.arguments 
            if hasattr(pp, 'code'):
                pp_code = pp.code 
            if hasattr(pp, 'library'):
                pp_lib = pp.library 
            if hasattr(pp, 'layout'):
                pp_layout = pp.layout 

        _pp_map_expr = 'postprocess with mapexpression is not allowed when operation does not provide map expression'
        if map_expr is not None:
            _pp_map_expr = map_expr

        pp_code = pystache.render(pp_code, {
            'MAP_EXPR': _pp_map_expr
        })

        argument_list += pp_args

        cl_args = [' '.join(a[1:]) for a in argument_list]

        if self.arguments is not None:
            cl_args.insert(0, self.arguments)

        libraries = ''
        if hasattr(self.operation, 'libraries'):
            libraries = self.operation.libraries

        src = pystache.render(MatrixElementWise._SOURCE, {
            'PROCEDURE'          :  self.operation.code,
            'PROCEDURE_ARGUMENTS': ', \n    '.join(cl_args),
            'PROCEDURE_FUNCTIONS': libraries,
            'POSTPROCESS'        : pp_code,
            'CAARD'              : self.layout[0],
            'DIM'                : self.layout[1],
            'OUT_DIM'            : out_domain_split[1],
            'CAARD_FACTOR'       : domain_split[0],
            'DIM_FACTOR'         : domain_split[1],
            'KERNEL_NAME'        : self.name,
        })

        self._kernel_layout = pp_layout
        self._kernel_args = [a[0] for a in argument_list]
        self._kernel = cl.Program(self.ctx, src).build()
        self._build = True

    def __call__(self, queue, length, *args, **kwargs):
        if not self._build:
            self.build()
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

        layout = (length,)
        if self._kernel_layout is not None: 
            layout = self._kernel_layout
            if layout[0]*layout[1] < length:
                raise Exception('SCHEISSE')

        getattr(self._kernel, self.name)(queue, layout, None, *arguments)

    def __str__(self):
        return '{}({})'.format(self.name, ', '.join(self._kernel_args))

def _evaluate_factor(factor, caard, dim):
    is_number = ['0','1','2','3','4','5','6','7','8','9','.']
    expr = ''
    has_chars = False
    has_symbol = False

    factors = []
    for char in factor:
        if char in is_number:
            if has_symbol:
                raise ValueError('numbers are only allowed in front of symbols')
            expr += char 
        elif char == 'c':
            if len(expr):
                factors.append(float(expr))
                expr = ''
            factors.append(caard)
        elif char == 'd':
            if len(expr):
                factors.append(float(expr))
                expr = ''
            factors.append(dim)
    if len(expr):
        factors.append(float(expr))
    return reduce(mul, factors)

def _read_factors(descr, postfix='*'):
    is_number = ['0','1','2','3','4','5','6','7','8','9','.']
    expr = ''
    has_chars = False
    has_symbol = False
    for char in descr:
        if char in is_number:
            if has_symbol:
                raise ValueError('numbers are only allowed in front of symbols')
            expr += char 
            has_chars = True
        elif char == 'c':
            if not has_chars:
                expr = 'CAARD'
                has_chars = True
            else:
                expr += '*CAARD'
            has_symbol = True
        elif char == 'd':
            if not has_chars:
                expr = 'DIM'
                has_chars = True
            else:
                expr += '*DIM'
            has_symbol = True

    return expr+postfix


