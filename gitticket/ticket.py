# -*- coding:utf-8 -*-

from datetime import datetime
import time
import calendar
from gitticket import util
import blessings


g_term = blessings.Terminal()


class Comment(object):
    _format = u'''Comment {t.green}#{s.id}{t.normal} {t.magenta}{s.created_by}{t.normal} at {t.yellow}{s.update}{t.normal}
{hline}
{s.body}
'''
    def __init__(self, dct):
        self.id = dct['id']
        self.body = dct['body']
        self.created_by = dct['created_by']
        self.create = dct['create'] # datetime
        # option value
        self.update = dct.get('update', None) # datetime

        self._init()

    def __getitem__(self, name):
        return getattr(self, name)

    def _init(self):
        self.id = str(self.id)
        self.create = humandate(self.create)
        if self.update:
            self.update = humandate(self.update)
        else:
            self.update = self.create
        self.body = self.body.rstrip()

    def format(self, template=None):
        term = blessings.Terminal()
        if template is None:
            template = Comment._format
            
        return template.format(s=self, t=term, hline=horline(), hhline=horline(u'='))
        

class Ticket(object):
    _list_format = u"{s[state___bcyan_^b_$e_l23]} {s[id__^#_bred]} ({s[update__byellow]}) {s.title} - {s[assign__bmagenta]}"
    _show_format = u'''
    [{s[state__bcyan]}]{s[labels__bgreen_^b_$e]} {s.title}
    created by {s[assign__bmagenta]} at {s[create__byellow]}, updated at {s[update__yellow]}

{s.body}
'''
    def __init__(self, **dct):
        self.id = dct['id']
        self.state = dct['state']
        self.title = dct['title']
        self.created_by = dct['created_by']
        self.assign = dct['assign']
        self.create = dct['create'] # datetime
        self.update = dct['update'] # datetime
        self.body = dct['body'] or u''
        # オプション
        self.priority = dct.get('priority', None)
        self.commentnum = dct.get('commentnum', None)
        self.closed = dct.get('closed', None) # datetime
        self._rawlabels = dct.get('labels', None) or []
        self.milestone = dct.get('milestone', None) or {} # TODO: milestoneをもっと詳細化
        self.closed_by = dct.get('closed_by', None)
        self._init()  # reformatting

    def __getitem__(self, name):
        if name.count('__') != 1:
            return getattr(self, name)
        l = name.split(u'__')
        key, args = l
        args = args.split(u'_')
        r = self[key]
        for arg in args:
                ## r1, l5, c24 等でアライメント
            if arg.startswith('^'):
                p = arg[1:]
                r = u'{pre}{0}'.format(r, pre={'b':'[', 'e':']'}.get(p, p))
            elif arg.startswith('$'):
                p = arg[1:]
                r = u'{0}{post}'.format(r, post={'b':'[', 'e':']'}.get(p, p))
            elif arg.startswith('b'):
                r = getattr(g_term, arg[1:])(r)
            elif arg.startswith(('l', 'r', 'c')):
                r = u'{0:{dir}{num}}'.format(r, dir={'l':'<', 'r':'>', 'c':'^'}[arg[0]], num=int(arg[1:]))
        return r


    def _init(self):
        self.id = str(self.id)
        if not self.assign:
            self.assign = 'None'
        if self.commentnum is not None:
            self.commentnum = str(self.commentnum)
        self.create = humandate(self.create)
        self.update = humandate(self.update)
        self.closed = humandate(self.closed)
        if not self.closed_by:
            self.closed_by = 'None'
        self.labels = u', '.join(self._rawlabels)
        # self.milestone = str(self.milestone)

    def format(self, template=None):
        if template is None:
            template = Ticket._list_format
        # s == self, t == term
        return template.format(s=self, t=g_term, hline=horline(), hhline=horline(u'='))

        
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


def template(disps, **kwargs):
    u"""dispsに作る項目名、kwargs[name]['default']にデフォルトで表示する項目、kwargs[name]['comment']にコメント表示する文字列、
    kwargs[name]['disp']に置き換える項目名を入れる
    <name> title, assign, labels, milestone
    """
    names = ('title', 'assign', 'labels', 'milestone', 'tracker', 'priority', 'status', 'description', 'notes')
    t = u''
    for name in names:
        if name in kwargs and 'comment' in kwargs[name]:
            t += u'## {0}\n'.format(kwargs[name]['comment'])
    for name in names:
        if name not in disps:
            continue
        disp = name
        default = u''
        if name in kwargs:
            disp = kwargs[name].get('disp', disp)
            default = kwargs[name].get('default', default)
        t += u':{0}: '.format(disp)
        if name in ('description', 'notes'):
            t += u'\n'
        t += default + u'\n'
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
        else: # 継続行とみなす
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
