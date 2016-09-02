#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import sys
import urllib
import urllib2

# https://query1.finance.yahoo.com/v7/finance/quote?formatted=true&symbols=yhoo&fields=regularMarketPrice%2CregularMarketChange%2CregularMarketChangePercent%2CpostMarketPrice%2CpostMarketChange%2CpostMarketChangePercent
def fetch_quote(symbol):
    params = urllib.urlencode({
        "symbols": urllib.quote(symbol),
        "formatted": "true",
        "fields": ','.join([
            "regularMarketPrice",
            "regularMarketChange",
            "regularMarketChangePercent",
            "preMarketPrice",
            "preMarketChange",
            "preMarketChangePercent",
            "postMarketPrice",
            "postMarketChange",
            "postMarketChangePercent",
            ]),
        })
    url = 'https://query1.finance.yahoo.com/v7/finance/quote?'+params

    return json.loads(urllib2.urlopen(url).read())


def text_quote(symbol, data=None):
    q = quote(symbol, data)
    try:
        afterhours = " Afterhours: %s change from close: %s (%s)." % (
                q['ah_price'],
                q['ah_change'],
                q['ah_pctchg'],
                )
    except KeyError:
        afterhours = ""

    try:
        premarket = " Premarket: %s change from close: %s (%s)." % (
                q['pre_price'],
                q['pre_change'],
                q['pre_pctchg'],
                )
    except KeyError:
        premarket = ""

    return "%s: %s as of %s. A change of %s (%s).%s" % (
            q['symbol'],
            q['price'],
            q['time'],
            q['change'],
            q['pctchg'],
            afterhours or premarket,
            )


def quote(symbol, data=None):
    if data is None:
        data = fetch_quote(symbol)

    data = data['quoteResponse']['result'][0]

    q = {
            "symbol": data['symbol'],
            "price":  data['regularMarketPrice']['fmt'],
            "time":   data['regularMarketTime']['fmt'],
            "change": data['regularMarketChange']['fmt'],
            "pctchg": data['regularMarketChangePercent']['fmt'],
            }

    if data['marketState'].lower() == 'post':
        q.update({
            "ah_price":  data['postMarketPrice']['fmt'],
            "ah_time":   data['postMarketTime']['fmt'],
            "ah_change": data['postMarketChange']['fmt'],
            "ah_pctchg": data['postMarketChangePercent']['fmt'],
            })

    if data['marketState'].lower() == 'pre':
        q.update({
            "pre_price":  data['preMarketPrice']['fmt'],
            "pre_time":   data['preMarketTime']['fmt'],
            "pre_change": data['preMarketChange']['fmt'],
            "pre_pctchg": data['preMarketChangePercent']['fmt'],
            })

    return q


if __name__ == "__main__":
    for symbol in sys.argv[1:]:
        print text_quote(symbol)
