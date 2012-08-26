#!/usr/bin/env python
# -*- coding:utf-8 -*-

import json
import urlparse
import requests

BASEURL = 'https://api.github.com'
AUTH = urlparse.urljoin(BASEURL, 'authorizations')
REPO = urlparse.urljoin(BASEURL, 'repos/{name}/{repo}')
ASSIGNEES = urlparse.urljoin(REPO, 'assignees')
ISSUES = urlparse.urljoin(REPO, 'issues')
ISSUE = urlparse.urljoin(ISSUES, '{issueid}')
ISSUE_COMMENTS = urlparse.urljoin(ISSUE, 'comments')
ISSUE_COMMENT = urlparse.urljoin(ISSUE_COMMENTS, '{commentid}')
ISSUES_EVENT = urlparse.urljoin(ISSUES, 'events')
ISSUE_EVENT = urlparse.urljoin(ISSUE, 'events')
LABELS = urlparse.urljoin(REPO, 'labels')
LABEL = urlparse.urljoin(LABELS, '{label}')
ISSUE_LABELS = urlparse.urljoin(ISSUE, 'labels')
ISSUE_LABEL = urlparse.urljoin(ISSUE_LABELS, '{label}')
MILESTONES = urlparse.urljoin(REPO, 'milestones')
MILESTONE = urlparse.urljoin(MILESTONES, '{milestoneid}')

def authorize(name, pswd):
    r = requests.post(AUTH, data=json.dumps({'scopes':['repo'], 'note':'git-ticket'}), auth=(name, pswd))
    return r.json

def issues(cfg):
    u"""name, repoが含まれる辞書"""
    r = requests.get(ISSUES.format(**cfg))
    return r.json
    
