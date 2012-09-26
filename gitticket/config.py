#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
import re
from gitticket import util


@util.memoize
def git():
    rawstrs = util.cmd_stdout(('git', 'config', '-l')).split('\n')
    return dict(x.split('=', 1) for x in filter(None, rawstrs))


def is_inside_work_tree():
    return util.cmd_stdout(('git', 'rev-parse', '--is-inside-work-tree')) == 'true'


def gitdir():
    if not is_inside_work_tree():
        return None
    return os.path.normpath(os.path.join(os.path.abspath(util.cmd_stdout(('git', 'rev-parse', '-q', '--git-dir'))), '..')) # .gitの一つ上


@util.memoize
def parseconfig():
    u"""Parse git config key-values and set for issue handling.
    name: ticket.name 優先、user.nameが次点
    repo: ticket.repo 優先、guess_repo_nameが次点 
    gtoken: github/access_token
    rtoken: redmine/apikey
    """
    gconfig = git()
    config = {}
    # basic information
    config['name'] = gconfig.get('ticket.name', gconfig.get('user.name', None))
    config['repo'] = gconfig.get('ticket.repo', None) or guess_repo_name()
    from gitticket import github, bitbucket, redmine
    config['service_name'] = gconfig.get('ticket.service', None) or guess_service()
    config['service'] = {'github':github,
                         'bitbucket':bitbucket,
                         'redmine':redmine,
                         }.get(config['service_name'], None)
    # ssl
    config['sslverify'] = gconfig.get('http.sslVerify', 'true')
    if config['sslverify'] in ('false', 'False', 'FALSE'):
        config['sslverify'] = False
    else:
        config['sslverify'] = True
    # list and show formatting
    config['format_list'] = gconfig.get('ticket.format.list', None)
    config['format_show'] = gconfig.get('ticket.format.show', None)
    config['format_comment'] = gconfig.get('ticket.format.comment', None)
    # github
    config['gtoken'] = gconfig.get('ticket.github.token', None)
    # bitbucket
    config['btoken'] = gconfig.get('ticket.bitbucket.token', None)
    config['btoken_secret'] = gconfig.get('ticket.bitbucket.token-secret', None)
    # redmine
    config['rurl'] = gconfig.get('ticket.redmine.url', None)
    if config['rurl']:
        config['rurl'] = config['rurl'].rstrip(u'/')
    config['rpassword'] = gconfig.get('ticket.redmine.password', None)
    config['rtoken'] = gconfig.get('ticket.redmine.token', None)
    verify(config)
    return config


def verify(cfg):
    """Check if configuration values are valid."""
    if not cfg['service_name']:
        raise ValueError("Can't guess a service. Try 'git config ticket.service [github|bitbucket|redmine]'")
    if cfg['service_name'] not in ('github', 'bitbucket', 'redmine'):
        raise ValueError(u"{0} is a unknown service. You must choose a service from github, bitbucket, and redmine")
    if not cfg['repo']:
        raise ValueError("Can't guess a repository name. Try 'git config ticket.repo <repository_name>'")
    # nameは何かしらあるだろうけど、gitのuser.nameが設定されていないという万一のことがある
    if not cfg['name']:
        raise ValueError("You must set your account name to ticket.name or user.name. Try 'git config ticket.name <your_account_name>'")
    if cfg['service_name'] == 'redmine':
        if not cfg['rurl']:
            raise ValueError(u"You must set a URL of your redmine. Try 'git config ticket.redmine.url <redmine_url>'")


def guess_repo_name():
    gcfg = git()
    origin_url = gcfg.get('remote.origin.url', None)
    if origin_url:
        if not isurl(origin_url):
            origin_url = originalurl(origin_url)
        r = origin_url.rsplit('/', 1)
        if len(r) == 2:
            return r[1].replace('.git', '')
    # originが見つからなかったら、ディレクトリ名にする
    gdir = gitdir() # gitリポジトリ外の場合にはNone
    if gitdir:
        gdir = os.path.basename(gdir)
    return gdir


def guess_service():
    u"""github, bitbucketなどサービスをoriginのurlから推測する"""
    gcfg = git()
    origin_url = gcfg.get('remote.origin.url', None)
    if origin_url is None:
        return None
    if not isurl(origin_url):
        origin_url = originalurl(origin_url)
    if 'github.com' in origin_url:
        return 'github'
    elif 'bitbucket.org' in origin_url:
        return 'bitbucket'
    else:
        return ''


def isurl(s):
    return '://' in s


def originalurl(s):
    gcfg = git()
    urlkeys = filter(lambda x: x.startswith('url.'), gcfg.keys())
    if not urlkeys:
        return s # no alias
    # (url, alias)
    for urlkey in urlkeys:
        alias = gcfg[urlkey]
        url = util.regex_extract(ur'^url\.(.+)\.insteadof', urlkey)
        if url and s.startswith(alias):
            return s.replace(alias, url, 1)
    return s # not aliased?


def nested_access(d, keystr, default=None):
    keys = keystr.split('.')
    tgt = d
    for k in keys:
        if not tgt or k not in tgt:
            return default
        tgt = tgt[k]
    return tgt


def conftodict(config):
    d = {}
    for kstr, v in config.items():
        keys = kstr.split('.')
        nd = d
        for k in keys[:-1]:
            nd = nd.setdefault(k, {})
        nd[keys[-1]] = v
    return d
