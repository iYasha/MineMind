from enum import Enum

class HandshakingNextState(Enum):
    STATUS = b'\x01'
    LOGIN = b'\x02'
    TRANSFER = b'\x03'


class ConnectionState(str, Enum):
    HANDSHAKING = 'handshaking'
    STATUS = 'status'
    LOGIN = 'login'
    CONFIGURATION = 'configuration'
    PLAY = 'play'

