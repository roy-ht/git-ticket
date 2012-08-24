#!/usr/bin/env python
# -*- coding:utf-8 -*-

import subprocess as sp

def gitconfig(name=''):
    rawstrs = sp.Popen(['git', 'config', '-l'], stdout=sp.PIPE).communicate()[0].split('\n')
    configstrs = [x.split('.', 1) for x in filter(None, rawstrs)]
    print configstrs
    if name:
        configstrs = filter(lambda x: x[0] == name, configstrs)
        return dict(x[1].split('=', 1) for x in configstrs)
    else:
        configdict = {}
        for k, v in configstrs:
            configdict.setdefault(k, {}).update((v.split('=', 1),))
        return configdict
