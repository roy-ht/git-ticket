# -*- coding:utf-8 -*-

from datetime import datetime
import time
import calendar
from gitticket import util

class Comment(object):
    def __init__(self, dct):
        self.id = dct['id']
        self.body = dct['body']
        self.created_by = dct['created_by']
        self.create = dct['create'] # datetime
        # option value
        self.update = dct.get('update', None) # datetime

        self._format()

    def __getitem__(self, name):
        return getattr(self, name)

    def _format(self):
        self.id = str(self.id)
        self.create = humandate(self.create)
        if self.update:
            self.update = humandate(self.update)
        

class Ticket(object):
    def __init__(self, dct):
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
        self.c = dct.get('commentnum', None)
        self.closed = dct.get('closed', None) # datetime
        self.labels = dct.get('labels', None) or []
        self.milestone = dct.get('milestone', None) or {}
        self.closed_by = dct.get('closed_by', None)
        self.comments = dct.get('comments', None)
        
        self._format()

    def __getitem__(self, name):
        return getattr(self, name)

    def _format(self):
        self.id = str(self.id)
        if not self.assign:
            self.assign = 'None'
        if self.c:
            self.c = str(self.c)
        self.create = humandate(self.create)
        self.update = humandate(self.update)
        self.closed = humandate(self.closed)
        if not self.closed_by:
            self.closed_by = 'None'
        # self.milestone = str(self.milestone)

    def tostr(self, name, width):
        tgt = getattr(self, name)
        if util.strwidth(tgt) > width:
            while util.strwidth(tgt) + 2 > width:
                tgt = tgt[:-1]
            tgt += u'..'
        return tgt + u' ' * (width - util.strwidth(tgt))
        
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

