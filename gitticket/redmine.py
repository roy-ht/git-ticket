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

REPO = '{rurl}/'
ASSIGNEES = os.path.join(REPO, 'assignees')
ISSUES = os.path.join(REPO, 'issues.json')
ISSUE = os.path.join(REPO, 'issues/{issueid}.json')
ISSUE_URL = os.path.join(REPO, 'issues/{issueid}')
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

def issues(params={}):
    cfg = config.parseconfig()
    url = ISSUES.format(**cfg)
    if 'limit' not in params:
        params['limit'] = 50
    params['project_id'] = cfg['repo']
    if 'state' in params:
        if params['state'] not in ('open', 'closed'):
            raise ValueError('Invarid query: available state are (open, closed)')
        params['status_id'] = params.pop('state')
    params['sort'] = params.pop('order', 'updated_on:desc')
    if params['sort'] == 'updated':
        params['sort'] = 'updated_on:desc'
    r = _request('get', url, params=params).json
    tickets = []
    for j in r['issues']:
        create = todatetime(j['created_on'])
        update = todatetime(j['updated_on'])
        t = ticket.Ticket({'id':j['id'],
                           'state':nested_access(j, 'status.name'),
                           'title':j['subject'],
                           'body':j.get('description', ''),
                           'created_by':nested_access(j, 'author.name'),
                           'assign':nested_access(j, 'assigned_to.name'),
                           'create':create,
                           'update':update})
        tickets.append(t)
    return tickets
    
def issue(number, params={}):
    cfg = config.parseconfig()
    url = ISSUE.format(issueid=number, **cfg)
    j = _request('get', url, params=params).json['issue']
    tic = ticket.Ticket({'id':j['id'],
                         'state':nested_access(j, 'status.name'),
                         'priority':nested_access(j, 'priority.name'),
                         'title':j['subject'],
                         'labels':[nested_access(j, 'tracker.name')],
                         'body':j.get('description', u''),
                         'created_by':nested_access(j, 'author.name'),
                         'assign':nested_access(j, 'assigned_to.name'),
                         'create':todatetime(j['created_on']),
                         'update':todatetime(j['updated_on'])})
    return tic


def add(params={}):
    template = u"""Title: 
Assign: 
Tracker:
Priority:

Description:

"""
    val = util.inputwitheditor(template)
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    data['issue']['project_id'] = cfg['repo']
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'}).json['issue']
    return {'number':r['id'], 'html_url':ISSUE_URL.format(issueid=r['id'], **cfg)}


def update(number, params={}):
    tic = issue(number, params)
    template = u"""Title: {tic_title}
Assign: {tic_assign}
Tracker: {tic_tracker}
Priority: {tic_priority}

Description:

{tic_description}
""".format(tic_title=tic.title,
           tic_assign=tic.assign if tic.assign != u'None' else u'',
           tic_tracker=u', '.join(tic.labels),
           tic_priority=tic.priority,
           tic_description=tic.body)
    val = util.inputwitheditor(template)
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    r = _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'}).json
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
    data = {}
    title = util.regex_extract(ur'Title:([^#\n]+?)[#\n]', s, '').strip()
    assign = util.regex_extract(ur'Assign:([^#\n]+?)[#\n]', s, '').strip()
    tracker = util.regex_extract(ur'Tracker:([^#\n]+?)[#\n]', s, '').strip()
    priority = util.regex_extract(ur'Priority:([^#\n]+?)[#\n]', s, '').strip()
    description = util.rmcomment(util.regex_extract(ur'Description:(.*)', s, '')).strip()
    if not title:
        raise ValueError('You must write a title')
    data['subject'] = title
    if assign:
        data['assigned_to_id'] = assign
    if tracker:
        data['tracker_id'] = tracker
    if priority:
        data['priority_id'] = priority
    if description:
        data['description'] = description
    return {'issue':data}
    

def _request(rtype, url, params={}, data=None, headers={}):
    cfg = config.parseconfig()
    r = None
    # params['key'] = cfg['rtoken']
    auth = (cfg['rtoken'] or cfg['name'], cfg['rpassword'] or 'password')
    if data:
        r = getattr(requests, rtype)(url, data=data, params=params, headers=headers, auth=auth)
    else:
        r = getattr(requests, rtype)(url, params=params, headers=headers, auth=auth)
    if not 200 <= r.status_code < 300:
        print data
        raise requests.exceptions.HTTPError('[{0}] {1}'.format(r.status_code, r.url))
    return r


    
def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
