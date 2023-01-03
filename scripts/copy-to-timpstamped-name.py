#!/usr/bin/env

'''
Given a file, make a copy to name + last-modifed-timestamp
'''

import os
import os.path
import sys
import datetime
import shutil

fname = sys.argv[1]
result = os.stat(fname)
mtime = result.st_mtime

# get this into a compact string
TIMESTAMP = '%Y%m%d_%H:%M:%S'
timestamp = datetime.datetime.fromtimestamp(mtime, tz=datetime.timezone.utc).strftime(TIMESTAMP)

new_fname = fname + '.' + timestamp

if not os.path.isfile(new_fname):
    shutil.copy2(fname, new_fname)
