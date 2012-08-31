# -*- coding:utf-8 -*-

import subprocess as sp

def strwidth(s):
    return sum(1 if ord(x) < 256 else 2 for x in s)

def cmd_stdout(arglist):
    return sp.Popen(arglist, stdout=sp.PIPE).communicate()[0].strip()

