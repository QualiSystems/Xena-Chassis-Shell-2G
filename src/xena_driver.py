"""
Xena chassis shell driver.
"""
import logging

from cloudshell.logging.qs_logger import get_qs_logger
from cloudshell.shell.core.driver_context import AutoLoadDetails, InitCommandContext, ResourceCommandContext
from cloudshell.shell.core.resource_driver_interface import ResourceDriverInterface
from cloudshell.traffic.helpers import get_cs_session
from trafficgenerator.tgn_utils import ApiType
from xenavalkyrie.xena_app import XenaChassis, XenaModule, init_xena
from xenavalkyrie.xena_port import XenaPort

from xena_data_model import GenericTrafficGeneratorModule, GenericTrafficGeneratorPort, XenaChassisShell2G


class XenaChassisDriver(ResourceDriverInterface):
    """Xena chassis shell driver."""

    def __init__(self) -> None:
        """Initialize object variables, actual initialization is performed in initialize method."""
        self.logger: logging.Logger = None
        self.resource: XenaChassisShell2G = None

    def initialize(self, context: InitCommandContext) -> None:
        """Initialize Xena chassis shell (from API)."""
        self.logger = get_qs_logger(log_group="traffic_shells", log_file_prefix=context.resource.name)
        self.logger.setLevel(logging.DEBUG)

    def cleanup(self) -> None:
        """Cleanup Xena chassis shell (from API)."""
        super().cleanup()

    def get_inventory(self, context: ResourceCommandContext) -> AutoLoadDetails:
        """Return device structure with all standard attributes."""
        self.resource = XenaChassisShell2G.create_from_context(context)
        address = context.resource.address
        port = self.resource.controller_tcp_port
        port = int(port) if port else 22611
        encrypted_password = self.resource.password
        self.logger.info(type(context))
        password = get_cs_session(context).DecryptPassword(encrypted_password).Value

        xm = init_xena(ApiType.socket, self.logger, "quali-cs")
        xm.session.add_chassis(address, port, password)
        xm.session.inventory()
        self._load_chassis(xm.session.chassis_list[address])
        return self.resource.create_autoload_details()

    def _load_chassis(self, chassis: XenaChassis) -> None:

        self.resource.model_name = chassis.c_info["c_model"]
        self.resource.serial_number = chassis.c_info["c_serialno"]
        self.resource.vendor = "Xena"
        self.resource.version = chassis.c_info["c_versionno"]

        for module_id, module in chassis.modules.items():
            self._load_module(module_id, module)

    def _load_module(self, module_id: int, module: XenaModule) -> None:
        """Get module resource and attributes."""
        gen_module = GenericTrafficGeneratorModule(f"Module{module_id}")
        self.resource.add_sub_resource(f"M{module_id}", gen_module)
        gen_module.model_name = module.m_info["m_model"]
        gen_module.serial_number = module.m_info["m_serialno"]
        gen_module.version = module.m_info["m_versionno"]

        for port_id, port in module.ports.items():
            self._load_port(gen_module, port_id, port)

    @staticmethod
    def _load_port(gen_module: GenericTrafficGeneratorModule, port_id: int, port: XenaPort) -> None:
        """Get port resource and attributes."""
        gen_port = GenericTrafficGeneratorPort(f"Port{port_id}")
        gen_module.add_sub_resource(f"P{port_id}", gen_port)
        gen_port.max_speed = int(port.p_info["p_speed"])
