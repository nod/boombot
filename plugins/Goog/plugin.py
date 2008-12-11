###
###

import re
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import simplejson
import urllib2
from html2text import html2text

class Goog(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(Goog, self)
        self.__parent.__init__(irc)
        self.__url = 'http://ajax.googleapis.com/ajax/services/search/web?v=1.0&q='
	self.__calcurl = 'http://www.google.com/search?num=1&q='

    def goog(self, irc, msg, args):
        """gewgle!"""
        try:
            sstr = "+".join(args)
            results = self.__getresults(sstr)
            count = 1
            ircStr = '[goog] '
            if not results:
                irc.reply('[goog] no results')
            for r in results:
                ircStr += '%d) %s (%s)   ' % (count, html2text(r['title']).strip(), r['url'])
                count += 1
            irc.reply(ircStr)
        except:
            irc.reply('doh.  meltdown')

    def gcalc(self, irc, msg, args):	
        """google calculatah"""
        try:
            cre = re.compile('<font size=\+1><b>(.*?)</b>')
            sstr = "+".join(args)
            req = urllib2.Request(self.__calcurl+sstr)
            req.add_header('User-Agent', 'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.1; .NET CLR 1.1.4322; HbTools 4.7.3)')
            opn = urllib2.build_opener()
            feed = opn.open(req).read()
            if cre.search(feed):
                ans = cre.search(feed).groups()[0]
                irc.reply(ans)
                return
            irc.reply('unable to calculate... its underdogs fault')
        except:
            irc.reply('doh.  meltdown')

    def __getresults(self, searchStr):
        try:
            res = simplejson.load(urllib2.urlopen(self.__url+searchStr))
            if res['responseStatus'] == 200:
                # add logic for allowing more than 1 response here
                if len(res['responseData']['results']) > 2:
                    return res['responseData']['results'][:2]
                return res['responseData']['results']
            return False
        except IndexError:
            return False

Class = Goog

# vim:se     shiftwidth=4 softtabstop=4 expandtab textwidth=79:
