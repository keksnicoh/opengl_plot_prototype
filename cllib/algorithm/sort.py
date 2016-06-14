import pystache
import pyopencl as cl
import numpy as np
import pyopencl.array
from cllib.common import kernel_helpers

class Related():
	"""
	sort multiple systems of simple array and applies order to additional buffers
	@todo:
		- define sorting order (descending ascending)
		- key-function for more specific key-arrays (with different types)
		- extract bubble sort algorithm to exchange with different sorting techniques
		- fix issue with while-loop condition if sort is done earlier (set dim to 10)
	"""
	SWAP_SRC = """
		for(int l=0; l < {{{BLOCKSIZE}}}; l++) {
			{{{DTYPE}}} b = {{{BUFFER_NAME}}}[glid*{{{DIMENSION}}}*{{{BLOCKSIZE}}} + i*{{{DIMENSION}}} + l];
			{{{BUFFER_NAME}}}[glid*{{{DIMENSION}}}*{{{BLOCKSIZE}}} + i*{{{DIMENSION}}} + l] = {{{BUFFER_NAME}}}[glid*{{{DIMENSION}}}*{{{BLOCKSIZE}}} + (i+1)*{{{DIMENSION}}} + l];
			{{{BUFFER_NAME}}}[glid*{{{DIMENSION}}}*{{{BLOCKSIZE}}} + (i+1)*{{{DIMENSION}}} + l] = b;
		}
	"""

	SORT_KERNEL = """
		{{{LIBS}}}
		{{{STRUCTS}}}
	__kernel void bubble_sort(__global float* values, {{{RELATED_BUFFERS}}})
		{
			int glid = get_global_id(0);

			__private bool did_change_something = true;

			int c = 0;
			while(did_change_something) {
				//did_change_something = false;
				for(int i=0; i < {{{DIMENSION}}}-1; i++) {
					if (values[glid*{{{DIMENSION}}}+ i] {{{ORDER}}} values[glid*{{{DIMENSION}}}+ i+1]) {
						did_change_something = true;
						float bigger = values[glid*{{{DIMENSION}}}+ i];

						values[glid*{{{DIMENSION}}}+ i]   = values[glid*{{{DIMENSION}}}+ i+1];
						values[glid*{{{DIMENSION}}}+ i+1] = bigger;

						{{{SHIFT_RELATED_BUFFERS}}}
					}
				}

				c++;
				if (c>{{{DIMENSION}}}) {
					did_change_something = false;
				}
			}
		}
	"""

	def __init__(self, ctx, key_shape, blocksizes=[]):
		self.ctx = ctx
		self._key_shape = key_shape

		is_tuple  = lambda x: type(x) is tuple
		only_type = lambda x: len(x) == 1
		get_bs    = lambda x: x[1] if is_tuple(x) and not only_type(x) else 1
		get_dtype = lambda x: x[0] if is_tuple(x) else x

		self._blocksizes = [(get_dtype(x), get_bs(x)) for x in blocksizes]

	def _build_related_buffer_block(self, buffer_id, bs):
		return pystache.render(self.SWAP_SRC, {
			'BUFFER_NAME': 'r_{}'.format(buffer_id),
			'BLOCKSIZE': str(bs[1]),
			'DTYPE': bs[0],
			'DIMENSION': self._key_shape[1]
		}).encode('ascii')

	def build(self, descending=False):
		arguments = [('r_{}'.format(i), 'global', x[0], '*r_{}'.format(i)) for i, x in enumerate(self._blocksizes)]
		arguments, strcts, cl_arg_declr, includes, _ = kernel_helpers.process_arguments_declaration(self.ctx.devices[0], arguments)

		related_buffer_blocks = [self._build_related_buffer_block(i, (arguments[i][2], x[1]))  for i, x in enumerate(self._blocksizes)]

		src = pystache.render(self.SORT_KERNEL, {
			'LIBS': '\n'.join('#include <{}>'.format(i) for i in includes),
			'STRUCTS': '\n'.join(strcts),
		    'RELATED_BUFFERS': ', '.join(cl_arg_declr),
		    'SHIFT_RELATED_BUFFERS': '\n'.join(related_buffer_blocks),
		    'ORDER': '<' if descending else '>',
		    'DIMENSION': self._key_shape[1]
		}).encode('ascii')

		self._program = cl.Program(self.ctx, src).build()

	def __call__(self, queue, values_buffer, *args):
		self._program.bubble_sort(queue, (self._key_shape[0],), None, values_buffer, *args)


if __name__ == '__main__':
	dim     = 10
	systems = 3
	descending = False

	random_search_array = np.array(np.random.rand(dim*systems), dtype=np.float32).reshape(systems, dim)

	random_related_arrays = [
		np.array(range(systems*dim*dim), dtype=np.float32).reshape(systems, dim, dim)
	]

	platform = cl.get_platforms()[0]
	devices = platform.get_devices()
	gpu_device = devices[1]
	ctx    = cl.Context(devices=[gpu_device])
	queue = cl.CommandQueue(ctx)

	sort = Related(ctx, random_search_array.shape, [(np.float32, x.shape[1]) for x in random_related_arrays])

	if descending:
		sort.build(descending=True)

		cl_search_array = cl.array.to_device(queue, random_search_array)
		cl_related_arrays = [cl.array.to_device(queue, x) for x in random_related_arrays]
		sort(queue, cl_search_array.data, *[x.data for x in cl_related_arrays])

		cl_sorted = cl_search_array.get()
		for system in range(systems):
			assert np.array_equal(cl_sorted[system], np.sort(random_search_array[system])[::-1])

		index_of_sort = np.argsort(random_search_array)[:,::-1]

		sorted_related_arrays = []
		for related_array in random_related_arrays:
			sorted_related_array = np.zeros(systems*dim*dim).reshape(systems, dim, dim)
			for system in range(systems):
				sorted_related_array[system] = related_array[system][index_of_sort[system]]

			sorted_related_arrays.append(sorted_related_array)

			for cl_data, np_data in zip(cl_related_arrays, sorted_related_arrays):
				#print(cl_data.get())
				#print(np_data)
				assert np.array_equal(cl_data.get(), np_data)

		exit(0)


	sort.build()


	cl_search_array = cl.array.to_device(queue, random_search_array)
	cl_related_arrays = [cl.array.to_device(queue, x) for x in random_related_arrays]
	sort(queue, cl_search_array.data, *[x.data for x in cl_related_arrays])


	# check key buffer
	cl_sorted = cl_search_array.get()
	for system in range(systems):
		assert np.array_equal(cl_sorted[system], np.sort(random_search_array[system]))

	# check related buffers
	index_of_sort = np.argsort(random_search_array)

	sorted_related_arrays = []
	for related_array in random_related_arrays:
		sorted_related_array = np.zeros(systems*dim*dim).reshape(systems, dim, dim)
		for system in range(systems):
			sorted_related_array[system] = related_array[system][index_of_sort[system]]

		sorted_related_arrays.append(sorted_related_array)




	for cl_data, np_data in zip(cl_related_arrays, sorted_related_arrays):
		#print(cl_data.get())
		#print(np_data)
		assert np.array_equal(cl_data.get(), np_data)










