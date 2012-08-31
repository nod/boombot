###
###

import re
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.ircmsgs as ircmsgs
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
#import MySQLdb
import urllib
from biblebooks import books
from html2text import html2text

class Bible(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(Bible, self)
        self.__parent.__init__(irc)
        self.q = {}
        self.q['error'] = 'generic'
        self.trans = 'nasb'
        self.vre = re.compile('([1-3A-Za-z\ ]+)\ ([0-9]{1,4}\:[0-9]{1,4}\-[0-9]{1,4}\:[0-9]{1,4}|[0-9]{1,4}\:[0-9]{1,4}\-[0-9]{1,4}|[0-9]{1,4}\:[0-9]{1,4}|[0-9]{1,4})')
        self.cv0_re = re.compile('([0-9]{1,4})')
        self.cv1_re = re.compile('([0-9]{1,4})\:([0-9]{1,4})')
        self.cv2_re = re.compile('([0-9]{1,4})\:([0-9]{1,4})\-([0-9]{1,4})')
        self.cv3_re = re.compile('([0-9]{1,4})\:([0-9]{1,4})\-([0-9]{1,4})\:([0-9]{1,4})')
        self.cv4_re = re.compile('([0-9]{1,4})\-([0-9]{1,4})')
        self.cv5_re = re.compile('([0-9]{1,4})\-([0-9]{1,4})\:([0-9]{1,4})')
        self.srch1_re = re.compile('^\/([1-3A-Za-z\ \.\,]+)$')
        self.srch2_re = re.compile('^\/')
        self.srch3_re = re.compile('^in\:([A-Za-z1-3]+)')
        self.srch4_re = re.compile('^in\:([A-Za-z1-3]+) \/([1-3A-Za-z\ \.\,]+)$')
        self.conn = False
        self.cursor = False
        self.translations = {
            'nkjv':'nkjv',
            'nasb':'nasb',
            'niv':'niv',
            'msg':'msg',
            'nlt':'nlt',
            'nrsv':'nrsv',
            'net':'net',
        }

    def __bsearch(self):
        try:
            if not self.q.has_key('searchtext'):
                self.q['error'] = 'dunno why you are here'
                return False
            if len(self.q['searchtext']) <= 3:
                self.q['error'] = 'search string must be atleast 4 characters long.'
                return False
            self.q['searchtext'] = re.sub('^\/','',self.q["searchtext"])
            searchStr = '%'.join(self.q['searchtext'].split())
            searchStr = '%'+searchStr+'%'
            query = "select books.name, CONCAT(i.chapter,':',i.verse) as cv, text.text, books.abbr "
            query += "FROM bible_%s text " % (self.trans)
            query += "LEFT JOIN bible_index i ON i.id = text.id "
            query += "LEFT JOIN bible_books books on i.book = books.id "
            query += "WHERE text.text like '%s' " % (searchStr)
            if self.q.has_key('in'):
                if self.q['in'] == 'ot' or self.q['in'] == 'old':
                    query += "AND books.id <= '37'"
                elif self.q['in'] == 'nt' or self.q['in'] == 'nt':
                    query += "AND books.id >= '38'"
                else:
                    book_match = [x for x in books if x.replace(' ','').startswith(self.q['in'].replace(' ','').lower())]
                    if not book_match:
                        self.q['error'] = 'invalid in parameter'
                        return False
                    query += "AND ("
                    for bm in book_match:
                        query += " books.id = '%s' or" % (books[bm])
                    query = re.sub('or$',')',query)
            self.__connectDB()
            self.cursor.execute(query)
            rows = self.cursor.fetchall()
            self.__disconnectDB()
            if not rows:
                self.q['error'] = 'no matches found'
                return False
            verses_num = len(rows)
            count = 0
            ircStr = '[search] '
            for row in rows:
                count += 1
                if count > 50:
                    pass
                else:
                    ircStr += ' %s %s ,' % (row[3], row[1])
                    #ircStr += '%d) %s %s ' % (count, row[3], row[1])
            ircStr = re.sub(',$','',ircStr)
            ircStr += " (total: %d)" % (verses_num)
            #irc.reply(ircStr)
            self.q['response'] = ircStr
            return True

        except Exception, e:
            self.q['response'] = '%s' % e
            return False

    def b(self, irc, msg, args):
        """ uses:
            !<trans> <book> <verse>
            !<trans> in:<ot|nt|book> /<search text>
            !<trans> /<search text>
        """
	self.q = {}
        try:
            self.trans = self.translations[args[0]]
            vreq = ' '.join(args[1:]).lower()
        except KeyError:
            vreq = ' '.join(args).lower()

        self.q['translation'] = self.trans
        if self.srch2_re.match(vreq) or self.srch3_re.match(vreq):
            # request is going to be a search
            self.q['action'] = 'search'
            if self.srch3_re.match(vreq):
                # user making specific query in:something
                if not self.srch4_re.match(vreq):
                    self.q['error'] = 'invalid search parameters.'
                    irc.reply(self.q['error'])
                    return
                self.q['in'], self.q['searchtext'] = self.srch4_re.match(vreq).groups()
                if not self.__bsearch():
                    irc.reply(self.q['error'])
                    return
            elif self.srch1_re.match(vreq):
                self.q['searchtext'] = vreq
                if not self.__bsearch():
                    irc.reply(self.q['error'])
                    return
            else:
                irc.reply('invalid search parameters.')
                return
            # above logic processed, returning response from bsearch
            irc.reply(self.q['response'])
            return
        vre = self.vre.match(vreq)
        if not vre:
            irc.reply('cannot determine verse')
            return

        try:
            book,cv = vre.groups()
            book_match = [x for x in books if x.replace(' ','').startswith(book.replace(' ',''))]
            if not book_match:
                irc.reply('invalid request')
                return
            book_id = books[book_match[0]]

            verses = self.__get_verses(book_id, cv)

            if verses.has_key('error'):
                irc.reply(verses['error'])
                return
            elif verses.has_key('verses'):
                current_chapter = 0
                ircStr = ''
                if len(verses['verses']) > 3:
                    irc.reply('limited to 3 verses per request... try again')
                    return
                for v in verses['verses']:
                    if v['text'] == '':
                        irc.reply('invalid verse request')
                        return
                    if current_chapter == 0:
                        chapter, verse = v['cv'].split(':')
                        current_chapter = chapter
                        ircStr += "%s %s %s " % (v['book'], v['cv'], v['text'])
                    else:
                        chapter, verse = v['cv'].split(':')
                        if current_chapter != chapter:
                            current_chapter = chapter
                            ircStr += "%s %s " % (v['cv'], v['text'])
                        else:
                            ircStr += "%s %s " % (verse, v['text'])
                ircStr = "%s (%s)" % (ircStr, self.trans)
                irc.reply(ircStr)
                return
        except Exception, e:
            ircStr = 'error: %s. try @bible' % e
            irc.reply(ircStr)

        return

    def __get_verses(self, book_id, cv):
        res = {}
        verses = []
        try:
            self.__connectDB()
            if self.cv3_re.match(cv):
                cv_res = self.cv3_re.match(cv).groups()
                s = 3
                chapter1 = cv_res[0]
                verse1 = cv_res[1]
                chapter2 = cv_res[2]
                verse2 = cv_res[3]
                if chapter1 > chapter2:
                    res['error'] = 'invalid verse range'
                    return res
                if chapter1 == chapter2 and verse1 > verse2:
                    res['error'] = 'invalid verse range'
                    return res
                query = "SELECT books.name, CONCAT(i.chapter,':',i.verse) as cv, text.text "
                query += "FROM bible_"+self.trans+" text "
                query += "LEFT JOIN bible_index i ON i.id = text.id "
                query += "LEFT JOIN bible_books books on i.book = books.id "
                query += "WHERE text.id >= ( SELECT id FROM bible_index WHERE book = ( "
                query += "SELECT id FROM bible_books WHERE id = '"+str(book_id)+"') "
                query += "AND chapter = '"+str(chapter1)+"' AND verse = '"+str(verse1)+"') "
                query += "AND text.id <= ( SELECT id FROM bible_index WHERE book = ( "
                query += "SELECT id FROM bible_books WHERE id = '"+str(book_id)+"') "
                query += "AND chapter = '"+str(chapter2)+"' AND verse = '"+str(verse2)+"') "
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                #test = "%d" % (len(rows))
                #irc.reply(test)
                if not rows:
                    res['error'] = 'invalid verse definition'
                    return res
                res['verses'] = self.__build_verses(rows)
                self.__disconnectDB()
                return res
            if self.cv2_re.match(cv):
                cv_res = self.cv2_re.match(cv).groups()
                s = 2
                chapter1 = cv_res[0]
                verse1 = cv_res[1]
                verse2 = cv_res[2]
                if verse1 > verse2:
                    res['error'] = 'invalid verse range'
                    return res
                query = "SELECT books.name, CONCAT(i.chapter,':',i.verse) as cv, text.text "
                query += "FROM bible_"+self.trans+" text "
                query += "LEFT JOIN bible_index i ON i.id = text.id "
                query += "LEFT JOIN bible_books books on i.book = books.id "
                query += "WHERE text.id >= ( SELECT id FROM bible_index WHERE book = ( "
                query += "SELECT id FROM bible_books WHERE id = '"+str(book_id)+"') "
                query += "AND chapter = '"+str(chapter1)+"' AND verse = '"+str(verse1)+"') "
                query += "AND text.id <= ( SELECT id FROM bible_index WHERE book = ( "
                query += "SELECT id FROM bible_books WHERE id = '"+str(book_id)+"') "
                query += "AND chapter = '"+str(chapter1)+"' AND verse = '"+str(verse2)+"') "
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                #test = "%d" % (len(rows))
                #irc.reply(test)
                if not rows:
                    res['error'] = 'invalid verse definition'
                    return res
                res['verses'] = self.__build_verses(rows)
                self.__disconnectDB()
                return res
            elif self.cv1_re.match(cv):
                cv_res = self.cv1_re.match(cv).groups()
                s = 1
                chapter1 = cv_res[0]
                verse1 = cv_res[1]
                query = "SELECT books.name, CONCAT(i.chapter,':',i.verse) as cv, text.text "
                query += "FROM bible_"+self.trans+" text "
                query += "LEFT JOIN bible_index i ON i.id = text.id "
                query += "LEFT JOIN bible_books books on i.book = books.id "
                query += "WHERE text.id = ( SELECT id FROM bible_index WHERE book = ( "
                query += "SELECT id FROM bible_books WHERE id = '"+str(book_id)+"') "
                query += "AND chapter = '"+str(chapter1)+"' AND verse = '"+str(verse1)+"')"
                self.cursor.execute(query)
                rows = self.cursor.fetchall()
                if not rows:
                    res['error'] = 'invalid verse definition'
                    return res

                res['verses'] = self.__build_verses(rows)
                self.__disconnectDB()
                return res

            else:
                res['error'] = 'incorrect verse definition'
                return res
        except:
            res['error'] = 'doh.  meltdown'

    def __db2irc(self, data):
        data = re.sub('\\\i1 ','[',data)
        data = re.sub('\\\i0 ',']',data)
        return data

    def __build_verses(self, rows):
        verses = []
        for row in rows:
            v = {}
            v['book'] = row[0]
            v['cv'] = row[1]
            if self.trans == 'net':
                v['text'] = html2text(row[2]).strip()
            else:
                v['text'] = self.__db2irc(row[2])
            verses.append(v)
        return verses

    def __connectDB(self):
        return None  # mysql db no longer exists
        #self.conn = MySQLdb.connect(
        #    host = None,
        #    port = 3307,
        #    user = None,
        #    passwd = None,
        #    db = 'bible')
        #self.cursor = self.conn.cursor()

    def __disconnectDB(self):
        self.cursor.close()
        self.conn.close()

    def nasb(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('nasb')
        args.reverse()
        self.b(irc, msg, args)
        return

    def niv(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('niv')
        args.reverse()
        self.b(irc, msg, args)
        return

    def nkjv(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('nkjv')
        args.reverse()
        self.b(irc, msg, args)
        return

    def nlt(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('nlt')
        args.reverse()
        self.b(irc, msg, args)
        return

    def msg(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('msg')
        args.reverse()
        self.b(irc, msg, args)
        return

    def nrsv(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('nrsv')
        args.reverse()
        self.b(irc, msg, args)
        return

    def bible(self, irc, msg, args):
        url = "http://labs.bible.org/api/?passage="
        verse = urllib.urlopen(url+urllib.quote(' '.join(args))).read()
        verse = verse.replace("<b>", "<")
        verse = verse.replace("</b>", ">")
        irc.reply(verse)
        return
        #args = list(args)
        #args.reverse()
        #args.append('net')
        #args.reverse()
        #self.b(irc, msg, args)
        #return

Class = Bible

# vim:set tabstop=4 shiftwidth=4 softtabstop=4 expandtab textwidth=79:
