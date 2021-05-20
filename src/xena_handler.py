import logging

from cloudshell.shell.core.driver_context import AutoLoadCommandContext, AutoLoadDetails, InitCommandContext
from cloudshell.traffic.helpers import get_cs_session
from cloudshell.traffic.tg import TgChassisHandler
from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import XenaChassis, XenaModule, XenaPort, init_xena

from xena_data_model import GenericTrafficGeneratorModule, GenericTrafficGeneratorPort, XenaChassisShell2G


class XenaHandler(TgChassisHandler):
    def initialize(self, context: InitCommandContext, logger: logging.Logger) -> None:
        resource = XenaChassisShell2G.create_from_context(context)
        super().initialize(resource, logger)

    def load_inventory(self, context: AutoLoadCommandContext) -> AutoLoadDetails:
        """Return device structure with all standard attributes. """
        address = context.resource.address
        port = self.resource.controller_tcp_port
        port = int(port) if port else 22611
        encrypted_password = self.resource.password
        password = get_cs_session(context).DecryptPassword(encrypted_password).Value

        self.xm = init_xena(ApiType.socket, self.logger, "quali-cs")
        self.xm.session.add_chassis(address, port, password)
        self.xm.session.inventory()
        self._load_chassis(self.xm.session.chassis_list[address])
        return self.resource.create_autoload_details()

    def _load_chassis(self, chassis: XenaChassis) -> None:

        self.resource.model_name = chassis.c_info["c_model"]
        self.resource.serial_number = chassis.c_info["c_serialno"]
        self.resource.vendor = "Xena"
        self.resource.version = chassis.c_info["c_versionno"]

        for module_id, module in chassis.modules.items():
            self._load_module(module_id, module)

    def _load_module(self, module_id: int, module: XenaModule) -> None:
        """Get module resource and attributes. """
        gen_module = GenericTrafficGeneratorModule(f"Module{module_id}")
        self.resource.add_sub_resource(f"M{module_id}", gen_module)
        gen_module.model_name = module.m_info["m_model"]
        gen_module.serial_number = module.m_info["m_serialno"]
        gen_module.version = module.m_info["m_versionno"]

        for port_id, port in module.ports.items():
            self._load_port(gen_module, port_id, port)

    def _load_port(self, gen_module: GenericTrafficGeneratorModule, port_id: int, port: XenaPort) -> None:
        """Get port resource and attributes. """
        gen_port = GenericTrafficGeneratorPort(f"Port{port_id}")
        gen_module.add_sub_resource(f"P{port_id}", gen_port)
        gen_port.max_speed = int(port.p_info["p_speed"])
