"""
Tests for XenaChassisDriver.
"""
# pylint: disable=redefined-outer-name
from typing import Iterable

import pytest
from _pytest.fixtures import SubRequest
from cloudshell.api.cloudshell_api import AttributeNameValue, CloudShellAPISession, ResourceInfo
from cloudshell.shell.core.driver_context import AutoLoadCommandContext
from cloudshell.traffic.tg import TGN_CHASSIS_FAMILY, XENA_CHASSIS_MODEL
from shellfoundry_traffic.test_helpers import TestHelpers, create_session_from_config, print_inventory

from xena_driver import XenaChassisDriver


@pytest.fixture(params=[("demo.xenanetworks.com", "22611", "xena", "h8XUgX3gyjY0vKMg0wQxKg==")])
def dut(request: SubRequest) -> list:
    """Yield Xena device under test parameters."""
    return request.param


@pytest.fixture(scope="session")
def session() -> CloudShellAPISession:
    """Yield session."""
    return create_session_from_config()


@pytest.fixture(scope="session")
def test_helpers(session: CloudShellAPISession) -> TestHelpers:
    """Yield initialized TestHelpers object."""
    return TestHelpers(session)


@pytest.fixture
def driver(test_helpers: TestHelpers, dut: list) -> Iterable[XenaChassisDriver]:
    """Yield initialized TestCenterChassisDriver."""
    address, controller_port, _, encrypted_password = dut
    attributes = {
        f"{XENA_CHASSIS_MODEL}.Controller TCP Port": controller_port,
        f"{XENA_CHASSIS_MODEL}.Password": encrypted_password,
    }
    init_context = test_helpers.resource_init_command_context(TGN_CHASSIS_FAMILY, XENA_CHASSIS_MODEL, address, attributes)
    driver = XenaChassisDriver()
    driver.initialize(init_context)
    yield driver
    driver.cleanup()


@pytest.fixture
def autoload_context(test_helpers: TestHelpers, dut: list) -> AutoLoadCommandContext:
    """Yield Xena chassis resource for shell autoload testing."""
    address, controller_port, _, encrypted_password = dut
    attributes = {
        f"{XENA_CHASSIS_MODEL}.Controller TCP Port": controller_port,
        f"{XENA_CHASSIS_MODEL}.Password": encrypted_password,
    }
    return test_helpers.autoload_command_context(TGN_CHASSIS_FAMILY, XENA_CHASSIS_MODEL, address, attributes)


@pytest.fixture
def autoload_resource(session: CloudShellAPISession, test_helpers: TestHelpers, dut: list) -> Iterable[ResourceInfo]:
    """Yield STC resource for shell autoload testing."""
    address, controller_port, password, _ = dut
    attributes = [
        AttributeNameValue(f"{XENA_CHASSIS_MODEL}.Controller TCP Port", controller_port),
        AttributeNameValue(f"{XENA_CHASSIS_MODEL}.Password", password),
    ]
    resource = test_helpers.create_autoload_resource(XENA_CHASSIS_MODEL, "tests/test-xena", address, attributes)
    yield resource
    session.DeleteResource(resource.Name)


def test_autoload(driver: XenaChassisDriver, autoload_context: AutoLoadCommandContext) -> None:
    """Test direct (driver) auto load command."""
    inventory = driver.get_inventory(autoload_context)
    print_inventory(inventory)


def test_autoload_session(session: CloudShellAPISession, autoload_resource: ResourceInfo, dut: dut) -> None:
    """Test indirect (shell) auto load command."""
    session.AutoLoad(autoload_resource.Name)
    resource_details = session.GetResourceDetails(autoload_resource.Name)
    assert len(resource_details.ChildResources) == 1
    assert resource_details.ChildResources[0].FullAddress == f"{dut[0]}/M0"
