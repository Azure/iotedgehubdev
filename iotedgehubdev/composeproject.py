from .compose_parser import CreateOptionParser
import json
import yaml
from collections import OrderedDict
import sys

COMPOSE_VERSION = 3.6


class ComposeProject(object):
    edge_network_name = 'azure-iot-edge'

    def __init__(self, deployment_config):
        self.deployment_config = deployment_config
        self.yaml_dict = OrderedDict()
        self.Services = {}
        self.Networks = {}
        self.Volumes = {}
        self.edge_info = {}

    def compose(self):
        self.config_egde_hub()
        self.parse_services()
        self.parse_networks()
        self.parse_volumes()

    def parse_services(self):
        custom_modules = self.deployment_config['moduleContent']['$edgeAgent']['properties.desired']['modules']
        for service_name, config in custom_modules.items():
            self.Services[service_name] = {}
            create_option_str = config['settings']['createOptions']
            create_option = json.loads(create_option_str)
            create_option_parser = CreateOptionParser(create_option)
            self.Services[service_name].update(create_option_parser.parse_create_option())
            self.Services[service_name]['image'] = config['settings']['image']
            self.Services[service_name]['container_name'] = service_name

            if 'volumes' not in self.Services[service_name]:
                self.Services[service_name]['volumes'] = []
            self.Services[service_name]['volumes'].append({
                'type': 'volume',
                'source': self.edge_info['volume_info']['MODULE_VOLUME'],
                'target': self.edge_info['volume_info']['MODULE_MOUNT']
            })

            if 'environment' not in self.Services[service_name]:
                self.Services[service_name]['environment'] = []
            for module_env in self.edge_info['env_info']['module_env'].values():
                self.Services[service_name]['environment'].append(module_env)
            self.Services[service_name]['environment'].append(self.edge_info['ConnStr_info'][service_name])

            if 'networks' not in self.Services[service_name]:
                self.Services[service_name]['networks'] = {}
            self.Services[service_name]['networks'][ComposeProject.edge_network_name] = None

    def get_edge_info(self, info):
        self.edge_info = info

    def config_egde_hub(self):
        self.Services['edgeHub'] = {
            'image': self.deployment_config['moduleContent']['$edgeAgent']['properties.desired']['systemModules']['edgeHub']['image'],
            'environment': list(self.edge_info['env_info']['hub_env'].values()),
            'volumes': [{
                'type': 'volume',
                'source': self.edge_info['volume_info']['HUB_VOLUME'],
                'target': self.edge_info['volume_info']['HUB_MOUNT']
            }],
            'networks': {
                ComposeProject.edge_network_name: {
                    'aliases': [self.edge_info['network_info']['ALIASES']]
                }
            }
        }

        routes_env = self.parse_routes()
        for e in routes_env:
            self.Services['edgeHub']['environment'].append(e)

        self.Services['edgeHub']['environment'].append(self.edge_info['ConnStr_info']['edgeHub'])

    def parse_routes(self):
        routes = self.deployment_config['moduleContent']['$edgeHub']['properties.desired']['routes']
        routes_env = []
        for name, path in routes:
            routes_env.append(name + '__' + path)
        return routes_env

    # TODO: implement this in a future PR
    def parse_networks(self):
        self.Networks = {
            ComposeProject.edge_network_name: {
                'external': True,
                'name': self.edge_info['network_info']['NW_NAME']
            }
        }

    # TODO: implement this in a future PR
    def parse_volumes(self):
        self.Volumes = {
            self.edge_info['volume_info']['HUB_VOLUME']: {
                'external': True
            },
            self.edge_info['volume_info']['MODULE_VOLUME']: {
                'external': True
            }
        }

    def dump(self, target):
        def setup_yaml():
            def represent_dict_order(self, data):
                return self.represent_mapping('tag:yaml.org,2002:map', data.items())
            yaml.add_representer(OrderedDict, represent_dict_order)
        setup_yaml()

        def my_unicode_repr(self, data):
            return self.represent_str(data.encode('utf-8'))

        if sys.version_info[0] < 3:
            # Add # noqa: F821 to ignore undefined name 'unicode' error
            yaml.add_representer(unicode, my_unicode_repr)  # noqa: F821
        stream = open(target, 'w')

        self.yaml_dict['version'] = str(COMPOSE_VERSION)
        self.yaml_dict['services'] = self.Services
        self.yaml_dict['networks'] = self.Networks
        self.yaml_dict['volumes'] = self.Volumes
        yaml.dump(self.yaml_dict, stream, default_flow_style=False)
