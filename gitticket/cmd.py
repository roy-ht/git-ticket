#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import github
import blessings
from gitticket import config
from gitticket import display

def show(opts):
    cfg = config.parseconfig()
    try:
        tic = github.issue(cfg, opts['number'])
    except ValueError as e:
        print e
        return
    print display.ticketdetail(tic)

def list(opts):
    cfg = config.parseconfig()
    try:
        r = github.issues(cfg)
    except ValueError as e:
        print e
        return
    print display.ticketlist(r)
                         
def mine(opts):
    cfg = config.parseconfig()
    opts['assignee'] = cfg['name']
    try:
        r = github.issues(cfg)
    except ValueError as e:
        print e
        return
    print display.ticket(r)

def add(opts):
    cfg = config.parseconfig()
    try:
        r = github.add(cfg)
    except ValueError as e:
        print e
        return
    term = blessings.Terminal()
    print u'Added {term.green}#{0}{term.normal}\nURL: {1}\n'.format(r['number'], r['html_url'], term=term)

def close(opts):
    return update(opts)

def update(opts):
    cfg = config.parseconfig()
    try:
        github.update(cfg, opts['number'])
    except ValueError as e:
        print e
        return


def local(opts):
    pass

def github_auth(opts):
    import getpass
    cfg = config.parseconfig()
    pswd = getpass.getpass('github password for {0}: '.format(cfg['name']))
    r = github.authorize(cfg['name'], pswd)
    if 'message' in r:
        sys.exit(r['message'])
    print 'You got an access token: {0}'.format(r['token'])
    print 'If you want to set global, type:\ngit config --global ticket.github.token {0}'.format(r['token'])
