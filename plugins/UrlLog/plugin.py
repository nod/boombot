###
###

import os
import ConfigParser
from Goog.safebrowsing.query_lookup import Lookup

import re

import pydelicious
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from urlparse import urlsplit
from socket import gethostbyname, gaierror

class UrlLog(callbacks.PluginRegexp):
    regexps = ['grabUrl']
    def __init__(self, irc):
        self.__parent = super(UrlLog, self)
        self.__parent.__init__(irc)
        self.__dUser = 'url33ad'
        self.__dPass = 'b0tl3r'

    def die(self):
        pass

    def callCommand(self, command, irc, msg, *args, **kwargs):
        try:
            self.__parent.callCommand(command, irc, msg, *args, **kwargs)
        except utils.web.Error, e:
            irc.error(str(e))

    def randomurl(self, irc, msg, args):
        try:
            tag = args[0]
            irc.reply(self.__geturlbytag(tag))
        except IndexError:
            irc.reply(self.__geturl())
        except:
            pass

    def __geturl(self):
        try:
            urls = pydelicious.get(self.__dUser,self.__dPass,"")['posts']
            if len(urls) > 0:
                from random import randint
                bm = urls[randint(0,len(urls)-1)]
                rmsg = "url: %s <-- %s (%s)" % (bm['href'],bm['extended'],bm['tag'])
            else:
                rmsg = "No urls found."
            return rmsg
        except IndexError:
            rmsg = "No urls found."
            return rmsg

    def __geturlbytag(self, tag):
        try:
            urls = pydelicious.get(self.__dUser,self.__dPass,tag)['posts']
            if len(urls) > 0:
                from random import randint
                bm = urls[randint(0,len(urls)-1)]
                rmsg = "url: %s <-- %s (%s)" % (bm['href'],bm['extended'],bm['tag'])
            else:
                rmsg = "No urls for %s found." % (tag)
            return rmsg
        except IndexError:
            rmsg = "No urls for %s found." % (tag)
            return rmsg
        except:
            rmsg = "doh.  meltdown" 
            return rmsg

    def grabUrl(self, irc, msg, match):
        r"https?://[^\])>\s]{5,}.+$"
        try:
            channel = msg.args[0]
            if not irc.isChannel(channel): return
            str = match.group().split()
            url = str[0]
            domain = urlsplit(url)[1]
            # just hide certain URLs
            if re.match(".*ibm.com$",domain.lower()):
                return
            if gethostbyname(domain):
                desc = url
                if len(str) > 1:
                    if re.match("[\W]+",str[1]):
                        if len(str) > 2:
                            desc = ' '.join(str[2:])
                    else:
                        desc = ' '.join(str[1:])
               # now check that it's not malicious 
                config = ConfigParser.ConfigParser()
                config.readfp(open(os.path.expanduser('~/.safebrowsing.cfg')))
                safebrowsing_db_path = config.get('safebrowsing', 'db_path')
                lookup = Lookup(safebrowsing_db_path)
                verdict = lookup.lookup_by_url(url)
                if not verdict:
                    res = pydelicious.add(self.__dUser,self.__dPass,url,url,msg.nick,desc)
                else:
                    irc.reply("FJEER! MALICIOUS!  Not adding %s to del.icio.us" % url)

        except:
            pass

Class = UrlLog

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
