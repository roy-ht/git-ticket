#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import blessings
from gitticket import config


def show(opts):
    cfg = config.parseconfig()
    r = cfg['service'].issue(opts['number'])
    ticket, comments = None, None
    # rがtupleの時は(ticket, comments)
    if isinstance(r, tuple):
        ticket, comments = r
    else:
        ticket = r
    print ticket.format(cfg['format_show'] or ticket._show_format)
    if not opts.get('nocomment', False):
        if comments is None:
            comments = cfg['service'].comments(opts['number'])
        for comment in comments:
            print comment.format(cfg['format_comment'])


def list(opts):
    cfg = config.parseconfig()
    tickets = cfg['service'].issues(opts)
    if not tickets:
        print u'No tickets.\n'
    else:
        for tic in tickets:
            print tic.format(cfg['format_list'])


def add(opts):
    cfg = config.parseconfig()
    r = cfg['service'].add()
    term = blessings.Terminal()
    print u'Added {term.green}#{0}{term.normal}\nURL: {1}\n'.format(r['number'], r['html_url'], term=term)


def close(opts):
    cfg = config.parseconfig()
    if not opts['nocomment']:
        cfg['service'].comment(opts['number'])
    cfg['service'].changestate(opts['number'], 'closed')


def update(opts):
    cfg = config.parseconfig()
    cfg['service'].update(opts['number'])


def comment(opts):
    cfg = config.parseconfig()
    cfg['service'].comment(opts['number'])


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
