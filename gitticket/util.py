# -*- coding:utf-8 -*-

def strwidth(s):
    return sum(1 if ord(x) < 256 else 2 for x in s)
