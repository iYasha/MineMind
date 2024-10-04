import logging
import os

DEBUG_TRACE = logging.DEBUG + 1  # Trace all packets
logging.addLevelName(DEBUG_TRACE, 'DEBUG_TRACE')

DEBUG_PROTOCOL = logging.DEBUG + 2  # Trace all protocol messages
logging.addLevelName(DEBUG_PROTOCOL, 'DEBUG_PROTOCOL')

DEBUG_GAME_EVENTS = logging.DEBUG + 3  # Trace all game events
logging.addLevelName(DEBUG_GAME_EVENTS, 'DEBUG_GAME_EVENTS')

DEBUG_LEVEL = int(os.getenv('DEBUG', -1))
if DEBUG_LEVEL > 3:
    raise ValueError('DEBUG level should be in range 1-3')
DEFAULT_LEVEL = logging.INFO if DEBUG_LEVEL == -1 else logging.DEBUG + DEBUG_LEVEL

logging.basicConfig(
    level=DEFAULT_LEVEL,
    #   format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    format='%(asctime)s | %(levelname)-17s | [%(name)s] | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
)
