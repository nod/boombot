
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks

import distorm

class Disasm(callbacks.Plugin):
    """bit twiddling is fun"""

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def dasm(self, irc, msg, args):
        "Disassemble hex bytes.  use -a to get the addresses"
        if args[0] == "-a":
            inc_addr = True
            bytes = " ".join(args[1:])
        else:
            inc_addr = False
            bytes = " ".join(args)
        address = 0x0

        rawbytes = ""
        for byte in bytes.split():
            try:
                rawbytes = rawbytes + chr(int(byte,16))
            except:
                pass
        disasm = distorm.Decode(address, rawbytes, distorm.Decode32Bits)

        ret = [""]
        for i in disasm:
            if inc_addr:
                ret.append( "%02X: %s"%(i[0],i[2]))
            else:
                ret.append( "%s"%(i[2]))
        irc.reply(("   ".join(ret)).strip())

Class = Disasm

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
