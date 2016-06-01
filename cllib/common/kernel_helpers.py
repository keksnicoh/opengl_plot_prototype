#-*- coding: utf-8 -*-
"""
helpers for kernel building objects.

:author: Nicolas 'keksnicoh' Heimann
"""

# XXX
# - process_arguments_declaration: find possible numpy dtypes corresponding
#   to floatn, intn, ... (e.g. dtype([np.float32, np.float32]))

import pyopencl as cl
import pyopencl.tools

import numpy as np

from copy import copy

CL_TYPES = [
    # TODO
    # - abstract opencl types:
    #    https://www.khronos.org/registry/cl/sdk/1.2/docs/man/xhtml/abstractDataTypes.html
    # - keep reserved types in mind
    #    https://www.khronos.org/registry/cl/sdk/1.2/docs/man/xhtml/reservedDataTypes.html
    'bool','char','uchar','short','ushort','int','uint', 'long', 'ulong', 'float', 'double', 'half',
    'size_t','ptrdiff_t','intptr_t','uintptr_t','void',
    'half2','half3','half4','half8','half16',
    'char2','char3','char4','char8','char16',
    'uchar2','uchar3','uchar4','uchar8','uchar16',
    'short2','short3','short4','short8','short16',
    'ushort2','ushort3','ushort4','ushort8','ushort16',
    'int2','int3','int4','int8','int16',
    'uint2','uint3','uint4','uint8','uint16',
    'long2','long3','long4','long8','long16',
    'ulong2','ulong3','ulong4','ulong8','ulong16',
    'float2','float3','float4','float8','float16',
    'double2','double3','double4','double8','double16',
    'image2d_t','image3d_t','image2d_array_t','image1d_t','image1d_buffer_t','image1d_array_t','sampler_t','event_t',
]


def get_attribute_or_item(value, attr):
    """
    check whether value has attribute attr
    or value[attr] is accessible and returns
    first match.
    """
    if hasattr(value, attr):
        return getattr(value, attr)
    elif (hasattr(value, '__contains__')
        and attr in value
        and hasattr(value, '__getitem__')):
        return value[attr]

def ensure_valid_cl_type(type):
    if type not in CL_TYPES:
        raise ValueError('invalid cl_type "{}"'.format(type))

def process_arguments_declaration(device, arguments):
    """
    process tuple argument declarations.
    find structures, check types and convert
    numpy dtypes to cl_types.
    """
    strcts = []
    arg_declr = [None]*len(arguments)
    require_complex_numbers = False
    require_cdouble = False

    for i, cl_arg in enumerate(arguments):
        cl_type = cl_arg[2]
        if type(cl_type) is np.dtype and cl_type.fields is None:
            cl_type = getattr(np, cl_type.name)

        if type(cl_type) is str:
            try:
                ensure_valid_cl_type(cl_type)
                arg_declr[i] = arguments[i]
            except ValueError:
                raise ValueError((
                    'argument #{} "{}" invalid cl_type "{}" '
                    'checkout https://www.khronos.org/registry/cl/sdk/1.2/docs/man/xhtml/dataTypes.html for available types.'
                ).format(i, cl_arg[0], cl_type))

        elif type(cl_type) is np.dtype:
            strct_name = 't_{}'.format(cl_arg[0])
            _, c_decl = cl.tools.match_dtype_to_c_struct(
                device,
                strct_name,
                cl_type,
            )
            strcts.append(c_decl)
            arg_declr[i] = (cl_arg[0], cl_arg[1], strct_name, cl_arg[3])

        elif cl_type == np.int64: arg_declr[i] = (cl_arg[0], cl_arg[1], 'long', cl_arg[3])
        elif cl_type == np.uint64: arg_declr[i] = (cl_arg[0], cl_arg[1], 'ulong', cl_arg[3])
        elif cl_type == np.int32: arg_declr[i] = (cl_arg[0], cl_arg[1], 'int', cl_arg[3])
        elif cl_type == np.uint32: arg_declr[i] = (cl_arg[0], cl_arg[1], 'uint', cl_arg[3])
        elif cl_type == np.int16: arg_declr[i] = (cl_arg[0], cl_arg[1], 'short', cl_arg[3])
        elif cl_type == np.uint16: arg_declr[i] = (cl_arg[0], cl_arg[1], 'ushort', cl_arg[3])
        elif cl_type == np.int8: arg_declr[i] = (cl_arg[0], cl_arg[1], 'char', cl_arg[3])
        elif cl_type == np.uint8: arg_declr[i] = (cl_arg[0], cl_arg[1], 'uchar', cl_arg[3])
        elif cl_type == np.float16: arg_declr[i] = (cl_arg[0], cl_arg[1], 'half', cl_arg[3])
        elif cl_type == np.float32: arg_declr[i] = (cl_arg[0], cl_arg[1], 'float', cl_arg[3])
        elif cl_type == np.float64: arg_declr[i] = (cl_arg[0], cl_arg[1], 'double', cl_arg[3])
        elif cl_type == np.complex64:
            arg_declr[i] = (cl_arg[0], cl_arg[1], 'cfloat_t', cl_arg[3])
            require_complex_numbers = True

        elif cl_type == np.complex128:
            arg_declr[i] = (cl_arg[0], cl_arg[1], 'cdouble_t', cl_arg[3])
            require_complex_numbers = True
            require_cdouble = True

        else:
            raise ValueError((
                'argument #{} "{}" type "{}" not understood. '
                'Must be string cl_type or numpy.dtype. '
                'Supported numpty types are: np.dtype, np.(u)int(8|16|32|64), '
                'np.float(16|32|64), np.complex(32|64|128)'
            ).format(i, cl_arg[0], cl_arg[2]))

    cl_args = [' '.join(a[1:]) for a in arg_declr]

    defines = []
    includes = []
    if require_complex_numbers:
        includes.append('pyopencl-complex.h')

    if require_cdouble:
        defines.append('PYOPENCL_DEFINE_CDOUBLE')

    return arg_declr, strcts, cl_args, includes, defines

def create_knl_args_ordered(arg_declr, args, kwargs):
    """
    creates a list of kernel arguments from args and kwargs
    by using arg_declr (maybe generated by process_arguments_declaration)
    """
    knl_args = []
    available_args = copy(arg_declr)

    for arg in args:
        knl_args.append(arg)
        del available_args[0]

    for name in available_args:
        if name not in kwargs:
            raise ValueError('argument "{}" missing'.format(name))
        knl_args.append(kwargs[name])
        del kwargs[name]

    if len(kwargs):
        for key in kwargs:
            if key in arg_declr:
                raise ArgumentError((
                    'cannot use {} as keyword argument'
                    + ' since it is allready used as '
                    + 'positional argument').format(key)
                )
        raise ArgumentError('unkown argument: {}'.format(', '.join(kwargs.keys())))
    return knl_args