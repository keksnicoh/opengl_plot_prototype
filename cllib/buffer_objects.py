import pyopencl as cl 
import numpy as np
import pyopencl.tools
import pyopencl.array

class ClStructDict():
    """
    represents an opencl stucture as python 
    dict.

    usage:

    d = ClStructDict('my_funny_struct_name', [
        ('derp', np.float32),
        ('dorp', np.int32)
    ])

    d.init_cl(context)
    
    # put struct into some kernel
    code = d.render_cl_struct()
    kernel_program = code
    kernel_program += "some advanced cl code"
    program = build_dat_kernel(kernel_program)

    d['derp'] = 34
    d['dorp'] = 1
    buffer = d.get_cl_buffer(queue)

    """
    def __init__(self, struct_name, fields):
        self.struct_name    = struct_name
        self.fields         = fields
        self._dtype         = np.dtype(fields)
        self.ctx            = None
        self._values        = {}
        self.cl_array = None
        self._synced_values = {}

    def init_cl(self, ctx):
        self.ctx = ctx

    def __setitem__(self, name, value):
        self.assert_fieldname(name)
        if not hasattr(value, 'dtype') or value.dtype is not self._dtype.fields[name][0]:
            value = self._dtype.fields[name][0].type(value)
        self._values[name] = value

    def __getitem__(self, name):
        self.assert_fieldname(name)
        if not name in self._values:
            return None 
        return self._values[name]

    def assert_fieldname(self, name):
        """
        checks whether a fieldname exists
        """
        field_names = list([n for n, dtype in self.fields])
        if not name in field_names:
            raise NameError('unkown field name "{}->{}". available fieldnames are "{}"'.format(self.struct_name, name, ', '.join(field_names)))

    def render_cl_struct(self):
        """
        returns struct code to inject
        into opencl kernel
        """
        self._dtype, my_struct_c_decl = cl.tools.match_dtype_to_c_struct(self.ctx.devices[0], self.struct_name, self._dtype)
        return my_struct_c_decl

    def update(self, values):
        for key, value in values.items():
            self[key] = value
    def items(self): return self._values.items()
    def keys(self): return self._values.keys()
    
    def push_cl(self, queue, force=False):
        """
        pushes the state to opencl
        if neccessary.
        :param queue:
        :param force: forces sync even if there are no changes within python state
        """
        host = np.empty(1, self._dtype)
        has_changes = False
        for name in self._dtype.fields:
            if name not in self._values or self._values[name] is None:
                raise ValueError('field "{}->{}" must be neither undefined nor None'.format(self.struct_name, name))
            if not name in self._synced_values or self._values[name] != self._synced_values[name]:
                has_changes = True
            host[name].fill(self._values[name])
            print(name, self._values[name])
            self._synced_values[name] = self._values[name]

        if force or has_changes:
            try:
                self.cl_array = cl.array.to_device(queue, host)
            except Exception as e:
                self._synced_values = {}
                raise e

    def get_cl_buffer(self, queue):
        if self.cl_array is None:
            self.push_cl(queue)
        return self.cl_array.data