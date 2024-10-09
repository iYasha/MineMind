from minemind import DEBUG_PROTOCOL
from minemind.client import Client
from minemind.mc_types import String, UShort, VarInt
from minemind.protocols.enums import ConnectionState, HandshakingNextState
from minemind.protocols.utils import get_logger
from minemind.protocols.v765.outbound.handshaking import SetProtocolRequest

logger = get_logger('Handshake')


async def handshake(client: Client, next_state: HandshakingNextState):
    client.state = ConnectionState.HANDSHAKING
    request = SetProtocolRequest(
        VarInt(client.protocol_version),
        String(client.host),
        UShort(client.port),
        VarInt(next_state.value),
    )
    await client.send_packet(request)

    if next_state == HandshakingNextState.LOGIN:
        client.state = ConnectionState.LOGIN
    elif next_state == HandshakingNextState.STATUS:
        client.state = ConnectionState.STATUS
    else:
        raise ValueError(f'Invalid next state: {next_state}')
    logger.log(DEBUG_PROTOCOL, f'Handshake finished. Switching to {client.state.name} state')
