#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import github
from gitticket import config
from gitticket import display

def show(opts):
    pass

def list(opts):
    cfg = config.parseconfig()
    r = github.issues(cfg)
    print display.json(r, [{'key':'number', 'name':'id'},
                         {'key':'state'},
                         {'key':'title', 'trunc':True},
                         {'key':'assignee.login', 'name':'assignee'},
                         {'key':'comments', 'name':'c'},
                         {'key':'created_at', 'name':'create'},
                         {'key':'updated_at', 'name':'update'},
                         {'key':'closed_at', 'name':'closed'},
                         ])
                         
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
    import getpass
    cfg = config.parseconfig()
    pswd = getpass.getpass('github password for {0}: '.format(cfg['name']))
    r = github.authorize(cfg['name'], pswd)
    if 'message' in r:
        sys.exit(r['message'])
    print 'You got an access token: {0}'.format(r['token'])
    print 'If you want to set global, type:\ngit config --global ticket.github.token {0}'.format(r['token'])
