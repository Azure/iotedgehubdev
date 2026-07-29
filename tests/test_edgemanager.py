import os
import platform
import unittest
from unittest import mock
from iotedgehubdev.edgemanager import EdgeManager
from iotedgehubdev.errors import EdgeError, RegistriesLoginError


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

    @unittest.skip("Temporarily skipped pending test environment updates; tracked for follow-up.")
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
        except Exception as e:
            self.fail("No exception should be raised to update module twin here: {0}".format(e))

    def _run_stop_with_compose(self, safe_load_return):
        edgedockerclient = mock.MagicMock()
        with mock.patch('iotedgehubdev.edgemanager.os.path.exists', return_value=True), \
                mock.patch('iotedgehubdev.edgemanager.open', mock.mock_open(read_data=''), create=True), \
                mock.patch('iotedgehubdev.edgemanager.yaml.safe_load', return_value=safe_load_return), \
                mock.patch('iotedgehubdev.edgemanager.Utils.exe_proc') as mock_exe_proc:
            EdgeManager.stop(edgedockerclient)
        edgedockerclient.stop_remove_by_label.assert_called_once_with(EdgeManager.LABEL)
        return mock_exe_proc

    def test_stop_runs_compose_down_when_services_present(self):
        mock_exe_proc = self._run_stop_with_compose({'services': {'edgeHub': {}}})
        expected_cmd = "docker compose -f {0} down".format(EdgeManager.COMPOSE_FILE).split()
        mock_exe_proc.assert_called_once_with(expected_cmd)

    def test_stop_skips_compose_down_when_no_services(self):
        for content in [None, {}, {'version': '3.6'}]:
            with self.subTest(content=content):
                mock_exe_proc = self._run_stop_with_compose(content)
                mock_exe_proc.assert_not_called()

    def test_stop_skips_compose_down_when_content_not_a_mapping(self):

        mock_exe_proc = self._run_stop_with_compose('just a string')
        mock_exe_proc.assert_not_called()

    def test_ensure_compose_available_passes_when_plugin_present(self):
        with mock.patch('iotedgehubdev.edgemanager.subprocess.check_call') as mock_check_call:
            EdgeManager._ensure_compose_available()
        mock_check_call.assert_called_once_with(
            ['docker', 'compose', 'version'],
            stdout=mock.ANY, stderr=mock.ANY)

    def test_ensure_compose_available_raises_when_plugin_missing(self):
        with mock.patch('iotedgehubdev.edgemanager.subprocess.check_call',
                        side_effect=OSError('not found')):
            with self.assertRaises(EdgeError):
                EdgeManager._ensure_compose_available()
