import unittest
from iotedgehubdev.edgemanager import EdgeManager
from iotedgehubdev.errors import RegistriesLoginError


class TestEdgeManager(unittest.TestCase):

    def test_LoginRegistries(self):
        moduleContent = {
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
            EdgeManager.loginRegistries(moduleContent)
        except RegistriesLoginError as e:
            self.assertEqual(4, len(e.registries))
            return
        self.fail("No expception throws when registries login fail")
