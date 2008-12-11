
import supybot.utils as utils
from supybot.commands import *
import supybot.utils.web as web
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs

import os
import sys
import time
import socket
import threading

MY_SOCKETWRITER_PASS = "SET THIS TO SOMETHING ELSE"

class SocketWriter(callbacks.Plugin):
    """SocketWriter """
    threaded = True

    def __init__(self, irc):
        self.irc = irc
        self.__parent = super(SocketWriter, self)
        self.__parent.__init__(irc)
        self.log.debug("inside __init__")
        self.stop = False
        try:
            t = threading.Thread(target=self._startServer, 
                                 args=(irc,))
            t.setDaemon(True)
            t.start()
        except callbacks.Error, e:
            print("Couldn't do this")                    
        except Exception:
            print "DOH! ", sys.exc_info()[0]

    def die(self):
        self.__parent.die()
        self.stop = True

    def _dosock(self):
        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sf = "/tmp/s.boom"
        try:
            s.bind(sf)   # race condition? yup
        except:
            os.unlink(sf)
            s.bind(sf)   # race condition? yup
        os.system("chmod go+w %s" % (sf))
        return s

    def _startServer(self, irc):
        self.irc = irc
        s = self._dosock()
        s.listen(1)
        timecounter = time.time()
        while not self.stop:
            data = ""
            try:
                conn,addr = s.accept()
                data = conn.recv(512)
            except:
                pass
            if data:
                self._handle_input(data)
            # let's redo the sock about once every couple ofhours
            nowcounter = time.time()
            if timecounter - nowcounter > 60*60*4:
                timecounter = nowcounter
                s.close()
                s = self._dosock()

    def _handle_input(self, input):
        try:
            tmp = input.split("|")
            passwd = tmp.pop(0)
            if passwd != MY_SOCKETWRITER_PASS:
                return
            chan = tmp.pop(0)
            msg = "|".join(tmp)
            self._announce(chan, msg) 
        except:
            pass

    def _announce(self, chan, msg):
        self.irc.sendMsg(ircmsgs.privmsg(chan, msg, "[trac]"))
 
Class = SocketWriter

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
