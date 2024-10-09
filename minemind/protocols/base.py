from minemind.dispatcher import EventDispatcher


class InteractionModule:

    def __new__(cls, *args, **kwargs):
        instance = super().__new__(cls)
        EventDispatcher.add_callback_instance(instance)
        return instance

    def __del__(self):
        EventDispatcher.remove_callback_instance(self)
