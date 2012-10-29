
from supybot.commands import *
import supybot.callbacks as callbacks

from weather import Weather

class Outside(callbacks.Plugin):
    """Some useful tools for Outside."""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def forecast(self, irc, msg, args, loc):
        """[location]
            location must be zip
            (sorry, you international folks have to go look out a window)
            tells you the forecast for your area
        """
        irc.reply(Weather.forecast(loc))
    forecast = wrap(forecast, ['text'])

    def weather(self, irc, msg, args, loc):
        """[location]
            location must be zip
            (sorry, you international folks have to go look out a window)
            tells you the current weather for your area"""
        irc.reply(Weather.current(loc))
    weather = wrap(weather, ['text'])

Class = Outside

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
