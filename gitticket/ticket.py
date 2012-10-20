# -*- coding:utf-8 -*-

from datetime import datetime
import time
import calendar
from gitticket import util
import blessings


g_term = blessings.Terminal()

def _decorate(s, arg):
    u"""特殊な属性を使って変数を装飾する
    ^: 前に文字を付加
    $: 後ろに文字を付加
    b: blessingsのflavor
    l, r, c: 左寄せ、右寄せ、中央寄せ
    s: スペースを周りにつける
    """
    if arg.startswith('^'):
        p = arg[1:]
        s = u'{pre}{0}'.format(s, pre={'b':'[', 'e':']'}.get(p, p))
    elif arg.startswith('$'):
        p = arg[1:]
        s = u'{0}{post}'.format(s, post={'b':'[', 'e':']'}.get(p, p))
    elif arg.startswith('b'):
        s = getattr(g_term, arg[1:])(u'{0}'.format(s))
    elif arg.startswith(('l', 'r', 'c')):
        s = u'{0:{dir}{num}}'.format(s, dir={'l':'<', 'r':'>', 'c':'^'}[arg[0]], num=int(arg[1:]))
    elif arg.startswith('s'):
        s = u' {0}'.format(s)
    return s


class Ticket(object):
    _list_format = u"{s[number__^#_bred]} ({s[updated__byellow]}) [{s[state___bcyan]}] {s.title} - {s[assignee__bmagenta]}"
    _show_format = u'''
    {s[number__^#_bred]} [{s[state__bcyan]}]{s[priority__bblue_^b_$e]}{s[labels__bgreen_^b_$e]}{s[milestone__bcyan_^b_$e]}{s[version__bblue_^b_$e]}{s[component__bgreen_^b_$e]} {s[pull_request__^<_$>_bred]}{s.title}
    Created by{s[creator__bmagenta_s]}{s[creator_fullname__^(_$)_bmagenta_s]} at {s[created__byellow]}, updated at {s[updated__byellow]}
   {s[assignee__bmagenta_s]}{s[assignee_fullname__^(_$)_bmagenta_s]} is assigned
    link: {s[html_url]}

{s[body]}
'''
    def __init__(self, **dct):
        attributes = ['html_url', 'number', 'state', 'title', 'body', 'creator', 'creator_fullname', 'labels', 'assignee', 'assignee_fullname',
                      'milestone', 'comments', 'pull_request', 'closed', 'created', 'updated', 'priority', 'version', 'component']
        for attr in attributes:
            if attr in dct and dct[attr] is not None:
                setattr(self, attr, dct[attr])
        self._init()  # reformatting

    def __getitem__(self, name):
        if not isinstance(name, basestring):
            raise TypeError('Ticket indices must be str, not integers')
        if name.count('__') != 1:
            try:
                return getattr(self, name)
            except AttributeError:
                return u''
        l = name.split(u'__')
        key, args = l
        args = args.split(u'_')
        try:
            r = getattr(self, key)
        except AttributeError:
            return u''
        for arg in args:
            r = _decorate(r, arg)
        return r


    def _init(self):
        if not hasattr(self, 'assignee'):
            self.assignee = u'No one'
        for attr in ('created', 'updated', 'closed'):
            if hasattr(self, attr):
                setattr(self, attr, humandate(getattr(self, attr)))
        if hasattr(self, 'labels'):
            self._rawlabels = self.labels
            delattr(self, 'labels')
            if self._rawlabels:
                self.labels = u', '.join(self._rawlabels) if isinstance(self._rawlabels, (list, tuple)) else self._rawlabels

    def format(self, template=None):
        if template is None:
            template = Ticket._list_format
        # s == self, t == term
        return template.format(s=self, t=g_term, hline=horline(), hhline=horline(u'='))


class Comment(object):
    _format = u'''Comment {s[number__^#_bgreen]} {s[created__bmagenta]} at {s[updated__byellow]}
{hline}
{s.body}
'''
    def __init__(self, **dct):
        attributes = ['number', 'html_url', 'body', 'creator', 'creator_fullname', 'created', 'updated']
        for attr in attributes:
            if attr in dct and dct[attr] is not None:
                setattr(self, attr, dct[attr])
        self._init()

    def __getitem__(self, name):
        if name.count('__') != 1:
            return getattr(self, name)
        l = name.split(u'__')
        key, args = l
        args = args.split(u'_')
        try:
            r = getattr(self, key)
        except AttributeError:
            return u''
        for arg in args:
            r = _decorate(r, arg)
        return r

    def _init(self):
        for attr in ('created', 'updated'):
            if hasattr(self, attr):
                setattr(self, attr, humandate(getattr(self, attr)))
        if not hasattr(self, 'updated'):
            self.updated = self.created
        self.body = self.body.rstrip()

    def format(self, template=None):
        term = blessings.Terminal()
        if template is None:
            template = Comment._format
        return template.format(s=self, t=term, hline=horline(), hhline=horline(u'='))


def utctolocal(dt):
    u"""convert UTC+0000 datetime.datetime to local datetime.datetime
    """
    secs = calendar.timegm(dt.timetuple())
    return datetime(*time.localtime(secs)[:6])


def humandate(dt):
    if not dt:
        return 'not yet'
    dt = utctolocal(dt)
    now = datetime.now()
    delta = now - dt
    if delta.days >= 365:
        year = delta.days // 365
        return '{0} year{1} ago'.format(year, 's' if year > 1 else '')
    elif delta.days > 30 and now.month != dt.month:
        mon = now.month - dt.month + (0 if now.month > dt.month else 12)
        return '{0} month{1} ago'.format(mon, 's' if mon > 1 else '')
    elif delta.days > 0:
        return '{0} day{1} ago'.format(delta.days, 's' if delta.days > 1 else '')
    elif delta.seconds >= 3600:
        hour = delta.seconds // 3600
        return '{0} hour{1} ago'.format(hour, 's' if hour > 1 else '')
    elif delta.seconds >= 60:
        minute = delta.seconds // 60
        return '{0} minute{1} ago'.format(minute, 's' if minute > 1 else '')
    elif delta.seconds > 0:
        return '{0} second{1} ago'.format(delta.seconds, 's' if delta.seconds > 1 else '')
    else:
        return 'just now'


def template(disps, tic=None, comment=None):
    u"""dispsに作る項目名、ticは既存のチケット、commentは付加コメント。
    ticを与えると、入力フォームにticの内容を予め入力する。
    """
    names = ('number', 'state', 'title', 'creator', 'creator_fullname', 'labels', 'assignee', 'assignee_fullname',
             'milestone', 'milestone_id', 'priority', 'version', 'component', 'body', 'notes')
    t = u''
    # preset header
    if tic is not None:
        fstr = u'## ticket #{t.number} created by {t.creator}'
        if hasattr(tic, 'creator_fullname'):
            fstr += u' ({t.creator_fullname})'
        t += fstr.format(t=tic) + u'\n'
    # comments
    t += u'\n'.join(u'## {0}'.format(x) for x in comment.split('\n')) + u'\n'
    t += u'\n'
    for name in names:
        if name not in disps:
            continue
        t += u':{0}: '.format(name)
        if name in ('body', 'notes'):
            t += u'\n'
        if tic is not None and hasattr(tic, name):
            t += u'{0}'.format(getattr(tic, name))
        t += u'\n'
            
    return t


def templatetodic(s, mapping={}):
    s = util.rmcomment(s)
    lines = s.split(u'\n')
    d = {}
    name = None
    for line in lines:
        content = util.regex_extract(ur'^:(.+?):(.*)', line)
        if content:
            name = content[0].replace(u' ', u'_').lower()
            name = mapping.get(name, name)
            d[name] = content[1].strip(u' ')
        elif name is not None: # 継続行とみなす
            d[name] += u'\n' + line.rstrip(u' ')
    for k, v in d.items():
        d[k] = v.strip('\n')
        if len(d[k]) == 0: # stringであることを暗に
            del d[k]
    return d
    

def termwidth():
    term = blessings.Terminal()
    if not term.width:
        return 80
    return term.width


def horline(linestr=u'-'):
    return linestr * termwidth()
