
from BeautifulSoup import BeautifulSoup
import urllib
import re


class Weather(object):

    def _getsoup(self,url):
        try:
            page = urllib.urlopen(url).read()
            soup = BeautifulSoup(page)
            return soup
        except IOError:
            return False

    def _getweather(self,loc,sel):
        baseurl = "http://forecast.weather.gov/zipcity.php"
        firsturl = baseurl + "?inputstring=%s" % urllib.quote(loc)
        soup = self._getsoup(firsturl)
        return soup

    def forecast(self, loc):
        """[location]
            location can be either zip or city, state
            (sorry, you international folks have to go look out a window)
            tells you the forecast for your area
        """
        soup = self._getweather(loc,1)  # 1 is forecast
        forecasts = soup.findAll('b')
        ret = []
        ret.append("%s -" % loc)
        print forecasts
        for i in range(2,5):
           try:
               ret.append(forecasts[i].next.upper().strip())
               ret.append(forecasts[i].nextSibling.strip())
           except: pass
        return ' '.join(ret)

    def weather(self, loc):
        """[location]
            location can be either zip or city, state
            (sorry, you international folks have to go look out a window)
            tells you the current weather for your area"""
        soup = self._getweather(loc,3)  # 3 is current conditions
        ul = soup.find('ul', "current-conditions-detail")
        conditions = []
        for label, txt in ul.findAll("li"):
            conditions.append("%s: %s" % (label.text,txt.replace('&deg;','')))
        return " - ".join(conditions)

    def metar(self,loc):
        """[ICAO Location]
            Current Meteorological Codes from
            http://weather.noaa.gov/weather/metar.shtml
        """
        soup = self._getsoup("http://www.aviationweather.gov/adds/metars/?station_ids=%s&std_trans=standar&chk_metars=ond&hoursStr=most+recent+only" % urllib.quote(loc))
        metar = soup.find("font")
        try:
            metar = metar.contents[0].strip()
        except AttributeError:
            metar = "unknown ICAO airport abbreviation"
        return metar




if __name__ == '__main__':
    print "simple cheap tests.  printing weather for 78641"

    print "----------------------"
    print "forecast('78641')"
    print Weather().forecast('78641')
    print "----------------------"
    print "weather('78641')"
    print Weather().weather('78641')


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
