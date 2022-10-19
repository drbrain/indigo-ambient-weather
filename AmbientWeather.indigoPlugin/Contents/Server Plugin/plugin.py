import indigo

from ambient import AmbientWeather

def appleAirQualityPM25(pm25, valid):
    if not valid:
        return 0 # unknown
    elif pm25 < 12:
        return 1 # excellent
    elif pm25 < 35.5:
        return 2 # good
    elif pm25 < 55.5:
        return 3 # fair
    elif pm25 < 150.5:
        return 4 # inferior
    else:
        return 5 # poor

def appleAirQualityPM10(pm10, valid):
    if not valid:
        return 0 # unknown
    elif pm10 < 55:
        return 1 # excellent
    elif pm10 < 155:
        return 2 # good
    elif pm10 < 255:
        return 3 # fair
    elif pm10 < 355:
        return 4 # inferior
    else:
        return 5 # poor

class Plugin(indigo.PluginBase):
    def __init__(self, pluginId, pluginDisplayName, pluginVersion, pluginPrefs):
        indigo.PluginBase.__init__(self, pluginId, pluginDisplayName,
                                   pluginVersion, pluginPrefs)

        self.debug   = pluginPrefs.get("debug", False)
        self.api_key = pluginPrefs.get("apiKey", False)

        self.devices = {}
        self.weather_stations = {}

    def deviceStartComm(self, device):
        if device.deviceTypeId != "station":
            device.updateStateOnServer("onOffState", True)

        if device.id not in self.devices:
            self.devices[device.id] = device

        if device.deviceTypeId == "station":
            self.weather_stations.setdefault(device.address, [])
        else:
            children = self.weather_stations.setdefault(device.address, [])
            children.append(device.id)

    def deviceStopComm(self, device):
        if device.deviceTypeId != "station":
            device.updateStateOnServer("onOffState", False)

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

                aqi = device.states["aqi_pm25_aqin"]
                pm25 = device.states["pm25_in_aqin"]
                pm10 = device.states["pm10_in_aqin"]

                dewpoint = device.states["dewPointin"]
                temp = device.states["tempinf"]

                valid = temp - dewpoint > 3.6

                appleAirQuality = max(appleAirQualityPM25(pm25, valid), appleAirQualityPM10(pm10, valid))

                child.updateStateOnServer("sensorValue", aqi)
                child.updateStateOnServer("aqi", aqi)
                child.updateStateOnServer("co2", device.states["co2_in_aqin"])
                child.updateStateOnServer("pm25", pm25)
                child.updateStateOnServer("pm10", pm10)
                child.updateStateOnServer("appleAirQuality", appleAirQuality)
                child.updateStateOnServer("valid", valid)

            if child.deviceTypeId == "PM25":
                self.debugLog("Updating PM25 %s" % child.address)

                aqi = device.states["aqi_pm25"]
                pm25 = device.states["pm25"]

                dewpoint = device.states["dewPoint"]
                temp = device.states["tempf"]

                valid = temp - dewpoint > 3.6

                child.updateStateOnServer("sensorValue", aqi)
                child.updateStateOnServer("aqi", aqi)
                child.updateStateOnServer("pm25", pm25)
                child.updateStateOnServer("appleAirQuality", appleAirQualityPM25(pm25, valid))
                child.updateStateOnServer("valid", valid)

    def updateAll(self):
        for _, device in iter(self.devices.items()):
            self.update(device)

    def runConcurrentThread(self):
        while True:
            if len(self.devices) > 0:
                self.updateAll()

            self.sleep(300)

