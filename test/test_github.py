# -*- coding:utf-8 -*-

import pytest
from gitticket import github
from gitticket import ticket
from gitticket import config
from gitticket import util


def mock_git():
    return {'ticket.name': 'user',
            'ticket.repo': 'testrepo',
            'ticket.service': 'github',
            'ticket.format.list': 'list_format',
            'ticket.format.show': 'show_format',
            'ticket.format.comment': 'comment_format',
            'ticket.github.token': 'github_token',
            'ticket.bitbucket.token': 'bitbucket_token',
            'ticket.bitbucket.token-secret': 'bitbucket_token_secret',
            'ticket.redmine.url': 'http://example.com/',
            'ticket.redmine.token': 'redmine_token',
            'http.sslVerify': 'true'}



def mock_request_list(*args, **kwargs):
    return  [{u'body': u'body',
             u'title': u"title",
             u'url': u'https://api.github.com/repos/name/repo/issues/1',
             u'pull_request': {u'diff_url': None, u'html_url': None, u'patch_url': None},
             u'labels': [{u'color': u'fc2929', u'url': u'https://api.github.com/repos/name/repo/labels/bug', u'name': u'bug'}],
             u'updated_at': u'2012-09-15T00:23:14Z',
             u'html_url': u'https://github.com/name/repo/issues/1',
             u'number': 1,
             u'assignee': {u'url': u'https://api.github.com/users/name', u'login': u'name', u'avatar_url': u'http://example.com', u'id': 1, u'gravatar_id': u''},
             u'state': u'closed',
             u'user': {u'url': u'https://api.github.com/users/name', u'login': u'name', u'avatar_url': u'https://example.com', u'id': 1, u'gravatar_id': u''},
             u'milestone': None,
              u'id': 0,
             u'closed_at': u'2012-09-15T00:23:14Z',
             u'created_at': u'2012-09-15T00:19:10Z',
             u'comments': 0}]


def mock_request_assignees(*args, **kwargs):
    return  [{u'login': u'name1'},
             {u'login': u'name2'}]


def mock_request_show(*args, **kwargs):
    return  {u'body': u'body',
             u'title': u"title",
             u'url': u'https://api.github.com/repos/name/repo/issues/1',
             u'pull_request': {u'diff_url': None, u'html_url': None, u'patch_url': None},
             u'labels': [{u'color': u'fc2929', u'url': u'https://api.github.com/repos/name/repo/labels/bug', u'name': u'bug'}],
             u'updated_at': u'2012-09-15T00:23:14Z',
             u'html_url': u'https://github.com/name/repo/issues/1',
             u'number': 1,
             u'assignee': {u'url': u'https://api.github.com/users/name', u'login': u'name', u'avatar_url': u'http://example.com', u'id': 1, u'gravatar_id': u''},
             u'state': u'closed',
             u'user': {u'url': u'https://api.github.com/users/name', u'login': u'name', u'avatar_url': u'https://example.com', u'id': 1, u'gravatar_id': u''},
             u'milestone': None,
             u'id': 0,
             u'closed_at': u'2012-09-15T00:23:14Z',
             u'created_at': u'2012-09-15T00:19:10Z',
             u'comments': 0}


def mock_request_comments(*args, **kwargs):
    return [{"id": 1,
             "url": "https://api.github.com/repos/octocat/Hello-World/issues/comments/1",
             "body": "Me too",
             "user": {
                "login": "octocat",
                "id": 1,
                "avatar_url": "https://github.com/images/error/octocat_happy.gif",
                "gravatar_id": "somehexcode",
                "url": "https://api.github.com/users/octocat"
                },
             "created_at": "2011-04-14T16:00:49Z",
             "updated_at": "2011-04-14T16:00:49Z"
             }]


def test_list(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(github, '_request', mock_request_list)
    r = github.issues()
    assert len(r) == 1
    tic = r[0]
    assert tic.title == u'title'
    assert tic.body == u'body'
    assert tic.assignee == u'name'


def test_show(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(github, '_request', mock_request_show)
    tic = github.issue(0)
    assert isinstance(tic, ticket.Ticket)
    assert tic.title == u'title'
    assert tic.body == u'body'
    assert tic.assignee == u'name'


def test_comments(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(github, '_request', mock_request_comments)
    r = github.comments(0)
    assert len(r) == 1
    com = r[0]
    assert com.body == u'Me too'
    assert com.creator == u'octocat'


def mock_editor(template):
    return u'''## Available assignees: bug, duplicate, enhancement, invalid, question, wontfix
## Available labels: aflc
:title: test issue
:labels: bug
:assignee: name
:milestone_id: 
:body: this is a body.
'''

def mock_labels():
    return ['bug', 'duplicate', 'enhancement', 'invalid', 'question', 'wontfix']


def mock_assignees():
    return ['name']


def test_add(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(util, 'inputwitheditor', mock_editor)
    monkeypatch.setattr(github, '_request', mock_request_show)
    monkeypatch.setattr(github, 'labels', mock_labels)
    monkeypatch.setattr(github, 'assignees', mock_assignees)
    r = github.add()
    assert r['html_url'] == u'https://github.com/name/repo/issues/1'
    assert r['number'] == 1


def test_update(monkeypatch):
    """TODO: Test with the content"""
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(util, 'inputwitheditor', mock_editor)
    monkeypatch.setattr(github, '_request', mock_request_show)
    monkeypatch.setattr(github, 'labels', mock_labels)
    monkeypatch.setattr(github, 'assignees', mock_assignees)
    github.update(1)


def test_changestate(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(github, '_request', mock_request_list)
    github.changestate(1, 'open')
    github.changestate(1, 'closed')
    with pytest.raises(ValueError):
        github.changestate(1, 'close')

def test_commentto(monkeypatch):
    """TODO: Test with the content"""
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(util, 'inputwitheditor', mock_editor)
    monkeypatch.setattr(github, '_request', mock_request_show)
    github.commentto(1)


def test_assignees(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    monkeypatch.setattr(github, '_request', mock_request_assignees)
    r = github.assignees()
    assert len(r) == 2
    assert r[0] == 'name1'
    assert r[1] == 'name2'


def test_labels(monkeypatch):
    assert False
