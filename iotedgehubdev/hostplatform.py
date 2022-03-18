# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import os
import platform
from .errors import EdgeInvalidArgument


class HostPlatform(object):
    _edge_dir = '.iotedgehubdev'
    _edgehub_config = 'edgehub.json'
    _setting_ini = 'setting.ini'
    _certs = 'certs'
    _data = 'data'
    _platforms = {
        'linux': {
            'supported_deployments': ['docker'],
            'default_deployment': 'docker',
            'default_edge_meta_dir_env': 'HOME',
            'deployment': {
                'docker': {
                    'linux': {
                        'default_uri': 'unix:///var/run/docker.sock'
                    },
                }
            }
        },
        'windows': {
            'supported_deployments': ['docker'],
            'default_deployment': 'docker',
            'default_edge_meta_dir_env': 'LOCALAPPDATA',
            'deployment': {
                'docker': {
                    'linux': {
                        'default_uri': 'unix:///var/run/docker.sock'
                    },
                    'windows': {
                        'default_uri': 'npipe://./pipe/docker_engine'
                    }
                }
            }
        },
        'darwin': {
            'supported_deployments': ['docker'],
            'default_deployment': 'docker',
            'default_edge_meta_dir_env': 'HOME',
            'deployment': {
                'docker': {
                    'linux': {
                        'default_uri': 'unix:///var/run/docker.sock'
                    },
                }
            }
        }
    }

    # @staticmethod
    # def is_host_supported(host):
    #     if host is None:
    #         raise EdgeInvalidArgument('host cannot be None')

    #     host = host.lower()
    #     if host in _platforms:
    #         return True
    #     return False

    @staticmethod
    def get_edge_dir(host):
        return os.path.join(os.getenv(HostPlatform._platforms[host]['default_edge_meta_dir_env']), HostPlatform._edge_dir)

    @staticmethod
    def get_config_path():
        host = platform.system()
        if host is None:
            raise EdgeInvalidArgument('host cannot be None')
        host = host.lower()
        if host in HostPlatform._platforms:
            return os.path.join(HostPlatform.get_edge_dir(host), 'config')
        return None

    @staticmethod
    def get_data_path():
        host = platform.system()
        if host is None:
            raise EdgeInvalidArgument('host cannot be None')
        host = host.lower()
        if host in HostPlatform._platforms:
            return os.path.join(HostPlatform.get_edge_dir(host), 'data')
        return None

    @staticmethod
    def get_config_file_path():
        configPath = HostPlatform.get_config_path()
        if configPath is not None:
            return os.path.join(configPath, HostPlatform._edgehub_config)
        return None

    @staticmethod
    def get_setting_ini_path():
        configPath = HostPlatform.get_config_path()
        if configPath is not None:
            return os.path.join(configPath, HostPlatform._setting_ini)
        return None

    @staticmethod
    def get_default_cert_path():
        host = platform.system()
        if host is None:
            raise EdgeInvalidArgument('host cannot be None')
        host = host.lower()
        if host in HostPlatform._platforms:
            return os.path.join(HostPlatform.get_data_path(), HostPlatform._certs)
        return None

    @staticmethod
    def get_share_data_path():
        host = platform.system()
        if host is None:
            raise EdgeInvalidArgument('host cannot be None')
        host = host.lower()
        if host in HostPlatform._platforms:
            return os.path.join(HostPlatform.get_data_path(), HostPlatform._data)
        return None
