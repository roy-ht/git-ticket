#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import github
import blessings
from gitticket import config
from gitticket import display


def show(opts):
    try:
        tic = github.issue(opts['number'])
    except ValueError as e:
        print e
        return
    print display.ticketdetail(tic)


def list(opts):
    try:
        r = github.issues()
    except ValueError as e:
        print e
        return
    print display.ticketlist(r)


def mine(opts):
    try:
        r = github.issues()
    except ValueError as e:
        print e
        return
    print display.ticket(r)


def add(opts):
    try:
        r = github.add()
    except ValueError as e:
        print e
        return
    term = blessings.Terminal()
    print u'Added {term.green}#{0}{term.normal}\nURL: {1}\n'.format(r['number'], r['html_url'], term=term)


def close(opts):
    try:
        if not opts['nocomment']:
            github.comment(opts['number'])
        github.changestate(opts['number'], 'closed')
    except ValueError as e:
        print e
        return


def update(opts):
    try:
        github.update(opts['number'])
    except ValueError as e:
        print e
        return


def comment(opts):
    try:
        github.comment(opts['number'])
    except ValueError as e:
        print e
        return


def github_auth(opts):
    import getpass
    cfg = config.parseconfig()
    pswd = getpass.getpass('github password for {0}: '.format(cfg['name']))
    r = github.authorize(cfg['name'], pswd)
    if 'message' in r:
        sys.exit(r['message'])
    print 'You got an access token: {0}'.format(r['token'])
    print 'If you want to set global, type:\ngit config --global ticket.github.token {0}'.format(r['token'])
