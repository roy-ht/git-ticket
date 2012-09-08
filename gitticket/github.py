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
    cfg = config.parseconfig()
    r = requests.post(AUTH, data=json.dumps({'scopes':['repo'], 'note':'git-ticket'}), auth=(name, pswd), verify=cfg['sslverify'])
    return r.json

def issues(params={}):
    cfg = config.parseconfig()
    url = ISSUES.format(**cfg)
    if 'state' in params and params['state'] not in ('open', 'closed'):
        raise ValueError('Invarid query: available state are (open, closed)')
    if 'order' in params:
        params['sort'] = params.pop('order')
    r = _request('get', url, params=params).json
    if 'message' in r:
        raise ValueError('Invarid query: {0}'.format(r['message']))
    tickets = []
    for j in r:
        create = todatetime(j['created_at'])
        update = todatetime(j['updated_at'])
        closed = todatetime(j['closed_at'])
        t = ticket.Ticket(id = j['number'],
                          state = j['state'],
                          title = j['title'],
                          body = j['body'],
                          created_by = nested_access(j, 'user.login'),
                          assign = nested_access(j, 'assignee.login'),
                          commentnum = j['comments'],
                          create = create,
                          update = update,
                          closed = closed)
        tickets.append(t)
    return tickets
    
def issue(number, params={}):
    cfg = config.parseconfig()
    url = ISSUE.format(issueid=number, **cfg)
    j = _request('get', url, params=params).json
    if 'message' in j:
        raise ValueError('Invarid query: {0}'.format(j['message']))
    labels = [x['name'] for x in j['labels']]
    cj = requests.get(ISSUE_COMMENTS.format(issueid=number, **cfg), params=params, verify=cfg['sslverify']).json
    if 'message' in cj:
        raise ValueError('Invarid query: {0}'.format(cj['message']))
    comments = [ticket.Comment({'id':x['id'],
                                'body':x['body'],
                                'created_by':nested_access(x, 'user.login'),
                                'create':todatetime(x['created_at']),
                                'update':todatetime(x['updated_at']),
                                }) for x in cj]
    tic = ticket.Ticket(id = j['number'],
                        state = j['state'],
                        title = j['title'],
                        body = j['body'],
                        closed_by = j['closed_by'],
                        labels = labels,
                        milestone = j['milestone'],
                        created_by = nested_access(j, 'user.login'),
                        assign = nested_access(j, 'assignee.login'),
                        commentnum = j['comments'],
                        create = todatetime(j['created_at']),
                        update = todatetime(j['updated_at']),
                        closed = todatetime(j['updated_at']),
                        comments = comments)
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
    template = ticket.template(('title', 'assign', 'labels', 'milestone', 'description'),
                               assign={'comment':'Available assignee: {0}'.format(u', '.join(assignees()))},
                               labels={'comment':'Available labels: {0}'.format(u', '.join(labels()))},
                               milestone={'disp':'Milestone Id'})
    val = util.inputwitheditor(template)
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params).json
    if 'message' in r:
        raise ValueError('Request Error: {0}'.format(r['message']))
    else:
        return r

def update(number, params={}):
    tic = issue(number, params)
    template = ticket.template(('title', 'assign', 'labels', 'milestone', 'description'),
                               title={'default':tic.title},
                               assign={'comment':'Available assignee: {0}'.format(u', '.join(assignees())),
                                       'default':tic.assign if tic.assign != 'None' else u''},
                               labels={'comment':'Available labels: {0}'.format(u', '.join(labels())),
                                       'default':u', '.join(tic.labels)},
                               milestone={'disp':'Milestone Id', 'default':tic.milestone.get('number', u'')},
                               description={'default':tic.body})
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
    data = ticket.templatetodic(s, {'assign':'assignee', 'milestone_id':'milestone', 'description':'body'})
    if 'title' not in data:
        raise ValueError('You must write a title')
    if 'labels' in data:
        data['labels'] = [x.strip() for x in data['labels'].split(u',')]
    if 'milestone' in data:
        data['milestone'] = int(data['milestone'])
    return data
    

def _request(rtype, url, params={}, data=None):
    cfg = config.parseconfig()
    if 'gtoken' in cfg:
        params['access_token'] = cfg['gtoken']
    r = None
    if data:
        r = getattr(requests, rtype)(url, data=data, params=params, verify=cfg['sslverify'])
    else:
        r = getattr(requests, rtype)(url, params=params, verify=cfg['sslverify'])
    if not 200 <= r.status_code < 300:
        raise requests.exceptions.HTTPError('[{0}] {1}'.format(r.status_code, r.url))
    return r


    
def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
