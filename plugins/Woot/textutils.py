#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# get text from BeautifulSoup
#

from BeautifulSoup import BeautifulSoup, Comment
import re

def filter_unicode(s):
    import unicodedata
    if not isinstance(s,unicode):
        s = unicode(s, 'UTF-8')
    unicodes = {
            # unicode dash
            u'\u2013' : '--',
            # unicode single quotes
            u'\u2018' : '\'',
            u'\u2019' : '\'',
    }
    for k in unicodes:
        s = s.replace(k, unicodes[k])
    # ignore all other unicode chars
    s = unicodedata.normalize('NFC', s).encode('ASCII', 'ignore')
    return unicode(s)

def entity2ascii(s):
    entities = {
            '&nbsp;'  : ' ',
            '&#160;'  : ' ',
            '&#0160;' : ' ',
            '&quot;'  : '"',
            '&laquo;' : '"',
            '&#171;'  : '"',
            '&#0171;' : '"',
            '&raquo;' : '"',
            '&#187;'  : '"',
            '&#0187;' : '"',
            '&ldquo;' : '"',
            '&rdquo;' : '"',
            '&lsquo;' : '\'',
            '&rsquo;' : '\'',
            # ellipse
            '&hellip;': '...',
            # bullet
            '&bul;'   : '*',
            # dash
            '&mdash;' : '-',
            '&ndash;' : '-',
            '&#151;'  : '-',
            '&#0151;' : '-',
            '&#45;'   : '-',
            '&#045;'  : '-',
            # single quote
            '&#39;'   : '\'',
            '&#039;'  : '\'',
            # copyright
            '&#169;'  : '(c)',
            '&#0169;' : '(c)',
            # dash
            '&#8211;' : '--',
            # dash
            '&#8212;' : '--',
            '&#x2014;' : '--',
            # open single quote
            '&#8216;' : '\'',
            # apostrophe
            '&#8217;' : '\'',
            # open double quote
            '&#8220;' : '"',
            # close double quote
            '&#8221;' : '"',
            # bullet
            '&#8226;' : '-',
            # ellipsis
            '&#8230;' : '...',
            # square dot
            '&#9632;' : '-',
            # ampersands
            '&amp;'   : '&',
            '&#34;'   : '"',
            '&#034;'  : '"',
            '&#38;'   : '&',
            '&#038;'  : '&',
            '&#124;'  : '|',
            '&#0124;' : '|',
    }
    s = filter_unicode(s)
    for k in entities:
        s = s.replace(k, entities[k])
    return s

def get_text(soup):
    """
    >>> s = BeautifulSoup("<p><!-- <valueof param> --> Text here")
    >>> get_text(s)
    u'Text here'
    >>> s = BeautifulSoup(' hot <a href="example.com">Google Trends keywords</a>, maintaining')
    >>> get_text(s)
    u'hot Google Trends keywords, maintaining'
    >>> s = BeautifulSoup(u'Big Bird\u2019s nest')
    >>> get_text(s)
    u"Big Bird's nest"
    >>> s = "\xc2\xa0The majority "
    >>> get_text(s)
    u'The majority'
    >>> s = BeautifulSoup('<title>title with » funny char</title>')
    >>> get_text(s)
    u'title with funny char'
    """
    if not soup:
        return ""
    text = []
    # sometimes we're passed a BeautifulSoup object, sometimes not
    try:
        soup.findAll
    except:
        soup = BeautifulSoup(soup)
    for s in soup.findAll(text=lambda text:not isinstance(text,Comment)):
        text.append(' '.join(entity2ascii(s).split()))
    return re.sub(r'\s+([,.;?!])',r'\1', ' '.join(text)).strip()

def _test():
    import doctest
    doctest.testmod()

if __name__ == '__main__':
    _test()
