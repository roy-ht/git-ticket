# -*- coding:utf-8 -*-

import pytest
from gitticket import config


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


def mock_git_noservice():
    return {}


def mock_git_norepo():
    return {'ticket.name': 'user',
            'ticket.repo': None,
            'ticket.service': 'github'}


def mock_git_noname():
    return {'ticket.name': None,
            'ticket.repo': 'repo',
            'ticket.service': 'github'}


## サービスが無い -> repo名の推測に失敗 -> nameが無い


def test_noservice(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git_noservice)
    monkeypatch.setattr(config, 'guess_service', lambda: None)
    with pytest.raises(ValueError) as excinfo:
        config.parseconfig()
    assert excinfo.value.message == "Can't guess a service. Try 'git config ticket.service [github|bitbucket|redmine]'"


def test_norepo(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git_norepo)
    monkeypatch.setattr(config, 'guess_repo_name', lambda: None)
    with pytest.raises(ValueError) as excinfo:
        config.parseconfig()
    assert excinfo.value.message == "Can't guess a repository name. Try 'git config ticket.repo <repository_name>'"


def test_noname(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git_noname)
    with pytest.raises(ValueError) as excinfo:
        config.parseconfig()
    assert excinfo.value.message == "You must set your account name to ticket.name or user.name. Try 'git config ticket.name <your_account_name>'"


def test_parseconfig_success(monkeypatch):
    monkeypatch.setattr(config, 'git', mock_git)
    cfg = config.parseconfig()
    assert cfg['name'] == 'user'
    assert cfg['repo'] == 'testrepo'
    assert cfg['service_name'] == 'github'
    import gitticket.github
    assert cfg['service'] is gitticket.github
    assert cfg['sslverify'] == True
    assert cfg['format_list'] == 'list_format'
    assert cfg['format_show'] == 'show_format'
    assert cfg['format_comment'] == 'comment_format'
    assert cfg['gtoken'] == 'github_token'
    assert cfg['btoken'] == 'bitbucket_token'
    assert cfg['btoken_secret'] == 'bitbucket_token_secret'
    assert cfg['rurl'] == 'http://example.com'
    assert cfg['rtoken'] == 'redmine_token'
