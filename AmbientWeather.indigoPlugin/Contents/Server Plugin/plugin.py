import indigo

from ambient import AmbientWeather

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName,
                                   pluginVersion, pluginPrefs)

        self.debug   = pluginPrefs.get('debug', False)
        self.api_key = pluginPrefs.get('apiKey', False)

        self.devices = {}

    def deviceStartComm(self, device):
        if device.id not in self.devices:
            self.devices[device.id] = device

    def deviceStopComm(self, device):
        if device.id in self.devices:
            self.devices.pop(device.id)

    def update(self, device):
        self.debugLog('Updating station %s' % device.address)

        api = AmbientWeather(self, device.address)

        data = api.latest()

        self.debugLog(str(data))

        for key, value in data.iteritems():
            if key == "24hourrainin":
                key = "last24hourrainin"

            device.updateStateOnServer(key, value)

    def updateAll(self):
        for _, device in self.devices.iteritems():
            self.update(device)

    def runConcurrentThread(self):
        while True:
            if len(self.devices) > 0:
                self.updateAll()

            self.sleep(300)

