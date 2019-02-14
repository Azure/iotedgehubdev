# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import json
import os
import shutil

import pytest

import iotedgehubdev.compose_parser
from iotedgehubdev.composeproject import ComposeProject
from iotedgehubdev.edgemanager import EdgeManager

OUTPUT_PATH = os.path.join('tests', 'output')


@pytest.fixture(autouse=True)
def tear_down(request):

    def rm_output_path():
        if os.path.exists(OUTPUT_PATH):
            shutil.rmtree(OUTPUT_PATH)

    request.addfinalizer(rm_output_path)


@pytest.mark.parametrize('deployment_json_file, actual_output_filename, expected_output_filename',
                         [('deployment.json',
                           'docker-compose_test.yml',
                           'docker-compose.yml'),
                          ('deployment_with_chunked_create_options.json',
                           'docker-compose_test_with_chunked_create_options.yml',
                           'docker-compose_with_chunked_create_options.yml')])
def test_compose(deployment_json_file, actual_output_filename, expected_output_filename):
    test_resources_dir = os.path.join('tests', 'test_compose_resources')
    with open(os.path.join(test_resources_dir, deployment_json_file)) as json_file:
        compose_project = create_test_compose_project(json_file)
        compose_project.compose()

        actual_output_path = os.path.join(OUTPUT_PATH, actual_output_filename)
        compose_project.dump(actual_output_path)

        actual_output = open(actual_output_path, 'r').read()
        expected_output = open(os.path.join(test_resources_dir, expected_output_filename), 'r').read()
        assert ''.join(sorted(expected_output)) == ''.join(sorted(actual_output))


def test_service_parser_expose():
    expose_API = {
        "22/tcp": {}
    }
    expose_list = ["22/tcp"]
    assert expose_list == iotedgehubdev.compose_parser.service_parser_expose({'ExposedPorts': expose_API})


def test_service_parser_command():
    cmd_list = ["bundle", "exec", "thin", "-p", "3000"]
    cmd_str = "bundle exec thin -p 3000"
    assert cmd_str == iotedgehubdev.compose_parser.service_parser_command({'Cmd': cmd_list})


def test_service_parser_healthcheck():
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


def test_invalid_service_parser_healthcheck():
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


def test_service_parser_hostconfig_devices():
    devices_API = [
        {
            'PathOnHost': '/dev/random',
            'CgroupPermissions': 'rwm',
            'PathInContainer': '/dev/mapped-random'
        }
    ]
    devices_list = ["/dev/random:/dev/mapped-random:rwm"]
    assert devices_list == iotedgehubdev.compose_parser.service_parser_hostconfig_devices({'Devices': devices_API})


def test_service_parser_hostconfig_restart():
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


def test_invalid_service_parser_hostconfig_restart():
    restart_API_keyerr = {"Name": "on-failure"}
    restart_API_valerr = {"Name": "never"}
    with pytest.raises(KeyError):
        iotedgehubdev.compose_parser.service_parser_hostconfig_restart({'RestartPolicy': restart_API_keyerr})
    with pytest.raises(ValueError):
        iotedgehubdev.compose_parser.service_parser_hostconfig_restart({'RestartPolicy': restart_API_valerr})


def test_parser_hostconfig_ulimits():
    ulimits_API = [
        {"Name": "nofile", "Soft": 1024, "Hard": 2048}
    ]

    ulimits_dict = {
        "nofile": {"soft": 1024, "hard": 2048}
    }
    assert ulimits_dict == iotedgehubdev.compose_parser.service_parser_hostconfig_ulimits({'Ulimits': ulimits_API})


def test_service_parser_hostconfig_logging():
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


def test_service_parser_hostconfig_ports():
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


def test_service_parser_networks():
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


def test_service_parser_volumes():
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
        },
        'Binds': [
            '/tmp:/tmp2:ro'
        ]
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
        },
        {
            'target': '/tmp2',
            'type': 'bind',
            'source': '/tmp',
            'read_only': True
        }
    ]

    assert volumes_list == iotedgehubdev.compose_parser.service_parser_volumes(volumes_config)


def create_bind_combos():
    sources_win = ['tmp', 'c:\\', 'c:\\foo bar\\tmp\\tmp', 'c:/foo bar/tmp/tmp', None]
    targets_win = ['/tmp/tmp', 'c:\\', 'c:\\foo bar\\tmp', 'c:/foo bar/tmp']

    sources_linux = ['tmp', '/foo bar/tmp/tmp', None]
    targets_linux = ['/foo bar/tmp']

    modes = ['ro', 'rw', None]

    combos_win = [(s, t, m) for s in sources_win for t in targets_win for m in modes]
    combos_linux = [(s, t, m) for s in sources_linux for t in targets_linux for m in modes]
    combos = combos_win + combos_linux

    return combos


@pytest.mark.parametrize('source, target, mode', create_bind_combos())
def test_bind(source, target, mode):
    bind = {
        'Binds': [':'.join([i for i in (source, target, mode) if i is not None])]
    }

    source = source or ''
    volume = {
        'source': source,
        'target': target,
        'type': 'bind' if source is not None and os.path.isabs(source) else 'volume'
    }

    if mode == 'ro':
        volume['read_only'] = True

    assert [volume] == iotedgehubdev.compose_parser.service_parser_volumes(bind)


def test_invalid_service_parser_volumes():
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

    # Invalid path c://tmp
    invalid_binds_config = {
        'Binds': {
            'c:\\tmp:c://tmp:ro:'
        }
    }

    with pytest.raises(ValueError):
        iotedgehubdev.compose_parser.service_parser_volumes(invalid_binds_config)

    # Invalid mode r
    invalid_binds_config = {
        'Binds': {
            'c:\\tmp:/tmp:r'
        }
    }

    with pytest.raises(ValueError):
        iotedgehubdev.compose_parser.service_parser_volumes(invalid_binds_config)

    # Extra colon
    invalid_binds_config = {
        'Binds': {
            'c:\\tmp:/tmp:ro:'
        }
    }

    with pytest.raises(ValueError):
        iotedgehubdev.compose_parser.service_parser_volumes(invalid_binds_config)

    # Empty source
    invalid_binds_config = {
        'Binds': {
            ':/tmp:ro:'
        }
    }

    with pytest.raises(ValueError):
        iotedgehubdev.compose_parser.service_parser_volumes(invalid_binds_config)


def test_join_create_options():
    valid_settings = json.loads('''{
        "createOptions": "{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'",
        "createOptions01": ": {'PortBindings': {'43/udp': [{'HostPort': '4",
        "createOptions02": "3'}], '42/tcp': [{'HostPort': '42'}]}}}"
    }''')
    assert ComposeProject._join_create_options(valid_settings) == """{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig': {'PortBindings'\
: {'43/udp': [{'HostPort': '43'}], '42/tcp': \
[{'HostPort': '42'}]}}}"""

    valid_settings_unsorted = json.loads('''{
        "createOptions01": ": {'PortBindings': {'43/udp': [{'HostPort': '4",
        "createOptions02": "3'}], '42/tcp': [{'HostPort': '42'}]}}}",
        "createOptions": "{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'"
        }''')
    assert ComposeProject._join_create_options(valid_settings_unsorted) == """{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig': {'PortBindings'\
: {'43/udp': [{'HostPort': '43'}], '42/tcp': \
[{'HostPort': '42'}]}}}"""

    valid_settings_full = json.loads('''{
        "createOptions": "{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'",
        "createOptions01": ": {'PortBindings': {'43/udp': [{'HostPort': '4",
        "createOptions02": "3'}], '42/tcp': [{'HostPort': '42'",
        "createOptions03": "}",
        "createOptions04": "]",
        "createOptions05": "}",
        "createOptions06": "}",
        "createOptions07": "}"
    }''')
    assert ComposeProject._join_create_options(valid_settings_full) == """{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig': {'PortBindings'\
: {'43/udp': [{'HostPort': '43'}], '42/tcp': \
[{'HostPort': '42'}]}}}"""

    invalid_settings_1 = json.loads('''{
        "createOptions": "{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'",
        "createOptions02": ": {'PortBindings': {'43/udp': [{'HostPort': '4",
        "createOptions03": "3'}], '42/tcp': [{'HostPort': '42'}]}}}"
        }''')
    assert ComposeProject._join_create_options(invalid_settings_1) == """{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'"""

    invalid_settings_2 = json.loads('''{
        "createOptions01": "{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'",
        "createOptions02": ": {'PortBindings': {'43/udp': [{'HostPort': '4",
        "createOptions03": "3'}], '42/tcp': [{'HostPort': '42'}]}}}"
        }''')
    assert ComposeProject._join_create_options(invalid_settings_2) == ''

    invalid_settings_3 = json.loads('''{
        "createOptions00": "{'Env': ['k1=v1', 'k2=v2', 'k3=v3'], 'HostConfig'",
        "createOptions01": ": {'PortBindings': {'43/udp': [{'HostPort': '4",
        "createOptions02": "3'}], '42/tcp': [{'HostPort': '42'}]}}}"
        }''')
    assert ComposeProject._join_create_options(invalid_settings_3) == ''


def create_test_compose_project(json_file):
    deployment_config = json.load(json_file)
    if 'modulesContent' in deployment_config:
        module_content = deployment_config['modulesContent']
    elif 'moduleContent' in deployment_config:
        module_content = deployment_config['moduleContent']

    module_names = [EdgeManager.EDGEHUB_MODULE]
    custom_modules = module_content['$edgeAgent']['properties.desired']['modules']
    for module_name in custom_modules:
        module_names.append(module_name)

    ConnStr_info = {}
    for module_name in module_names:
        ConnStr_info[module_name] = \
            "HostName=HostName;DeviceId=DeviceId;ModuleId={};SharedAccessKey=SharedAccessKey".format(module_name)

    mount_base = '/mnt'
    env_info = {
        'hub_env': [
            EdgeManager.HUB_CA_ENV.format(mount_base),
            EdgeManager.HUB_CERT_ENV.format(mount_base),
            EdgeManager.HUB_SRC_ENV,
            EdgeManager.HUB_SSLPATH_ENV.format(mount_base),
            EdgeManager.HUB_SSLCRT_ENV
        ],
        'module_env': [
            EdgeManager.MODULE_CA_ENV.format(mount_base)
        ]
    }

    volume_info = {
        'HUB_MOUNT': EdgeManager.HUB_MOUNT.format(mount_base),
        'HUB_VOLUME': EdgeManager.HUB_VOLUME,
        'MODULE_VOLUME': EdgeManager.MODULE_VOLUME,
        'MODULE_MOUNT': EdgeManager.MODULE_MOUNT.format(mount_base)
    }

    network_info = {
        'NW_NAME': EdgeManager.NW_NAME,
        'ALIASES': 'gatewayhost'
    }

    compose_project = ComposeProject(module_content)
    compose_project.set_edge_info({
        'ConnStr_info': ConnStr_info,
        'env_info': env_info,
        'volume_info': volume_info,
        'network_info': network_info,
        'hub_name': EdgeManager.EDGEHUB,
        'labels': EdgeManager.LABEL
    })

    return compose_project
