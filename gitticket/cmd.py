#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import blessings
from gitticket import config
from gitticket import display


def show(opts):
    cfg = config.parseconfig()
    try:
        tic = cfg['service'].issue(opts['number'])
    except ValueError as e:
        print e
        return
    print display.ticketdetail(tic)


def list(opts):
    cfg = config.parseconfig()
    try:
        r = cfg['service'].issues(opts)
    except ValueError as e:
        print e
        return
    if not r:
        print u'No tickets.\n'
    else:
        print display.ticketlist(r)


def add(opts):
    cfg = config.parseconfig()
    try:
        r = cfg['service'].add()
    except ValueError as e:
        print e
        return
    term = blessings.Terminal()
    print u'Added {term.green}#{0}{term.normal}\nURL: {1}\n'.format(r['number'], r['html_url'], term=term)


def close(opts):
    cfg = config.parseconfig()
    try:
        if not opts['nocomment']:
            cfg['service'].comment(opts['number'])
        cfg['service'].changestate(opts['number'], 'closed')
    except ValueError as e:
        print e


def update(opts):
    cfg = config.parseconfig()
    try:
        cfg['service'].update(opts['number'])
    except ValueError as e:
        print e


def comment(opts):
    cfg = config.parseconfig()
    try:
        cfg['service'].comment(opts['number'])
    except ValueError as e:
        print e


def github_auth(opts):
    import getpass
    from gitticket import github
    cfg = config.parseconfig()
    pswd = getpass.getpass('github password for {0}: '.format(cfg['name']))
    r = github.authorize(cfg['name'], pswd)
    if 'message' in r:
        sys.exit(r['message'])
    print 'You got an access token: {0}'.format(r['token'])
    print 'If you want to set global, type:\ngit config --global ticket.github.token {0}'.format(r['token'])


def bitbucket_auth(opts):
    from gitticket import bitbucket
    r = bitbucket.authorize()
    print 'You got an access token and access token secret:\n{token}\n{secret}'.format(token=r[0], secret=r[1])
    print 'If you want to set global, type:'
    print 'git config --global ticket.bitbucket.token {0}'.format(r[0])
    print 'git config --global ticket.bitbucket.token-secret {0}'.format(r[1])
