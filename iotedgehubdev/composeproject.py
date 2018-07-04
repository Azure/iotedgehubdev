from .compose_parser import CreateOptionParser
import json
from ruamel.yaml import YAML

COMPOSE_VERSION = 3.6


class ComposeProject(object):
    def __init__(self, deployment_config):
        self.deployment_config = deployment_config
        self.yaml_dict = {}
        self.Services = {}
        self.Networks = {}
        self.Volumes = {}

    def compose(self):
        self.parse_services()
        self.parse_networks()
        self.parse_volumes()

    def parse_services(self):
        custom_modules = self.deployment_config['modulesContent']['$edgeAgent']['properties.desired']['modules']
        for service_name, config in custom_modules.items():
            self.Services[service_name] = {}
            create_option_str = config['settings']['createOptions']
            create_option = json.loads(create_option_str)
            create_option_parser = CreateOptionParser(create_option)
            self.Services[service_name].update(create_option_parser.parse_create_option())
            self.Services[service_name]['image'] = config['settings']['image']
            self.Services[service_name]['container_name'] = service_name

    # TODO: implement this in a future PR
    def parse_networks(self):
        pass

    # TODO: implement this in a future PR
    def parse_volumes(self):
        pass

    def dump(self, target):
        stream = open(target, 'w')
        yaml = YAML()
        self.yaml_dict['version'] = str(COMPOSE_VERSION)
        self.yaml_dict['services'] = self.Services
        self.yaml_dict['networks'] = self.Networks
        self.yaml_dict['volumes'] = self.Volumes
        yaml.dump(self.yaml_dict, stream)
