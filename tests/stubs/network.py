STA_IF = 0


class WLAN:
    def __init__(self, iface):
        self._active = False
        self._connected = False

    def active(self, v=None):
        if v is not None:
            self._active = v
        return self._active

    def connect(self, ssid, psk):
        self._connected = True

    def isconnected(self):
        return self._connected

    def ifconfig(self):
        return ("0.0.0.0", "0.0.0.0", "0.0.0.0", "0.0.0.0")

    def status(self, what=None):
        return 0

    def disconnect(self):
        self._connected = False
