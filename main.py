import os
import signal
from datetime import datetime, date
from pathlib import Path
from time import sleep

import requests
from PIL.ImageFont import truetype
from dotenv import load_dotenv, find_dotenv
from luma.core.interface.serial import spi, noop
from luma.core.legacy import text, show_message
from luma.core.legacy.font import proportional, CP437_FONT, LCD_FONT
from luma.core.render import canvas
from luma.core.virtual import viewport
from luma.led_matrix.device import max7219

load_dotenv(find_dotenv())
serial = spi(port=0, device=0, gpio=noop())


def get_device(n=None, block_orientation=None, rotate=None, reverse=None):
    return max7219(serial, cascaded=n or 1, block_orientation=block_orientation, rotate=rotate or 0,
                   blocks_arranged_in_reverse_order=reverse)


def display(n, block_orientation, rotate, reverse):
    device = get_device(n=n, block_orientation=block_orientation, rotate=rotate, reverse=reverse)

    while True:
        show_time(device, 10)
        show_motd(device)
        show_date(device)
        show_weather(device)
        show_now_playing(device)


def make_font(name, size):
    font_path = str(Path(__file__).resolve().parent.joinpath('fonts', name))
    return truetype(font_path, size)


def draw_time(device, left_padding, font):
    with canvas(device) as draw:
        now = datetime.now()
        draw.text((left_padding, 0), now.strftime('%H:%M'), fill="white", font=font)
        sleep(1)


def show_time(device, seconds):
    left_padding = 2
    font = make_font("pixelmix.ttf", 8)
    virtual = viewport(device, width=device.width, height=device.height * 2)

    virtual.set_position((0, device.height))
    draw_time(virtual, left_padding, font)

    for i in range(device.height, -1, -1):
        virtual.set_position((0, i))
        sleep(0.1)

    for _ in range(seconds):
        draw_time(virtual, left_padding, font)

    for i in range(device.height):
        virtual.set_position((0, i))
        sleep(0.1)


def draw_message_slide_down(device, words):
    virtual = viewport(device, width=device.width, height=len(words) * 8)

    with canvas(virtual) as draw:
        for i, word in enumerate(words):
            text(draw, (0, i * 8), word, fill="white", font=proportional(CP437_FONT))

    for i in range(virtual.height - device.height):
        virtual.set_position((0, i))
        sleep(0.05)


def show_motd(device):
    response = requests.get('http://192.168.0.5:5000/api/message').json()
    msg = response.get('message', None)

    if not msg:
        return

    draw_separator(device)

    show_message(device, msg, fill='white', font=proportional(LCD_FONT), scroll_delay=0.015)
    sleep(0.5)


def show_date(device):
    draw_separator(device)

    show_message(device, "It's {}".format(date.today().strftime("%B %d, %Y")), fill="white",
                 font=proportional(CP437_FONT), scroll_delay=0.015)
    sleep(0.5)


def show_weather(device):
    draw_separator(device)

    response = requests.get('http://192.168.0.5:5000/api/weather').json()
    weather = response.get('message', None)

    if not weather:
        return

    show_message(device, weather, fill="white", font=proportional(CP437_FONT), scroll_delay=0.015)
    sleep(0.5)


def show_now_playing(device):
    response = requests.get('http://192.168.0.5:5000/api/currently_playing').json()
    current_song = response.get('message', None)

    if not current_song:
        return

    draw_separator(device)

    draw_message_slide_down(device, [" ", "NOW", "PLAY", "ING:", " "])

    show_message(device, current_song, fill="white", font=proportional(CP437_FONT), scroll_delay=0.015)
    sleep(0.5)


def draw_separator(device, delay=0.005):
    line_width = 2

    virtual = viewport(device, width=(device.width * 2), height=device.height)

    with canvas(virtual) as draw:
        draw.line([(device.width, 0), (device.width, 8)], width=line_width, fill="white")

    for i in range(virtual.width - device.width):
        virtual.set_position((i, 0))
        sleep(delay)

    for i in range(virtual.width - device.width + 1):
        virtual.set_position((device.width - i, 0))
        sleep(delay)

    sleep(0.5)


def clear_display():
    device = get_device()

    with canvas(get_device()) as draw:
        draw.rectangle(device.bounding_box, fill="white")
        sleep(0.5)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, clear_display)

    try:
        display(os.getenv('CASCADED', 4), os.getenv('BLOCK_ORIENTATION', -90), os.getenv('ROTATE', 0),
                os.getenv('REVERSE_ORDER', False))
    except KeyboardInterrupt:
        pass
