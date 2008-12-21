#!/usr/bin/python

# ~/.safebrowsing.cfg should look like
#   [safebrowsing]
#   db_path = "/tmp/safebrowsing.sqlite"
#   api_key = "SOME-API-KEY-FROM-GOOGLE"

import os
import sys
import ConfigParser
from safebrowsing.query_lookup import Lookup


def main():
    # too lazy for optparse
    if len(sys.argv) == 1: return
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser('~/.boombot.cfg')))
    safebrowsing_db_path = config.get('safebrowsing', 'db_path')
    L = Lookup(safebrowsing_db_path)
    for x in sys.argv[1:]:
        lkup = L.lookup_by_url(x)
        if lkup: print lkup, x

if __name__ == '__main__':
    main()

