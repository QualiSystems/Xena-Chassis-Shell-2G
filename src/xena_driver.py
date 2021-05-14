from cloudshell.traffic.tg import TrafficDriver

from xena_handler import XenaHandler


class XenaChassisDriver(TrafficDriver):
    def __init__(self):
        self.handler = XenaHandler()

    def initialize(self, context):
        super().initialize(context)

    def cleanup(self):
        super().cleanup()

    def get_inventory(self, context):
        return super().get_inventory(context)
