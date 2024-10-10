from minemind import DEBUG_PROTOCOL
from minemind.client import Client
from minemind.dispatcher import EventDispatcher
from minemind.mc_types import nbt
from minemind.protocols.base import InteractionModule
from minemind.protocols.utils import get_logger
from minemind.protocols.v765.constants import ITEMS
from minemind.protocols.v765.inbound.play import SetContainerContentResponse, SetContainerSlotResponse


class Slot:

    def __init__(self, item_id: int, item_count: int, properties: nbt.NBT | None = None):
        self.item_id = item_id
        item = ITEMS.get(str(item_id), 'Unknown')
        self.item_name = item['name']
        self.stack_size = item['stackSize']
        self.item_count = item_count
        self.properties = properties

    def __repr__(self):
        return f'Slot({self.item_name}, {self.item_count})'


class InventoryWindow:

    def __init__(self):
        self._slots: dict[int, Slot] = {}
        self.state_id = -1
        self.carried_item = None

    def __repr__(self):
        return f'InventoryWindow({self._slots})'

    def set_slot(self, slot_id: int, slot: Slot):
        self._slots[slot_id] = slot


class Inventory(InteractionModule):
    logger = get_logger('Inventory')

    def __init__(self, client: Client):
        self.client = client
        self.window = InventoryWindow()

    @EventDispatcher.subscribe(SetContainerSlotResponse)
    async def set_container_slot(self, data: SetContainerSlotResponse):
        if data.window_id.int != 0:
            self.logger.log(DEBUG_PROTOCOL, f'Ignoring SetContainerSlotResponse for window_id {data.window_id.int}')
            return
        self.window.state_id = data.state_id.int
        if data.slot_data.present.bool:
            self.window.set_slot(
                data.slot.int,
                Slot(
                    item_id=data.slot_data.item_id.int,
                    item_count=data.slot_data.item_count.int,
                    properties=data.slot_data.nbt_data,
                ),
            )

    @EventDispatcher.subscribe(SetContainerContentResponse)
    async def set_container_content(self, data: SetContainerContentResponse):
        if data.window_id.int != 0:
            self.logger.log(DEBUG_PROTOCOL, f'Ignoring SetContainerSlotResponse for window_id {data.window_id.int}')
            return
        self.window.state_id = data.state_id.int
        self.window.carried_item = data.carried_item if data.carried_item.present.bool else None
        for slot_id, slot in enumerate(data.slots):
            if slot.present.bool:
                self.window.set_slot(slot_id, Slot(slot.item_id.int, slot.item_count.int, slot.nbt_data))
