# borrowed and merged from
# http://code.google.com/p/safebrowsing-python/
# the license for this file can be found at 
# http://code.google.com/p/safebrowsing-python/source/browse/trunk/LICENSE.txt
#
# This code is the combination of multiple files from the safebrowsing-python
# framework.  Their work is much appreciated.

import re
import urllib2
import string
try:
    from hashlib import md5
except ImportError:
    import md5
try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite

url_re = re.compile("^(([^:/?#]+):)?(//([^/?#]*))?([^?#]*)(\?([^#]*))?(#(.*))?")

class Google_Blacklist(object):
    """
    Google Blacklist class that is used to fetch and prepare hashes to be
    stored in the database.
    """
    def __init__(self,key,url,dbname="",badware_type="malware", initdb=False):
        """
        The constructor initializes the module.
        """
        badware_dict = {"malware": "M","black": "B"}
        self.key = key
        self.dbname = dbname
        self.url = url
        self.badware_type = badware_type
        try:
            self.badware_code = badware_dict[badware_type]
        except KeyError:
            raise KeyError("Invalid Badware Type")
        try:
            assert self.key
            assert self.dbname
            assert self.url
            assert self.badware_type
        except AssertionError:
            raise AssertionError("Key/Dbname/URL is/are missing.")            
        if initdb: self._initialize_db()

    def _initialize_db(self):
        print "DBN:",self.dbname
        conn = sqlite.connect(self.dbname)
        for badtype in "malware","black":
            conn.execute(
                "create table %s_version (version_number string)" % badtype )
        conn.execute("""
            create table url_hashes_table 
            (badware_type string, url_hash string)""" )
        conn.close()

    def fetch_data(self):
            try:
                conn = sqlite.connect(self.dbname)
                cur = conn.cursor()
                cur.execute("select * from %s_version;" %(self.badware_type))
                row = cur.fetchall()
            except sqlite.DatabaseError:
                raise sqlite.DatabaseError("Error in a database specific operation.")
            # TODO: Python 2.5 only, Python 2.4???
            s = string.Template(self.url)
            try:
                assert row
                self.version_number = row[0][0]
            except AssertionError:
                # Start from Version 1:-1
                self.version_number = "1:-1"
            self.final_url = s.safe_substitute(key = self.key,
                                               badware_type = self.badware_type,
                                               version = self.version_number)
            self.fetch_url_pointer = urllib2.urlopen(self.final_url)
            self.url_hashes_data = self.fetch_url_pointer.readlines()
            if self.url_hashes_data == []:
                # No data, so no point checking version 
                # number. This case might be because of
                # throttling or no updates available.
                return 0
            for url_hash in self.url_hashes_data[1:-1]:
                if re.match("^-\w+", url_hash):
                    cur.execute("delete from url_hashes_table where "
                                "badware_type='%s' and url_hash='%s';" %(self.badware_code, url_hash[1:].strip()))
                    del self.url_hashes_data[self.url_hashes_data.index(url_hash)]
            new_version_number = ":".join(re.compile("\d\.\d+").search(self.url_hashes_data[0]).group().split("."))
            if self.version_number == "1:-1":
                self.version_number = new_version_number
                cur.execute("insert into %s_version (version_number) "
                            "values ('%s');" %(self.badware_type, self.version_number))
            else:
                cur.execute("update %s_version set version_number='%s' "
                            "where version_number='%s';" %(self.badware_type, 
                                                           new_version_number, 
                                                           self.version_number))
            for url_hash in self.url_hashes_data[1:]:
                if not url_hash == '\n':
                    cur.execute("insert into url_hashes_table (badware_type,url_hash) values ('%s','%s');" %(self.badware_code, url_hash[1:].strip()))
            cur.close()
            conn.commit()
            conn.close()
            return 0
                                                            
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
            
