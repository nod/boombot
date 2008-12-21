from django.core import validators
from django.utils.translation import ugettext as _
from django.conf import settings

def isBadwareURL(field_data, all_data):
    import urllib2
    try:
        try:
            validators.isValidURL(field_data,all_data)
        except validators.ValidationError:
            raise validators.ValidationError(_("A valid URL is required."))
	req = urllib2.Request("http://thejaswi.info/badware_check/?badware_url=%s" %(field_data), None, \
				{"User-Agent":settings.URL_VALIDATOR_USER_AGENT})
        u = urllib2.urlopen(req)
        output =  u.read().strip()
        if output == "None":
            return
        elif output == "M":
            raise validators.ValidationError(_("""For Malware Detection:\n-----------------------\nThis page appears to contain malicious code that could be downloaded to your computer without your consent. You can learn more about harmful web content including viruses and other malicious code and how to protect your computer at StopBadware.org.\n\nAdvisory Provided by Google: Check http://code.google.com/support/bin/answer.py?answer=70015\n---------------------------------------------------------------------------------------------\nGoogle works to provide the most accurate and up-to-date phishing and malware information.However, it cannot guarantee that its information is comprehensive and error-free: some risky sites may not be identified, and some safe sites may be identified in error."""))
        else:
            raise validators.ValidationError(_("""For Blacklist Detection:\n-------------------------\nThis page may be a forgery or imitation of another website, designed to trick users into sharing personal or financial information. Entering any personal information on this page may result in identity theft or other abuse. You can find out more about phishing from www.antiphishing.org.\n\nAdvisory Provided by Google: Check http://code.google.com/support/bin/answer.py?answer=70015\n---------------------------------------------------------------------------------------------\nGoogle works to provide the most accurate and up-to-date phishing and malware information.However, it cannot guarantee that its information is comprehensive and error-free: some risky sites may not be identified, and some safe sites may be identified in error."""))
    except urllib2.URLError:
        return -1
