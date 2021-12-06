"""CircuitPython weather display.
"""
# pyright: reportMissingImports=false
# pylint: disable=line-too-long, missing-function-docstring, invalid-name, no-else-return
import time
import board
import busio
from digitalio import DigitalInOut

from adafruit_esp32spi import adafruit_esp32spi
from adafruit_esp32spi import adafruit_esp32spi_wifimanager
from adafruit_esp32spi import PWMOut

import adafruit_rgbled


# from adafruit_fakerequests import Fake_Requests as fr

from sparkfun_serlcd import Sparkfun_SerLCD_UART


try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

print("ESP32 SPI webclient test")

esp32_cs = DigitalInOut(board.GP17)
esp32_ready = DigitalInOut(board.GP14)
esp32_reset = DigitalInOut(board.GP13)

spi = busio.SPI(board.GP18, board.GP19, board.GP16)
esp = adafruit_esp32spi.ESP_SPIcontrol(spi, esp32_cs, esp32_ready, esp32_reset)

# LED setup
RED_LED = PWMOut.PWMOut(esp, 26)
GREEN_LED = PWMOut.PWMOut(esp, 27)
BLUE_LED = PWMOut.PWMOut(esp, 25)

status_light = adafruit_rgbled.RGBLED(RED_LED, BLUE_LED, GREEN_LED)

wifi = adafruit_esp32spi_wifimanager.ESPSPI_WiFiManager(esp, secrets, debug=True)

# Display setup
uart = busio.UART(board.GP12, None)
disp = Sparkfun_SerLCD_UART(uart)

# Weather setup
OPENWEATHER_ENDPOINT = "https://api.openweathermap.org/data/2.5/onecall?lat={lat}&lon={lon}&units={units}&appid={appid}&exclude=minutely,hourly".format(
    lat=secrets["latitude"],
    lon=secrets["longitude"],
    units=secrets["units"],
    appid=secrets["openweather_token"],
)

current_temp = 0
today_temp = 0
rain_chance = 0
uvi = 0


def get_weather():
    global current_temp, today_temp, rain_chance, uvi  # pylint: disable=global-statement
    print("GETting OpenWeather...")
    weather_response = wifi.get(OPENWEATHER_ENDPOINT)
    # weather_response = fr("openweather_sample.json")
    weather_json = weather_response.json()
    print(weather_response.json())
    weather_response.close()
    print("OK!")

    current_temp = weather_json["current"]["temp"]
    today_temp = weather_json["daily"][0]["temp"]["day"]
    rain_chance = weather_json["daily"][0]["pop"]
    uvi = weather_json["daily"][0]["uvi"]


def get_color(temp, rain, uv):
    """
    Returns a color representing the weather conditions, given the temp (ºF), rain chance, and UV index.
    """
    RED = 0xFF0000
    BLUE = 0x0000FF
    GREEN = 0x00FF00
    ORANGE = 0xFFA500
    WHITE = 0xFFFFFF

    if temp < 55 or rain > 0.45:
        return BLUE
    elif temp < 65:
        return GREEN
    elif temp < 76 or uv > 6:
        return ORANGE
    elif temp >= 76 or uv > 8:
        return RED
    else:
        return WHITE


disp.clear()
disp.write("Loading...")
# disp.cursor(True)
get_weather()
print("Now: " + str(current_temp))
print("Today: " + str(today_temp))
print("Rain: " + str(rain_chance))

disp.set_fast_backlight(get_color(current_temp, rain_chance, uvi))

disp.clear()
disp.write("Now: ")  # + str(current_temp) + "°")
disp.write(str(int(current_temp)))

disp.set_cursor(0, 1)

disp.write("Day: ")
disp.write(str(int(today_temp)))

disp.set_cursor(10, 0)
disp.write("UV: ")
disp.write(str(int(uvi)))

if rain_chance != 0:
    disp.set_cursor(9, 1)
    disp.write("Rn: ")
    disp.write(rain_chance)

time.sleep(0.5)  # ugly hack to stop closing uart early
