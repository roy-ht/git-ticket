#!/usr/bin/env python
# -*- coding:utf-8 -*-
def main():
    import argparse
    from gitticket import cmd
    psr = argparse.ArgumentParser(description='Welcome to git-ticket!!')
    subpsr = psr.add_subparsers(help='commands')
    
    psr_help = subpsr.add_parser('help', help='Show this message.')
    #
    psr_show = subpsr.add_parser('show', help='See detail of selected issue.')
    psr_show.add_argument('-n', '--no-comment', dest='nocomment', help='Do not retrieve and show comments of an issue')
    psr_show.add_argument('number', metavar='num', type=int, help='an issue number')
    #
    psr_list = subpsr.add_parser('list', help='Show open issues')
    psr_list.add_argument('-s', '--state', dest='state', help='select an state to display')
    psr_list.add_argument('-a', '--assignee', help='filter by assignee')
    psr_list.add_argument('-o', '--order', choices=('created', 'updated', 'comments'), default='updated',
                          help='sort order of issues.')
    #
    psr_add = subpsr.add_parser('add', help='Add an issue')
    #
    psr_close = subpsr.add_parser('close', help='Close an issue')
    psr_close.add_argument('number', metavar='num', type=int, help='an issue number')
    psr_close.add_argument('-n', '--no-comment', dest='nocomment', action='store_true', default=False,
                           help='Close a ticket without comment.')
    #
    psr_update = subpsr.add_parser('update', help='Update an issue')
    psr_update.add_argument('number', metavar='num', type=int, help='an issue number')
    #
    psr_comment = subpsr.add_parser('comment', help='Comment to an issue')
    psr_comment.add_argument('number', metavar='num', type=int, help='an issue number')
    #
    psr_github_auth = subpsr.add_parser('github-authorize', help='')
    #
    psr_bitbucket_auth = subpsr.add_parser('bitbucket-authorize', help='')
    #
    psr_help.set_defaults(cmd=lambda x: psr.print_help())
    psr_github_auth.set_defaults(cmd=cmd.github_auth)
    psr_bitbucket_auth.set_defaults(cmd=cmd.bitbucket_auth)
    psr_show.set_defaults(cmd=cmd.show)
    psr_list.set_defaults(cmd=cmd.list)
    psr_add.set_defaults(cmd=cmd.add)
    psr_close.set_defaults(cmd=cmd.close)
    psr_update.set_defaults(cmd=cmd.update)
    psr_comment.set_defaults(cmd=cmd.comment)
    opts = psr.parse_args()
    dopts = {}
    for k, v in vars(opts).items():
        if v is not None:
            dopts[k] = v if not isinstance(v, str) else v.decode('utf-8')
    cmd = dopts.pop('cmd')
    cmd(dopts)
