#!/usr/bin/python

import re

try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite

try:
    from hashlib import md5
except ImportError:
    import md5

url_re = re.compile("^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")

class Lookup(object):
    def __init__(self,dbname):
        """
        For URL parsing refer to RFC 2396
        http://www.ietf.org/rfc/rfc2396.txt

        For the url http://a.b.c.d.e.f.g/1.html?param=1#Tag the client will try these possible strings:
        a.b.c.d.e.f.g/1.html?param=1#Tag
        a.b.c.d.e.f.g/1.html?param=1
        a.b.c.d.e.f.g/1.html
        a.b.c.d.e.f.g/        
        c.d.e.f.g/1.html?param=1#Tag
        c.d.e.f.g/1.html?param=1
        c.d.e.f.g/1.html
        c.d.e.f.g/
        d.e.f.g/1.html?param=1#Tag
        d.e.f.g/1.html?param=1
        d.e.f.g/1.html
        d.e.f.g/
        e.f.g/1.html?param=1#Tag
        e.f.g/1.html?param=1
        e.f.g/1.html
        e.f.g/
        f.g/1.html?param=1#Tag
        f.g/1.html?param=1
        f.g/1.html
        f.g/

        Refer to http://code.google.com/apis/safebrowsing/ for more details.
        """
        self.dbname = dbname

    def lookup_by_url(self, url):
        """
        Lookup Method by URL.
        """
        self.url = url.lower()
        try:
            conn = sqlite.connect(self.dbname)
            cur = conn.cursor()
        except sqlite.DatabaseError:
            raise Exception("Database Specific Error")
        
        # Break URL into components
        url_components = url_re.match(self.url).groups()

        # Prepare the lookup list as given in the main docstring.
        self.lookup_list = []
        hostname = url_components[3]
        try:
            hostname_5_comp = hostname.split(".")[-5:]
        except AttributeError:
            raise AttributeError("Invalid URL.")
        for i in xrange(5):
            self.lookup_list.append(".".join(hostname_5_comp[i:])+"/")
            if not url_components[4] == None:
                self.lookup_list.append(".".join(hostname_5_comp[i:])+url_components[4])
                if not url_components[5] == None:
                    self.lookup_list.append(".".join(hostname_5_comp[i:])+''.join(url_components[4:6]))
                    if not url_components[7] == None:
                        self.lookup_list.append(".".join(hostname_5_comp[i:])+''.join(url_components[4:6])+url_components[7])
            
        # Prepare the MD5 hash list for lookups.
        md5_hash_list = []
        for url_comp in self.lookup_list:
            md5_hash_list.append(md5(url_comp).hexdigest())
        for md5_hash in md5_hash_list:
            cur.execute("select * from url_hashes_table where url_hash='%s';" %(md5_hash))
            row = cur.fetchall()
            try:
                assert row
                # If row is non-empty then the URL is in 
                # database and stop operation by returning 1
                if row[0][0] == "M":
                    return "M"
                else:
                    return "B"
            except AssertionError:
                continue
        cur.close()
        conn.close()
        return None           
              

    def lookup_by_md5(self, md5):
        """
        Lookup by MD5 hash.
        """
        self.md5 = md5
        try:
            conn = sqlite.connect(self.dbname)
            cur = conn.cursor()
            cur.execute("select * from url_hashes_table url_hash='%s';" %(self.md5))
            row = cur.fetchall()
        except sqlite.DatabaseError:
            raise Exception("Database Specific Error")
        try:
            assert row
            if row[0][0] == "M":
                return "M"
            else:
                return "B"                   
        except AssertionError:
            pass
        cur.close()
        conn.close()
        return None
            
