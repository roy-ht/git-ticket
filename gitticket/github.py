#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import json
import requests
import os
from gitticket.config import nested_access
from gitticket import ticket

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
    tickets = []
    for j in r:
        create = datetime.datetime.strptime(j['created_at'].replace('Z', 'UTC'), DATEFMT) if j['created_at'] else None
        update = datetime.datetime.strptime(j['updated_at'].replace('Z', 'UTC'), DATEFMT) if j['updated_at'] else None
        closed = datetime.datetime.strptime(j['closed_at'].replace('Z', 'UTC'), DATEFMT) if j['closed_at'] else None
        t = ticket.Ticket({'id':j['number'], 'state':j['state'], 'title':j['title'], 'assign':nested_access(j, 'assignee.login'),
                           'commentnum':j['comments'], 'create':create, 'update':update, 'closed':closed})
        tickets.append(t)
    return tickets
    
def issue(cfg, number, params={}):
    url = ISSUE.format(issueid=number, **cfg)
    if 'gtoken' in cfg:
        params['access_token'] = cfg['gtoken']
    j = requests.get(url, params=params).json
    create = datetime.datetime.strptime(j['created_at'].replace('Z', 'UTC'), DATEFMT) if j['created_at'] else None
    update = datetime.datetime.strptime(j['updated_at'].replace('Z', 'UTC'), DATEFMT) if j['updated_at'] else None
    closed = datetime.datetime.strptime(j['closed_at'].replace('Z', 'UTC'), DATEFMT) if j['closed_at'] else None
    tic = ticket.Ticket({'id':j['number'],
                            'state':j['state'],
                            'title':j['title'],
                            'assign':nested_access(j, 'assignee.login'),
                            'commentnum':j['comments'],
                            'create':create,
                            'update':update,
                            'closed':closed})
    return tic
    
def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
