# -*- coding:utf-8 -*-

from datetime import datetime
import time
import calendar
from gitticket import util

class Ticket(object):
    def __init__(self, dct):
        self.id = dct['id']
        self.state = dct['state']
        self.title = dct['title']
        self.assign = dct['assign']
        self.c = dct['commentnum']
        self.create = dct['create'] # datetime
        self.update = dct['update'] # datetime
        self.closed = dct['closed'] # datetime
        
        self._format()

    def __getitem__(self, name):
        return getattr(self, name)

    def _format(self):
        self.id = str(self.id)
        if not self.assign:
            self.assign = 'None'
        self.c = str(self.c)
        self.create = self._date(self.create)
        self.update = self._date(self.update)
        self.closed = self._date(self.closed)

    def _date(self, dt):
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
            return '{0} minute{1} ago'.format(delta.seconds, 's' if delta.seconds > 1 else '')
        else:
            return 'just now'

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
        return '{0} minute{1} ago'.format(delta.seconds, 's' if delta.seconds > 1 else '')
    else:
        return 'just now'

