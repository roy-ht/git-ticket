#!/usr/bin/env python
# -*- coding:utf-8 -*-
import datetime
import json
import os
import requests
from rauth.service import OAuth1Service
from rauth.hook import OAuth1Hook
from gitticket.config import nested_access
from gitticket import config
from gitticket import ticket
from gitticket import util

CONSUMER_KEY = 'Bq7A3PXEdgGeWy94VA'
CONSUMER_SECRET = 'jWvtdn3tR4Q9vGn3USbQJZZHAnd7neXM'

OAUTH_REQUEST = 'https://bitbucket.org/api/1.0/oauth/request_token'
OAUTH_AUTH = 'https://bitbucket.org/api/1.0/oauth/authenticate'
OAUTH_ACCESS = 'https://bitbucket.org/api/1.0/oauth/access_token'

BASEURL = 'https://api.bitbucket.org/1.0'
ISSUEURL = 'https://bitbucket.org/{name}/{repo}/issue/{issueid}'
REPO = os.path.join(BASEURL, 'repositories/{name}/{repo}')
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

DATEFMT = "%Y-%m-%d %H:%M:%S%Z"

def authorize():
    service = OAuth1Service(name='bitbucket', consumer_key=CONSUMER_KEY, consumer_secret=CONSUMER_SECRET,
                         request_token_url=OAUTH_REQUEST,
                         access_token_url=OAUTH_ACCESS,
                         authorize_url=OAUTH_AUTH)
    rtoken, rtokensecret = service.get_request_token(method='GET')
    auth_url = service.get_authorize_url(rtoken)
    print "Visit this url and copy&paste your PIN.\n{0}".format(auth_url)
    pin = raw_input('Please enter your PIN:')
    r = service.get_access_token('POST', request_token=rtoken, request_token_secret=rtokensecret,
                                 data={'oauth_verifier': pin})
    content = r.content
    return content['oauth_token'], content['oauth_token_secret']


def issues(params={}):
    cfg = config.parseconfig()
    url = ISSUES.format(**cfg)
    if 'limit' not in params:
        params['limit'] = 50
    if 'state' in params:
        avail_states = ('new', 'open', 'resolved', 'on hold', 'invalid', 'duplicate', 'wontfix')
        if params['state'] not in avail_states:
            raise ValueError('Invarid query: available state are ')
        params['status'] = params.pop('state')
    if 'assignee' in params:
        params['responsible'] = params.pop('assignee')
    params['sort'] = params.pop('order', 'utc_last_updated')
    if params['sort'] == 'updated':
        params['sort'] = 'utc_last_updated'
    r = _request('get', url, params=params).json
    tickets = []
    for j in r['issues']:
        create = todatetime(j['utc_created_on'])
        update = todatetime(j['utc_last_updated'])
        t = ticket.Ticket({'id':j['local_id'],
                           'state':j['status'],
                           'title':j['title'],
                           'body':j['content'],
                           'created_by':nested_access(j, 'reported_by.username'),
                           'assign':nested_access(j, 'responsible.username'),
                           'commentnum':j['comment_count'],
                           'create':create,
                           'update':update})
        tickets.append(t)
    return tickets
    
def issue(number, params={}):
    cfg = config.parseconfig()
    j = _request('get', ISSUE.format(issueid=number, **cfg), params=params).json
    cj = _request('get', ISSUE_COMMENTS.format(issueid=number, **cfg), {'limit':50}).json
    cj = [x for x in cj if x['content'] is not None]
    # commentは特殊。statusの変更がコメント化され、APIからは補足できないので
    # その手のコメントは削る必要がある。
    comments = [ticket.Comment({'id':x['comment_id'],
                                'body':x['content'] or u'',
                                'created_by':nested_access(x, 'author_info.username'),
                                'create':todatetime(x['utc_created_on']),
                                'update':todatetime(x['utc_updated_on']),
                                }) for x in cj]
    tic = ticket.Ticket({'id':j['local_id'],
                         'state':j['status'],
                         'title':j['title'],
                         'body':j['content'],
                         'labels':[nested_access(j, 'metadata.kind')],
                         'milestone':nested_access(j, 'metadata.milestone'),
                         'created_by':nested_access(j, 'reported_by.username'),
                         'assign':nested_access(j, 'responsible.username'),
                         'commentnum':j['comment_count'],
                         'create':todatetime(j['utc_created_on']),
                         'update':todatetime(j['utc_last_updated']),
                         'comments':comments,
                         })
    return tic


def add(params={}):
    template = """Title: 
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
    template = """Title: {tic_title}
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
    session = requests
    if cfg['btoken'] and cfg['btoken_secret']:
        oauth = OAuth1Hook(CONSUMER_KEY, CONSUMER_SECRET,
                           access_token=cfg['btoken'], access_token_secret=cfg['btoken_secret'])
        session = requests.session(hooks={'pre_request': oauth})
    if data:
        return getattr(session, rtype)(url, data=data, params=params)
    else:
        return getattr(session, rtype)(url, params=params)

    
def todatetime(dstr):
    if isinstance(dstr, basestring):
        return datetime.datetime.strptime(dstr.replace('+00:00', 'UTC'), DATEFMT)
