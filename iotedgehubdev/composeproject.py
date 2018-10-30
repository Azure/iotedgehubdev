# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import json
import os
import sys
from collections import OrderedDict

import yaml
from six import StringIO

from .compose_parser import CreateOptionParser

COMPOSE_VERSION = 3.6

CREATE_OPTIONS_MAX_CHUNKS = 100


class ComposeProject(object):

    def __init__(self, module_content):
        self.module_content = module_content
        self.yaml_dict = OrderedDict()
        self.Services = OrderedDict()
        self.Networks = {}
        self.Volumes = {}
        self.edge_info = {}

    def compose(self):
        modules = {
            self.edge_info['hub_name']:
            self.module_content['$edgeAgent']['properties.desired']['systemModules']['edgeHub']
        }
        modules.update(self.module_content['$edgeAgent']['properties.desired']['modules'])
        for service_name, config in modules.items():
            self.Services[service_name] = {}
            create_option_str = ComposeProject._join_create_options(config['settings'])
            if create_option_str:
                create_option = json.loads(create_option_str)
                create_option_parser = CreateOptionParser(create_option)
                self.Services[service_name].update(create_option_parser.parse_create_option())
            self.Services[service_name]['image'] = config['settings']['image']
            self.Services[service_name]['container_name'] = service_name

            if 'networks' not in self.Services[service_name]:
                self.Services[service_name]['networks'] = {}
            self.Services[service_name]['networks'][self.edge_info['network_info']['NW_NAME']] = None

            if 'labels' not in self.Services[service_name]:
                self.Services[service_name]['labels'] = {self.edge_info['labels']: ""}
            else:
                self.Services[service_name]['labels'][self.edge_info['labels']] = ""

            try:
                self.Services[service_name]['restart'] = {
                    'never': 'no',
                    'on-failure': 'on-failure',
                    'always': 'always'
                }[config['restartPolicy']]
            except KeyError as e:
                raise KeyError('Unsupported restart policy {0} in solution mode.'.format(e))

            if 'env' in config:
                self.Services[service_name]['environment'] = self.config_env(
                    self.Services[service_name].get('environment', []), config['env'])

            if service_name == self.edge_info['hub_name']:
                self.config_edge_hub(service_name)
            else:
                self.config_modules(service_name)

            for nw in self.Services[service_name]['networks']:
                self.Networks[nw] = {
                    'external': True
                }

            for vol in self.Services[service_name]['volumes']:
                if vol['type'] == 'volume':
                    self.Volumes[vol['source']] = {
                        'name': vol['source']
                    }

    def set_edge_info(self, info):
        self.edge_info = info

    def config_modules(self, service_name):
        config = self.Services[service_name]
        if 'volumes' not in config:
            config['volumes'] = []
        config['volumes'].append({
            'type': 'volume',
            'source': self.edge_info['volume_info']['MODULE_VOLUME'],
            'target': self.edge_info['volume_info']['MODULE_MOUNT']
        })

        if 'environment' not in config:
            config['environment'] = []
        for module_env in self.edge_info['env_info']['module_env']:
            config['environment'].append(module_env)
        config['environment'].append(
            'EdgeHubConnectionString=' + self.edge_info['ConnStr_info'][service_name]
        )

        if 'depends_on' not in config:
            config['depends_on'] = []
        config['depends_on'].append(self.edge_info['hub_name'])

    def config_edge_hub(self, service_name):
        config = self.Services[service_name]
        if 'volumes' not in config:
            config['volumes'] = []
        config['volumes'].append({
            'type': 'volume',
            'source': self.edge_info['volume_info']['HUB_VOLUME'],
            'target': self.edge_info['volume_info']['HUB_MOUNT']
        })

        config['networks'][self.edge_info['network_info']['NW_NAME']] = {
            'aliases': [self.edge_info['network_info']['ALIASES']]
        }

        if 'environment' not in config:
            config['environment'] = []
        routes_env = self.parse_routes()
        for e in routes_env:
            config['environment'].append(e)
        config['environment'].append(
            'IotHubConnectionString=' + self.edge_info['ConnStr_info']['$edgeHub'])
        config['environment'].extend(self.edge_info['env_info']['hub_env'])

    def config_env(self, env_list, env_section):
        env_dict = {}
        for env in env_list:
            if '=' in env:
                k, v = env.split('=', 1)
            else:
                k, v = env, ''
            env_dict[k] = v
        for k, v in env_section.items():
            if 'value' not in v:
                env_dict[k] = ''
            else:
                env_dict[k] = v['value']
        ret = []
        for k, v in env_dict.items():
            ret.append("{0}={1}".format(k, v))
        return ret

    def parse_routes(self):
        routes = self.module_content['$edgeHub']['properties.desired']['routes']
        routes_env = []
        route_id = 1
        for path in routes.values():
            routes_env.append('routes__r{0}={1}'.format(route_id, path))
            route_id = route_id + 1
        return routes_env

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
        yml_stream = StringIO()

        yaml.dump(self.yaml_dict, yml_stream, default_flow_style=False)
        yml_str = yml_stream.getvalue().replace('$', '$$')

        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))

        with open(target, 'w') as f:
            f.write(yml_str)

    @staticmethod
    def _join_create_options(settings):
        if 'createOptions' not in settings:
            return ''

        res = settings['createOptions']

        i = 0
        while True:
            i += 1
            key = 'createOptions{0:0=2d}'.format(i)
            if i < CREATE_OPTIONS_MAX_CHUNKS and key in settings:
                res += settings[key]
            else:
                break

        return res
