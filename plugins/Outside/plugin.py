
from supybot.commands import *
import supybot.callbacks as callbacks

from datetime import datetime

from weather import Weather

class Outside(callbacks.Plugin):
    """Some useful tools for Outside."""

    _api_limits = {}

    def _limit_api(self, irc, f, empty_message=''):
        """
        the wunderground api is limited to 10 requests per second
        this creates a class member dictionary of Day_of_yearHourMin that
        keeps counts.
        """
        self.log.info( "API_LIIMTS: {}".format(
            '...'.join( '{}:{}'.format(k,v) for k,v in Outside._api_limits.iteritems())))
        # clean out older keys so the cache doesn't grow huge
        yesterday_of_year = str(int(datetime.now().strftime('%j')) - 1)
        for k in Outside._api_limits.keys():
            if k.startswith(yesterday_of_year):
                del Outside._api_limits[k]

        # now create our new key and save it
        n = datetime.now().strftime('%j%H%M')
        Outside._api_limits[n] = Outside._api_limits.get(n, 0) + 1

        # now make sure we're not over limit
        if Outside._api_limits[n] >= 10:
            return irc.reply(
                'api rate limited per minute. try again in a few seconds'
                )

        results = f() # call our weather api method
        # output results
        if not results:
            return irc.reply(empty_message)
        if isinstance(results, basestring):
            irc.reply(results)
        else:
            for r in results: irc.reply(r)

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def forecast(self, irc, msg, args, loc):
        """[location]
            location must be zip
            (sorry, you international folks have to go look out a window)
            tells you the forecast for your area
        """
        self._limit_api(irc, lambda: Weather.forecast(loc))
    forecast = wrap(forecast, ['text'])

    def weather(self, irc, msg, args, loc):
        """[location]
            location must be zip
            (sorry, you international folks have to go look out a window)
            tells you the current weather for your area
        """
        self._limit_api(irc, lambda:Weather.current(loc))
    weather = wrap(weather, ['text'])

    def severe(self, irc, msg, args, loc):
        """[location]
            returns severe warnings for the area
            location must be zip
            (sorry, you international folks have to go look out a window)
            tells you the forecast for your area
        """
        self._limit_api(irc, lambda: Weather.severe(loc), 'no alerts')
    severe = wrap( severe, ['text'])

    def hurricanes(self, irc, msg, args):
        """
        returns list of current hurricanes suitable for calling @hurricane NAME 
        """
        self._limit_api(irc, lambda: Weather.hurricane(), 'no hurricanes' )
    hurricanes = wrap(hurricanes, [])

    def hurricane(self, irc, msg, args, cane=None):
        """<hurricane>
        returns hurricane listing for given hurricane
        """
        self._limit_api(irc, lambda: Weather.hurricane(cane), 'no data' )
    hurricane = wrap(hurricane, ['text'])

Class = Outside

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
