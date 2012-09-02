#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import json
import requests
import os
from gitticket.config import nested_access
from gitticket import config
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

def issues(params={}):
    cfg = config.parseconfig()
    url = ISSUES.format(**cfg)
    if 'state' in params and params['state'] not in ('open', 'closed'):
        raise ValueError('Invarid query: available state are (open, closed)')
    if 'order' in params:
        params['sort'] = params['order']
        del params['order']
    r = _request('get', url, params=params).json
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
    
def issue(number, params={}):
    cfg = config.parseconfig()
    url = ISSUE.format(issueid=number, **cfg)
    j = _request('get', url, params=params).json
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


def assignees(params={}):
    cfg = config.parseconfig()
    r = _request('get', ASSIGNEES.format(**cfg), params=params).json
    return [x['login'] for x in r]


def labels(params={}):
    cfg = config.parseconfig()
    r = _request('get', LABELS.format(**cfg), params=params).json
    return [x['name'] for x in r]


def add(params={}):
    template = u"""Title: 
# Available assignee: {assign}
Assign: 
# Available labels: {lbls}
Labels: 
MilestoneId: 

Description:

""".format(lbls=', '.join(labels()), assign=', '.join(assignees()))
    val = util.inputwitheditor(template)
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params).json
    if 'message' in r:
        raise ValueError('Request Error: {0}'.format(r['message']))
    else:
        return r

def changestate(number, state):
    if state not in ('open', 'closed'):
        raise ValueError('Unknown state: {0}'.format(state))
    data = {'state': state}
    cfg = config.parseconfig()
    r = _request('patch', ISSUE.format(issueid=number, **cfg), data=json.dumps(data)).json
    if 'message' in r:
        raise ValueError('Request Error: {0}'.format(r['message']))
    else:
        return r
    

def update(number, params={}):
    tic = issue(number, params)
    template = u"""Title: {tic_title}
# Available assignee: {assign}
Assign: {tic_assign}
# Available labels: {lbls}
Labels: {tic_lbls}
MilestoneId: {tic_mstoneid}

Description:
{tic_body}
""".format(lbls=u', '.join(labels()),
           assign=u', '.join(assignees()),
           tic_title=tic.title,
           tic_assign=tic.assign if tic.assign != 'None' else u'',
           tic_lbls=u', '.join(tic.labels),
           tic_mstoneid=tic.milestone.get('number', ''),
           tic_body=tic.body)
    val = util.inputwitheditor(template)
    if val == template:
        return
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    r = _request('patch', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params).json
    if 'message' in r:
        raise ValueError('Request Error: {0}'.format(r['message']))
    else:
        return r


def comment(number, params={}):
    template = """# comment below here\n"""
    val = util.inputwitheditor(template)
    data = {'body': util.rmcomment(val)}
    cfg = config.parseconfig()
    r = _request('post', ISSUE_COMMENTS.format(issueid=number, **cfg), data=json.dumps(data), params=params).json
    if 'message' in r:
        raise ValueError('Request Error: {0}'.format(r['message']))
    else:
        return r
    

def _issuedata_from_template(s):
    data = {}
    title = util.regex_extract(ur'Title:([^#]+?)[#\n]', s, '').strip()
    assign = util.regex_extract(ur'Assign:([^#]+?)[#\n]', s, '').strip()
    lbls = util.regex_extract(ur'Labels:([^#]+?)[#\n]', s, '').strip()
    mstoneid = util.regex_extract(ur'MilestoneId:([^#]+?)[#\n]', s, '').strip()
    description = util.rmcomment(util.regex_extract(ur'Description:(.*)', s, '')).strip()
    if not title:
        raise ValueError('You must write a title')
    data['title'] = title
    if assign:
        data['assignee'] = assign
    if lbls:
        data['labels'] = [x.strip() for x in lbls.split(u',')]
    if mstoneid:
        data['milestone'] = mstoneid
    if description:
        data['body'] = description
    return data
    

def _request(rtype, url, params={}, data=None):
    cfg = config.parseconfig()
    if 'gtoken' in cfg:
        params['access_token'] = cfg['gtoken']
    if data:
        return getattr(requests, rtype)(url, data=data, params=params)
    else:
        return getattr(requests, rtype)(url, params=params)

    
def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
