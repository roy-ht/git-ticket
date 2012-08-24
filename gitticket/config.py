#!/usr/bin/env python
# -*- coding:utf-8 -*-

import subprocess as sp

def git():
    d = {}
    rawstrs = sp.Popen(['git', 'config', '-l'], stdout=sp.PIPE).communicate()[0].split('\n')
    configstrs = [x.split('=', 1) for x in filter(None, rawstrs)]
    for kstr, v in configstrs:
        keys = kstr.split('.')
        nd = d
        for k in keys[:-1]:
            nd = nd.setdefault(k, {})
        nd[keys[-1]] = v
    return d
