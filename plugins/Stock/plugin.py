###
# Copyright (c) 2005, James Vega
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import supybot.utils as utils
from supybot.commands import *
import supybot.callbacks as callbacks
from math import floor


class Stock(callbacks.Plugin):
    threaded = True

    def _get_data(self,symbol):
        url = 'http://finance.yahoo.com/d/quotes.csv?s=%s' \
              '&f=sl1d1t1c1ohgv&e=.csv' % symbol
        try:
            quote = utils.web.getUrl(url)
        except utils.web.Error, e:
            irc.error(str(e), Raise=True)
        data = quote.split(',')
        return data

    def howmany(self,irc,msg,args,symbol,amount):
        """<company symbol>  <amount to spend>

        Will tell you how many shares you can purchase for a given amount if
        bought at the current (delayed) price.  Assumes a flat $7 trade cost.
        """
        tradecosts = 7  # scottrade is $7
        amount = float(amount)
        data = self._get_data(symbol)
        price = float(data[1])
        num =  int(floor( (amount-tradecosts)/price)) 
        tradecosts = 14.0 / num
        breakevenprice = price + tradecosts
        irc.reply("At curr price of %4.2f for %s, "
            "with %4.2f you can purchase %d shares"
            " with a breakeven price of %4.2f." % (
            price, symbol, amount, num,breakevenprice ) )
    howmany = wrap(howmany, ['somethingWithoutSpaces','somethingWithoutSpaces'])

    def breakeven(self,irc,msg,args,symbol,num):
        """<company symbol>  <number purchased>

        Will tell you the price you'd need to sell at to break even if you
        bought at the current (delayed) price.  Assumes a flat $7 trade cost.
        """
        data = self._get_data(symbol)
        price = float(data[1])
        num = int(num)
        tradecosts = 14.0 / num
        irc.reply("curr price of %s is %4.3f. "
            "Breakeven would be %4.3f." % (symbol, price, price+tradecosts ) )
    breakeven = wrap(breakeven, ['somethingWithoutSpaces','somethingWithoutSpaces'])

    def stockquote(self, irc, msg, args, symbol):
        """<company symbol>

        Gets the information about the current price and change from the
        previous day of a given company (represented by a stock symbol).
        """
        data = self._get_data(symbol)
        if data[1] != '0.00':
            irc.reply('The current price of %s is %s, as of %s EST.  '
                      'A change of %s from the last business day.' %
                      (data[0][1:-1], data[1], data[3][1:-1], data[4]))
        else:
            s = 'I couldn\'t find a listing for %s' % symbol
            irc.error(s)
    stockquote = wrap(stockquote, ['somethingWithoutSpaces'])


Class = Stock


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
