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
STATUSES = os.path.join(REPO, 'issue_statuses.json')
TRACKERS = os.path.join(REPO, 'trackers.json')
MEMBERSHIPS = os.path.join(REPO, 'projects/{repo}/memberships.json')
USER = os.path.join(REPO, 'users/{userid}.json')
ISSUES = os.path.join(REPO, 'issues.json')
ISSUE = os.path.join(REPO, 'issues/{issueid}.json')
ISSUE_URL = os.path.join(REPO, 'issues/{issueid}')

DATEFMT = "%Y-%m-%dT%H:%M:%S%Z"

def issues(params={}):
    cfg = config.parseconfig()
    if 'limit' not in params:
        params['limit'] = 50
    params['project_id'] = cfg['repo']
    if 'state' in params:
        avail_state = ('open', 'closed', '*')
        if params['state'] not in avail_state:
            raise ValueError(u'Invarid query: available status are ({0})'.format(u', '.join(avail_state)))
        params['status_id'] = params.pop('state')
    else:
        params['status_id'] = '*'
    params['sort'] = params.pop('order', 'updated_on:desc')
    if params['sort'] == 'updated':
        params['sort'] = 'updated_on:desc'
    r = _request('get', ISSUES.format(**cfg), params=params).json
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
    params['include'] = u','.join(('journals', 'children', 'changesets'))
    j = _request('get', ISSUE.format(issueid=number, **cfg), params=params).json['issue']
    comments = [ticket.Comment(_parse_journal(x)) for x in reversed(j['journals'])]
    tic = ticket.Ticket({'id':j['id'],
                         'state':nested_access(j, 'status.name'),
                         'priority':nested_access(j, 'priority.name'),
                         'title':j['subject'],
                         'labels':[nested_access(j, 'tracker.name')],
                         'body':j.get('description', u''),
                         'created_by':nested_access(j, 'author.name'),
                         'assign':nested_access(j, 'assigned_to.name'),
                         'comments':comments,
                         'create':todatetime(j['created_on']),
                         'update':todatetime(j['updated_on'])})
    # additional attributes
    tic.priority_id = nested_access(j, 'priority.id')

    return tic


def add(params={}):
    template = u"""Title:
# Available assignees: {assignees}
Assign:
# Available trackers: {trackers}
Tracker:
# Available priorities: 3-7 (low to high)
Priority: 
# Available statuses: {statuses}
Status: 
Description:

""".format(trackers=u', '.join(trackers()), statuses=u', '.join(statuses()),
           assignees=u', '.join(u'{login}({name})'.format(login=x, name=y['name']) for x, y in assignees().items()))
    val = util.inputwitheditor(template)
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    data['issue']['project_id'] = cfg['repo']
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'}).json['issue']
    return {'number':r['id'], 'html_url':ISSUE_URL.format(issueid=r['id'], **cfg)}


def update(number, params={}):
    tic = issue(number, params)
    nees = assignees()
    assignee = 'None'
    if tic.assign != 'None':
        cand = [x for x, y in nees.items() if y['name'] == tic.assign]
        assignee = cand[0] if len(cand) == 1 else 'Not found'
    template = u"""Title: {tic.title}
# Available assignees: {assignees}
Assign: {tic_assign}
# Available trackers: {trackers}
Tracker: {tic_tracker}
# Available priorities: 3-7 (low to high)
Priority: {tic.priority_id}
# Available statuses: {statuses}
Status: 
Description:
{tic.body}

Notes:

""".format(trackers=u', '.join(trackers()),
           statuses=u', '.join(statuses()),
           assignees=u', '.join(u'{login}({name})'.format(login=x, name=y['name']) for x, y in nees.items()),
           tic=tic,
           tic_assign=assignee,
           tic_tracker=u', '.join(tic.labels))
           
    val = util.inputwitheditor(template)
    if val == template:
        return
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    r = _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'}).json
    return r


def changestate(number, state):
    avail_state = statuses()
    if state not in avail_state:
        if state == u'closed':
            if u'終了' in avail_state:
                state = u'終了'
            elif u'close' in avail_state:
                state = u'close'
            else:
                raise ValueError(u'Invarid query: available status are ({0})'.format(u', '.join(avail_state)).encode('utf-8'))
    data = {'issue':{'status_id': avail_state[state]}}
    cfg = config.parseconfig()
    r = _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), headers={'content-type': 'application/json'})
    return r.json
    

def comment(number, params={}):
    template = """# comment below here\n"""
    val = util.inputwitheditor(template)
    data = {'notes': util.rmcomment(val)}
    cfg = config.parseconfig()
    _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'}).json


def statuses():
    cfg = config.parseconfig()
    r = _request('get', STATUSES.format(**cfg)).json
    return dict((x['name'], x['id']) for x in r['issue_statuses'])


def trackers():
    cfg = config.parseconfig()
    r = _request('get', TRACKERS.format(**cfg)).json
    return dict((x['name'], x['id']) for x in r['trackers'])


def memberships():
    cfg = config.parseconfig()
    r = _request('get', MEMBERSHIPS.format(**cfg)).json
    return r['memberships']


def user(n):
    cfg = config.parseconfig()
    r = _request('get', USER.format(userid=n, **cfg)).json
    return r['user']
    

def assignees():
    r = memberships()
    nees = {}
    for member in r:
        mainrole = min(member['roles'], key=lambda x: x['id'])  # idが小さいrole程権限がでかいと仮定
        if int(mainrole['id']) < 5:
            u = user(nested_access(member, 'user.id'))
            nees[u['login']] = {'id':u['id'], 'name':nested_access(member, 'user.name')}
    return nees


def _issuedata_from_template(s):
    data = {}
    title = util.regex_extract(ur'Title:([^#\n]+?)[#\n]', s, '').strip()
    assign = util.regex_extract(ur'Assign:([^#\n]+?)[#\n]', s, '').strip()
    tracker = util.regex_extract(ur'Tracker:([^#\n]+?)[#\n]', s, '').strip()
    priority = util.regex_extract(ur'Priority:([^#\n]+?)[#\n]', s, '').strip()
    status = util.regex_extract(ur'Status:([^#\n]+?)[#\n]', s, '').strip()
    notes = util.regex_extract(ur'Notes:(.*)', s, '').strip()
    description = util.rmcomment(util.regex_extract(ur'Description:(.*?)Notes:', s, '')).strip()
    if not title:
        raise ValueError('You must write a title')
    data['subject'] = title
    if assign:
        data['assigned_to_id'] = assignees()[assign]
    if tracker:
        data['tracker_id'] = trackers()[tracker]
    if priority:
        data['priority_id'] = priority
    if status:
        data['status_id'] = statuses()[status]
    if description:
        data['description'] = description
    if notes:
        data['notes'] = notes
    return {'issue':data}


def _parse_journal(j):
    r = {}
    r['id'] = j['id']
    r['created_by'] = nested_access(j, 'user.name')
    r['create'] = todatetime(j['created_on'])
    r['body'] = u''
    # make body
    if 'notes' in j:
        r['body'] += j['notes'] + u'\n'
    r['body'] += u'\n'.join(u'{term.red}*{term.normal} ' + _parse_detail(x) for x in j['details'])
    r['body'] = r['body'].strip()
    return r

def _parse_detail(j):
    if 'old_value' in j:
        if j['name'] == 'description':
            return u'Update {{term.bold}}{name}{{term.normal}}'.format(**j)
        return u'Change {{term.bold}}{name}{{term.normal}} from {{term.cyan}}{old_value}{{term.normal}} to {{term.cyan}}{new_value}{{term.normal}}'.format(**j)
    else:
        return u'Add {{term.bold}}{name}{{term.normal}}'.format(**j)


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
