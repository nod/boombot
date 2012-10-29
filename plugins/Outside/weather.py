# found at https://github.com/agabel/python-underground
# modified to not use simplejson

import os
import json
import urllib2

# Setting this for future use
API_VERSION = '1.0'

URL = 'http://api.wunderground.com/api'

FEATURES_STRATUS = (
    'autocomplete',
    'astronomy',
    'conditions',
    'forecast',
    'geolookup',
)

FEATURES_CUMULUS = FEATURES_STRATUS + (
    'forecast7day',
    'hourly',
    'satellite',
    'radar',
    'alerts',
)

FEATURES_ANVIL = FEATURES_CUMULUS + (
    'hourly7day',
    'yesterday',
    'webcams',
)

ADD_ONS = 'history'

FEATURES = (
    'geolookup',
    'conditions',
    'forecast',
    'astronomy',
    'radar',
    'satellite',
    'webcams',
    'history',
    'alerts',
    'hourly',
    'hourly7day',
    'forecast7day',
    'yesterday',
    'autocomplete',
)


class WeatherException(Exception): pass
class WeatherInvalidFeature(WeatherException): pass
class WeatherServerException(WeatherException): pass


class Wunder(object):

    def _get_key(self):
        return os.environ['WUNDERGROUND_KEY']

    def __init__(self, api_version=API_VERSION, timeout=None):
        self.key = self._get_key()
        self.api_version = api_version
        self.timeout = timeout

    def request(self,features=[], location=''):
        feature_string = "/".join(features)
        uri = '%s/%s/%s/q/%s.json' % (URL, self.key, feature_string, location)
        response = urllib2.urlopen(uri,timeout=self.timeout)
        data = response.read()
        return json.loads(data)


class Weather(object):

    @classmethod
    def forecast(cls, loc):
        w = Wunder()
        data = w.request(features=['forecast'], location=loc)
        ret = []
        for d in data['forecast']['txt_forecast']['forecastday'][:4]:
            ret.append('[{}] {}'.format(d['title'], d['fcttext']))
        return '; '.join(ret)

    @classmethod
    def current(cls, loc):
        w = Wunder()
        data = w.request(features=['conditions'], location=loc)
        ret = []
        return 'currently in {}: {}, {} F, feels like {}'.format(
            data['current_observation']['observation_location']['full'],
            data['current_observation']['weather'],
            data['current_observation']['temp_f'],
            data['current_observation']['feelslike_string']
            )

    @classmethod
    def severe(cls, loc):
        w = Wunder()
        data = w.request(features=['alerts'], location=loc)
        ret = []
        for a in data['alerts'][:2]:
            ret.append( '{}: {} (expires: {})'.format(
                a['description'],
                a['message'].replace('\n',' ')[:300],
                a['expires']
                ) )
        return ret


if __name__ == '__main__':

    print "----------- forecast ------------"
    print Weather.forecast('78641')


    print "----------- current ------------"
    print Weather.current('78641')


    print Weather.severe('78641')
    print Weather.severe('08204')
