# type: ignore
import requests

minecraft_version = '1.20.3'

base_url = (
    f'https://raw.githubusercontent.com/PrismarineJS/minecraft-data/refs/heads/master/data/pc/{minecraft_version}'
)
# Need https://raw.githubusercontent.com/PrismarineJS/minecraft-data/refs/heads/master/data/pc/1.20.3/blocks.json
# https://github.com/PrismarineJS/minecraft-data/blob/master/data/pc/1.20.2/biomes.json
version_url = f'{base_url}/version.json'
entities_url = f'{base_url}/entities.json'


def get_version():
    return requests.get(version_url).json()


version = get_version()
path_to_constants = f'mc_protocol/protocols/v{version["version"]}/constants.py'


def get_entities():
    return requests.get(entities_url).json()


def save_constants(constants: dict[str, any]):
    # stupid way to save python obj
    constant_file = ''
    for key, value in constants.items():
        constant_file += f'{key} = {value}\n'
    with open(path_to_constants, 'w') as f:
        f.write(constant_file)


if __name__ == '__main__':
    entities = get_entities()
    constants = {}

    mapped_entities = {}
    for entity in entities:
        entity_id = entity.pop('id')
        entity.pop('metadataKeys')
        entity.pop('internalId')
        mapped_entities[entity_id] = entity

    constants['ENTITIES'] = mapped_entities
    save_constants(constants)
