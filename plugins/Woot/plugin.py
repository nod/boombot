
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sys,time,random,string
from webutil.textutils import get_text
from BeautifulSoup import BeautifulSoup
import urllib2
import re


class Woot(callbacks.Plugin):
    """Some useful tools for Woot."""
    tips = 0

    _allchars = string.maketrans('','')

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)


    def __woot_reply(self, irc, soup):
            descr =soup.find('div',attrs={'class':'productDescription'})
            prod = get_text(descr.find('h2'))
            price = get_text(descr.find('h3'))
            wootitem = "%s - %s" % (prod, price)
            soldout = soup.find('a', attrs={'class':'soldOut'})
            if soldout:
                wootitem += " (Sold Out!)"
            wootoff = self.__wootoff(soup)
            if wootoff:
                wootitem += " [Woot Off! %s]" % wootoff
            wootitem = "".join(
                    [ 32<=ord(c)<=126 and str(c) or "."  for c in wootitem ]
                )
            irc.reply(wootitem)


    def woot(self, irc, msg, args):
        """woot!"""
        commands = {
            'sidedeals': self._woot_sidedeals,
            'sd': self._woot_sidedeals,
            'descr': self._woot_description,
            'description': self._woot_description,
            'sellout': self._woot_sellout,
            'so': self._woot_sellout,
        } 
        try:
            cmd = args[0]
            # getattr(self, "_woot_" + cmd)(irc)
            commands[cmd](irc)
        except IndexError:
            # no cmd
            self._woot(irc)
        except IOError:
            irc.reply('error')
        except KeyError:
            # bogus command
            irc.reply('usage: woot [%s] %s' % ("|".join(commands.keys()),cmd))


    def _woot_sellout(self, irc):
        """display woot item [default]"""
        soup = self._woot_soupcontent(irc, "http://sellout.woot.com")
        if soup:
            self.__woot_reply(irc,soup)


    def _woot(self, irc):
        """display woot item [default]"""
        soup = self._woot_soupcontent(irc, "http://www.woot.com")
        if soup:
            self.__woot_reply(irc,soup)

    def _woot_description(self, irc):
        """woot! display current woot description"""
        soup = self._woot_soupcontent(irc, "http://www.woot.com")
        if soup:
            desc = soup.find('div',attrs={'class':'descriptionContent'})
            wd = "".join([ 32<=ord(c)<=126 and str(c) or "."  for c in desc.p.contents[0]])
            wootdesc = '%s...(more at woot.com!)' % (wd[:350])
            irc.reply(wootdesc)


    def _woot_sidedeals(self, irc):
        """woot! display side deals """
        soup = self._woot_soupcontent(irc, "http://www.woot.com")
        if soup:
            sd = soup.find('div',attrs={'class':'sponsor'})
            # sp = sd.find('a').findAll(text=True)
            # sd = sd.find('font').findAll('a')
            wootsd = ''
            for i in range(0, len(sd)):
                wootsd += "%s - " % sd[i].contents[0]
            # sponser = sp[len(sp)-1]
            # wootsd += "sponser: %s" % sponser
            irc.reply(wootsd)


    def __wootoff(self, soup):
        """woot! wootoff determination (test only)"""
        try:
            wootoff = soup.find('div', attrs={'id':'ContentPlaceHolderLeadIn_ContentPlaceHolderLeadIn_SaleControl_PanelWootOffProgressBar'})
            if not wootoff: return None
            else:
                wootoffpct = wootoff.find("div", {'class':'wootOffProgressBarValue'})
                if not wootoffpct: return "SoldOut!"
                s = wootoffpct.get('style')
                left = re.search(r'(\d+%)', s.split().pop())
                return left.group(1) + " left"
        except TypeError:
            return None


    def _woot_soupcontent(self, irc, wooturl):
        """fetch woot! web content"""
        try:
            # page = urllib.urlopen("http://www.woot.com").read()
            page = urllib2.urlopen(wooturl).read()
            soup = BeautifulSoup(page)
            return soup
        except IOError:
            error = 'error fetching woot url'
            irc.reply(error)
            return False
        except UnicodeDecodeError,e:
            error = "UnicodeDecodeError: " + str(e)
            irc.reply(error)
            return False

Class = Woot


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
