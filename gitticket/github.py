#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import json
import re
import requests
import os
import tempfile
from gitticket.config import nested_access
from gitticket import ticket
from gitticket import util

BASEURL = 'https://api.github.com'
AUTH = os.path.join(BASEURL, 'authorizations')
REPO = os.path.join(BASEURL, 'repos/{name}/{repo}')
ASSIGNEES = os.path.join(REPO, 'assignees')
ISSUES = os.path.join(REPO, 'issues')
ISSUE = os.path.join(ISSUES, '{issueid}')
ISSUE_COMMENTS = os.path.join(ISSUE, 'comments')
ISSUE_COMMENT = os.path.join(ISSUE_COMMENTS, '{commentid}')
ISSUES_EVENT = os.path.join(ISSUES, 'events')
ISSUE_EVENT = os.path.join(ISSUE, 'events')
LABELS = os.path.join(REPO, 'labels')
LABEL = os.path.join(LABELS, '{label}')
ISSUE_LABELS = os.path.join(ISSUE, 'labels')
ISSUE_LABEL = os.path.join(ISSUE_LABELS, '{label}')
MILESTONES = os.path.join(REPO, 'milestones')
MILESTONE = os.path.join(MILESTONES, '{milestoneid}')

DATEFMT = "%Y-%m-%dT%H:%M:%S%Z"

def authorize(name, pswd):
    r = requests.post(AUTH, data=json.dumps({'scopes':['repo'], 'note':'git-ticket'}), auth=(name, pswd))
    return r.json

def issues(cfg, params={}):
    url = ISSUES.format(**cfg)
    if 'gtoken' in cfg:
        params['access_token'] = cfg['gtoken']
    r = requests.get(url, params=params).json
    if 'message' in r:
        raise ValueError('Invarid query: {0}'.format(r['message']))
    tickets = []
    for j in r:
        create = todatetime(j['created_at'])
        update = todatetime(j['updated_at'])
        closed = todatetime(j['closed_at'])
        t = ticket.Ticket({'id':j['number'],
                           'state':j['state'],
                           'title':j['title'],
                           'body':j['body'],
                           'created_by':nested_access(j, 'user.login'),
                           'assign':nested_access(j, 'assignee.login'),
                           'commentnum':j['comments'],
                           'create':create,
                           'update':update,
                           'closed':closed})
        tickets.append(t)
    return tickets
    
def issue(cfg, number, params={}):
    url = ISSUE.format(issueid=number, **cfg)
    if 'gtoken' in cfg:
        params['access_token'] = cfg['gtoken']
    j = requests.get(url, params=params).json
    if 'message' in j:
        raise ValueError('Invarid query: {0}'.format(j['message']))
    labels = [x['name'] for x in j['labels']]
    cj = requests.get(ISSUE_COMMENTS.format(issueid=number, **cfg), params=params).json
    if 'message' in cj:
        raise ValueError('Invarid query: {0}'.format(cj['message']))
    comments = [ticket.Comment({'id':x['id'],
                                'body':x['body'],
                                'created_by':nested_access(x, 'user.login'),
                                'create':todatetime(x['created_at']),
                                'update':todatetime(x['updated_at']),
                                }) for x in cj]
    tic = ticket.Ticket({'id':j['number'],
                         'state':j['state'],
                         'title':j['title'],
                         'body':j['body'],
                         'closed_by':j['closed_by'],
                         'labels':labels,
                         'milestone':j['milestone'],
                         'created_by':nested_access(j, 'user.login'),
                         'assign':nested_access(j, 'assignee.login'),
                         'commentnum':j['comments'],
                         'create':todatetime(j['created_at']),
                         'update':todatetime(j['updated_at']),
                         'closed':todatetime(j['updated_at']),
                         'comments':comments,
                         })
    return tic


def assignees(cfg):
    r = requests.get(ASSIGNEES.format(**cfg)).json
    return [x['login'] for x in r]


def labels(cfg):
    r = requests.get(LABELS.format(**cfg)).json
    return [x['name'] for x in r]


def add(cfg, params={}):
    template = """Title: 
# Available assignee: {assign}
Assign:
# Available labels: {lbls}
Labels: 
MilestoneId: 

# description below here

""".format(lbls=', '.join(labels(cfg)), assign=', '.join(assignees(cfg)))
    editor = util.cmd_stdout(('git', 'var', 'GIT_EDITOR'))
    tmpfile = tempfile.mkstemp()
    with open(tmpfile[1], 'w') as fo:
        fo.write(template)
    util.cmd_stdout((editor, tmpfile[1]))
    
    val = open(tmpfile[1]).read()
    title = util.regex_extract(ur'Title:([^#]+?)[#\n]', val, '').strip()
    assign = util.regex_extract(ur'Assign:([^#]+?)[#\n]', val, '').strip()
    lbls = util.regex_extract(ur'Labels:([^#]+?)[#\n]', val, '').strip()
    mstoneid = util.regex_extract(ur'MilestoneId:([^#]+?)[#\n]', val, '').strip()
    description = util.regex_extract(ur'# description below here.*?\n(.*)', val, '').strip()
    data = {}
    if not title:
        raise ValueError('You must write a title')
    data['title'] = title
    if assign:
        data['assign'] = assign
    if lbls:
        data['labels'] = [x.strip() for x in lbls.split(u',')]
    if mstoneid:
        data['milestone'] = mstoneid
    if description:
        data['body'] = description
    print data

    
def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
