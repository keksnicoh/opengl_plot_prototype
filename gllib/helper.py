#-*- coding: utf-8 -*-
"""
some generic helper functions
:author: Nicolas 'keksnicoh' Heimann 
"""

import os
import struct
BASE = os.path.dirname(os.path.abspath(__file__))

def load_lib_file(relative_path):
    with open(BASE + '/' + relative_path, 'r') as content_file:
        content = content_file.read()

    return content

def resource_path(*path):
    return os.path.join(BASE, 'resources', *path)

def hex_to_rgb(hexstr):
    try:
        return [float(i)/255 for i in struct.unpack('BBB', hexstr.decode('hex'))]
    except:
        return [float(i)/255 for i in struct.unpack('BBB', bytes.fromhex(hexstr))]

def hex_to_rgba(hexstr):
    try:
        return [float(i)/255 for i in struct.unpack('BBBB', hexstr.decode('hex'))]
    except:
        return [float(i)/255 for i in struct.unpack('BBBB', bytes.fromhex(hexstr))]