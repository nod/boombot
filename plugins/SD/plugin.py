###
# Copyright (c) 2007, No Body
# All rights reserved.
#
###

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import urllib
import xml.etree.ElementTree as ET 
import time
from html2text import html2text

class MacRumor:
    def __init__(self, item):
        self.title = item.findtext("title")
        self.description = item.findtext("description")
        self.pubdate = item.findtext("pubDate")
        self.link = item.findtext("link")

class SDeal:
    def __init__(self, item):
        self.link = item.findtext("link")
        self.title = item.findtext("title")
        self.pubdate = item.findtext("pubDate")

class SD(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(SD, self)
        self.__parent.__init__(irc)
   
    def mr_getposts(self):
      uri = "http://www.macrumors.com/macrumors.xml"
      tree = ET.parse(urllib.urlopen(uri))
      return map(MacRumor, tree.getiterator("item"))

    def macrumor(self, irc, msg, args):
      """latest www.macrumors.com"""
      try:
        resp = ""
        rumors = self.mr_getposts()
        if not rumors:
          irc.reply("unable to fetch macrumors")
          return
        title = html2text(rumors[0].title).strip()
        desc = html2text(rumors[0].description).strip()
        title = title.replace("\'", "")
        desc = desc.replace("\'", "")
        desc = desc.replace("\n", "")
        resp += "%s - %s   " % (title, desc)
        irc.reply(resp)
      except Exception, e:
        irc.reply("unable to fetch macrumors [e] %s" % e)

    def getposts(self):
        uri = "http://feeds.feedburner.com/SlickdealsnetFP?format=xml"
        tree = ET.parse(urllib.urlopen(uri))
        return map(SDeal, tree.getiterator("item"))

    def sd(self, irc, msg, args):
        """slickdeals!"""
        try:
            dlmsg = ""
            deals = self.getposts()
            today = int(time.strftime('%d'))
            for deal in deals:
                if time.strptime(deal.pubdate, "%a, %d %b %Y %H:%M:%S GMT")[2] == today:
                    dlmsg += "[sd] %s " % (deal.title)
            if dlmsg:
                irc.reply(dlmsg)
            else:
                irc.reply("[sd] No Deals")
        except:
            irc.reply("crap")

Class = SD
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
