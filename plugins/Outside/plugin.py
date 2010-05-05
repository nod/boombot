
from supybot.commands import *
import supybot.callbacks as callbacks
from BeautifulSoup import BeautifulSoup
import urllib
import urllib2
import re


class Outside(callbacks.Plugin):
    """Some useful tools for Outside."""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def _getsoup(self,url):
        try:
            page = urllib.urlopen(url).read()
            soup = BeautifulSoup(page)
            return soup
        except IOError:
            return False

    def _getweather(self,loc,sel):
        baseurl = "http://mobile.weather.gov/"
        firsturl = baseurl + "port_zc.php?inputstring=%s" % urllib.quote(loc)
        soup = self._getsoup(firsturl)
        if soup:
            secondurl = baseurl + soup.find('a')['href'] + '&select=%d'%sel
            soup = self._getsoup(secondurl)
        return soup

    def forecast(self, irc, msg, args, loc):
        """[location]
            location can be either zip or city, state
            (sorry, you international folks have to go look out a window)
            tells you the forecast for your area
        """
        soup = self._getweather(loc,1)  # 1 is forecast
        if not soup:
            self.errout(irc,"error retreiving %s info.  Are you sure it's still there?" % loc)
            return
        forecasts = soup.findAll('b')
        ret = []
        ret.append("%s -" % loc)
        for i in range(2,5):
           try:
               ret.append(forecasts[i].next.upper().strip())
               ret.append(forecasts[i].nextSibling.strip())
           except: pass
        irc.reply(' '.join(ret))
    forecast = wrap(forecast, ['text'])


    def weather(self, irc, msg, args, loc):
        """[location]
            location can be either zip or city, state
            (sorry, you international folks have to go look out a window)
            tells you the current weather for your area"""
        soup = self._getweather(loc,3)  # 3 is current conditions
        if not soup:
            self.errout(irc,"error retreiving %s info.  Are you sure it's still there?" % loc)
            return
        conditions = []
        try: conditions.append(soup.div.contents[2].strip()) # location
        except: pass
        try: conditions.append(soup.div.contents[8].strip().replace('&nbsp;','')) # gps
        except: pass
        try: conditions.append(soup.div.contents[12].strip().replace('&deg;','')) # conditions
        except: pass
        try: conditions.append(soup.div.contents[14].strip().replace('&deg;','').replace(' ','')) # temp
        except: pass
        try: conditions.append(soup.div.contents[16].strip().replace(' ','')) # humidity
        except: pass
        try: conditions.append(soup.div.contents[18].strip().replace(' ','')) # wind
        except: pass
        irc.reply(" - ".join(conditions))
    weather = wrap(weather, ['text'])

    def metar(self,irc,msg,args,loc):
        """[ICAO Location]
            Current Meteorological Codes from
            http://weather.noaa.gov/weather/metar.shtml
        """
        soup = self._getsoup("http://weather.noaa.gov/cgi-bin/mgetmetar.pl?cccc=%s" % urllib.quote(loc))
        if not soup:
            self.errout(irc,"error retreiving weather.noaa.gov.  Are you sure it's still there?")
            return
        #timestamp = soup.findAll("b")[1]
        #timestamp = timestamp.contents[0].replace('\n','').strip()
        metar = soup.find("font", {'face':"courier",'size':"5"})
        metar = metar.contents[0].strip()
        #irc.reply(timestamp+": "+metar)
        irc.reply(metar)
    metar = wrap(metar, ['text'])

    def errout(self,irc,msg):
        irc.reply(msg)
        return


Class = Outside

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
