#!/usr/bin/python

# ~/.safebrowsing.cfg should look like
#   [safebrowsing]
#   db_path = "/tmp/safebrowsing.sqlite"
#   api_key = "SOME-API-KEY-FROM-GOOGLE"

import os
import sys
import ConfigParser
from safebrowsing import Google_Blacklist


def main():
    # too lazy for optparse
    if len(sys.argv) > 1 and "--initdb" in sys.argv[1:]:
        initdb = True
    else: initdb = False
    config = ConfigParser.ConfigParser()
    config.readfp(open(os.path.expanduser('~/.boombot.cfg')))
    safebrowsing_db_path = config.get('safebrowsing', 'db_path')
    api_key = config.get('safebrowsing', 'api_key')
    data_url = (
        "http://sb.google.com/safebrowsing/update?"
        "client=api&apikey=${key}"
        "&version=goog-${badware_type}-hash:${version}" )
    Google_Blacklist(api_key,data_url,
        safebrowsing_db_path,"malware",initdb=initdb).fetch_data()
    Google_Blacklist(api_key,data_url,safebrowsing_db_path,"black").fetch_data()


if __name__ == '__main__':
    main()

