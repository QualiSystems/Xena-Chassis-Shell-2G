from cloudshell.traffic.tg import TrafficDriver

from xena_handler import XenaHandler


class XenaChassisDriver(TrafficDriver):
    def __init__(self) -> None:
        self.handler = XenaHandler()

    def initialize(self, context) -> None:
        super().initialize(context)

    def cleanup(self) -> None:
        super().cleanup()

    def get_inventory(self, context):
        return super().get_inventory(context)
