import numpy as np
import pyopencl as cl
import pyopencl.tools, os

#os.environ['PYOPENCL_COMPILER_OUTPUT'] = '1'

platform = cl.get_platforms()[0]
devices = platform.get_devices()
gpu_device = devices[1]


ctx    = cl.Context(devices=[gpu_device])
queue = cl.CommandQueue(ctx)

mf = cl.mem_flags

def test_complex64():
    res_np = np.zeros(2, dtype=np.complex64)

    prg = cl.Program(ctx, """
    #include <pyopencl-complex.h>

    __kernel void test(__global cfloat_t *res_g) {
          int gid = get_global_id(0);
          res_g[gid] = cfloat_new(5.0f, gid);
    }
""").build()

    expected = np.array([5+0j, 5+1j], dtype=np.complex64)

    return (res_np, prg, expected)

def test_complex128():
    res_np = np.zeros(2, dtype=np.complex128)

    prg = cl.Program(ctx, """

    #define PYOPENCL_DEFINE_CDOUBLE

    #pragma OPENCL EXTENSION cl_khr_fp64 : enable
    #include <pyopencl-complex.h>

    __kernel void test(__global cdouble_t *res_g) {
          int gid = get_global_id(0);
          res_g[gid] = cdouble_new(5.0, gid);
    }
""").build()

    expected = np.array([5+0j, 5+1j], dtype=np.complex128)

    return (res_np, prg, expected)

def test_float64():
    res_np = np.zeros(2, dtype=np.float64)

    prg = cl.Program(ctx, """
    #pragma OPENCL EXTENSION cl_khr_fp64 : enable

    __kernel void test(__global double *res_g) {
          int gid = get_global_id(0);
          res_g[gid] = 5.123456789;
    }
""").build()

    expected = np.array([5.123456789]*2, dtype=np.float64)

    return (res_np, prg, expected)


def run_test(test_case):

    res_np, prg, expected = test_case()

    res_g = cl.Buffer(ctx, mf.WRITE_ONLY, res_np.nbytes)
    prg.test(queue, res_np.shape, None, res_g)
    cl.enqueue_copy(queue, res_np, res_g)

    assert np.array_equal(res_np, expected), (res_np, expected)


run_test(test_float64)






