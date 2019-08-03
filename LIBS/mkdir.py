#!/usr/bin/env python

"""
Functions for automatic check and creation of folders
"""

import os

def check_create_dir(path):
    """Create forlder if it doesn't exist"""
    if os.path.exists(path):
        print "The folder '%s' already exists"%path 
    else: 
        os.makedirs(path) 
        print "The folder '%s' has been created"%path
