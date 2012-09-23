# -*- coding:utf-8 -*-

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
    
