import indigo

from ambient import AmbientWeather

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName,
                                   pluginVersion, pluginPrefs)

        self.debug   = pluginPrefs.get("debug", False)
        self.api_key = pluginPrefs.get("apiKey", False)

        self.devices = {}
        self.weather_stations = {}

    def deviceStartComm(self, device):
        if device.id not in self.devices:
            self.devices[device.id] = device
        if device.deviceTypeId == "station":
            self.weather_stations.setdefault(device.address, [])
        else:
            children = self.weather_stations.setdefault(device.address, [])
            children.append(device.id)

    def deviceStopComm(self, device):
        if device.id in self.devices:
            self.devices.pop(device.id)

    def update(self, device):
        if device.deviceTypeId != "station":
            return

        self.debugLog("Updating station %s" % device.address)

        api = AmbientWeather(self, device.address)

        data = api.latest()

        if data == None:
            return

        self.debugLog(str(data))

        for key, value in iter(data.items()):
            if key == "24hourrainin":
                key = "last24hourrainin"

            device.updateStateOnServer(key, value)

        children = self.weather_stations.setdefault(device.address, [])

        for childId in children:
            child = indigo.devices[childId]
            
            if child.deviceTypeId == "AQIN":
                self.debugLog("Updating AQIN %s" % child.address)

                child.updateStateOnServer("sensorValue", device.states["aqi_pm25_aqin"])
                child.updateStateOnServer("co2", device.states["co2_in_aqin"])
                child.updateStateOnServer("pm25", device.states["pm25_in_aqin"])
                child.updateStateOnServer("pm10", device.states["pm10_in_aqin"])

            if child.deviceTypeId == "PM25":
                self.debugLog("Updating PM25 %s" % child.address)

                child.updateStateOnServer("sensorValue", device.states["aqi_pm25"])
                child.updateStateOnServer("pm25", device.states["pm25"])

    def updateAll(self):
        for _, device in iter(self.devices.items()):
            self.update(device)

    def runConcurrentThread(self):
        while True:
            if len(self.devices) > 0:
                self.updateAll()

            self.sleep(300)

