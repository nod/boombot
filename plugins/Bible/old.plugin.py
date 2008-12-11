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
import MySQLdb
from biblebooks import books
from html2text import html2text

class Bible(callbacks.Plugin):
    def __init__(self, irc):
        self.__parent = super(Bible, self)
        self.__parent.__init__(irc)
        self.trans = 'nasb'
        self.vre = re.compile('([1-3A-Za-z\ ]+)\ ([0-9]{1,4}\:[0-9]{1,4}\-[0-9]{1,4}\:[0-9]{1,4}|[0-9]{1,4}\:[0-9]{1,4}\-[0-9]{1,4}|[0-9]{1,4}\:[0-9]{1,4}|[0-9]{1,4})')
        self.cv0_re = re.compile('([0-9]{1,4})')
        self.cv1_re = re.compile('([0-9]{1,4})\:([0-9]{1,4})')
        self.cv2_re = re.compile('([0-9]{1,4})\:([0-9]{1,4})\-([0-9]{1,4})')
        self.cv3_re = re.compile('([0-9]{1,4})\:([0-9]{1,4})\-([0-9]{1,4})\:([0-9]{1,4})')
        self.cv4_re = re.compile('([0-9]{1,4})\-([0-9]{1,4})')
        self.cv5_re = re.compile('([0-9]{1,4})\-([0-9]{1,4})\:([0-9]{1,4})')
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

    def b(self, irc, msg, args):
        try:
            self.trans = self.translations[args[0]]
            vreq = ' '.join(args[1:]).lower()
        except KeyError:
            vreq = ' '.join(args).lower()
        
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
            ircStr = 'error: %s' % e
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
        self.conn = MySQLdb.connect(
            host = '69.31.131.141',
            user = 'boom',
            passwd = '33ad!',
            db = 'bible')
        self.cursor = self.conn.cursor()

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

    def net(self, irc, msg, args):
        args = list(args)
        args.reverse()
        args.append('net')
        args.reverse()
        self.b(irc, msg, args)
        return

Class = Bible

# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
