#!/usr/bin/env python
# -*- coding:utf-8 -*-
import os
import sys
from gitticket import util

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
    

def git():
    rawstrs = util.cmd_stdout(('git', 'config', '-l')).split('\n')
    return dict(x.split('=', 1) for x in filter(None, rawstrs))

def is_inside_work_tree():
    return util.cmd_stdout(('git', 'rev-parse', '--is-inside-work-tree')) == 'true'

def git_dir():
    if not is_inside_work_tree():
        return None
    return os.path.normpath(os.path.join(os.path.abspath(util.cmd_stdout(('git', 'rev-parse', '-q', '--git-dir'))), '..')) # .gitの一つ上

def guess_repo_name():
    origin_url = util.cmd_stdout(('git', 'config', '--get', 'remote.origin.url'))
    if origin_url:
        return origin_url.rsplit('/', 1)[1].replace('.git', '')
    # originが見つからなかったら、ディレクトリ名にする
    return os.path.basename(git_dir())

def guess_service():
    u"""github, bitbucketなどサービスをoriginのurlから推測する"""
    origin_url = util.cmd_stdout(('git', 'config', '--get', 'remote.origin.url'))
    if 'github.com' in origin_url:
        return 'github'
    elif 'bitbucket.org' in origin_url:
        return 'bitbucket'
    else:
        return ''

def parseconfig():
    u"""Parse git config key-values and set for issue handling.
    name: ticket.name 優先、user.nameが次点
    repo: ticket.repo 優先、guess_repo_nameが次点 
    gtoken: github/access_token
    rtoken: redmine/apikey
    """
    gconfig = git()
    config = {}
    config['name'] = gconfig.get('ticket.name', gconfig.get('user.name', None)) or sys.exit('Please set ticket.name or user.name to git config file')
    config['repo'] = gconfig.get('ticket.repo', guess_repo_name())
    from gitticket import github, bitbucket, redmine
    config['service_name'] = gconfig.get('ticket.service', guess_service())
    config['service'] = {'github':github,
                         'bitbucket':bitbucket,
                         'redmine':redmine,
                         }.get(config['service_name'], None)
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
    return config
