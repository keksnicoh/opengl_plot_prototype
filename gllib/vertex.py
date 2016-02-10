import numpy as np 

from OpenGL.GL import * 
from operator import mul

def validate_nbytes_dtype(nbytes, itemsize):
    print(itemsize)
    if nbytes % itemsize > 0:
        raise Exception(
            'buffersize {}b must be dividable by itemsize {}b'.format(
                nbytes, 
                itemsize
            )
        )

def _create_new_vbo_allocator(data=None):
    def _alloc(nbytes, target, usage):
        vbo = glGenBuffers(1)
        glBindBuffer(target, vbo)
        glBufferData(target, nbytes, data, usage)
        glBindBuffer(target, 0)
        return vbo
    return _alloc
    

class BufferObject():
    @classmethod
    def empty(cls, shape, dtype):
        return cls(shape, dtype)

    @classmethod
    def empty_like(cls, data):
        return cls(data.shape, data.dtype)

    @classmethod
    def zeros(cls, shape, dtype):
        data = np.zeros(shape, dtype=dtype)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data))

    @classmethod
    def zeros_like(cls, data):
        data = np.zeros_like(data)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data))

    @classmethod
    def ones(cls, data):
        data = np.ones(shape, dtype=dtype)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data))

    @classmethod
    def ones_like(cls, data):
        data = ones_like.ones(data)
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data))

    @classmethod
    def to_device(cls, data):
        return cls(data.shape, data.dtype, allocator=_create_new_vbo_allocator(data))

    def arange(cls, *args, **kwargs):
        data = numpy.arange(*args, **kwargs)
        return cls.to_device(data)

    def __init__(self, shape=None, dtype=None, target=GL_ARRAY_BUFFER, usage=GL_STATIC_DRAW, allocator=None):

        self.shape = shape if type(shape) is tuple else (shape, )
        self.dtype = np.dtype(dtype)
        self.itemsize = np.dtype(dtype).itemsize
        self.nbytes = self.itemsize*reduce(mul, self.shape)

        self._target = target
        self._usage = usage
        self._cl_array = None
        self._allocator = allocator or _create_new_vbo_allocator()

        self.gl_vbo_id = self._allocator(self.nbytes, self._target, self._usage)

        self.sync_with_vbo(True)

    def __len__(self):
        """
        returns first shape dimension
        """
        return self.shape[0]

    def sync_with_vbo(self, check=False):
        """
        syncs buffer parameters with
        this object: 
          - BUFFER_SIZE
          - USAGE
        """
        glBindBuffer(self._target, self.gl_vbo_id)
        nbytes = glGetBufferParameteriv(self._target, GL_BUFFER_SIZE)
        if check and nbytes != self.nbytes:
            raise Exception('buffer {} has size {}b but BufferObject requires its size to be {}b'.format(
                self.gl_vbo_id,
                nbytes,
                self.nbytes
            ))

        validate_nbytes_dtype(nbytes, self.itemsize)
        self._nbytes = nbytes
        
        usage = glGetBufferParameteriv(self._target, GL_BUFFER_USAGE)
        if check and self._usage is not None and usage != self._usage:
            raise Exception(
                'usage of buffer {} does not equal defined BufferObject.usage {}'.format(
                    usage,
                    self._usage 
                )
            )
        self._usage = usage

        glBindBuffer(self._target, 0)

    def set(self, ndarray, offset=0, length=None):
        """
        sets new data. 
        """
        if ndarray.dtype != self.dtype:
            raise Exception('FOO')

        self.shape = ndarray.shape 
        self.nbytes = ndarray.nbytes

        glBindBuffer(self._target, self.gl_vbo_id)
        glBufferData(self._target, self.nbytes, ndarray, self._usage)
        glBindBuffer(self._target, 0)

    def get(self):
        """
        loads data from buffer
        """
        glBindBuffer(self._target, self.gl_vbo_id)
        data = glGetBufferSubData(self._target, 0, self.nbytes)
        glBindBuffer(self._target, 0)
        return data.view(self.dtype).reshape(self.shape)

    def get_cl_array(self, queue):
        """
        returns pyopencl array allocated
        to the vbo. note the interoperatibility must be enabled.
        """
        if self._cl_buffer is None:
            import pyopencl as cl 

            self._cl_array = cl.array.Array(
                queue, 
                self.shape, 
                self.dtype, allocator=lambda b: cl.GLBuffer(ctx, cl.mem_flags.READ_WRITE, int(self.gl_vbo_id))
            )

        return self._cl_array

class ArrayObject():
    pass

if __name__ == '__main__':
    from gllib.application import GlApplication, GlWindow
    application = GlApplication()
    window = GlWindow(100, 100)
    application.windows.append(window)
    application.init()
    test_buffer = BufferObject.to_device(np.array([([1,1],2),((2,3), 1)], dtype=np.dtype('2float32, uint8')))


    bla  = test_buffer.get()
    bla[0][0][0] = 5
    print(bla)