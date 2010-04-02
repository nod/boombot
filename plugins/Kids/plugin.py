
import calculator
reload(calculator)
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import sys,time,random,string
from webutil.BeautifulSoup import BeautifulSoup
from webutil.textutils import get_text
import urllib
import urllib2
import re
import simplejson as json

def _get_lotto_numbers(soup,drawing='lotto'):
    m = re.match(r'(lotto|mega)',drawing,re.IGNORECASE)
    if m:
        drawing = m.group(1).capitalize()
    return " ".join(map(get_text, soup.findAll('td','NewLatestResults%s'%drawing)))

def _longurl_org(shorturl):
    url = urllib.quote_plus(args[0])
    url = 'http://api.longurl.org/v2/expand?url=%s' % url
    html = urllib2.urlopen(url).read()
    soup = BeautifulSoup(html)
    longurl = soup.find('long-url')
    return get_text(longurl)

def _longurlplease(shorturl):
    url = urllib.quote(shorturl)
    url = 'http://www.longurlplease.com/api/v1.1?q=%s' % shorturl
    html = urllib2.urlopen(url).read()
    longurl = json.loads(html)
    longurl = longurl.get(shorturl)
    if longurl:
        return longurl
    else:
        return shorturl

def longurl(shorturl):
    #return _longurl_org(shorturl)
    return _longurlplease(shorturl)

def get_url_title(url):
    title = None
    html = urllib2.urlopen(url).read()
    try:
        soup = BeautifulSoup(html)
        title = soup.find('title')
    except:
        # if BeatifulSoup cant parse the html, try a simple regex instead
        title_re = re.compile(r'<title>(.*?)</title>',re.DOTALL|re.IGNORECASE)
        m = title_re.search(html)
        if m:
            title = get_text(m.group(1))
    return get_text(title)

class Kids(callbacks.Plugin):
    """Some useful tools for Kids."""
    tips = 0

    _allchars = string.maketrans('','')

    def _prepare_term(self,s,keep=""):
        #return self._makefilter(string.letters+keep)(s).capitalize()
        return self._makefilter(string.letters+string.digits+keep)(s)

    def _makefilter(self,keep):
        _delchars = self._allchars.translate(self._allchars,keep)
        return lambda s,a=self._allchars,d=_delchars: s.translate(a,d)

    def __init__(self,irc):
        callbacks.Privmsg.__init__(self,irc)

    def define(self,irc,msg,args):
        """[word]
        look up the word in wordnet"""
        if len(args) != 1:
            irc.reply("you gotta give me a word to define")
            return
        word = self._prepare_term(args[0],"")
        url = 'http://wordnet.princeton.edu/perl/webwn?s=' + word
        html = urllib2.urlopen(url).read()
        soup = BeautifulSoup()
        soup.feed(html)
        maintable = soup.fetch('li')
        retdef = []
        checkfordefs = len(maintable)
        if checkfordefs != 0:
            for lines in maintable:
                converttostring = str(lines)
                definition = re.sub('^.*\(|\).*$', '', converttostring)
                retdef.append(definition)
        else:
            retdef.append("not found.  Is %s spelled corectly?" % word)
        irc.reply(word + ": " + "; ".join(retdef))

    def calc(self,irc,msg,args):
        """
        >>>(405 - 396) * 3
        (405-396)*3 = 27.0
        """
        s = " ".join(args).strip().replace(' ','')
        val = calculator.parse_and_calc(s)
        result = "%s = %s"%(s, val.__str__(), )
        irc.reply(result)

    def _is_cve_number(self,cve):
        """
        >>> _is_cve_number('CVE-2009-1234') and True
        True
        >>> _is_cve_number('can-2009-1234') and True
        True
        >>> _is_cve_number('2009-1234') and True
        True
        """
        cve_re = re.compile(r'^(?:(?:can|cve)?\-?)\d{4}\-\d+$',re.IGNORECASE)
        return cve_re.match(cve)

    def _cve(self,cve):
        """
        return url and description for a cve entry
        """
        url = 'http://cve.mitre.org/cgi-bin/cvename.cgi?name=' + cve
        html = urllib2.urlopen(url).read()
        soup = BeautifulSoup(html)
        err = soup.find('h2').contents[0]
        if re.search(r'ERROR', err):
            return "No data found regarding " + cve
        div = soup.find('div',id='GeneratedTable')
        if not div or not div.table:
            return "Parse error searching for " + cve
        desc = div.table.findAll('tr')[3].td.contents[0]
        desc = ' '.join(desc.split())
        ret = "%s %s" % (url, desc)
        return ret.strip()

    def cve(self,irc,msg,args):
        word= self._prepare_term(args[0],"-")
        if self._is_cve_number(word):
            irc.reply(self._cve(word))
        else:
            irc.reply("Not a CVE number: " + word)

    def url(self,irc,msg,args):
        """<shorturl>
        expand a shortened url (like tinyurl, bit.ly, etc)
        """
        usage = "usage: url <shorturl> [with_title]"
        if len(args) < 1:
            irc.reply(usage)
            return
        try:
            expanded_url = longurl(args[0])
        except Exception, e:
            irc.reply("%s: error looking up %s" % (e, args[0]))
            return
        title = ""
        if len(args) > 1:
            title = get_url_title(expanded_url)
            if title:
                title = " <-- %s" % get_text(title)
        irc.reply("%s%s" % (expanded_url, title))

    def lotto(self, irc, msg, args):
        """[lotto|mega]

        Gets winning numbers for the most recent Texas Lotto drawing
        """
        if len(args):
            drawing = args[0]
        else:
            drawing = "lotto"
        try:
            html = urllib2.urlopen("http://www.txlottery.org/export/sites/default/index.html").read()
            html = re.sub(r'</</p>','</p>',html) # fix bad html
            soup = BeautifulSoup(html)
        except:
            irc.reply("error looking up lotto")
            return
        irc.reply(_get_lotto_numbers(soup, drawing))

    def rtsq(self, irc, msg, args):
        """<company symbol>

        Gets the real time stock quote for the given symbol.
        """
        if len(args) < 1:
            irc.reply(usage)
            return
        symbol = args[0]
        url = urllib.quote_plus(symbol)
        url = 'http://finance.yahoo.com/q?s=%s' % url
        try:
            html = urllib2.urlopen(url).read()
            soup = BeautifulSoup(html)
        except:
            irc.reply("error looking up %s" % symbol)
            return
        time = soup.find('span',id='yfs_t50_%s'%symbol.lower())
        if not time:
                time = soup.find('span',id='yfs_t10_%s'%symbol.lower())
        time = time and get_text(time) or ""
        price = soup.find('span',id='yfs_l90_%s'%symbol.lower())
        if not price:
                price = soup.find('span',id='yfs_l10_%s'%symbol.lower())
        price = price and get_text(price) or ""
        change = soup.find('span',id='yfs_c60_%s'%symbol.lower())
        if not change:
                change = soup.find('span',id='yfs_c10_%s'%symbol.lower())
        change = change and get_text(change) or ""
        pctchg = soup.find('span',id='yfs_p40_%s'%symbol.lower())
        if not pctchg:
                pctchg = soup.find('span',id='yfs_pp0_%s'%symbol.lower())
        pctchg = pctchg and get_text(pctchg) or ""
        if not price:
            irc.reply("error looking up %s" % symbol)
        else:
            irc.reply("%s: %s as of %s. A change of %s %s." % (symbol, price, time, change, pctchg))


Class = Kids


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=78:
