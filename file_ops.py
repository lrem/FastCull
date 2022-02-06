"""Operations on bunches of files.

Given a directory and a JPEG file basename, pefrom file operations on the JPEG
file itself, the RAW file and all other files with the same filename ignoring
the extension.
"""

import os
import stat

from typing import List

def prefix(basename: str) -> str:
    return '.'.join(basename.split('.')[:-1])

def related_files(dir: str, basename: str) -> List[str]:
    assert(os.path.isfile(os.path.join(dir, basename)))
    result = []
    wanted = prefix(basename)
    for fname in os.listdir(dir):
        if prefix(fname) == wanted:
            result.append(fname)
    return result


RO_MASK = 0o777 ^ (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)
W_MASK = (stat.S_IWRITE | stat.S_IWGRP | stat.S_IWOTH)

def protect(dir: str, basename: str):
    for fname in related_files(dir, basename):
        path = os.path.join(dir, fname)
        mode = os.stat(path).st_mode
        os.chmod(path, mode & RO_MASK)

def unprotect(dir: str, basename: str):
    for fname in related_files(dir, basename):
        path = os.path.join(dir, fname)
        mode = os.stat(path).st_mode
        os.chmod(path, mode | W_MASK)

def is_protected(dir:str, basename:str) -> bool:
    path = os.path.join(dir, basename)
    mode = os.stat(path).st_mode
    return not bool(mode & W_MASK)
    