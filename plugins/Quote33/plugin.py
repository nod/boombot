###
# Copyright (c) 2004, Daniel DiPaolo
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
import time
import random

import supybot.dbi as dbi
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sqlite3

class QuoteGrabsRecord(dbi.Record):
    __fields__ = [
        'by',
        'text',
        'grabber',
        'at',
        'hostmask',
        ]

    def __str__(self):
        at = time.strftime(conf.supybot.reply.format.time(),
                           time.localtime(float(self.at)))
        grabber = plugins.getUserName(self.grabber)
        return '%s (Said by: %s; grabbed by %s at %s)' % \
                  (self.text, self.hostmask, grabber, at)


def nickeq(s1, s2):
    return int(ircutils.nickEqual(s1.encode('iso8859-1'),
				  s2.encode('iso8859-1')))


class SqliteQuoteGrabsDB(plugins.ChannelDBHandler):

    def makeFilename(self, channel):
        return plugins.makeChannelFilename("QuoteGrabs.sqlite.db", channel)

    def makeDb(self, filename):
        """Create the database and connect to it."""
        if os.path.exists(filename):
            db = sqlite3.connect(filename)
            db.text_factory = str
            return db
        db = sqlite3.connect(filename)
        db.text_factory = str
        cursor = db.cursor()
        cursor.execute("""CREATE TABLE quotegrabs (
                          id INTEGER PRIMARY KEY,
                          nick TEXT,
                          hostmask TEXT,
                          added_by TEXT,
                          added_at TIMESTAMP,
                          quote TEXT,
                          votes INTEGER DEFAULT 0
                          );""")
        db.commit()
        return db

    def get(self, channel, id):
        db = self.getDb(channel)
        cursor = db.cursor()
        cursor.execute("""SELECT id, nick, quote, hostmask, added_at, added_by
                          FROM quotegrabs WHERE id = ?""", (id,))
        quote = cursor.fetchone()
        if quote:
            return QuoteGrabsRecord(quote[0], by=quote[1], text=quote[2],
                                    hostmask=quote[3], at=quote[4],
                                    grabber=quote[5])
        else:
            raise dbi.NoRecordError

    def random(self, channel, nick):

        db = self.getDb(channel)
        cursor = db.cursor()
        if nick:
            db.create_function('nickeq', 2, nickeq)
            cursor.execute("""SELECT id, quote, votes FROM quotegrabs
                              WHERE nickeq(nick, ?)
                              AND votes >= 0
                              ORDER BY (random()%800+votes) DESC LIMIT 1""", (nick,))
        else:
            cursor.execute("""SELECT id, quote, votes FROM quotegrabs
                              WHERE votes >= 0
                              ORDER BY (random()%800+votes) DESC LIMIT 1""")
        quote = cursor.fetchone()
        if quote:
            return "%s (%d:%d)" % (quote[1], quote[0], quote[2])
        else:
            raise dbi.NoRecordError

    def list(self, channel, nick):
        db = self.getDb(channel)
        cursor = db.cursor()
        db.create_function('nickeq', 2, nickeq)
        cursor.execute("""SELECT id, quote FROM quotegrabs
                          WHERE nickeq(nick, ?)
                          ORDER BY id DESC""", (nick,))
        return [QuoteGrabsRecord(id, text=quote)
                for (id, quote) in cursor.fetchall()]

    def getQuote(self, channel, nick):
        db = self.getDb(channel)
        cursor = db.cursor()
        db.create_function('nickeq', 2, nickeq)
        cursor.execute("""SELECT id, quote, votes FROM quotegrabs
                          WHERE nickeq(nick, ?)
                          ORDER BY id DESC LIMIT 1""", (nick,))
        quote = cursor.fetchone()
        if quote:
            return "%s (%d:%d)" % (quote[1], quote[0], quote[2])
        else:
            raise dbi.NoRecordError

    def select(self, channel, nick):
        db = self.getDb(channel)
        cursor = db.cursor()
        db.create_function('nickeq', 2, nickeq)
        cursor.execute("""SELECT added_at FROM quotegrabs
                          WHERE nickeq(nick, ?)
                          ORDER BY id DESC LIMIT 1""", (nick,))
        addedTime = cursor.fetchone()
        if addedTime:
            return addedTime[0]
        else:
            raise dbi.NoRecordError

    def updateVote(self, channel, id, vote):
        db = self.getDb(channel)
        cursor = db.cursor()
        query = """UPDATE quotegrabs
                   SET votes = votes + %d
                   WHERE id = %s""" % (vote, id)
        cursor.execute(query)
        db.commit()

    def add(self, msg, by):
        channel = msg.args[0]
        db = self.getDb(channel)
        cursor = db.cursor()
        text = ircmsgs.prettyPrint(msg)
        # Check to see if the latest quotegrab is identical
        cursor.execute("""SELECT quote FROM quotegrabs
                          WHERE nick=?
                          ORDER BY id DESC LIMIT 1""", (msg.nick,))
        quote = cursor.fetchone()
        if quote and text == quote[0]:
            return
        cursor.execute("""INSERT INTO quotegrabs
                          VALUES (NULL, ?, ?, ?, ?, ?, 0)""",
                       (msg.nick, msg.prefix, by, int(time.time()), text))
        db.commit()

    def search(self, channel, text):
        db = self.getDb(channel)
        cursor = db.cursor()
        text = '%' + text + '%'
        cursor.execute("""SELECT id, nick, quote FROM quotegrabs
                          WHERE quote LIKE ?
                          ORDER BY id DESC""", (text,))
        quotes = [QuoteGrabsRecord(id, text=quote, by=nick)
                  for (id, nick, quote) in cursor]
        if quotes:
            return quotes
        else:
            raise dbi.NoRecordError

QuoteGrabsDB = plugins.DB('QuoteGrabs', {'sqlite3': SqliteQuoteGrabsDB})

class QuoteGrabs(callbacks.Plugin):
    """Add the help for "@help QuoteGrabs" here."""
    def __init__(self, irc):
        self.__parent = super(QuoteGrabs, self)
        self.__parent.__init__(irc)
        self.db = QuoteGrabsDB()

    def doPrivmsg(self, irc, msg):
        irc = callbacks.SimpleProxy(irc, msg)
        if irc.isChannel(msg.args[0]):
            (channel, payload) = msg.args
            words = self.registryValue('randomGrabber.minimumWords',
                                       channel)
            length = self.registryValue('randomGrabber.minimumCharacters',
                                        channel)
            grabTime = \
            self.registryValue('randomGrabber.averageTimeBetweenGrabs',
                               channel)
            if self.registryValue('randomGrabber', channel):
                if len(payload) > length and len(payload.split()) > words:
                    try:
                        last = int(self.db.select(channel, msg.nick))
                    except dbi.NoRecordError:
                        self._grab(irc, msg, irc.prefix)
                        self._sendGrabMsg(irc, msg)
                    else:
                        elapsed = int(time.time()) - last
                        if random.random()*elapsed > grabTime/2:
                            self._grab(irc, msg, irc.prefix)
                            self._sendGrabMsg(irc, msg)

    def _grab(self, irc, msg, addedBy):
        self.db.add(msg, addedBy)

    def _sendGrabMsg(self, irc, msg):
        s = 'jots down a new quote for %s' % msg.nick
        irc.reply(s, action=True, prefixNick=False)

    def grab(self, irc, msg, args, channel, nick):
        """[<channel>] <nick>

        Grabs a quote from <channel> by <nick> for the quotegrabs table.
        <channel> is only necessary if the message isn't sent in the channel
        itself.
        """
        # chan is used to make sure we know where to grab the quote from, as
        # opposed to channel which is used to determine which db to store the
        # quote in
        chan = msg.args[0]
        if chan is None:
            raise callbacks.ArgumentError
        if ircutils.nickEqual(nick, msg.nick):
            irc.error('You can\'t quote grab yourself.', Raise=True)
        for m in reversed(irc.state.history):
            if m.command == 'PRIVMSG' and ircutils.nickEqual(m.nick, nick) \
                    and ircutils.strEqual(m.args[0], chan):
                self._grab(irc, m, msg.prefix)
                irc.replySuccess()
                return
        irc.error('I couldn\'t find a proper message to grab.')
    grab = wrap(grab, ['channeldb', 'nick'])

    def quote(self, irc, msg, args, channel, nick):
        """[<channel>] <nick>

        Returns <nick>'s latest quote grab in <channel>.  <channel> is only
        necessary if the message isn't sent in the channel itself.
        """
        try:
            irc.reply(self.db.getQuote(channel, nick))
        except dbi.NoRecordError:
            irc.error('I couldn\'t find a matching quotegrab for %s.' % nick,
                      Raise=True)
    quote = wrap(quote, ['channeldb', 'nick'])

    def list(self, irc, msg, args, channel, nick):
        """[<channel>] <nick>

        Returns a list of shortened quotes that have been grabbed for <nick>
        as well as the id of each quote.  These ids can be used to get the
        full quote.  <channel> is only necessary if the message isn't sent in
        the channel itself.
        """
        try:
            records = self.db.list(channel, nick)
            L = []
            for record in records:
                # strip the nick from the quote
                quote = record.text.replace('<%s> ' % nick, '', 1)
                item = utils.str.ellipsisify('#%s: %s' % (record.id, quote),50)
                L.append(item)
            irc.reply(utils.str.commaAndify(L))
        except dbi.NoRecordError:
            irc.error('I couldn\'t find any quotegrabs for %s.' % nick,
                      Raise=True)
    list = wrap(list, ['channeldb', 'nick'])


    def _strip_addressed(self, s):
        import re
        # "<nick> nick2: msg" becomes "<nick> msg"
        return re.sub(r'^(<[^>]+>\s*)\S+:\s*',r'\1',s)


    def _random_and_strip_addressed(self, channel,nick=None):
        # this really should be handed off to a regex -jk-
        qq = self.db.random(channel, nick)
        return self._strip_addressed(qq)

    def random(self, irc, msg, args):
        """<nick|*n> <*n|nick> ...

        Returns a randomly grabbed quote, or if nick is specified the last
        grabbed quote for that nick.  if *n is used, it will randomly retrieve
        n quotes.  Separate nicks and *n by spaces.
        """
        channel = msg.args[0]
        if len(args) > 4:
            return irc.reply("too many, jerk")
        import re
        nick_re = re.compile("^\*(\d+)$")
        # allow old style syntax:  *2,nick
        args = [ x for arg in args for x in arg.split(',') if x ]
        wildcard_grabbed = False # used to check for multiple wildcard queries
        if not args:
            irc.reply( self._random_and_strip_addressed(channel) )
            return
        for nick in args:
            try:
                found = nick_re.match(nick)
                if not found:
                    irc.reply(self.db.getQuote(channel, nick))
                elif wildcard_grabbed:
                    # if they go through with a wildcard once, then don't let
                    # them do it again. yes, i'm looking at you jeff.
                    irc.reply('ignoring excessive wildcard requests. toad.')
                    break
                else:
                    wildcard_grabbed = True
                    n = int(found.groups()[0])
                    if n > 3:
                        irc.reply("NO SOUP FOR YOU (limited to 3)")
                        return
                    while n >= 1:
                        irc.reply( self._random_and_strip_addressed(channel) )
                        n -= 1
            except dbi.NoRecordError:
                if nick:
                    irc.error('Couldn\'t get a random quote for that nick.')
                else:
                    irc.error('Couldn\'t get a random quote.  Are there any '
                        'grabbed quotes in the database?')

    def get(self, irc, msg, args, channel, id):
        """[<channel>] <id>

        Return the quotegrab with the given <id>.  <channel> is only necessary
        if the message isn't sent in the channel itself.
        """
        try:
            irc.reply(self.db.get(channel, id))
        except dbi.NoRecordError:
            irc.error('No quotegrab for id %s' % utils.str.quoted(id),
                      Raise=True)
    get = wrap(get, ['channeldb', 'id'])

    def search(self, irc, msg, args, channel, text):
        """[<channel>] <text>

        Searches for <text> in a quote.  <channel> is only necessary if the
        message isn't sent in the channel itself.
        """
        try:
            records = self.db.search(channel, text)
            L = []
            for record in records:
                # strip the nick from the quote
                quote = record.text.replace('<%s> ' % record.by, '', 1)
                item = utils.str.ellipsisify('#%s: %s' % (record.id, quote),50)
                L.append(item)
            irc.reply(utils.str.commaAndify(L))
        except dbi.NoRecordError:
            irc.error('No quotegrabs matching %s' % utils.str.quoted(text),
                       Raise=True)
    search = wrap(search, ['channeldb', 'text'])

    def vote(self, irc, msg, args, channel, text):
        """[<channel>] <id>(++|--)
        """
        import re
        vote_re = re.compile("(\d+)(--|\+\+)")
        if not vote_re.match(text):
            irc.reply("vote syntax: <id>[++|--]");
            return
        vid, vorder = vote_re.match(text).groups()
        vorder = 1 if '+' in vorder else -1
        try:
            self.db.updateVote(channel, vid, vorder)
            irc.reply('vote recorded')
        except Exception, e:
            irc.reply('error updating vote - %s' % (e))
    vote = wrap(vote, ['channeldb', 'text'])

Class = QuoteGrabs

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
