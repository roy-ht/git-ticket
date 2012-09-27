#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import blessings
from gitticket import config


def list(opts):
    cfg = config.parseconfig()
    tickets = cfg['service'].issues(opts)
    if not tickets:
        print u'No tickets.\n'
    else:
        for tic in tickets:
            print tic.format(cfg['format_list'])


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


def add(opts):
    cfg = config.parseconfig()
    r = cfg['service'].add()
    if r is None:
        print u'Abort. Canceled to add a ticket for some reason.'
    else:
        term = blessings.Terminal()
        print u'Added {term.green}#{0}{term.normal}\nURL: {1}\n'.format(r['number'], r['html_url'], term=term)


def update(opts):
    cfg = config.parseconfig()
    r = cfg['service'].update(opts['number'])
    if r is None:
        print u'Abort. Canceled to update a ticket for some reason.'
    else:
        term = blessings.Terminal()
        print u'Ticket {term.green}#{0} was successfully updated.'.format(opts['number'], term=term)


def close(opts):
    cfg = config.parseconfig()
    if not opts['nocomment']:
        cfg['service'].commentto(opts['number'])
    cfg['service'].changestate(opts['number'], 'closed')


def comment(opts):
    cfg = config.parseconfig()
    cfg['service'].commentto(opts['number'])


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
