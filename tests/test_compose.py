import iotedgehubdev.compose_parser
import unittest
from iotedgehubdev.edgemanager import EdgeManager
from iotedgehubdev.composeproject import ComposeProject
import json
import pytest

OUTPUT_PATH = 'tests/output'


class ComposeTest(unittest.TestCase):
    def test_compose(self):
        with open('tests/test_compose_resources/deployment.json') as json_file:
            deployment_config = json.load(json_file)

            module_names = [EdgeManager.EDGEHUB_MODULE]
            custom_modules = deployment_config['moduleContent']['$edgeAgent']['properties.desired']['modules']
            for module_name in custom_modules:
                module_names.append(module_name)

            ConnStr_info = {}
            for module_name in module_names:
                ConnStr_info[module_name] = \
                    "HostName=HostName;DeviceId=DeviceId;ModuleId={};SharedAccessKey=SharedAccessKey".format(module_name)

            env_info = {
                'hub_env': [
                    EdgeManager.HUB_CA_ENV,
                    EdgeManager.HUB_CERT_ENV,
                    EdgeManager.HUB_SRC_ENV,
                    EdgeManager.HUB_SSLPATH_ENV,
                    EdgeManager.HUB_SSLCRT_ENV
                ],
                'module_env': [
                    EdgeManager.MODULE_CA_ENV
                ]
            }

            volume_info = {
                'HUB_MOUNT': EdgeManager.HUB_MOUNT,
                'HUB_VOLUME': EdgeManager.HUB_VOLUME,
                'MODULE_VOLUME': EdgeManager.MODULE_VOLUME,
                'MODULE_MOUNT': EdgeManager.MODULE_MOUNT
            }

            network_info = {
                'NW_NAME': EdgeManager.NW_NAME,
                'ALIASES': 'gatewayhost'
            }

            compose_project = ComposeProject(deployment_config)
            compose_project.set_edge_info({
                'ConnStr_info': ConnStr_info,
                'env_info': env_info,
                'volume_info': volume_info,
                'network_info': network_info,
                'hub_name': EdgeManager.EDGEHUB,
                'labels': EdgeManager.LABEL
            })
            compose_project.compose()
            compose_project.dump('{}/docker-compose_test.yml'.format(OUTPUT_PATH))

            expected_output = open('tests/test_compose_resources/docker-compose.yml', 'r').read()
            actual_output = open('{}/docker-compose_test.yml'.format(OUTPUT_PATH), 'r').read()
            assert ''.join(sorted(expected_output)) == ''.join(sorted(actual_output))

    def test_service_parser_expose(self):
        expose_API = {
            "22/tcp": {}
        }
        expose_list = ["22/tcp"]
        assert expose_list == iotedgehubdev.compose_parser.service_parser_expose({'ExposedPorts': expose_API})

    def test_service_parser_command(self):
        cmd_list = ["bundle", "exec", "thin", "-p", "3000"]
        cmd_str = "bundle exec thin -p 3000"
        assert cmd_str == iotedgehubdev.compose_parser.service_parser_command({'Cmd': cmd_list})

    def test_service_parser_healthcheck(self):
        healthcheck_API = {
            "Test": ["CMD", "curl", "-f", "http://localhost"],
            "Interval": 1000000,
            "Timeout": 1000000,
            "Retries": 5,
            "StartPeriod": 1000000
        }

        healthcheck_dict = {
            "test": ["CMD", "curl", "-f", "http://localhost"],
            "interval": '1ms',
            "timeout": '1ms',
            "retries": 5,
            "start_period": '1ms'
        }
        assert healthcheck_dict == iotedgehubdev.compose_parser.service_parser_healthcheck({'Healthcheck': healthcheck_API})

    def test_invalid_service_parser_healthcheck(self):
        healthcheck_API_keyerr = {
            "Test": ["CMD", "curl", "-f", "http://localhost"],
            "Interval": 1000000,
            "Timeout": 1000000,
            "Retries": 5,
        }
        healthcheck_API_valerr = {
            "Test": ["CMD", "curl", "-f", "http://localhost"],
            "Interval": 10,
            "Timeout": 1000000,
            "Retries": 5,
            "StartPeriod": 1000000
        }
        with pytest.raises(KeyError):
            iotedgehubdev.compose_parser.service_parser_healthcheck({'Healthcheck': healthcheck_API_keyerr})
        with pytest.raises(ValueError):
            iotedgehubdev.compose_parser.service_parser_healthcheck({'Healthcheck': healthcheck_API_valerr})

    def test_service_parser_hostconfig_devices(self):
        devices_API = [
            {
                'PathOnHost': '/dev/random',
                'CgroupPermissions': 'rwm',
                'PathInContainer': '/dev/mapped-random'
            }
        ]
        devices_list = ["/dev/random:/dev/mapped-random:rwm"]
        assert devices_list == iotedgehubdev.compose_parser.service_parser_hostconfig_devices({'Devices': devices_API})

    def test_service_parser_hostconfig_restart(self):
        restart_API = [
            {"Name": "", "MaximumRetryCount": 0},
            {"Name": "always", "MaximumRetryCount": 0},
            {"Name": "unless-stopped", "MaximumRetryCount": 0},
            {"Name": "on-failure", "MaximumRetryCount": 5}
        ]

        restart_list = ["no", "always", "unless-stopped", "on-failure:5"]
        ret = []
        for restart_policy in restart_API:
            ret.append(iotedgehubdev.compose_parser.service_parser_hostconfig_restart({'RestartPolicy': restart_policy}))
        assert ret == restart_list

    def test_invalid_service_parser_hostconfig_restart(self):
        restart_API_keyerr = {"Name": "on-failure"}
        restart_API_valerr = {"Name": "never"}
        with pytest.raises(KeyError):
            iotedgehubdev.compose_parser.service_parser_hostconfig_restart({'RestartPolicy': restart_API_keyerr})
        with pytest.raises(ValueError):
            iotedgehubdev.compose_parser.service_parser_hostconfig_restart({'RestartPolicy': restart_API_valerr})

    def test_parser_hostconfig_ulimits(self):
        ulimits_API = [
            {"Name": "nofile", "Soft": 1024, "Hard": 2048}
        ]

        ulimits_dict = {
            "nofile": {"soft": 1024, "hard": 2048}
        }
        assert ulimits_dict == iotedgehubdev.compose_parser.service_parser_hostconfig_ulimits({'Ulimits': ulimits_API})

    def test_service_parser_hostconfig_logging(self):
        logconfig_API = {
            'Type': 'json-file',
            'Config': {
                'max-size': '200k',
                'max-file': '10'
            }
        }

        logging_dict = {
            'driver': 'json-file',
            'options': {
                'max-size': '200k',
                'max-file': '10'
            }
        }
        assert logging_dict == iotedgehubdev.compose_parser.service_parser_hostconfig_logging({'LogConfig': logconfig_API})

    def test_service_parser_hostconfig_ports(self):
        portsbinding = {
            "22/tcp": [
                {
                    "HostIp": "127.0.0.1",
                    "HostPort": "11022"
                }
            ]
        }
        ports_list = ["127.0.0.1:11022:22/tcp"]
        assert ports_list == iotedgehubdev.compose_parser.service_parser_hostconfig_ports({'PortBindings': portsbinding})

    def test_service_parser_networks(self):
        networkconfig = {
            "isolated_nw": {
                "IPAMConfig": {
                    "IPv4Address": "172.20.30.33",
                    "IPv6Address": "2001:db8:abcd::3033",
                },
                "Aliases": [
                    "server_x",
                    "server_y"
                ]
            }
        }
        network_dict = {
            'isolated_nw': {
                'aliases': [
                    'server_x',
                    'server_y'
                ],
                'ipv4_address': '172.20.30.33',
                'ipv6_address': '2001:db8:abcd::3033'
            }
        }
        assert network_dict == iotedgehubdev.compose_parser.service_parser_networks({'NetworkingConfig': networkconfig})

    def test_service_parser_volumes(self):
        volumes_config = {
            'Mounts': [
                {
                    "Type": "volume",
                    "Source": "edgehubdev",
                    "Target": "/mnt/edgehub",
                    "VolumeOptions": {
                        "NoCopy": False
                    },
                    "ReadOnly": True
                },
                {
                    "Type": "bind",
                    "Source": "/mnt/edgehubdev",
                    "Target": "/mnt/edgehub",
                    "BindOptions": {
                        "Propagation": "shared"
                    }
                },
                {
                    "Type": "tmpfs",
                    "Target": "/mnt/edgehub",
                    "TmpfsOptions": {
                        "SizeBytes": 65536
                    }
                }
            ],
            'Volumes': {
                "/mnt/edgehub": {}
            }
        }

        volumes_list = [
            {
                'target': '/mnt/edgehub',
                'type': 'volume',
                'source': 'edgehubdev',
                'read_only': True,
                'volume': {
                    'nocopy': False
                }
            },
            {
                'target': '/mnt/edgehub',
                'type': 'bind',
                'source': '/mnt/edgehubdev',
                'bind': {
                    'propagation': "shared"
                }
            },
            {
                'target': '/mnt/edgehub',
                'type': 'tmpfs',
                'tmpfs': {
                    'size': 65536
                }
            }
        ]

        assert volumes_list == iotedgehubdev.compose_parser.service_parser_volumes(volumes_config)

    def test_invalid_service_parser_volumes(self):
        volumes_config = {
            'Mounts': [
                {
                    "Type": "volume",
                    "Source": "edgehubdev",
                    "VolumeOptions": {
                        "NoCopy": False
                    },
                    "ReadOnly": True
                }
            ],
            'Volumes': {}
        }
        with pytest.raises(KeyError):
            iotedgehubdev.compose_parser.service_parser_volumes(volumes_config)
