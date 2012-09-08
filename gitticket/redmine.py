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
        t = ticket.Ticket(id = j['id'],
                          state = nested_access(j, 'status.name'),
                          title = j['subject'],
                          body = j.get('description', ''),
                          created_by = nested_access(j, 'author.name'),
                          assign = nested_access(j, 'assigned_to.name'),
                          create = create,
                          update = update)
        tickets.append(t)
    return tickets
    
def issue(number, params={}):
    cfg = config.parseconfig()
    params['include'] = u','.join(('journals', 'children', 'changesets'))
    j = _request('get', ISSUE.format(issueid=number, **cfg), params=params).json['issue']
    comments = [ticket.Comment(_parse_journal(x)) for x in reversed(j['journals'])]
    tic = ticket.Ticket(id = j['id'],
                        state = nested_access(j, 'status.name'),
                        priority = nested_access(j, 'priority.name'),
                        title = j['subject'],
                        labels = [nested_access(j, 'tracker.name')],
                        body = j.get('description', u''),
                        created_by = nested_access(j, 'author.name'),
                        assign = nested_access(j, 'assigned_to.name'),
                        comments = comments,
                        create = todatetime(j['created_on']),
                        update = todatetime(j['updated_on']))
    # additional attributes
    tic.priority_id = nested_access(j, 'priority.id')

    return tic


def add(params={}):
    asgns = u', '.join(u'{login}({name})'.format(login=x, name=y['name']) for x, y in assignees().items())
    trks = u', '.join(trackers())
    template = ticket.template(('title', 'assign', 'tracker', 'priority', 'status', 'description'),
                               assign={'comment':u'Available assignee: {0}'.format(asgns)},
                               tracker={'comment':u'Available trackers: {0}'.format(trks)},
                               priority={'comment':u'Available priorities: 3-7 (low to high)'},
                               status={'comment':u'Available statuses: {0}'.format(u', '.join(statuses()))},
                               )
    val = util.inputwitheditor(template)
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    data['issue']['project_id'] = cfg['repo']
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'}).json['issue']
    return {'number':r['id'], 'html_url':ISSUE_URL.format(issueid=r['id'], **cfg)}


def update(number, params={}):
    nees = assignees()
    tic = issue(number, params)
    asgns = u', '.join(u'{login}({name})'.format(login=x, name=y['name']) for x, y in nees.items())
    trks = u', '.join(trackers())
    # FIXME: この部分は表示名がかぶるとエラーになる恐れがある。
    assignee = u'None'
    if tic.assign != u'None':
        cand = [x for x, y in nees.items() if y['name'] == tic.assign]
        assignee = cand[0] if len(cand) == 1 else 'Not found'
    template = ticket.template(('title', 'assign', 'tracker', 'priority', 'status', 'description', 'notes'),
                               title={'default':tic.title},
                               assign={'comment':u'Available assignee: {0}'.format(asgns),
                                       'default':assignee},
                               tracker={'comment':u'Available trackers: {0}'.format(trks),
                                        'default':u', '.join(tic.labels)},
                               priority={'comment':u'Available priorities: 3-7 (low to high)',
                                         'default':str(tic.priority_id)},
                               status={'comment':u'Available statuses: {0}'.format(u', '.join(statuses())),
                                       'default':tic.state},
                               description={'default':tic.body})
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
    data = ticket.templatetodic(s, {'title':'subject', 'priority':'proirity_id'})    
    if 'subject' not in data:
        raise ValueError('You must write a title')
    if 'assign' in data:
        data['assigned_to_id'] = assignees()[data.pop('assign')]
    if 'tracker' in data:
        data['tracker_id'] = trackers()[data.pop('tracker')]
    if 'status' in data:
        data['status_id'] = statuses()[data.pop('status')]
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
        r = getattr(requests, rtype)(url, data=data, params=params, headers=headers, auth=auth, verify=cfg['sslverify'])
    else:
        r = getattr(requests, rtype)(url, params=params, headers=headers, auth=auth, verify=cfg['sslverify'])
    if not 200 <= r.status_code < 300:
        raise requests.exceptions.HTTPError('[{0}] {1}'.format(r.status_code, r.url))
    return r


def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
