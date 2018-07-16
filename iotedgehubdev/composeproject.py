from .compose_parser import CreateOptionParser
import json
import yaml
from collections import OrderedDict
import sys
import os
if sys.version_info[0] < 3:
    import StringIO
else:
    import io

COMPOSE_VERSION = 3.6


class ComposeProject(object):
    edge_hub = 'edgeHub'

    def __init__(self, deployment_config):
        self.deployment_config = deployment_config
        self.yaml_dict = OrderedDict()
        self.Services = OrderedDict()
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
            if create_option_str:
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
            for module_env in self.edge_info['env_info']['module_env']:
                self.Services[service_name]['environment'].append(module_env)
            self.Services[service_name]['environment'].append(
                'EdgeHubConnectionString=' + self.edge_info['ConnStr_info'][service_name])

            if 'networks' not in self.Services[service_name]:
                self.Services[service_name]['networks'] = {}
            self.Services[service_name]['networks'][self.edge_info['network_info']['NW_NAME']] = None

            if 'labels' not in self.Services[service_name]:
                self.Services[service_name]['labels'] = {self.edge_info['labels']: ""}
            else:
                self.Services[service_name]['labels'][self.edge_info['labels']] = ""

            self.Services[service_name]['depends_on'] = [ComposeProject.edge_hub]

            try:
                self.Services[service_name]['restart'] = {
                    'never': 'no',
                    'on-failure': 'on-failure',
                    'always': 'always'
                }[config['restartPolicy']]
            except KeyError as e:
                raise KeyError('Unsupported restart policy {0} in solution mode.'.format(e))

    def set_edge_info(self, info):
        self.edge_info = info

    def config_egde_hub(self):
        edgeHub_config = self.deployment_config['moduleContent']['$edgeAgent']['properties.desired']['systemModules']['edgeHub']
        self.Services[ComposeProject.edge_hub] = {
            'image': edgeHub_config['settings']['image'],
            'environment': self.edge_info['env_info']['hub_env'],
            'volumes': [{
                'type': 'volume',
                'source': self.edge_info['volume_info']['HUB_VOLUME'],
                'target': self.edge_info['volume_info']['HUB_MOUNT']
            }],
            'networks': {
                self.edge_info['network_info']['NW_NAME']: {
                    'aliases': [self.edge_info['network_info']['ALIASES']]
                }
            },
            'container_name': self.edge_info['hub_name']
        }

        routes_env = self.parse_routes()
        for e in routes_env:
            self.Services[ComposeProject.edge_hub]['environment'].append(e)

        self.Services[ComposeProject.edge_hub]['environment'].append(
            'IotHubConnectionString=' + self.edge_info['ConnStr_info']['$edgeHub'])

        self.Services[ComposeProject.edge_hub]['labels'] = {self.edge_info['labels']: ""}

        create_option_str = edgeHub_config['settings']['createOptions']
        if create_option_str:
            create_option = json.loads(create_option_str)
            create_option_parser = CreateOptionParser(create_option)
            self.Services[ComposeProject.edge_hub].update(create_option_parser.parse_create_option())

    def parse_routes(self):
        routes = self.deployment_config['moduleContent']['$edgeHub']['properties.desired']['routes']
        routes_env = []
        for name, path in routes.items():
            routes_env.append(('routes__' + name + '=' + path))
        return routes_env

    def parse_networks(self):
        nw_set = set()
        for service_config in self.Services.values():
            for nw in service_config['networks']:
                nw_set.add(nw)
        for nw in nw_set:
            self.Networks[nw] = {
                'external': True
            }

    # TODO: Parse user-defined volumes
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

        self.yaml_dict['version'] = str(COMPOSE_VERSION)
        self.yaml_dict['services'] = self.Services
        self.yaml_dict['networks'] = self.Networks
        self.yaml_dict['volumes'] = self.Volumes

        if sys.version_info[0] < 3:
            # Add # noqa: F821 to ignore undefined name 'unicode' error
            yaml.add_representer(unicode, my_unicode_repr)  # noqa: F821
            yml_stream = StringIO.StringIO()
        else:
            yml_stream = io.StringIO()

        yaml.dump(self.yaml_dict, yml_stream, default_flow_style=False)
        yml_str = yml_stream.getvalue().replace('$', '$$')

        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))

        with open(target, 'w') as f:
            f.write(yml_str)
