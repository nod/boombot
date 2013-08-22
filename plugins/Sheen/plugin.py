
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import sheenisms

from random import choice

class Sheen(callbacks.Plugin):
    """cuz crazy is funny"""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def sheen(self, irc, msg, args):
        """
        because he's funny
        """
        s = choice(sheenisms.sheenisms) 
        irc.reply(s)

Class = Sheen

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
