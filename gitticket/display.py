#!/usr/bin/env python
# -*- coding:utf-8 -*-

import operator as opr
import itertools as itrt
from gitticket.config import nested_access
import blessings

class Table(object):
    def __init__(self):
        self.colcfg = {}
        self.lines = []
        self.reducename = None
        self.margin = 2
    
    def addcolumn(self, name, **kwargs):
        kwargs['__ord__'] = len(self.colcfg)
        self.colcfg[name] = kwargs

    def addjson(self, j):
        u"""jsonを渡すことにより、それぞれのコラムのkeyに対応して
        抜き出して文字列リストにする
        """
        l = []
        for col in sorted(self.colcfg.values(), key=opr.itemgetter('__ord__')):
            l.append(unicode(nested_access(j, col['key'], col.get('default', None))))
        self.lines.append(l)

    def fit(self):
        for name, col in self.colcfg.items():
            col['width'] = max(self.stringwidth(x[col['__ord__']]) for x in self.lines)
            col['width'] = max(col['width'], self.stringwidth(name))
        if self.reducename:
            totwidth = sum(x['width'] for x in self.colcfg.values())
            deltawidth = totwidth - termwidth()
            if deltawidth > 0:
                self.colcfg[self.reducename]['width'] = max(self.colcfg[self.reducename]['width'] - deltawidth, self.stringwidth(self.reducename))
        
    def stringwidth(self, s):
        return sum(1 if ord(x) < 256 else 2 for x in s)

    def output(self):
        r = u''
        for name, col in sorted(self.colcfg.items(), key=lambda x: x[1]['__ord__']):
            gluelen = col['width'] - self.stringwidth(name)
            r += name + u' ' * (gluelen + self.margin)
        r += u'\n'
        for name, col in sorted(self.colcfg.items(), key=lambda x: x[1]['__ord__']):
            gluelen = col['width'] - self.stringwidth(name)
            r += u'-' * (len(name) + gluelen) + u' ' * self.margin
        r += u'\n'
        for line in self.lines:
            for col, t in itrt.izip(sorted(self.colcfg.values(), key=opr.itemgetter('__ord__')), line):
                gluelen = col['width'] - self.stringwidth(t)
                if gluelen >= 0:
                    r += t
                else:
                    for i in range(1, len(t) + 1):
                        gluelen = col['width'] - self.stringwidth(t[:-i]) - 2
                        if gluelen >= 0:
                            r += t[:-i] + u'..'
                            break
                r += u' ' * (gluelen + self.margin)
            r += u'\n'
        return r


def termwidth():
    term = blessings.Terminal()
    return term.width
        

def json(jsonlist, stgs):
    u"""stgに入っている情報を元にフォーマットして返す
    stgはリストで、その順番でコラムを作って返す
    """
    t = Table()
    for stg in stgs:
        t.addcolumn(stg.get('name', stg['key']), key=stg['key'])
    for j in jsonlist:
        t.addjson(j)
    t.reducename = 'title'
    t.fit()
    return t.output()
    
    
