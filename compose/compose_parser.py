import json
from ruamel.yaml import YAML
from collections import OrderedDict
from jsonpath_rw import parse


class CreateOptionParser(object):
    def __init__(self, create_option):
        self.create_option = create_option

    def parse_create_option(self):
        ret = {}
        for compose_key in COMPOSE_KEY_CREATE_OPTION_MAPPING:
            parser_func = COMPOSE_KEY_CREATE_OPTION_MAPPING[compose_key]['parser_func']
            create_option_value = self.get_create_option_value(compose_key)
            if create_option_value:
                ret[compose_key] = parser_func(create_option_value)
        return ret

    def get_create_option_value(self, compose_key):
        create_option_value_dict = {}
        for API_key, API_jsonpath in COMPOSE_KEY_CREATE_OPTION_MAPPING[compose_key]['API_Info'].items():
            jsonpath_expr = parse(API_jsonpath)
            value_list = jsonpath_expr.find(self.create_option)
            if value_list:
                create_option_value_dict[API_key] = value_list[0].value
        # If there is only one API key mapping to the compose key, we don't need a dict to specify the create option and just return the value
        if len(create_option_value_dict) == 1:
            create_option_value_dict = list(create_option_value_dict.values())[0]
        return create_option_value_dict


def service_parser_naive(create_options_details):
    return create_options_details


def service_parser_expose(create_options_details):
    return list(create_options_details.keys())


def service_parser_command(create_options_details):
    if not isinstance(create_options_details, list):
        return create_options_details
    command_ret = ""
    for cmd in create_options_details:
        command_ret = command_ret + ' ' + cmd
    return command_ret.lstrip().rstrip()


def service_parser_healthcheck(create_options_details):
    healthcheck_config = {}
    healthcheck_config['test'] = str(create_options_details['Test'])  # Maybe need a better fomat
    healthcheck_config['interval'] = time_ns_ms(create_options_details['Interval'])
    healthcheck_config['timeout'] = time_ns_ms(create_options_details['Timeout'])
    healthcheck_config['retries'] = create_options_details['Retries']
    healthcheck_config['start_period'] = time_ns_ms(create_options_details['StartPeriod'])
    return healthcheck_config


def service_parser_stop_timeout(create_options_details):
    return str(int(create_options_details)) + 's'


def time_ns_ms(ns):
    return str(int(ns / 1000000)) + 'ms'


'''
The mapping relationship between docker compose key and create option API key
'docker compose key': {'API_Info': {'API key':'API jsonpath'}, 'parser_func': parser_func},
'''
# TODO: The rest parser function will be added in the future.
COMPOSE_KEY_CREATE_OPTION_MAPPING = {
    'hostname': {'API_Info': {'Hostname': "$['Hostname']"}, 'parser_func': service_parser_naive},
    'domainname': {'API_Info': {'Domainname': "$['Domainname']"}, 'parser_func': service_parser_naive},
    'user': {'API_Info': {'User': "$['User']"}, 'parser_func': service_parser_naive},
    'expose': {'API_Info': {'ExposedPorts': "$['ExposedPorts']"}, 'parser_func': service_parser_expose},
    'tty': {'API_Info': {'Tty': "$['Tty']"}, 'parser_func': service_parser_naive},
    'environment': {'API_Info': {'Env': "$['Env']"}, 'parser_func': service_parser_naive},
    'command': {'API_Info': {'Cmd': "$['Cmd']"}, 'parser_func': service_parser_command},
    'healthcheck': {'API_Info': {'Healthcheck': "$['Healthcheck']"}, 'parser_func': service_parser_healthcheck},
    'image': {'API_Info': {'Image': "$['Image']"}, 'parser_func': service_parser_naive},
    'working_dir': {'API_Info': {'WorkingDir': "$['WorkingDir']"}, 'parser_func': service_parser_naive},
    'entrypoint': {'API_Info': {'Entrypoint': "$['Entrypoint']"}, 'parser_func': service_parser_naive},
    'mac_address': {'API_Info': {'MacAddress': "$['MacAddress']"}, 'parser_func': service_parser_naive},
    'labels': {'API_Info': {'Labels': "$['Labels']"}, 'parser_func': service_parser_naive},
    'stop_signal': {'API_Info': {'StopSignal': "$['StopSignal']"}, 'parser_func': service_parser_naive},
    'stop_grace_period': {'API_Info': {'StopTimeout': "$['StopTimeout']"}, 'parser_func': service_parser_stop_timeout},

    # # HostConfig
    'privileged': {'API_Info': {'Privileged': "$['HostConfig']['Hostname']"}, 'parser_func': service_parser_naive},
    # 'volumes:':{'API_Info':['Binds','Mounts'],'parser_func':service_parser_naive},
    # # 'volumes_from:':{'API_Info':'VolumesFrom','parser_func':service_parser_naive},
    'network_mode': {'API_Info': {'NetworkMode': "$['HostConfig']['NetworkMode']"}, 'parser_func': service_parser_naive},
    # 'devices:':{'API_Info':'Devices','parser_func':service_parser_naive},
    'dns': {'API_Info': {'Dns': "$['HostConfig']['Dns']"}, 'parser_func': service_parser_naive},
    'dns_search': {'API_Info': {'DnsSearch': "$['HostConfig']['DnsSearch']"}, 'parser_func': service_parser_naive},
    # 'restart:':{'API_Info':'RestartPolicy','parser_func':service_parser_naive},
    'cap_add': {'API_Info': {'CapAdd': "$['HostConfig']['CapAdd']"}, 'parser_func': service_parser_naive},
    'cap_drop': {'API_Info': {'CapDrop': "$['HostConfig']['CapDrop']"}, 'parser_func': service_parser_naive},
    # 'ulimits:':{'API_Info':'Ulimits','parser_func':service_parser_naive},
    # 'logging:':{'API_Info':'LogConfig','parser_func':service_parser_naive},
    'extra_hosts': {'API_Info': {'ExtraHosts': "$['HostConfig']['ExtraHosts']"}, 'parser_func': service_parser_naive},
    'read_only': {'API_Info': {'ReadonlyRootfs': "$['HostConfig']['ReadonlyRootfs']"}, 'parser_func': service_parser_naive},
    'pid': {'API_Info': {'PidMode': "$['HostConfig']['PidMode']"}, 'parser_func': service_parser_naive},
    'security_opt': {'API_Info': {'SecurityOpt': "$['HostConfig']['SecurityOpt']"}, 'parser_func': service_parser_naive},
    'ipc': {'API_Info': {'IpcMode': "$['HostConfig']['IpcMode']"}, 'parser_func': service_parser_naive},
    'cgroup_parent': {'API_Info': {'CgroupParent': "$['HostConfig']['CgroupParent']"}, 'parser_func': service_parser_naive},
    # 'shm_size:':{'API_Info':'ShmSize','parser_func':service_parser_naive},
    # 'sysctls:':{'API_Info':'Sysctls','parser_func':service_parser_naive},
    # 'tmpfs:':{'API_Info':'Tmpfs','parser_func':service_parser_naive},
    'userns_mode': {'API_Info': {'UsernsMode': "$['HostConfig']['UsernsMode']"}, 'parser_func': service_parser_naive},
    'isolation': {'API_Info': {'Isolation': "$['HostConfig']['Isolation']"}, 'parser_func': service_parser_naive},

    # # NetworkingConfig
    # 'aliases':{'API_Info':'IPv4Address','parser_func':service_parser_naive},
    # 'ipv4_address':{'API_Info':'IPv6Address','parser_func':service_parser_naive},
    # 'ipv6_address':{'API_Info':'Aliases','parser_func':service_parser_naive}
}
