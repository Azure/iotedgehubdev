import json
from ruamel.yaml import YAML
from collections import OrderedDict


def service_parser_naive(create_options_details):
    return create_options_details


def service_parser_expose(create_options_details):
    service_expose_ports = []
    for port in create_options_details:
        service_expose_ports.append(port)
    return service_expose_ports


def service_parser_command(create_options_details):
    if not isinstance(create_options_details, list):
        return create_options_details
    command_ret = ""
    for cmd in create_options_details:
        command_ret = command_ret + ' ' + cmd
    return command_ret


def service_parser_healthcheck(create_options_details):
    healthcheck_config = {}
    healthcheck_config['test'] = str(create_options_details['Test'])
    healthcheck_config['interval'] = (time_ns_ms(create_options_details['Interval']))
    healthcheck_config['timeout'] = time_ns_ms(create_options_details['Timeout'])
    healthcheck_config['retries'] = create_options_details['Retries']
    healthcheck_config['start_period'] = time_ns_ms(create_options_details['StartPeriod'])
    return healthcheck_config


def service_parser_stop_timeout(create_options_details):
    return str(int(create_options_details)) + 's'


def time_ns_ms(ns):
    return str(int(ns / 1000000)) + 'ms'


COMPOSE_KEY_CREATE_OPTION_MAPPING = {
    'hostname': {'API_key': 'Hostname', 'parser_func': service_parser_naive},
    'domainname': {'API_key': 'Domainname', 'parser_func': service_parser_naive},
    'user': {'API_key': 'User', 'parser_func': service_parser_naive},
    'expose': {'API_key': 'ExposedPorts', 'parser_func': service_parser_expose},
    'tty': {'API_key': 'Tty', 'parser_func': service_parser_naive},
    'environment': {'API_key': 'Env', 'parser_func': service_parser_naive},
    'command': {'API_key': 'Cmd', 'parser_func': service_parser_command},
    # 'healthcheck':{'API_key':'Healthcheck','parser_func':service_parser_healthcheck},
    'image': {'API_key': 'Image', 'parser_func': service_parser_naive},
    'working_dir': {'API_key': 'WorkingDir', 'parser_func': service_parser_naive},
    'entrypoint': {'API_key': 'Entrypoint', 'parser_func': service_parser_naive},
    'mac_address': {'API_key': 'MacAddress', 'parser_func': service_parser_naive},
    'labels': {'API_key': 'Labels', 'parser_func': service_parser_naive},
    'stop_signal': {'API_key': 'StopSignal', 'parser_func': service_parser_naive},
    'stop_grace_period': {'API_key': 'StopTimeout', 'parser_func': service_parser_stop_timeout},

    # # # HostConfig
    # 'privileged':{'API_key':['HostConfig','Privileged'],'parser_func':service_parser_naive},
    # # 'volumes:':{'API_key':['Binds','Mounts'],'parser_func':service_parser_naive},
    # # # 'volumes_from:':{'API_key':'VolumesFrom','parser_func':service_parser_naive},
    # 'network_mode':{'API_key':['HostConfig','NetworkMode'],'parser_func':service_parser_naive},
    # # 'devices:':{'API_key':'Devices','parser_func':service_parser_naive},
    # 'dns':{'API_key':['HostConfig','Dns'],'parser_func':service_parser_naive},
    # 'dns_search':{'API_key':['HostConfig','DnsSearch'],'parser_func':service_parser_naive},
    # # 'restart:':{'API_key':'RestartPolicy','parser_func':service_parser_naive},
    # 'cap_add':{'API_key':['HostConfig','CapAdd'],'parser_func':service_parser_naive},
    # 'cap_drop':{'API_key':['HostConfig','CapDrop'],'parser_func':service_parser_naive},
    # # 'ulimits:':{'API_key':'Ulimits','parser_func':service_parser_naive},
    # # 'logging:':{'API_key':'LogConfig','parser_func':service_parser_naive},
    # 'extra_hosts':{'API_key':['HostConfig','ExtraHosts'],'parser_func':service_parser_naive},
    # 'read_only':{'API_key':['HostConfig','ReadonlyRootfs'],'parser_func':service_parser_naive},
    # 'pid':{'API_key':['HostConfig','PidMode'],'parser_func':service_parser_naive},
    # 'security_opt':{'API_key':['HostConfig','SecurityOpt'],'parser_func':service_parser_naive},
    # 'ipc':{'API_key':['HostConfig','IpcMode'],'parser_func':service_parser_naive},
    # 'cgroup_parent':{'API_key':['HostConfig','CgroupParent'],'parser_func':service_parser_naive},
    # # 'shm_size:':{'API_key':'ShmSize','parser_func':service_parser_naive},
    # # 'sysctls:':{'API_key':'Sysctls','parser_func':service_parser_naive},
    # # 'tmpfs:':{'API_key':'Tmpfs','parser_func':service_parser_naive},
    # 'userns_mode':{'API_key':['HostConfig','UsernsMode'],'parser_func':service_parser_naive},
    # 'isolation':{'API_key':['HostConfig','Isolation'],'parser_func':service_parser_naive},

    # # # NetworkingConfig
    # # 'aliases':{'API_key':'IPv4Address','parser_func':service_parser_naive},
    # # 'ipv4_address':{'API_key':'IPv6Address','parser_func':service_parser_naive},
    # # 'ipv6_address':{'API_key':'Aliases','parser_func':service_parser_naive}
}
