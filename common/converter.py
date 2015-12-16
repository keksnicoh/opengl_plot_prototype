import numpy as np
from common.file_handler import *

def mathematica_data_to_numpy(file_path, dim):
    data_set = import_data_file(file_path)
    return np.array(data_set, dtype=np.float32).reshape(len(data_set)/dim, dim)