# Copy to config.py on the device (or deploy via tools/flash.sh).

WIFI_SSID = "REPLACE-ME"
WIFI_PSK = "REPLACE-ME"

# One or more ICAO identifiers. Press B / C on the badge to cycle.
# First entry is the default on boot when there's no saved selection.
METAR_STATIONS = ["KLBB", "KAUS", "KDFW"]

# How often to re-fetch the METAR for the currently-displayed station.
# aviationweather.gov updates hourly; 15 min is a polite cadence.
REFRESH_MINUTES = 15

# Auto-rotate the displayed station every N minutes. 0 disables.
AUTO_CYCLE_MINUTES = 0

# Hours to add to UTC for the sunrise/sunset display (CDT = -5, CST = -6,
# PDT = -7, GMT = 0, CET = +1, IST = +5.5, etc). Defaults to UTC.
TIMEZONE_OFFSET = 0

# Optional per-station primary runway heading in degrees. When set the
# display will compute and show the headwind / crosswind component on
# the clouds line, e.g. "FEW050  HW12 XW5L".
# Example: KLBB has runway 17R whose heading is 170.
RUNWAYS = {
    # "KLBB": 170,
}
