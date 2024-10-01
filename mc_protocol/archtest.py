import asyncio
from asyncio import StreamReader
from collections import defaultdict
from enum import Enum

from mc_protocol.utils import AsyncBytesIO

all_events = '*'

class Event(str, Enum):
    DAMAGED = 'damaged'


class SimpleEvent:
    event_id: Event
    reader: StreamReader | AsyncBytesIO


class EventLoop:
    subscribers: dict[int: dict[int | all_events, callable[[SimpleEvent], []]]] = defaultdict(list)

    @classmethod
    def subscribe(cls, klass, callback_method, event_id: int):
        # decorator can be used for methods and classes
        cls.subscribers[klass.state][event_id].append(callback_method)

    async def publish(self, state: str, event: SimpleEvent):
        tasks = []
        for callback in (self.subscribers[state].get(all_events, []) + self.subscribers[state][event.event_id]):
            tasks.append(callback(event))
        await asyncio.gather(tasks)


class ConcreteObserver:
    state = 'play'

    @EventLoop.subscribe(Event.DAMAGED)
    async def on_damaged(self, event: SimpleEvent):
        pass
