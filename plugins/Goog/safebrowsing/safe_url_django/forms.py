from django.forms.fields import URLField
from django.utils.translation import ugettext as _
from django.forms.util import ValidationError
from django.conf import settings

class Safe_URLField(URLField):
    default_error_messages = {
        'M': _(u"""<strong>For Malware Detection:</strong><br /><br /><hr/>This page appears to contain malicious code that could be downloaded to your computer without your consent. You can learn more about harmful web content including viruses and other malicious code and how to protect your computer at <a href="http://stopbadware.org">StopBadware.org</a>.<br /><br />Advisory Provided by Google: <a href="http://code.google.com/support/bin/answer.py?answer=70015">Check http://code.google.com/support/bin/answer.py?answer=70015</a><br /><br /><a href="http://www.google.com/">Google</a> works to provide the most accurate and uptodate phishing and malware information.However, it cannot guarantee that its information is comprehensive and errorfree: some risky sites may not be identified, and some safe sites may be identified in error."""),        
	'B': _(u"""<strong>For Blacklist Detection:</strong><br /><br /><hr />This page may be a forgery or imitation of another website, designed to trick users into sharing personal or financial information. Entering any personal information on this page may result in identity theft or other abuse. You can find out more about phishing from <a href="http://www.antiphishing.org/">www.antiphishing.org</a>.<br /><br />Advisory Provided by Google: Check <a href="http://code.google.com/support/bin/answer.py?answer=70015">http://code.google.com/support/bin/answer.py?answer=70015</a><br /><br /><a href="http://www.google.com/">Google</a> works to provide the most accurate and uptodate phishing and malware information.However, it cannot guarantee that its information is comprehensive and errorfree: some risky sites may not be identified, and some safe sites may be identified in error."""),
    }

    def __init__(self, max_length=None, min_length=None, badware_check=True, *args, **kwargs):
        self.badware_check = badware_check
        super(Safe_URLField, self).__init__(max_length, min_length, *args,**kwargs)

    def clean(self, value):
        import urllib2
        if value == u'':
            return value
        if value and '://' not in value:
            value = u'http://%s' % value
        try:
	    req = urllib2.Request("http://thejaswi.info/badware_check/?badware_url=%s" %(value), None, {"User-Agent":settings.URL_VALIDATOR_USER_AGENT})
            contents = urllib2.urlopen(req).read()
            if not contents in self.default_error_messages.keys():
                value = super(Safe_URLField, self).clean(value)
		return value
            else:
                raise ValidationError(self.error_messages[contents])
        except urllib2.URLError,e:
            return ValidationError(unicode(e))
        
