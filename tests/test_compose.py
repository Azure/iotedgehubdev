import iotedgehubdev.compose_parser
import unittest


class ComposeTest(unittest.TestCase):
    def test_service_parser_expose(self):
        expose_API = {
            "22/tcp": {}
        }
        expose_list = ["22/tcp"]
        assert expose_list == iotedgehubdev.compose_parser.service_parser_expose(expose_API)

    def test_service_parser_command(self):
        cmd_list = ["bundle", "exec", "thin", "-p", "3000"]
        cmd_str = "bundle exec thin -p 3000"
        assert cmd_str == iotedgehubdev.compose_parser.service_parser_command(cmd_list)

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
        assert healthcheck_dict == iotedgehubdev.compose_parser.service_parser_healthcheck(healthcheck_API)

    def test_service_parser_hostconfig_devices(self):
        devices_API = [
            {
                'PathOnHost': '/dev/random',
                'CgroupPermissions': 'rwm',
                'PathInContainer': '/dev/mapped-random'
            }
        ]
        devices_list = ["/dev/random:/dev/mapped-random:rwm"]
        assert devices_list == iotedgehubdev.compose_parser.service_parser_hostconfig_devices(devices_API)

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
            ret.append(iotedgehubdev.compose_parser.service_parser_hostconfig_restart(restart_policy))
        assert ret == restart_list

    def test_parser_hostconfig_ulimits(self):
        ulimits_API = [
            {"Name": "nofile", "Soft": 1024, "Hard": 2048}
        ]

        ulimits_dict = {
            "nofile": {"soft": 1024, "hard": 2048}
        }
        assert ulimits_dict == iotedgehubdev.compose_parser.service_parser_hostconfig_ulimits(ulimits_API)

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
        assert logging_dict == iotedgehubdev.compose_parser.service_parser_hostconfig_logging(logconfig_API)

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
        assert ports_list == iotedgehubdev.compose_parser.service_parser_hostconfig_ports(portsbinding)
