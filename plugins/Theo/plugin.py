
from supybot.commands import *
import supybot.callbacks as callbacks

import theoisms

from random import choice


class Theo(callbacks.Plugin):
    """cuz crazy is funny"""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def theo(self, irc, msg, args):
        """
        because he's funny
        """
        s = choice(theoisms.quotes) 
        irc.reply(s)

Class = Theo

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
