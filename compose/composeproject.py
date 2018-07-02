from compose.compose_parser import COMPOSE_KEY_CREATE_OPTION_MAPPING
import json
from ruamel.yaml import YAML

COMPOSE_VERSION = 3.4

class ComposeProject(object):
    def __init__(self,deployment_config):
        self.deployment_config = deployment_config
        self.custom_modules = deployment_config['modulesContent']['$edgeAgent']['properties.desired']['modules']
        self.yaml_dict = {}
        self.Services = {}
        self.Networks = self.parse_networks(deployment_config)
        self.Volumes = self.parse_volumes(deployment_config)

    def parse_services(self):
        for service_name,config in self.custom_modules.items():
            self.Services[service_name] = {}
            self.Services[service_name]['image'] = config['settings']['image']
            self.Services[service_name]['container_name'] = service_name
            create_option = config['settings']['createOptions']
            create_option = json.loads(create_option)
            for k in COMPOSE_KEY_CREATE_OPTION_MAPPING:
                ret = self.create_option_to_compose_option(create_option,COMPOSE_KEY_CREATE_OPTION_MAPPING[k]['parser_func'],k,COMPOSE_KEY_CREATE_OPTION_MAPPING[k]['API_key'])
                if ret != None : self.Services[service_name][k] = ret

    def parse_networks(self,networks_config):
        return None
    
    def parse_volumes(self,volumes_config):
        return None

    def create_option_to_compose_option(self,create_option,parser_func,compose_key,APIkeys):
        create_options_details = self.collect_create_options(create_option,APIkeys)
        if create_options_details != None:
            return parser_func(create_options_details)
        else: return None

    def get_create_option_value(self,create_option,key_path):
        '''
        Get CreateOption in different levels.
        create_option: dict
        key_path: string or list
        If key_path is a string, it means the key is at the top level of CreateOption, otherwise go through the path down to the right level.
        '''
        def dfs_create_option(create_option,key_path,level):
            if not key_path[level] in create_option: return None
            elif level == len(key_path)-1: return create_option[key_path[level]]
            else: return dfs_create_option(create_option[key_path[level]],key_path,level+1)

        if not isinstance(key_path,list): 
            if not key_path in create_option: return None
            else: return create_option[key_path] 
        else: return dfs_create_option(create_option,key_path,0)

    def collect_create_options(self,create_option,API_keys):
        if not isinstance(API_keys,list): return self.get_create_option_value(create_option,API_keys)
        if not isinstance(API_keys[0],list): return self.get_create_option_value(create_option,API_keys)
        
        create_options_dict = {}
        for key_path in API_keys:
            ret = self.get_create_option_value(create_option,key_path)
            if ret != None:
                if not isinstance(key_path,list): create_options_dict[key_path] = ret
                else: create_options_dict[key_path[-1]] = ret
        return create_options_dict 

    def dump(self,target):
        stream = open(target, 'w')
        yaml = YAML()
        self.yaml_dict['version'] = str(COMPOSE_VERSION)
        self.yaml_dict['services'] = self.Services
        self.yaml_dict['networks'] = self.Networks
        self.yaml_dict['volumes'] = self.Volumes
        yaml.dump(self.yaml_dict,stream)
