#!/usr/bin/env python

import sys
import re
import urllib2, pprint
from BeautifulSoup import BeautifulSoup

def parse(wordtosearch):

    url = 'http://dictionary.reference.com/search?q=' + wordtosearch
    # Read the URL and pass it to BeautifulSoup.
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup()
    soup.feed(html)

    # Read the main table, extracting the words from the table cells.
    maintable = soup.fetch('li')

    # There are 6 lines containg <li> at the bottom that we don't want to print
    # So we remove them from the list by adjustin the count
    removeli = len(maintable) - 6

    counter = 0
    # if removeli is 0 then we need to look for dl tags
    if removeli == 0:
        # fetch dl tags
        maintable = soup.fetch('dl')
        for defs in maintable:
            converttostring = str(defs)
            splitstring = converttostring.split('<dd>') 
            removetrash = re.sub('^ |</dd.*dl>|<li.*">|<ol.*">|<cite> </li>|<cite>|</cite>|</ol></li>|</li>|<a.*/a>', '', splitstring[1])
            addunderscores = re.sub('<u><i>|</i></u>', '_', removetrash)
            convertampersands = re.sub('&', '&', addunderscores)
            definition = convertampersands
            print definition
    else:    
        for counter in range(removeli):
            defs = maintable[counter]
            converttostring = str(defs)
            splitstring = converttostring.split('<li>')
            if len(splitstring) != 1:
                removetrash = re.sub('^ |(<li.*">|<ol.*">|<cite> </li>|<cite>|</cite>|</ol></li>|</li>|<a.*/a>)', '', splitstring[1])
                addunderscores = re.sub('(<u><i>|</i></u>)', '_', removetrash)
                convertampersands = re.sub('&', '&', addunderscores)
                definition = convertampersands
                print definition
                
            else:
                removetrash = re.sub('^ |<li.*">|<ol.*">|<cite> </li>|<cite>|</cite>|</ol></li>|</li>|<a.*/a>', '', splitstring[0])
                addunderscores = re.sub('<u><i>|</u></i>', '_', removetrash)
                convertampersands = re.sub('&', '&', addunderscores)
                definition = convertampersands
                print definition

            counter += 1

def USEAGE():
    print "USEAGE: " + sys.argv[0] + " <word to search for>"
    sys.exit(-1)


if __name__ == '__main__':
    
    # we are reading input from the command line
    args = sys.argv[1:]
    if len(args) == 0:
        USEAGE()
        sys.exit(-1)
    wordtosearch = args[0]
    
    parse(url)

