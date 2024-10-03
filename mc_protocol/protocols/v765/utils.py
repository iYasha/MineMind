from mc_protocol.client import Client
from mc_protocol.mc_types import String, UShort, VarInt
from mc_protocol.protocols.v765.outbound.handshaking import SetProtocolRequest
from mc_protocol.states.enums import ConnectionState, HandshakingNextState


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
