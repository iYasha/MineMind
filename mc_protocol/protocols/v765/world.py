import functools
import math
import time
from enum import Enum
from typing import NamedTuple

from mc_protocol import DEBUG_PROTOCOL
from mc_protocol.client import Client
from mc_protocol.dispatcher import EventDispatcher
from mc_protocol.mc_types import Array, Float, Long, Short, UByte, VarInt, UInt
from mc_protocol.mc_types.base import AsyncBytesIO, MCType, SocketReader, Vector3
from mc_protocol.protocols.base import InteractionModule
from mc_protocol.protocols.utils import get_logger
from mc_protocol.protocols.v765.constants import BIOMES, BLOCK_COLLISION_SHAPES, BLOCKS, DIMENSIONS
from mc_protocol.protocols.v765.inbound.play import (
    BlockEntityDataResponse,
    ChunkBatchFinishedResponse,
    ChunkBatchStartResponse,
    ChunkDataAndLightResponse,
    LoginResponse,
    RespawnResponse,
    UnloadChunkResponse,
    UpdateBlockResponse,
    UpdateSectionBlocksResponse,
)
from mc_protocol.protocols.v765.outbound.play import ChunkBatchReceivedRequest


class PalettedContainer(MCType):
    MAX_BITS_PER_BLOCK = int(
        functools.reduce(lambda high, block: max(high, block["maxStateId"]), BLOCKS, 0),
    ).bit_length()
    MAX_BITS_PER_BIOME = len(BIOMES).bit_length()

    MAX_INDIRECT_PALETTED_BPE_FOR_BLOCK = 8
    MAX_INDIRECT_PALETTED_BPE_FOR_BIOME = 3

    BLOCK_SECTION_VOLUME = 16 * 16 * 16  # SECTION_HEIGHT * SECTION_WIDTH * SECTION_WIDTH
    BIOME_SECTION_VOLUME = int(BLOCK_SECTION_VOLUME / (4 * 4 * 4))

    VALUES_PER_LONG_PER_BLOCK = math.floor(64 / MAX_BITS_PER_BLOCK)
    VALUES_PER_LONG_PER_BIOME = math.floor(64 / MAX_BITS_PER_BIOME)

    VALUE_MASK_FOR_BLOCK = (1 << MAX_BITS_PER_BLOCK) - 1
    VALUE_MASK_FOR_BIOME = (1 << MAX_BITS_PER_BIOME) - 1

    class PaletteType(str, Enum):
        SINGLE_VALUED = 'single_valued'
        DIRECT = 'direct'
        INDIRECT = 'indirect'

    class PaletteCategory(str, Enum):
        BLOCK = 'block'
        BIOME = 'biome'

    def __init__(
        self,
        palette_type: 'PalettedContainer.PaletteType',
        palette_category: 'PalettedContainer.PaletteCategory',
        bits_per_entry: int,
        palette: Array[Long | VarInt] | None = None,
        bitset_mask: dict[int, int] = None,
    ):
        self.palette_type = palette_type
        self.palette_category = palette_category
        self.bits_per_entry = bits_per_entry
        self.palette = palette
        self.bitset_mask = bitset_mask
        self.values_per_long = math.floor(64 / bits_per_entry) if bits_per_entry != 0 else 0
        self.value_mask = (1 << bits_per_entry) - 1 if bits_per_entry != 0 else 0

    @property
    def max_bits_per_entry(self) -> int:
        if self.palette_category == self.PaletteCategory.BLOCK:
            return self.MAX_BITS_PER_BLOCK
        return self.MAX_BITS_PER_BIOME

    def set_masked_value(self, block_index: int, palette_index: int):
        if self.palette_type == self.PaletteType.DIRECT:
            self.bitset_mask[block_index] = palette_index
            return
        start_long_index = math.floor(block_index / self.values_per_long)
        index_in_long = (block_index - start_long_index * self.values_per_long) * self.bits_per_entry
        if index_in_long >= 32:
            index_in_start_long = index_in_long - 32
            self.bitset_mask[start_long_index * 2 + 1] = (
                (self.bitset_mask[start_long_index * 2 + 1] & ~(self.value_mask << index_in_start_long))
                | ((palette_index & self.value_mask) << index_in_start_long)
            ) >> 0
            return
        index_in_start_long = index_in_long
        self.bitset_mask[start_long_index * 2] = (
            (self.bitset_mask[start_long_index * 2] & ~(self.value_mask << index_in_start_long))
            | ((palette_index & self.value_mask) << index_in_start_long)
        ) >> 0
        bit_offset_end = index_in_start_long + self.bits_per_entry
        if bit_offset_end > 32:
            self.bitset_mask[start_long_index * 2 + 1] = (
                (self.bitset_mask[start_long_index * 2 + 1] & ~((1 << (bit_offset_end - 32)) - 1))
                | (palette_index >> (32 - index_in_start_long))
            ) >> 0

    def get_unmasked_palette_index(self, index: int):
        start_long_index = math.floor(index / self.values_per_long)
        index_in_long = (index - start_long_index * self.values_per_long) * self.bits_per_entry
        if index_in_long >= 32:
            index_in_start_long = index_in_long - 32
            start_long = self.bitset_mask[start_long_index * 2 + 1]
            return (start_long >> index_in_start_long) & self.value_mask
        start_long = self.bitset_mask[start_long_index * 2]
        index_in_start_long = index_in_long
        result = start_long >> index_in_start_long
        bit_offset_end = index_in_start_long + self.bits_per_entry
        if bit_offset_end > 32:
            end_long = self.bitset_mask[start_long_index * 2 + 1]
            result |= end_long << (32 - index_in_start_long)
        return result & self.value_mask

    def get_state_id(self, index: int) -> int | None:
        try:
            if self.palette_type == self.PaletteType.SINGLE_VALUED:
                return self.palette[0].int
            if self.palette_type == self.PaletteType.DIRECT:
                return self.bitset_mask[index]
            return self.palette[self.get_unmasked_palette_index(index)].int
        except IndexError:
            return None

    def convert_to_direct_palette(self) -> 'PalettedContainer':
        if self.palette_type == self.PaletteType.DIRECT:
            return self
        new_bitset_mask = {}
        for i in self.bitset_mask:
            new_bitset_mask[i] = self.get_unmasked_palette_index(i)

        self.palette = Array()
        self.bitset_mask = new_bitset_mask
        self.palette_type = self.PaletteType.DIRECT
        return self

    @classmethod
    async def read_bitset_mask(cls, reader: SocketReader) -> dict[int, int]:
        bitset_len = (await VarInt.from_stream(reader)).int * 2
        bitset_mask = {}

        for i in range(0, bitset_len, 2):
            bitset_mask[i + 1] = (await UInt.from_stream(reader)).int
            bitset_mask[i] = (await UInt.from_stream(reader)).int
        return bitset_mask

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs):
        palette_category = kwargs.get('palette_category', cls.PaletteCategory.BLOCK)
        max_indirect_paletted_bpe = (
            cls.MAX_INDIRECT_PALETTED_BPE_FOR_BLOCK
            if palette_category == cls.PaletteCategory.BLOCK
            else cls.MAX_INDIRECT_PALETTED_BPE_FOR_BIOME
        )
        bits_per_entry = (await UByte.from_stream(reader)).int

        if bits_per_entry == 0:
            single_value = await VarInt.from_stream(reader)
            await UByte.from_stream(reader)
            return cls(
                cls.PaletteType.SINGLE_VALUED,
                palette_category,
                bits_per_entry,
                Array([single_value]),
            )

        if bits_per_entry > max_indirect_paletted_bpe:
            return cls(
                cls.PaletteType.DIRECT,
                palette_category,
                bits_per_entry,
                bitset_mask=await cls.read_bitset_mask(reader),
            )

        palette_length = await VarInt.from_stream(reader)
        pallete = await Array[VarInt].from_stream(reader, length=palette_length.int, mc_type=VarInt)
        return cls(
            cls.PaletteType.INDIRECT,
            palette_category,
            bits_per_entry,
            pallete,
            await cls.read_bitset_mask(reader),
        )


class Block:
    BlockState = NamedTuple('BlockState', [('name', str), ('type', str), ('num_values', int), ('values', list[str])])

    def __init__(
        self,
        state_id: int,
        block_id: int,
        name: str,
        display_name: str,
        hardness: float,
        resistance: float,
        stack_size: int,
        diggable: bool,
        material: str,
        transparent: bool,
        emit_light: int,
        filter_light: int,
        default_state: int,
        min_state_id: int,
        max_state_id: int,
        states: list['Block.BlockState'],
        drops: list[int],
        harvest_tools: list[str],
        bounding_box: str,
    ):
        self.state_id = state_id
        self.block_id = block_id
        self.name = name
        self.display_name = display_name
        self.hardness = hardness
        self.resistance = resistance
        self.stack_size = stack_size
        self.diggable = diggable
        self.material = material
        self.transparent = transparent
        self.emit_light = emit_light
        self.filter_light = filter_light
        self.default_state = default_state
        self.min_state_id = min_state_id
        self.max_state_id = max_state_id
        self.states = states
        self.drops = drops
        self.harvest_tools = harvest_tools
        self.bounding_box = bounding_box
        self.position: Vector3 | None = None

    def get_shapes(self) -> list[list[int]]:
        shape_ids = BLOCK_COLLISION_SHAPES['blocks'].get(self.name)
        if shape_ids is None:
            # if no shapes are present for this block (for example, some chemistry stuff we don't have BBs for), assume it's stone
            return BLOCK_COLLISION_SHAPES['shapes'][str(BLOCK_COLLISION_SHAPES['blocks']['stone'])]
        if not isinstance(shape_ids, list):
            return BLOCK_COLLISION_SHAPES['shapes'][str(shape_ids)]
        return [BLOCK_COLLISION_SHAPES['shapes'][str(shape_id)] for shape_id in shape_ids]

    @classmethod
    def from_state_id(cls, state_id: int) -> 'Block | None':
        for block in BLOCKS:
            if block['minStateId'] <= state_id <= block['maxStateId']:
                states = []
                for state in block['states']:
                    values = state.get('values', [])
                    states.append(
                        cls.BlockState(
                            name=state['name'],
                            type=state['type'],
                            num_values=state['num_values'],
                            values=values,
                        ),
                    )
                return cls(
                    state_id=state_id,
                    block_id=block['id'],
                    name=block['name'],
                    display_name=block['displayName'],
                    hardness=block['hardness'],
                    resistance=block['resistance'],
                    stack_size=block['stackSize'],
                    diggable=block['diggable'],
                    material=block['material'],
                    transparent=block['transparent'],
                    emit_light=block['emitLight'],
                    filter_light=block['filterLight'],
                    default_state=block['defaultState'],
                    min_state_id=block['minStateId'],
                    max_state_id=block['maxStateId'],
                    states=states,
                    drops=block['drops'],
                    harvest_tools=block.get('harvestTools', {}).keys(),
                    bounding_box=block['boundingBox'],
                )
        return None

    def __repr__(self):
        return f'<Block {self.name} {self.state_id=}>'

    def get_state(self, name: str) -> dict[str, str | int]:
        return next(iter([state for state in self.states if state.name == name]), {})


class ChunkSection(MCType):

    def __init__(self, solid_block_count: int, block_states: PalettedContainer, biomes: PalettedContainer):
        self.solid_block_count = solid_block_count
        self.block_states = block_states
        self.biomes = biomes

    @classmethod
    async def from_stream(cls, reader: SocketReader, **kwargs):
        solid_block_count = await Short.from_stream(reader)
        block_states = await PalettedContainer.from_stream(
            reader,
            palette_category=PalettedContainer.PaletteCategory.BLOCK,
        )
        biomes = await PalettedContainer.from_stream(
            reader,
            palette_category=PalettedContainer.PaletteCategory.BIOME,
        )
        return cls(solid_block_count.int, block_states, biomes)


class Chunk:
    logger = get_logger('Chunk')

    def __init__(self, min_y: int, world_height: int, chunk_x: int, chunk_z: int):
        self.min_y = min_y
        self.chunk_section_count = world_height >> 4
        self.chunk_x = chunk_x
        self.chunk_z = chunk_z
        self.chunk_sections: Array[ChunkSection] = Array()

    async def set_chunk_sections(self, raw_chunk_sections: bytes):
        reader = AsyncBytesIO(raw_chunk_sections)
        self.chunk_sections = await Array[ChunkSection].from_stream(
            reader,
            length=self.chunk_section_count,
            mc_type=ChunkSection,
        )

    @classmethod
    def get_position_in_chunk(cls, position: Vector3):
        return Vector3(
            x=math.floor(position.x) & 15,
            y=math.floor(position.y),
            z=math.floor(position.z) & 15,
        )

    def set_block_at(self, position: Vector3, state_id: int):
        position_in_chunk = self.get_position_in_chunk(position)
        old_block = self.get_block_at(position)
        try:
            section = self.chunk_sections[(int(position_in_chunk.y) - self.min_y) >> 4]
        except IndexError:
            self.logger.log(
                DEBUG_PROTOCOL,
                f'Trying to set block in a non-existent chunk section at {position=} and {state_id=}. Skipping',
            )
            return

        section_y = (int(position_in_chunk.y) - self.min_y) & 0xF
        block_index = (section_y << 8) | (int(position_in_chunk.z) << 4) | int(position_in_chunk.x)
        if old_block is not None and old_block.state_id == 0 and state_id != 0:
            section.solid_block_count += 1
        elif old_block is not None and old_block.state_id != 0 and state_id == 0:
            section.solid_block_count -= 1

        palette = section.block_states.palette
        palette_index = next(iter([idx for idx, palette in enumerate(palette) if palette.int == state_id]), None)
        if palette_index is None:
            self.logger.log(DEBUG_PROTOCOL, f'State ID {state_id} not found in the palette. Adding it')
            palette_index = len(palette)
            palette.append(VarInt(state_id))
            new_palette_index = len(palette) - 1
            bits_per_entry = new_palette_index.bit_length()
            if (
                bits_per_entry > section.block_states.bits_per_entry
                and bits_per_entry > section.block_states.max_bits_per_entry
            ):
                section.block_states.convert_to_direct_palette().set_masked_value(block_index, new_palette_index)
                return
        section.block_states.set_masked_value(block_index, palette_index)

    def get_block_at(self, position: Vector3) -> Block | None:
        chunk_section_position = self.get_position_in_chunk(position)
        chunk_section_index = (int(chunk_section_position.y) - self.min_y) >> 4
        try:
            section: ChunkSection = self.chunk_sections[chunk_section_index]
        except IndexError:
            return None

        section_y = (int(chunk_section_position.y) - self.min_y) & 0xF
        block_index = (section_y << 8) | (int(chunk_section_position.z) << 4) | int(chunk_section_position.x)
        block_state_id = section.block_states.get_state_id(block_index)

        if block_state_id is None:
            return None

        # # TODO: Stupid way to get block at position, need to refactor this
        block = Block.from_state_id(block_state_id)
        block.position = position.floored()
        return block


class World(InteractionModule):
    logger = get_logger('World')

    def __init__(self, client: Client):
        self.client = client

        self.chunk_batch_start_time = time.time()
        self.weighted_average = 2
        self.old_sample_weight = 1

        self.dimension = 'overworld'
        self.min_y = 0
        self.height = 256
        self.chunks: dict[tuple[int, int], Chunk] = {}

    def get_block_at(self, position: Vector3) -> Block | None:
        self.logger.log(DEBUG_PROTOCOL, f'Getting block at position: {position}')
        chunk = self.get_chunk_at(position.x, position.z)
        if chunk is None:
            return None
        return chunk.get_block_at(position)

    def get_chunk_at(self, x: float, z: float) -> Chunk | None:
        chunk_key = math.floor(x / 16), math.floor(z / 16)
        return self.chunks.get(chunk_key)

    @EventDispatcher.subscribe(LoginResponse, RespawnResponse)
    async def set_world_parameters(self, event: LoginResponse | RespawnResponse):
        self.dimension = event.dimension_type.str.split(':')[1]
        self.min_y = DIMENSIONS[self.dimension]['minY']
        self.height = DIMENSIONS[self.dimension]['height']
        self.logger.log(
            DEBUG_PROTOCOL,
            f'Set dimension: {self.dimension} | Height: {self.height} | Min Y: {self.min_y}',
        )

    @EventDispatcher.subscribe(ChunkBatchStartResponse)
    async def on_chunk_batch_start(self, data: ChunkBatchStartResponse):
        self.chunk_batch_start_time = time.time()

    @EventDispatcher.subscribe(ChunkBatchFinishedResponse)
    async def on_chunk_batch_finish(self, data: ChunkBatchFinishedResponse):
        ms_per_chunk = (time.time() - self.chunk_batch_start_time) * 1000 / data.batch_size.int
        clamped_ms_per_chunk = min(max(ms_per_chunk, self.weighted_average / 3.0), self.weighted_average * 3.0)
        self.weighted_average = ((self.weighted_average * self.old_sample_weight) + clamped_ms_per_chunk) / (
            self.old_sample_weight + 1
        )
        self.old_sample_weight = min(49, self.old_sample_weight + 1)
        await self.client.send_packet(ChunkBatchReceivedRequest(Float(7 / self.weighted_average)))
        self.logger.log(DEBUG_PROTOCOL, f'Chunk batch finished. Average time per chunk: {ms_per_chunk:.2f}ms')

    @EventDispatcher.subscribe(ChunkDataAndLightResponse)
    async def _update_chunk_and_light_data(self, data: ChunkDataAndLightResponse):
        self.logger.log(
            DEBUG_PROTOCOL,
            f'Chunk data and light received. Chunk position: x={data.chunk_x} z={data.chunk_z}',
        )
        chunk_key = (data.chunk_x.int, data.chunk_z.int)
        chunk = self.chunks.get(chunk_key)
        if chunk is None:
            chunk = Chunk(self.min_y, self.height, data.chunk_x.int, data.chunk_z.int)
            await chunk.set_chunk_sections(data.data)
            self.chunks[chunk_key] = chunk
        else:  # update chunk data
            await chunk.set_chunk_sections(data.data)

        if data.block_entities:
            # TODO: Need to finish this.
            for block in data.block_entities:
                self.logger.log(
                    DEBUG_PROTOCOL,
                    f'Received block entity: {BLOCKS[block.block_type.int]["name"]} | '
                    f'Position: x={block.packed_xz.x}, y={block.y.int}, z={block.packed_xz.z}',
                )

    @EventDispatcher.subscribe(UpdateSectionBlocksResponse)
    async def update_chunk_blocks(self, data: UpdateSectionBlocksResponse):
        chunk_position = Vector3(
            x=data.chunk_position.x,
            y=data.chunk_position.y,
            z=data.chunk_position.z,
        ).scale(16)
        chunk = self.get_chunk_at(chunk_position.x, chunk_position.z)
        if not chunk:
            self.logger.log(DEBUG_PROTOCOL, 'Chunk not found')
        for block in data.blocks:
            block_position = chunk_position.offset(block.x, block.y, block.z, inplace=False)
            chunk.set_block_at(block_position, block.state_id)
        self.logger.log(DEBUG_PROTOCOL, f'Updated {len(data.blocks)} blocks in chunk {data.chunk_position}')

    @EventDispatcher.subscribe(UpdateBlockResponse)
    async def _update_block(self, data: UpdateBlockResponse):
        chunk = self.get_chunk_at(data.location.x, data.location.z)
        if not chunk:
            self.logger.log(DEBUG_PROTOCOL, 'Chunk not found')
        position = Vector3(
            x=data.location.x,
            y=data.location.y,
            z=data.location.z,
        )
        chunk.set_block_at(position, data.state_id.int)

    @EventDispatcher.subscribe(UnloadChunkResponse)
    async def _unload_chunk(self, data: UnloadChunkResponse):
        removed_chunk = self.chunks.pop((data.chunk_x.int, data.chunk_z.int), None)
        if removed_chunk:
            self.logger.log(
                DEBUG_PROTOCOL,
                f'Chunk at x={data.chunk_x} z={data.chunk_z} unloaded',
            )

    @EventDispatcher.subscribe(BlockEntityDataResponse)
    async def _block_entity(self, data: BlockEntityDataResponse):
        print(data)
