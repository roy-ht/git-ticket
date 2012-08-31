# -*- coding:utf-8 -*-

import subprocess as sp
import re

def strwidth(s):
    return sum(1 if ord(x) < 256 else 2 for x in s)

def cmd_stdout(arglist):
    return sp.Popen(arglist, stdout=sp.PIPE).communicate()[0].strip()

def rmcomment(s):
    return s.split('#', 1)[0]

def regex_extract(pattern, tgt, default=None):
    r = re.search(pattern, tgt, re.M | re.S)
    if not r:
        return default
    grps = r.groups()
    if len(grps) == 1:
        return grps[0]
    return grps
