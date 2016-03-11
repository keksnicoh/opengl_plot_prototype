#-*- coding: utf-8 -*-
"""
dataset utilities

:author: Nicolas 'keksnicoh' Heimann 
"""
import numpy as np 

import argparse
from collections import OrderedDict

import os 

class Dataset():
    """
    a dataset is a group of tasks which share
    buffers and can depend on each other.
    """

    def __init__(self, parameters={}):

        self._tasks            = self._prepare_tasks()
        self.buffers           = {}
        self._parameters_dtype = np.dtype([x[0:2] for x in self.PARAMETERS])
        self.parameters        = None
        self._task_instances = {}
        self._read_parameters(parameters)

    @classmethod
    def create_argparse(cls):
        arg_parser = argparse.ArgumentParser(description='Process some integers.')
        for x in cls.PARAMETERS:
            name, dtype = x[0:2]
            default = None if not len(x) == 3 else (x[2] if not hasattr(x[2], '__call__') else None)
            arg_parser.add_argument('--'+name, type=dtype, default=default)
        return arg_parser

    def _read_parameters(self, parameters):
        """
        read parameters by using numpy dtype defined 
        in static member PARAMETERS = [(key, dtype, default)].
        note that if default is not None its value will be used
        as default value for parameter k. If contains a callable 
        it will be executed after all parameters was created. 
        """
        self.parameters = np.empty((1,), dtype=self._parameters_dtype)[0]
        callback_defaults = []
        for x in self.PARAMETERS:
            k, _ = x[0:2]
            if k in parameters and parameters[k] is not None:
                self.parameters[k] = parameters[k]
            elif len(x) == 3:
                if hasattr(x[2], '__call__'):
                    callback_defaults.append((k,x[2]))
                else:
                    self.parameters[k] = x[2]
            else:
                raise ValueError('missing parameter "{}"'.format(k))

        # now execute callbacks
        for k, d in callback_defaults:
            self.parameters[k] = d(self)

    def cl_init(self, ctx, queue):
        self.cl_ctx   = ctx 
        self.cl_queue = queue 

    @classmethod
    def _prepare_tasks(cls):
        tasks = getattr(cls, 'TASKS_QUEUE')
        
        tasks_dict = OrderedDict()
        for task in tasks:
            name, declr = task
            tasks_dict[name] = declr

        return tasks_dict

    def run_queue(self):
        for task_id, declr in self._tasks.items():
            self.run_task(task_id)

    def run_task(self, task_id):
        """
        runs a taks by its task_id.
        please note the comments in here to get 
        an idea how to declare a task
        within the structure read by this method.
        """
        declr = self._tasks[task_id]
        if not hasattr(declr, '__class__'): # if declr is a type then remap to minimal declr
            declr = {'cls': declr}

        if not task_id in self._task_instances:
            # if declr is string and there is a attribute in this class
            # with that name, we will use that attribute
            if type(declr) is str:
                if not hasattr(self, declr):
                    raise ValueError('task "{}" invalid. string declaration must correspond to a class method')
                lcl = getattr(self, declr)
                result = lcl() if hasattr(lcl, '__call__') else lcl
                self.buffers.update(result or {})
                return result or {}

            # if declr is callabl we will call it.
            elif hasattr(declr, '__call__'):
                result = declr(self)
                self.buffers.update(result or {})
                return result or {} 


            # create task instance.
            # arguments can be assigned as tuples (key, value)
            # or as plain values. if value is a string and there 
            # is a attribute within the dataset with name value,
            # then this value will be taken. if value is callable
            # then it will be called.
            cls_kwargs = {'ctx': self.cl_ctx, 'queue': self.cl_queue, 'parameters': self.parameters}
            cls_args = []
            if 'args' in declr:
                for arg in declr['args']:
                    val = arg[1] if type(arg) is tuple else arg
                    if type(val) is str and hasattr(self, val):
                        lcl = getattr(self, val)
                        val = lcl() if hasattr(lcl, '__call__') else lcl
                    elif hasattr(val, '__call__'):
                        val = val(self)

                    if type(arg) is tuple:
                        cls_kwargs[v[0]] = val
                    else:
                        cls_args.append(val)

            # run the task. decorate TypeError with some specific 
            # information about the task.
            try:
                task = declr['cls'](*cls_args, **cls_kwargs)
            except TypeError as e:
                raise TypeError('task "{}" class {}: {}'.format(task_id, declr['cls'].__name__, e))

            # fill buffers
            get_buffer = lambda k: lambda d: d.buffers[k]
            data_source = {k: get_buffer(k) for k in task.keys() if k in self.buffers}
            print(data_source)
            if 'data' in declr:
                data_source.update(declr['data'])

            for buf_name, v in data_source.items():
                print(buf_name, v if not hasattr(v, '__call__') else v(self))
                task[buf_name] = v if not hasattr(v, '__call__') else v(self)

            if hasattr(task, 'prepare'):
                task.prepare()

            self._task_instances[task_id] = task

        # go
        result = self._task_instances[task_id].run()

        buffers = dict(self._task_instances[task_id])
        if 'keep_buffer' in declr:
            for buff_id, alias in declr['keep_buffer'].items():
                if alias == False:
                    del buffers[buff_id]
                elif type(alias) is str:
                    buffers[alias] = buffers[buff_id]
                    del buffers[buff_id]
                else:
                    raise ValueError('keep_buffer bad entry')

        self.buffers.update(buffers)

        return result

    def persist(self, folder):
        if not os.path.exists(folder):
            os.mkdir(folder)

        np.save(os.path.join(folder, '__parameters'), self.parameters)
        for buff_id, buff in self.buffers.items():
            np.save(os.path.join(folder, buff_id), buff.get())
