import argparse
import json
import logging
import os
import sys
from .api import Scryfall

#region Command line parsing  # noqa


class ColorLogFormatter(logging.Formatter):
    '''
    Custom formatter that changes the color of logs based on the log level.
    '''

    grey = "\x1b[38;20m"
    green = "\u001b[32m"
    yellow = "\x1b[33;20m"
    red = "\x1b[31;20m"
    bold_red = "\x1b[31;1m"
    blue = "\u001b[34m"
    cyan = "\u001b[36m"
    reset = "\x1b[0m"

    timestamp = '%(asctime)s - '
    loglevel = '%(levelname)s'
    message = ' - %(message)s'

    FORMATS = {
        logging.DEBUG:    timestamp + blue + loglevel + reset + message,
        logging.INFO:     timestamp + green + loglevel + reset + message,
        logging.WARNING:  timestamp + yellow + loglevel + reset + message,
        logging.ERROR:    timestamp + red + loglevel + reset + message,
        logging.CRITICAL: timestamp + bold_red + loglevel + reset + message
    }

    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(log_fmt)
        return formatter.format(record)


def _init_logger(level=logging.INFO):
    logger = logging.getLogger()
    logger.setLevel(level)

    formatter = ColorLogFormatter()
    # create console handler and set level to debug
    ch = logging.StreamHandler()
    ch.setLevel(level)
    ch.setFormatter(formatter)
    logger.addHandler(ch)


class RawTextArgumentDefaultsHelpFormatter(argparse.ArgumentDefaultsHelpFormatter, argparse.RawTextHelpFormatter):
    pass


#endregion Command line parsing  # noqa

class App:
    def __init__(self) -> None:
        self.args = None
        self.parser = argparse.ArgumentParser(prog='scryfall')
        self.parser.add_argument('-v', '--verbosity',
                                 choices=['critical', 'error', 'warning', 'info', 'debug'],
                                 default='info',
                                 help='Set the logging verbosity level.')
        self.parser.add_argument('--server', default='https://api.scryfall.com', help="The Scryfall server URL.")
        self.parser.add_argument('-i', '--input',
                                 help='A file of card names. Alternatively, a comma-separated list of card names can be provided via stdin.')
        self.parser.add_argument('-o', '--output',
                                 default=os.getcwd(),
                                 help='The output directory.')
        self.parser.set_defaults(func=download_cards)

    def parse_args(self, args=None):
        self.args = self.parser.parse_args(args)

    def run(self):
        if not self.args:
            self.parse_args()
        _init_logger(getattr(logging, self.args.verbosity.upper()))
        logging.debug(f'command-line args: {self.args}')
        self.args.func(self.args)


def list_card_names(file_path=None):
    if file_path:
        with open(file_path, 'r') as f:
            return f.read().splitlines()
    else:
        return [line.strip() for line in sys.stdin]


def download_cards(args):
    for card_name in list_card_names():
        response = Scryfall(args.server).cards_named(card_name)
        response = response.json()
        logging.debug(f'{json.dumps(response)}')
        result = Scryfall(args.server).cards_image(response['id'])
        if result.content:
            with open(f'{card_name}.png', 'wb') as f:
                for chunk in result.iter_content(chunk_size=1024):
                    f.write(chunk)


def main():
    App().run()


if __name__ == '__main__':
    main()
