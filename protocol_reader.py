import os
import re
from collections import defaultdict

import requests

minecraft_version = '1.20.3'
base_url = (
    f'https://raw.githubusercontent.com/PrismarineJS/minecraft-data/refs/heads/master/data/pc/{minecraft_version}'
)
version_url = f'{base_url}/version.json'
protocol_url = f'{base_url}/protocol.json'

# get also entities to constants:


def get_version():
    return requests.get(version_url).json()


def get_protocol_json():
    return requests.get(protocol_url).json()


protocol = get_protocol_json()
version = get_version()

protocol_types = protocol['types']

type_mapping = {
    'varint': 'VarInt',
    'optvarint': 'VarInt',
    'u8': 'UByte',
    'u16': 'UShort',
    'u32': 'UInt',
    'u64': 'ULong',
    'i8': 'Byte',
    'i16': 'Short',
    'i32': 'Int',
    'i64': 'Long',
    'bool': 'Boolean',
    'f32': 'Float',
    'f64': 'Double',
    'UUID': 'UUID',
    'string': 'String',
}


def get_protocol() -> list[dict]:
    packets = []
    for state in protocol.keys():
        if state == 'types':
            continue
        for direction in ('toClient', 'toServer'):
            code_to_name_mapping = protocol[state][direction]['types']['packet'][1][0]['type'][1]['mappings']
            reversed_mapping = {v: k for k, v in code_to_name_mapping.items()}
            for packet in protocol[state][direction]['types'].keys():
                if packet == 'packet':
                    continue
                packet_name = packet.replace('packet_', '', 1)
                fields = protocol[state][direction]['types'][packet][1]
                packets.append(
                    {
                        'state': state,
                        'direction': direction,
                        'name': packet_name,
                        'id': reversed_mapping[packet_name],
                        'fields': fields,
                    },
                )
    return packets


def underscore_to_class_name(underscore_name: str) -> str:
    # Split the string by underscores, capitalize each part, and join them together
    return ''.join(word.capitalize() for word in underscore_name.split('_'))


def camel_to_snake(class_name: str) -> str:
    # Insert underscores before capital letters and convert to lowercase
    return re.sub(r'(?<!^)(?=[A-Z][a-z])', '_', re.sub(r'([A-Z]+)([A-Z][a-z])', r'\1_\2', class_name)).lower()


def generate_outbound_schema(parsed_protocol: list[dict]):
    def module_factory() -> str:
        return """from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import OutboundEvent
from mc_protocol.mc_types import *

        """

    modules: dict[str, str] = defaultdict(module_factory)
    for packet in parsed_protocol:
        if packet['direction'] == 'toClient':
            continue
        init_params = []
        init_attributes = []
        payload = []
        class_name = underscore_to_class_name(packet['name'])
        if not class_name.endswith('Request'):
            class_name += 'Request'
        cannot_parse = False
        for field in packet['fields']:
            try:
                field_type = field['type']
                if isinstance(field_type, list):
                    field_type = next(iter([t for t in field_type if isinstance(t, str) and t in type_mapping.keys()]))
                mapped_type = type_mapping[field_type]
            except Exception:
                print(f'Cannot parse field {field} in packet {packet["name"]}')
                cannot_parse = True
                break
            field_name = field['name']
            if field_name == 'payload':
                field_name = 'data'
            init_params.append(
                f'{camel_to_snake(field_name)}: {mapped_type},',
            )
            init_attributes.append(
                f'        self.{camel_to_snake(field_name)} = {camel_to_snake(field_name)}',
            )
            payload.append(
                f'self.{camel_to_snake(field_name)}.bytes',
            )
        if cannot_parse:
            continue
        if not packet['fields']:
            modules[
                packet['state']
            ] += f"""
class {class_name}(OutboundEvent):
    packet_id = {packet['id']}
    state = ConnectionState.{packet['state'].upper()}

            """
            continue
        init_params_str = ' '.join(init_params)
        init_attributes_str = '\n'.join(init_attributes)
        payload_str = ' + '.join(payload)

        modules[
            packet['state']
        ] += f"""
class {class_name}(OutboundEvent):
    packet_id = {packet['id']}
    state = ConnectionState.{packet['state'].upper()}

    def __init__(
        self,
        {init_params_str}
    ) -> None:
{init_attributes_str}

    @property
    def payload(self) -> bytes:
        return {payload_str}

        """
    return modules


def generate_inbound_schema(parsed_protocol: list[dict]):
    def module_factory():
        return """from mc_protocol.states.enums import ConnectionState
from mc_protocol.states.events import InboundEvent
from mc_protocol.mc_types import *

            """

    modules: dict[str, str] = defaultdict(module_factory)
    for packet in parsed_protocol:
        if packet['direction'] == 'toServer':
            continue
        init_params = []
        init_attributes = []
        from_stream = []
        class_name = underscore_to_class_name(packet['name'])
        if not class_name.endswith('Response'):
            class_name += 'Response'
        cannot_parse = False
        for field in packet['fields']:
            try:
                field_type = field['type']
                if isinstance(field_type, list):
                    field_type = next(iter([t for t in field_type if isinstance(t, str) and t in type_mapping.keys()]))
                mapped_type = type_mapping[field_type]
            except Exception:
                print(f'Cannot parse field {field} in packet {packet["name"]}')
                cannot_parse = True
                break
            field_name = field['name']
            if field_name == 'payload':
                field_name = 'data'
            snake_case_field = camel_to_snake(field_name)
            init_params.append(
                f'{snake_case_field}: {mapped_type},',
            )
            init_attributes.append(
                f'        self.{snake_case_field} = {snake_case_field}',
            )
            from_stream.append(
                f'{snake_case_field}=await {mapped_type}.from_stream(reader)',
            )
        if cannot_parse:
            continue
        if not packet['fields']:
            modules[
                packet['state']
            ] += f"""
class {class_name}(InboundEvent):
    packet_id = {packet['id']}
    state = ConnectionState.{packet['state'].upper()}

            """
            continue
        init_params_str = ' '.join(init_params)
        init_attributes_str = '\n'.join(init_attributes)
        from_stream_str = ','.join(from_stream)

        modules[
            packet['state']
        ] += f"""
class {class_name}(InboundEvent):
    packet_id = {packet['id']}
    state = ConnectionState.{packet['state'].upper()}

    def __init__(
        self,
        {init_params_str}
    ) -> None:
{init_attributes_str}

    @classmethod
    async def from_stream(cls, reader: SocketReader) -> '{class_name}':
        return cls(
            {from_stream_str}
        )

        """
    return modules


pc = get_protocol()
outbound_schema = generate_outbound_schema(pc)
inbound_schema = generate_inbound_schema(pc)

version_path = f'mc_protocol/protocols/v{version["version"]}'
os.makedirs(f'{version_path}/outbound', exist_ok=True)
os.makedirs(f'{version_path}/inbound', exist_ok=True)

open(f'{version_path}/outbound/__init__.py', 'w').write('')
open(f'{version_path}/inbound/__init__.py', 'w').write('')
open(f'{version_path}/__init__.py', 'w').write('')
open('mc_protocol/protocols/__init__.py', 'w').write('')
for module in outbound_schema.keys():
    open(f'{version_path}/outbound/{module}.py', 'w').write(outbound_schema[module])

for module in inbound_schema.keys():
    open(f'{version_path}/inbound/{module}.py', 'w').write(inbound_schema[module])
