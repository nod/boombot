import re
import urllib2
import string
try:
    import sqlite3 as sqlite
except ImportError:
    from pysqlite2 import dbapi2 as sqlite

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
                                                            
