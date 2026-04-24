WHITE = 15
BLACK = 0
WIDTH = 296
HEIGHT = 128


def _clear_white(display):
    display.set_pen(WHITE)
    display.rectangle(0, 0, WIDTH, HEIGHT)
    display.set_pen(BLACK)


def _battery_v():
    try:
        import machine
        # RP2040 VSYS sits on ADC channel 3 (GP29) via a 3:1 divider on the Pico W.
        vsys = machine.ADC(29)
        raw = vsys.read_u16()
        return raw * 3 * 3.3 / 65535
    except Exception:
        return None


def _battery_label(v):
    if v is None:
        return "Battery:  --"
    if v >= 4.5:
        source = "USB"
    else:
        source = "LiPo"
    return "Battery:  {0:.2f}V {1}".format(v, source)


def _wifi_info():
    try:
        import network
    except ImportError:
        return None
    w = network.WLAN(network.STA_IF)
    if not w.isconnected():
        return {"connected": False}
    try:
        ip = w.ifconfig()[0]
    except Exception:
        ip = None
    try:
        rssi = w.status("rssi")
    except Exception:
        rssi = None
    return {"connected": True, "ip": ip, "rssi": rssi}


def _free_mem():
    try:
        import gc
        gc.collect()
        return gc.mem_free()
    except Exception:
        return None


def _format_wifi_line(info):
    if info is None or not info.get("connected"):
        return "Wi-Fi:    offline"
    rssi = info.get("rssi")
    if rssi is not None:
        return "Wi-Fi:    {0} dBm".format(rssi)
    return "Wi-Fi:    connected"


def render(display, station, updated_z=None):
    _clear_white(display)
    display.set_pen(BLACK)
    display.set_font("bitmap8")

    display.text("Status", 8, 4, scale=2)
    display.text("B back", WIDTH - 60, 8, scale=1)
    display.line(0, 24, WIDTH, 24)

    y = 30
    row_h = 22

    display.text(_battery_label(_battery_v()), 8, y, scale=2)
    y += row_h

    info = _wifi_info()
    display.text(_format_wifi_line(info), 8, y, scale=2)
    y += row_h
    if info is not None and info.get("connected") and info.get("ip"):
        display.text(info["ip"], 8, y, scale=1)
        y += 12

    display.text("Station:  {0}".format(station or "--"), 8, y, scale=2)
    y += row_h

    if updated_z:
        display.text("Last:     {0}Z".format(updated_z), 8, y, scale=2)

    display.update()
