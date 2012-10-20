#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import json
import requests
import os
import blessings
from gitticket.config import nested_access
from gitticket import config
from gitticket import ticket
from gitticket import util

REPO = '{rurl}/'
ASSIGNEES = os.path.join(REPO, 'assignees')
STATUSES = os.path.join(REPO, 'issue_statuses.json')
TRACKERS = os.path.join(REPO, 'trackers.json')
MEMBERSHIPS = os.path.join(REPO, 'projects/{repo}/memberships.json')
USERS = os.path.join(REPO, 'users.json')
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
    params['status_id'] = params.pop('state', '*')
    avail_state = ('open', 'closed', '*')
    if params['status_id'] not in avail_state:
            raise ValueError(u'Invarid query: available status are ({0})'.format(u', '.join(avail_state)))
    params['sort'] = params.pop('order', 'updated_on:desc')
    r = _request('get', ISSUES.format(**cfg), params=params)
    tickets = [_toticket(x) for x in r['issues']]
    return tickets


def issue(number, params={}):
    cfg = config.parseconfig()
    params['include'] = u','.join(('journals', 'children', 'changesets'))
    r = _request('get', ISSUE.format(issueid=number, **cfg), params=params)['issue']
    comments = [ticket.Comment(**_parse_journal(x)) for x in reversed(r['journals'])]
    tic = _toticket(r)
    return tic, comments


def add(params={}):
    assigneedic = assignees()
    trackerdic = trackers()
    statusdic = statuses()
    comment = u'\n'.join((u'Available assignees: {0}',
                          u'Available labels: {1}',
                          u'Available priorities: 3-7 (low to high)',
                          u'Available states: {2}')
                         ).format(u', '.join(x['login'] for x in assigneedic.itervalues()),
                                  u', '.join(trackerdic.itervalues()),
                                  u', '.join(statusdic.itervalues()))
    template = ticket.template(('title', 'assignee', 'labels', 'priority', 'state', 'body'), comment=comment)
    val = util.inputwitheditor(template)
    if val == template:
        return
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    data['issue']['project_id'] = cfg['repo']
    r = _request('post', ISSUES.format(**cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'})['issue']
    return {'number':r['id'], 'html_url':ISSUE_URL.format(issueid=r['id'], **cfg)}


def update(number, params={}):
    assigneedic = assignees()
    trackerdic = trackers()
    statusdic = statuses()
    comment = u'\n'.join((u'Available assignees: {0}',
                          u'Available labels: {1}',
                          u'Available priorities: 3-7 (low to high)',
                          u'Available states: {2}')
                         ).format(u', '.join(x['login'] for x in assigneedic.itervalues()),
                                  u', '.join(trackerdic.itervalues()),
                                  u', '.join(statusdic.itervalues()))
    tic, _ = issue(number, params)
    tic.priority = tic.priority_id  # FIXME: monkey patch
    template = ticket.template(('title', 'assignee', 'labels', 'priority', 'state', 'body', 'notes'), tic, comment=comment)
    val = util.inputwitheditor(template)
    if val == template:
        return
    data = _issuedata_from_template(val)
    cfg = config.parseconfig()
    _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'})


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
    _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), headers={'content-type': 'application/json'})


def commentto(number, params={}):
    template = """# comment below here\n"""
    val = util.inputwitheditor(template)
    data = {'notes': util.rmcomment(val)}
    cfg = config.parseconfig()
    _request('put', ISSUE.format(issueid=number, **cfg), data=json.dumps(data), params=params, headers={'content-type': 'application/json'})


@util.memoize
def statuses():
    cfg = config.parseconfig()
    r = _request('get', STATUSES.format(**cfg))
    return dict((x['id'], x['name']) for x in r['issue_statuses'])


@util.memoize
def trackers():
    cfg = config.parseconfig()
    r = _request('get', TRACKERS.format(**cfg))
    return dict((x['id'], x['name']) for x in r['trackers'])


@util.memoize
def memberships():
    cfg = config.parseconfig()
    r = _request('get', MEMBERSHIPS.format(**cfg), params={'limit':100})
    return r['memberships']


@util.memoize
def users():
    cfg = config.parseconfig()
    r = _request('get', USERS.format(**cfg), params={'limit':100})
    return r['user']


@util.memoize
def user(n):
    cfg = config.parseconfig()
    r = _request('get', USER.format(userid=n, **cfg))
    return r['user']


@util.memoize
def assignees():
    r = memberships()
    nees = {}
    for member in r:
        mainrole = min(member['roles'], key=lambda x: x['id'])  # idが小さいrole程権限がでかいと仮定
        if int(mainrole['id']) < 5:
            u = user(nested_access(member, 'user.id'))
            nees[u['id']] = {'login':u['login'], 'name':u['firstname'] + u' ' + u['lastname']}
    return nees


def _toticket(d):
    cfg = config.parseconfig()
    j = dict(number = d['id'],
             state = nested_access(d, 'status.name'),
             priority = nested_access(d, 'priority.name'),
             labels = nested_access(d, 'tracker.name'),
             html_url = ISSUE_URL.format(issueid=d['id'], **cfg),
             title = d['subject'],
             body = d.get('description', None),
             creator = user(nested_access(d, 'author.id'))['login'],
             creator_fullname = nested_access(d, 'author.name'),
             assignee_fullname = nested_access(d, 'assigned_to.name'),
             created = _todatetime(d['created_on']),
             updated = _todatetime(d['updated_on']))
    if 'assigned_to' in d:
        j['assignee'] = user(nested_access(d, 'assigned_to.id'))['login']
    tic = ticket.Ticket(**j)
    setattr(tic, 'priority_id', nested_access(d, 'priority.id'))  # Redmineにpriorityを取得するAPIがないためあとで参照しなければならない
    return tic


def _issuedata_from_template(s):
    data = ticket.templatetodic(s, {'title':'subject', 'priority':'priority_id', 'body':'description'})
    if 'subject' not in data:
        raise ValueError('You must write a title')
    if 'assignee' in data:
        for k, v in assignees().iteritems():
            if data['assignee'] == v['login']:
                data['assigned_to_id'] = k
                break
        else:
            raise ValueError(u"assignee {0} not found".format(data['assignee']))
    if 'priority_id' in data:
        data['priority_id'] = int(data['priority_id'])
    if 'labels' in data:
        for tid, name in trackers().iteritems():
            if data['labels'] == name:
                data['tracker_id'] = tid
                break
        else:
            raise ValueError(u"tracker {0} not found".format(data['tracker']))
    if 'state' in data:
        for sid, name in statuses().iteritems():
            if data['state'] == name:
                data['status_id'] = sid
                break
        else:
            raise ValueError(u"state {0} not found".format(data['state']))
    return {'issue': data}


def _parse_journal(j):
    term = blessings.Terminal()
    r = {}
    r['number'] = j['id']
    r['creator'] = nested_access(j, 'user.name')
    r['created'] = _todatetime(j['created_on'])
    r['body'] = u''
    # make body
    if 'notes' in j:
        r['body'] += j['notes'] + u'\n'
    r['body'] += u'\n'.join(u'{term.red}*{term.normal} ' + _parse_detail(x) for x in j['details'])
    r['body'] = r['body'].strip()
    r['body'] = r['body'].format(term = term)
    return r

def _parse_detail(j):
    if 'old_value' in j and 'new_value' in j:
        if j['name'] == 'description':
            return u'Update {{term.bold}}{name}{{term.normal}}'.format(**j)
        return u'Change {{term.bold}}{name}{{term.normal}} from {{term.cyan}}{old_value}{{term.normal}} to {{term.cyan}}{new_value}{{term.normal}}'.format(**j)
    elif 'old_value' in j:
        return u'Delete {{term.bold}}{name}{{term.normal}}: {{term.cyan}}{old_value}{{term.normal}}'.format(**j)
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
    return r.json


def _todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('Z', 'UTC'), DATEFMT)
