#!/usr/bin/env python
# -*- coding:utf-8 -*-

import blessings
from gitticket import util

class Table(object):
    def __init__(self, tickets):
        self.colcfg = []
        self.tickets = tickets
        self.margin = 2
        self.reducename = None
    
    def addcolumn(self, kwargs):
        self.colcfg.append(kwargs)

    def fit(self):
        for col in self.colcfg:
            col['width'] = max(util.strwidth(x[col['name']]) for x in self.tickets)
            col['width'] = max(col['width'], util.strwidth(col['name']))
        if self.reducename:
            totwidth = sum(x['width'] for x in self.colcfg)
            deltawidth = totwidth - termwidth()
            if deltawidth > 0:
                self.colcfg[self.reducename]['width'] = max(self.colcfg[self.reducename]['width'] - deltawidth, util.strwidth(self.reducename))
        
    def output(self):
        term = blessings.Terminal()
        lines = [[], []]
        for col in self.colcfg:
            gluelen = col['width'] - util.strwidth(col['name'])
            lines[0].append(col['name'] + u' ' * gluelen)
            lines[1].append(term.bold(u'-' * (len(col['name']) + gluelen)))
        for ticket in self.tickets:
            line = []
            for col in self.colcfg:
                txt = ticket.tostr(col['name'], col['width'])
                if 'color' in col:
                    txt = getattr(term, col['color'])(txt)
                line.append(txt)
            lines.append(line)
        return u'\n'.join((u' ' * self.margin).join(x) for x in lines)


def ticketlist(tickets):
    u"""Ticketオブジェクトのリストを表示する"""
    t = Table(tickets)
    for colcfg in ({'name':'id', 'color':'green'}, {'name':'state', 'color':'cyan'},
                   {'name':'title'}, {'name':'assign', 'color':'magenta'},
                   {'name':'c'}, {'name':'create'}, {'name':'update'}):
        if all(getattr(x, colcfg['name'], None) is not None for x in tickets):
            t.addcolumn(colcfg)
    t.reducename = 'title'
    t.fit()
    return t.output()
            
def ticketdetail(tic):
    term = blessings.Terminal()
    r = u'\n'
    r += u'[{term.cyan}{tic.state}{term.normal}] {term.green}#{tic.id}{term.normal} created by {term.magenta}{tic.created_by}{term.normal} at {tic.create}, {tic.c} comments, updated at {tic.update}\n'.format(tic=tic, term=term)
    r += horline(u'=') + u'\n'
    r += u'Title:  {tic.title}\n'.format(tic=tic)
    r += u'Assign: {term.magenta}{tic.assign}{term.normal}\n'.format(tic=tic, term=term)
    if tic.labels:
        r += u'Labels: {0}\n'.format(u', '.join(tic.labels))
    if tic.milestone:
        r += u"MStone: {term.green}#{tic.milestone[number]}{term.normal} {tic.milestone[description]}\n".format(tic=tic, term=term)
    if tic.state == 'closed':
        r += u'Closed at: {tic.closed}\n'.format(tic=tic)
    r += u'\n'
    r += u'Description:\n' + tic.body + u'\n'
    r += u'\n'
    for comment in tic.comments or []:
        r += u'{term.green}#{com.id}{term.normal} {term.magenta}{com.created_by}{term.normal} commented at {com.create}\n'.format(com=comment, term=term)
        r += horline() + u'\n'
        r += u'\n'
        r += comment.body.format(term=term) + u'\n'
        r += u'\n'

    return r


def termwidth():
    term = blessings.Terminal()
    if not term.width:
        return 80
    return term.width


def horline(linestr=u'-'):
    return linestr * termwidth()
