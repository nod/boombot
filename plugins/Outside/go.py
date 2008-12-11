#!/usr/bin/env python
from BeautifulSoup import BeautifulSoup
import urllib

loc="78641"

baseurl = "http://mobile.weather.gov/"
firsturl = baseurl + "port_zc.php?inputstring=%s" % urllib.quote(loc)
page = urllib.urlopen(firsturl).read()
soup = BeautifulSoup(page)
secondurl = baseurl + soup.find('a')['href'] + '&select=1'
page = urllib.urlopen(secondurl).read()
soup = BeautifulSoup(page)

forecasts = soup.findAll('b')

for i in range(2,6):
    print forecasts[i].next + forecasts[i].nextSibling

