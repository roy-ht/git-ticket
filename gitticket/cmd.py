#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import github
from gitticket import config

def show(opts):
    pass

def list(opts):
    cfg = config.parseconfig()
    r = github.issues(cfg)
    print r

def mine(opts):
    pass

def commit(opts):
    pass

def add(opts):
    pass

def update(opts):
    pass

def local(opts):
    pass

def github_auth(opts):
    r = github.authorize()
    if 'message' in r:
        sys.exit(r['message'])
    print 'You got an access token: {0}'.format(r['token'])
    print 'If you want to set global, type:\ngit config --global ticket.github.token {0}'.format(r['token'])
