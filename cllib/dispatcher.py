
from multiprocessing import Pool, TimeoutError, Queue

EXIT_SUCCESS     = 0
EXIT_BADINIT     = 1
EXIT_BADRUN      = 2
EXIT_NO_CL_QUEUE = 4


_cq = Queue()
print(dir(_cq))
def _runner(task):
    import pyopencl as cl 
    """
    run a specific task
    """
    #if _cq.qsize() == 0:
    #    return (3, 'no context/queue available.')
    print('OINK')
    deviceinfo = _cq.get()
    try:
        platform_id, device_type, device_id = deviceinfo
        platform = cl.get_platforms()[platform_id]
        print(platform)
        devices = platform.get_devices(device_type=device_type)
        print(devices)
        ctx = cl.Context(devices=devices)
        print(ctx)
        queue = cl.CommandQueue(ctx, device=devices[device_id])
    except Exception as e:
        print(e)
    _cq.put(deviceinfo)

def run_threaded(deviceinfos, task_generator):
    for platform_id, device_type, device_id in deviceinfos:
        _cq.put((platform_id, device_type, device_id))

    pool = Pool(processes=len(deviceinfos)) 
    task_iter = pool.imap_unordered(_runner, task_generator)
    for task_i, task_result in enumerate(task_iter):
        print('bla')
        pass
        #print(task_i, task_result)


