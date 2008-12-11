import sys

sys.path.append('/home/sys/irc/boom.bot/plugins')

import datetime
from django.conf import settings
from djangobot.nag.models import Event
from dateutil.parser import parse as du_parse
from pyparsing import Word, Optional, OneOrMore, alphas, \
    alphanums, nums, oneOf, printables, SkipTo

# create table event (
#   id int, audience text, occur_time timestamp, note text 
#   );


def naglist():
    d = datetime.datetime.now()
    d0 = d.replace(second=0, microsecond=0)
    m = (d.minute+1)%60
    d1 = d.replace(minute=m,second=0, microsecond=0)
    return Event.objects.filter(time__gte=d0, time__lt=d1)

def getnag(id):
    try:
        return Event.objects.get(pk=id)
    except:
        return None

def listnags(nick):
    try:
        return Event.objects.filter(audience__icontains=nick)
    except:
        return []

class NagEvent:
    def __init__(self, id=None):
        self.error = ''
        if id:
            self.event = Event.objects.get(pk=id)
        else:
            self.event = Event()

    def is_complete(self):
        if self.event.audience and self.event.time and self.event.action:
            return True
        else:
            if not self.event.audience:
                self.error += ' audience is blank'
            if not self.event.time:
                self.error += ' time is blank'
            if not self.event.action:
                self.error += ' action is blank'
            return False

    def __str__(self):
        return "REMIND %s AT %s %s" % (
            self.event.audience,
            self.event.time,
            self.event.action, 
            )

    def save(self):
        self.event.save()


class NagParser:
    def __init__(self, nick):
        self._nick = nick
        self._grammar = list()
        self._context = dict()
        self._what_x()  # MUST GO FIRST
        self._when()
        self._who()
        self._snooze()
        self._with()
        self._snooze_expires()
        self._with()
        self._what()  # MUST GO LAST
        self._e = None

    def parse(self,s):
        """returns a NagEvent object from the parsed code"""
        self._e = NagEvent()
        for g in self._grammar:
            s = g.transformString(s)
        return self._e

    def __str__(self):
        return " ".join(["%s %s "%(k,self._context[k]) for k in self._context.keys()])

    def _when(self): 
        gWhen = Optional("on" + Word(alphas)) + ("at" + Word(nums) + Optional(':' + Word(nums)) + oneOf("am pm AM PM Am Pm aM pM")) | ("in" + Word(nums) + oneOf("m M h H d D"))
        def parseAction(s,l,t):
            if t[0] in ('on', 'at'):
                if t[0] == "on":
                    datestr = "%s at %s" % (t[1], "".join(t[3:]))
                else:
                    datestr = "".join(t[1:])
                self._e.event.time = du_parse(datestr)
            else:
                now = datetime.datetime.now()
                if t[-1] in 'mM':
                    self._e.event.time = now + datetime.timedelta(minutes=int(t[1]))
                elif t[-1] in 'hH':
                    self._e.event.time = now + datetime.timedelta(hours=int(t[1]))
                elif t[-1] in 'dD':
                    self._e.event.time = now + datetime.timedelta(days=int(t[1]))
            if self._e.event.time < datetime.datetime.now():
                self._e.event.time += datetime.timedelta(days=1)
            return ""
        gWhen.setParseAction(parseAction)
        self._grammar.append(gWhen)

    def _who(self):
        gWho = oneOf("remind nag") + Optional('#') + Word(printables) + Optional(OneOrMore("and" + Optional('#') + Word(printables)))
        def parseAction(s,l,t):
            L = 1
            while L < len(t):
                x = t[L]
                if x == "and":
                    L += 1
                    continue
                if x == "me":
                    x = self._nick
                if x == "#":
                    if L + 1 <= len(t):
                        x = "#" + t[L+1]
                        L+=1
                self._e.event.audience += x + ","
                L += 1
            return ""
        gWho.setParseAction(parseAction)
        self._grammar.append(gWho)

    def _with(self):
        withw = "with" + Word(alphanums) + Optional(OneOrMore("and" + Word(alphanums)))
        def parseAction(s,l,t):
            # self._context['with'] = ":".join(t[1:])
            return ""
        withw.setParseAction(parseAction)
        self._grammar.append(withw)

    def _what_x(self):
        gWhat = oneOf("to about") + "{" + SkipTo('}') + "}"
        def parseAction(s,l,t):
            self._e.event.action = "%s %s" % (t[0], " ".join(t[2:-1]))
            return ""
        gWhat.setParseAction(parseAction)
        self._grammar.append(gWhat)

    def _what(self):
        gWhat = oneOf("to about") + OneOrMore(Word(printables))
        def parseAction(s,l,t):
            self._e.event.action = " ".join(t)
            return ""
        gWhat.setParseAction(parseAction)
        self._grammar.append(gWhat)

    def _snooze(self):
        nag = "every" + Word(nums) + oneOf("m M h H")
        def parseAction(s,l,t):
            # self._context['snooze'] = "-".join(t[1:])
            return ""
        nag.setParseAction(parseAction)
        self._grammar.append(nag)

    def _snooze_expires(self):
        nag = "until" + Word(nums) + Optional(":" + Word(nums))
        def parseAction(s,l,t):
            # self._context['expires'] = "*".join(t[1:])
            return ""
        nag.setParseAction(parseAction)
        self._grammar.append(nag)


if __name__ == '__main__':
    # For testing purposes
    np = NagParser('test')
    
    tests = [
        "nag me on thursday at 9:30am about {going to the eaglepeak gunrange for the safety course at 10am}",
        "nag me to calling jimbo at 8:15pm",
        "nag me to calling jimbo in 20m",
        "nag me at 12pm about calling bob",
        "nag joe to call bobby at 12:08am",
        "nag #33ad to call bobby at his place at 12:23pm every 4m until 13:13",
        "nag me to call bobby at his place & see if he needs a ride at 12:23 every 4m until 13:13",
        "remind me to {call bobby with directions until he will remind me} at 2:23am every 4m until 13:13 with email and phone and cell",
        ]

    for t in tests:
        print "TESTING", t
        r = np.parse(t)
        print r

