# -*- coding:utf-8 -*-

from gitticket import ticket

def test_decorate():
    assert ticket._decorate('string', '^pre') == 'prestring'
    assert ticket._decorate('string', '$post') == 'stringpost'
    assert ticket._decorate('s', 'l5') == 's    '
    assert ticket._decorate('s', 'r5') == '    s'
    assert ticket._decorate('s', 'c5') == '  s  '
    assert ticket._decorate('string', 's') == ' string'
