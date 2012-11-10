#!/usr/bin/env python
# -*- coding:utf-8 -*-

import sys
import re
import blessings
import requests
from gitticket import config


def list(opts):
    cfg = config.parseconfig()
    tickets = cfg['service'].issues(opts)
    if not tickets:
        print u'No open tickets.\n'
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


def locals(opts):
    # チケット番号を見つける
    # id-xx, id/xx, idxx, #xxに対応
    def find_ticket_number(s):
        mo = re.search(r'(?:id[/-]|#)(\d+)', s)
        if mo:
            return int(mo.group(1))
        return None
    cfg = config.parseconfig()
    branches = config.git_branches()
    parsed_branches = filter(lambda x: x[0] is not None, ((find_ticket_number(x), x) for x in branches))
    for issue_number, branch_name in parsed_branches:
        try:
            r = cfg['service'].issue(issue_number)
        except requests.exceptions.HTTPError:
            continue
        ticket = r[0] if isinstance(r, tuple) else r
        print u'({0})'.format(branch_name), ticket.format(cfg['format_list'])


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


def show_config(opts):
    cfg = config.parseconfig(doverify=False)
    print ('service: {c[service_name]}\n'
           'username: {c[name]}\n'
           'repository: {c[repo]}\n'
           'sslverify: {c[sslverify]}').format(c=cfg)
    if cfg.get('service_name', '') == 'github':
        print 'github_token: {0}'.format(cfg['gtoken'])
    elif cfg.get('service_name', '') == 'bitbucket':
        print 'bitbucket_token: {0}'.format(cfg['btoken'])
        print 'bitbucket_token_secret: {0}'.format(cfg['btoken_secret'])
    elif cfg.get('service_name', '') == 'redmine':
        print 'redmine_endpoint: {0}'.format(cfg['rurl'])
        print 'redmine_token: {0}'.format(cfg['rtoken'])
