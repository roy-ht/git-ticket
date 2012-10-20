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
    r = _request('get', url, params=params)
    tickets = [_toticket(x) for x in r]
    return tickets


def issue(number, params={}):
    cfg = config.parseconfig()
    url = ISSUE.format(issueid=number, **cfg)
    r = _request('get', url, params=params)
    return _toticket(r)


def comments(number, params={}):
    cfg = config.parseconfig()
    r = _request('get', ISSUE_COMMENTS.format(issueid=number, **cfg), params=params)
    comments = [ticket.Comment(number = x['id'],
                               body = x['body'],
                               creator = nested_access(x, 'user.login'),
                               created = todatetime(x['created_at']),
                               updated = todatetime(x['updated_at'])) for x in r]
    return comments


def _toticket(d):
    j = dict(number = d['number'],
             state = d['state'],
             title = d['title'],
             body = d['body'],
             creator = nested_access(d, 'user.login'),
             assignee = nested_access(d, 'assignee.login'),
             labels = [x['name'] for x in d['labels']],
             comments = d['comments'],
             milestone = nested_access(d, 'milestone.title'),
             created = todatetime(d['created_at']),
             updated = todatetime(d['updated_at']),
             closed = todatetime(d['closed_at']),
             html_url = d['html_url']
             )
    if nested_access(d, 'pull_request.html_url'):
        j['pull_request'] = 'Pull Request'
    t = ticket.Ticket(**j)
    if nested_access(d, 'milestone.id'):
        t.milestone_id = nested_access(d, 'milestone.id')
    return t


def add(params={}):
    comment = 'Available assignees: {0}\nAvailable labels: {1}'.format(u', '.join(labels()), u', '.join(assignees()))
    template = ticket.template(('title', 'assignee', 'labels', 'milestone_id', 'body'), comment=comment)
    val = util.inputwitheditor(template)
    if val == template:
        return
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params)
    return r


def update(number, params={}):
    tic = issue(number, params)
    comment = 'Available assignees: {0}\nAvailable labels: {1}'.format(u', '.join(labels()), u', '.join(assignees()))
    template = ticket.template(('title', 'state', 'assignee', 'labels', 'milestone_id', 'body'), tic, comment=comment)
    val = util.inputwitheditor(template)
    if val == template:
        return
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    _request('patch', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params)


def changestate(number, state):
    if state not in ('open', 'closed'):
        raise ValueError('Unknown state: {0}'.format(state))
    data = {'state': state}
    cfg = config.parseconfig()
    _request('patch', ISSUE.format(issueid=number, **cfg), data=json.dumps(data))


def commentto(number, params={}):
    template = """# comment below here\n"""
    val = util.inputwitheditor(template)
    data = {'body': util.rmcomment(val)}
    cfg = config.parseconfig()
    _request('post', ISSUE_COMMENTS.format(issueid=number, **cfg), data=json.dumps(data), params=params)


def assignees(params={}):
    cfg = config.parseconfig()
    r = _request('get', ASSIGNEES.format(**cfg), params=params)
    return [x['login'] for x in r]


def labels(params={}):
    cfg = config.parseconfig()
    r = _request('get', LABELS.format(**cfg), params=params)
    return [x['name'] for x in r]


def _issuedata_from_template(s):
    data = ticket.templatetodic(s, {'milestone_id':'milestone'})
    if 'title' not in data:
        raise ValueError('You must write a title')
    if 'labels' in data:
        data['labels'] = [x.strip() for x in data['labels'].split(u',')]
    if 'assignee' in data and data['assignee'] == 'No one':
        data['assignee'] = u''
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
    if 'message' in r.json:
        raise ValueError('Invarid query: {0}'.format(r['message']))
    return r.json


def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
