###
# Copyright (c) 2006, Jeremy Kelley
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'djangobot.settings'

import time
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks

from nag import NagEvent, NagParser, naglist, listnags, getnag

seconds = 20

class Nag(callbacks.Plugin):
    """This plugin provides the ability for the bot to nag a user on
    whatever the user needs nagging on.
    """
    threaded = True

    def __init__(self, irc):
        self.__parent = super(Nag, self)
        self.__parent.__init__(irc)
        f = self._makeCommandFunction(irc)
        id = schedule.addEvent(f, time.time() + seconds)

    def die(self):
        self.__parent.die()
        schedule.removeEvent(self.name())

    def _makeCommandFunction(self, irc):
        """Makes a function suitable for scheduling from command."""
        def f():
            id = schedule.addEvent(f, time.time() + seconds)
            for y in naglist():
                for x in y.audience.split(','):
                    target = x
                    s = "NAGGING YOU " + y.action
                    irc.queueMsg(ircmsgs.privmsg(target, s))
                y.delete()
        return f

    def nag(self, irc, msg, args, cmdstr):
        """<command statement>
        
        See http://33ad.org/wiki/NagBot help on the syntax.
        """
        np = NagParser(msg.nick)
        ne = np.parse("nag " + cmdstr)
        if ne.is_complete():
            if ne.event.audience[:-1] == msg.nick or msg.nick == "nod":
                ne.save()
                dt = ne.event.time.strftime("for %a %b%d at %R")
                s = "#%d %s - NAG %s" % (ne.event.id, dt, ne.event.action)
                irc.reply("Added %s" % s)
            else:
                irc.reply("can't create nags for others")
        else:
            irc.reply(
                'something was wrong with your command:'
                + ne.error
                )
    nag = wrap(nag, ['text'])
    remind = wrap(nag, ['text'])

    def nags(self, irc, msg, args):
        """no arguments

        lists nags going to you
        """
        target = msg.nick
        n = listnags(msg.nick)
        for e in n:
            dt = e.time.strftime("on %a %b%d at %R")
            s = "#%d %s - NAG %s" % (e.id, dt, e.action)
            irc.queueMsg(ircmsgs.privmsg(target, s))
        if not n:
            irc.queueMsg(ircmsgs.privmsg(target, "no nags"))
    nags = wrap(nags)

    def cancel(self, irc, msg, args, id):
        """<id of nag>
        cancels a nag
        """
        n = getnag(id)
        if n and msg.nick == n.audience[:-1] or msg.nick == "nod":
            n.delete() 
            irc.reply("done")
        else:
            irc.reply("you don't have permission")
    cancel = wrap(cancel, ['int'])

Class = Nag


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
