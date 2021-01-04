from datetime import datetime
import simplejson as json
import string
import urllib2

class AmbientWeather:
    # Don't steal my application key, go generate your own:
    #
    #  https://dashboard.ambientweather.net/account
    #
    application_key = "6gmfmlc4csrpm63i436p4lgx6lrcl0x0999pfxpifg49mc6i4m6g19p4xs61l3c9"

    obfuscate = string.maketrans(
            "4c160ptnvbahjdy5zwe2uo87qklxfim3srg9",
            "abcdefghijklmnopqrstuvwxyz0123456789")

    def __init__(self, plugin, address):
        self.plugin  = plugin
        self.address = address

        self.api_key = plugin.api_key

        self.application_key = string.translate(AmbientWeather.application_key, AmbientWeather.obfuscate)

    def latest(self):
        device_url = "https://api.ambientweather.net/v1/devices/%s?apiKey=%s&applicationKey=%s&limit=1" % (self.address, self.api_key, self.application_key)

        data = self.__GET(device_url)

        if data == None:
            return

        data = data[0]

        dateutc = datetime.fromtimestamp(data["dateutc"] / 1000)
        data["dateutc"] = dateutc.isoformat()

        for key, value in data.iteritems():
            if key.startswith("batt"):
                data[key] = value == 1

        return data

    def __GET(self, url):
        req = urllib2.Request(url)
        req.add_header("User-Agent", "indigo-ambientweather")

        try:
            f = urllib2.urlopen(req, None, 60)
        except urllib2.HTTPError, e:
            self.plugin.errorLog('Error fetching %s: %s' % (url, str(e)))
            return

        response = json.load(f)

        f.close()

        return response

