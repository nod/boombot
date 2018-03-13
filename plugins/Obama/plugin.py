
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import obamaquotes

from random import choice

class Obama (callbacks.Plugin):
    """when you need to feel angry/sorry for your country"""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def obama(self, irc, msg, args):
        """
        Sometimes you need a little hope and/or change
        """
        o = choice(obamaquotes.hopenchange) 
        irc.reply(o)

Class = Obama

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
