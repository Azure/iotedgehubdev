import os
import platform
import unittest
from iotedgehubdev.edgemanager import EdgeManager
from iotedgehubdev.errors import RegistriesLoginError


class TestEdgeManager(unittest.TestCase):

    def test_Login_registries_fail(self):
        module_content = {
            "$edgeAgent": {
                "properties.desired": {
                    "schemaVersion": "1.0",
                    "runtime": {
                        "type": "docker",
                        "settings": {
                            "minDockerVersion": "v1.25",
                            "loggingOptions": "",
                            "registryCredentials": {
                                "a": {
                                    "username": "sa",
                                    "password": "pd",
                                    "address": "a"
                                },
                                "b": {
                                    "address": "b"
                                },
                                "c": {
                                    "address": "c",
                                    "username": "cpd"
                                },
                                "d": {
                                    "address": "d",
                                    "username": "du",
                                    "password": "dpwd"
                                }
                            }
                        }
                    }
                }
            }
        }
        try:
            EdgeManager.login_registries(module_content)
        except RegistriesLoginError as e:
            self.assertEqual(4, len(e.registries()))
            return
        self.fail("No expception throws when registries login fail")

    def test_no_registries(self):
        module_content = {
            "$edgeAgent": {
                "properties.desired": {
                    "schemaVersion": "1.0",
                    "runtime": {}
                }
            }
        }
        try:
            EdgeManager.login_registries(module_content)
        except Exception:
            self.fail("No expception should be raised when there is no registry")

    def test_update_module_twin(self):
        module_content = {
            "$edgeAgent": {},
            "$edgeHub": {},
            "testtwin": {
                "properties.desired": {
                    "sequence": 1,
                    "value": "test"
                }
            }
        }
        hub_conn_str = os.environ['IOTHUB_CONNECTION_STRING']
        device_conn_str = os.environ[platform.system().upper() + '_DEVICE_CONNECTION_STRING']
        edge_manager = EdgeManager(device_conn_str, 'localhost', '', hub_conn_str)
        edge_manager.getOrAddModule('testtwin', True)
        try:
            edge_manager.update_module_twin(module_content)
        except Exception:
            self.fail("No exception should be raised to update module twin here")
