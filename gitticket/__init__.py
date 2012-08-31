#!/usr/bin/env python
# -*- coding:utf-8 -*-
def main():
    import argparse
    from gitticket import cmd
    psr = argparse.ArgumentParser(description='Welcome to git-ticket!!')
    subpsr = psr.add_subparsers(help='commands')
    psr_help = subpsr.add_parser('help', help='Show this message.')
    psr_show = subpsr.add_parser('show', help='')
    psr_show.add_argument('number', metavar='num', type=int, help='an issue number')    
    psr_list = subpsr.add_parser('list', help='')
    psr_mine = subpsr.add_parser('mine', help='')
    psr_add = subpsr.add_parser('add', help='')
    psr_close = subpsr.add_parser('close', help='')
    psr_update = subpsr.add_parser('update', help='')
    psr_local = subpsr.add_parser('local', help='')
    psr_github_auth = subpsr.add_parser('github-authorize', help='')
    #
    psr_help.set_defaults(cmd=lambda x: psr.print_help())
    psr_github_auth.set_defaults(cmd=cmd.github_auth)
    psr_show.set_defaults(cmd=cmd.show)
    psr_list.set_defaults(cmd=cmd.list)
    psr_mine.set_defaults(cmd=cmd.mine)
    psr_add.set_defaults(cmd=cmd.add)
    psr_close.set_defaults(cmd=cmd.close)
    psr_update.set_defaults(cmd=cmd.update)
    psr_local.set_defaults(cmd=cmd.local)
    opts = psr.parse_args()
    opts.cmd(vars(opts))
