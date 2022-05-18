import io
import json
import os
import time
from pathlib import Path

import spotipy
from dotenv import load_dotenv
from luma.core.interface.serial import spi, noop
from luma.core.legacy import show_message
from luma.core.legacy.font import proportional, CP437_FONT
from luma.led_matrix.device import max7219

load_dotenv()
filename = Path(os.getenv('JSON_FILE'))


def display(n, block_orientation, rotate, reverse):
    serial = spi(port=0, device=0, gpio=noop())
    device = max7219(serial, cascaded=n or 1, block_orientation=block_orientation,
                     rotate=rotate or 0, blocks_arranged_in_reverse_order=reverse)

    while True:
        msg = load_text()
        show_message(device, msg, fill="white", font=proportional(CP437_FONT))
        time.sleep(0.5)


def load_text():
    message = read_value('message')
    auth_token = read_value('auth_token')
    sp = spotipy.Spotify(auth=auth_token)

    return '{} ::: {}'.format(message, sp.currently_playing()['item']['name'])


def read_value(value):
    create_file()
    f = open(filename)
    data = json.load(f)
    result = data.get(value, '')
    f.close()
    return result


def create_file():
    if not os.path.isfile(filename) or not os.access(filename, os.R_OK):
        with io.open(filename, 'w') as db_file:
            db_file.write(json.dumps({}))


if __name__ == "__main__":
    try:
        display(os.getenv('CASCADED', 4), os.getenv('BLOCK_ORIENTATION', -90), os.getenv('ROTATE', 0), os.getenv('REVERSE_ORDER', False))
    except KeyboardInterrupt:
        pass
