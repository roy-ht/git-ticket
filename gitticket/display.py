#!/usr/bin/env python
# -*- coding:utf-8 -*-

from gitticket.config import nested_access
import blessings

def json(jsonlist, stgs):
    u"""stgに入っている情報を元にフォーマットして返す
    stgはリストで、その順番でコラムを作って返す
    """
    term = blessings.Terminal()
    # itemは縦に詰まって行く。列ベースでフォーマットする
    columns = [[x.get('name', x['key'])] for x in stgs]
    for j in jsonlist:
        for idx, stg in enumerate(stgs):
            columns[idx].append(str(nested_access(j, stg['key'])))
    # すべての要素が入ったのでフォーマット
    widths = [max(map(len, x)) + 2 for x in columns]
    totalwidth = sum(widths)
    if totalwidth > term.width:
        for idx, stg in enumerate(stgs):
            if stg.get('trunc', False):
                # headerの文字数よりは小さくならない
                widths[idx] = max(len(columns[idx][0]) + 2, totalwidth - term.width)
                for i, content in enumerate(columns[idx]):
                    if len(content) > widths[idx]:
                        columns[idx][i] = columns[idx][i][:widths[idx] - 2] + '..'
                break
    # width formatting
    width_formats = ['{{:<{0}}}'.format(x) for x in widths]
    txt = ''
    for i in range(len(jsonlist) + 1):
        for ci, column in enumerate(columns):
            txt += width_formats[ci].format(column[i])
        txt += '\n'
        if i == 0:
            txt += '-' * sum(widths) + '\n'
    return txt
