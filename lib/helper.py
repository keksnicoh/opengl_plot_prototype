#-*- coding: utf-8 -*-
"""
some generic helper functions
:author: Nicolas 'keksnicoh' Heimann 
"""

import os
BASE = os.path.dirname(os.path.abspath(__file__))

def load_lib_file(relative_path):
    with open(BASE + '/' + relative_path, 'r') as content_file:
        content = content_file.read()

    return content