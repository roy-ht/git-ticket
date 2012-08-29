#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import github
from gitticket import config
from gitticket import display

def show(opts):
    cfg = config.parseconfig()
    try:
        tic = github.issue(cfg, opts['number'], params=opts)
    except ValueError as e:
        print e
        return
    print display.ticketdetail(tic)

def list(opts):
    cfg = config.parseconfig()
    try:
        r = github.issues(cfg, params=opts)
    except ValueError as e:
        print e
        return
    print display.ticketlist(r)
                         
def mine(opts):
    cfg = config.parseconfig()
    opts['assignee'] = cfg['name']
    try:
        r = github.issues(cfg, params=opts)
    except ValueError as e:
        print e
        return
    print display.ticket(r)

def add(opts):
    pass

def update(opts):
    pass

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
