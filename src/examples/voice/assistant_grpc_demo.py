#!/usr/bin/env python3
# Copyright 2017 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""A demo of the Google Assistant GRPC recognizer."""

import argparse
import locale
import logging
import signal
import sys
import time

from aiy.assistant.grpc import AssistantServiceClientWithLed
from aiy.assistant import auth_helpers, device_helpers, device_handler_helpers
from aiy.board import Board
from aiy.leds import Leds, Color

logger = logging.getLogger(__name__)

def volume(string):
    value = int(string)
    if value < 0 or value > 100:
        raise argparse.ArgumentTypeError('Volume must be in [0...100] range.')
    return value

def locale_language():
    language, _ = locale.getdefaultlocale()
    return language

def main():
    logging.basicConfig(level=logging.DEBUG)
    signal.signal(signal.SIGTERM, lambda signum, frame: sys.exit(0))

    parser = argparse.ArgumentParser(description='Assistant service example.')
    parser.add_argument('--language', default=locale_language())
    parser.add_argument('--volume', type=volume, default=50)
    args = parser.parse_args()

    credentials = auth_helpers.get_assistant_credentials()
    device_model_id, device_id = device_helpers.get_ids_for_service(credentials)
    device_handler = device_handler_helpers.DeviceRequestHandler(device_id)

    logger.info('device_model_id: %s', device_model_id)
    logger.info('device_id: %s', device_id)

    
    #------------------------------------------------------------------------------
    # Add custom device handlers here
    #------------------------------------------------------------------------------

    @device_handler.command('com.example.commands.BlinkLight')
    def blink(speed, number):
        logging.info('Blinking device %s times.' % number)
        delay = 0.5
        if speed == "SLOWLY":
            delay = 1
        elif speed == "QUICKLY":
            delay = 0.2
        with Leds() as leds:
            for i in range(int(number)):
                logging.info('Device is blinking.')
                leds.update(Leds.rgb_on(Color.BLUE))
                time.sleep(delay)
                leds.update(Leds.rgb_off())
                time.sleep(delay)

    #------------------------------------------------------------------------------

    with Board() as board:
        assistant = AssistantServiceClientWithLed(board=board,
                                                  volume_percentage=args.volume,
                                                  language_code=args.language,
                                                  credentials=credentials,
                                                  device_model_id=device_model_id,
                                                  device_id=device_id,
                                                  device_handler=device_handler)
        while True:
            logging.info('Press button to start conversation...')
            board.button.wait_for_press()
            logging.info('Conversation started!')
            assistant.conversation()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Bye")
