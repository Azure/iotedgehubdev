from jsonpath_rw import parse


class CreateOptionParser(object):
    def __init__(self, create_option):
        self.create_option = create_option

    def parse_create_option(self):
        ret = {}
        for compose_key in COMPOSE_KEY_CREATE_OPTION_MAPPING:
            create_option_value = self.get_create_option_value(compose_key)
            if create_option_value:
                parser_func = COMPOSE_KEY_CREATE_OPTION_MAPPING[compose_key]['parser_func']
                ret[compose_key] = parser_func(create_option_value)
        return ret

    def get_create_option_value(self, compose_key):
        create_option_value_dict = {}
        for API_key, API_jsonpath in COMPOSE_KEY_CREATE_OPTION_MAPPING[compose_key]['API_Info'].items():
            jsonpath_expr = parse(API_jsonpath)
            value_list = jsonpath_expr.find(self.create_option)
            if value_list:
                create_option_value_dict[API_key] = value_list[0].value
        # If there is only one API key mapping to the compose key,
        # we don't need a dict to specify the create option and just return the value
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
    return ' '.join(create_options_details).strip()


def service_parser_healthcheck(create_options_details):
    try:
        return {
            'test': create_options_details['Test'],
            'interval': time_ns_ms(create_options_details['Interval']),
            'timeout': time_ns_ms(create_options_details['Timeout']),
            'retries': create_options_details['Retries'],
            'start_period': time_ns_ms(create_options_details['StartPeriod'])
        }
    except KeyError as err:
        raise KeyError('Missing key : {0} in Healthcheck'.format(err))


def service_parser_stop_timeout(create_options_details):
    try:
        return str(int(create_options_details)) + 's'
    except TypeError:
        raise TypeError('StopTimeout should be an integer.')


def service_parser_hostconfig_devices(create_options_details):
    devices_list = []
    for device in create_options_details:
        try:
            devices_list.append("{0}:{1}:{2}".format(device['PathOnHost'],
                                                     device['PathInContainer'], device['CgroupPermissions']))
        except KeyError as err:
            raise KeyError('Missing key : {0} in HostConfig.Devices.'.format(err))
    return devices_list


def service_parser_hostconfig_restart(create_options_details):
    ret = ""
    if create_options_details['Name'] == "":
        ret = "no"
    elif create_options_details['Name'] == "on-failure":
        try:
            ret = "on-failure:{0}".format(create_options_details['MaximumRetryCount'])
        except KeyError as err:
            raise KeyError('Missing key : {0} in HostConfig.RestartPolicy.'.format(err))
    elif create_options_details['Name'] == "always" or create_options_details['Name'] == "unless-stopped":
        ret = create_options_details['Name']
    else:
        raise ValueError("RestartPolicy Name should be one of '', 'always', 'unless-stopped', 'on-failure'")
    return ret


def service_parser_hostconfig_ulimits(create_options_details):
    ulimits_dict = {}
    for ulimit in create_options_details:
        try:
            ulimits_dict[ulimit['Name']] = {
                'soft': ulimit['Soft'],
                'hard': ulimit['Hard']
            }
        except KeyError as err:
            raise KeyError('Missing key : {0} in HostConfig.Ulimits'.format(err))
    return ulimits_dict


def service_parser_hostconfig_logging(create_options_details):
    try:
        logging_dict = {
            'driver': create_options_details['Type'],
            'options': create_options_details['Config']
        }
    except KeyError as err:
        raise KeyError('Missing key : {0} in HostConfig.LogConfig'.format(err))
    return logging_dict


def service_parser_hostconfig_ports(create_options_details):
    ports_list = []
    for container_port, host_ports in create_options_details.items():
        for host_port_info in host_ports:
            host_port = ""
            if 'HostIp' in host_port_info and 'HostPort' in host_port_info:
                host_port = "{0}:{1}".format(host_port_info['HostIp'], host_port_info['HostPort'])
            elif 'HostIp' in host_port_info:
                host_port = host_port_info['HostIp']
            elif 'HostPort' in host_port_info:
                host_port = host_port_info['HostPort']
            ports_list.append("{0}:{1}".format(host_port, container_port))
    return ports_list


def time_ns_ms(ns):
    if ns is not 0 and ns < 1000000:
        raise ValueError('The time should be 0 or at least 1000000 (1 ms)')
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

    # HostConfig
    'ports': {'API_Info': {'PortBindings': "$['HostConfig']['PortBindings']"}, 'parser_func': service_parser_hostconfig_ports},
    'privileged': {'API_Info': {'Privileged': "$['HostConfig']['Privileged']"}, 'parser_func': service_parser_naive},
    'network_mode': {'API_Info': {'NetworkMode': "$['HostConfig']['NetworkMode']"}, 'parser_func': service_parser_naive},
    'devices': {'API_Info': {'Devices': "$['HostConfig']['Devices']"}, 'parser_func': service_parser_hostconfig_devices},
    'dns': {'API_Info': {'Dns': "$['HostConfig']['Dns']"}, 'parser_func': service_parser_naive},
    'dns_search': {'API_Info': {'DnsSearch': "$['HostConfig']['DnsSearch']"}, 'parser_func': service_parser_naive},
    'restart': {
        'API_Info': {'RestartPolicy': "$['HostConfig']['RestartPolicy']"},
        'parser_func': service_parser_hostconfig_restart
    },
    'cap_add': {'API_Info': {'CapAdd': "$['HostConfig']['CapAdd']"}, 'parser_func': service_parser_naive},
    'cap_drop': {'API_Info': {'CapDrop': "$['HostConfig']['CapDrop']"}, 'parser_func': service_parser_naive},
    'ulimits': {'API_Info': {'Ulimits': "$['HostConfig']['Ulimits']"}, 'parser_func': service_parser_hostconfig_ulimits},
    'logging': {'API_Info': {'LogConfig': "$['HostConfig']['LogConfig']"}, 'parser_func': service_parser_hostconfig_logging},
    'extra_hosts': {'API_Info': {'ExtraHosts': "$['HostConfig']['ExtraHosts']"}, 'parser_func': service_parser_naive},
    'read_only': {'API_Info': {'ReadonlyRootfs': "$['HostConfig']['ReadonlyRootfs']"}, 'parser_func': service_parser_naive},
    'pid': {'API_Info': {'PidMode': "$['HostConfig']['PidMode']"}, 'parser_func': service_parser_naive},
    'security_opt': {'API_Info': {'SecurityOpt': "$['HostConfig']['SecurityOpt']"}, 'parser_func': service_parser_naive},
    'ipc': {'API_Info': {'IpcMode': "$['HostConfig']['IpcMode']"}, 'parser_func': service_parser_naive},
    'cgroup_parent': {'API_Info': {'CgroupParent': "$['HostConfig']['CgroupParent']"}, 'parser_func': service_parser_naive},
    # 'shm_size:':{'API_Info':'ShmSize','parser_func':service_parser_naive},
    'sysctls': {'API_Info': {'Sysctls': "$['HostConfig']['Sysctls']"}, 'parser_func': service_parser_naive},
    # 'tmpfs:':{'API_Info':'Tmpfs','parser_func':service_parser_naive},
    'userns_mode': {'API_Info': {'UsernsMode': "$['HostConfig']['UsernsMode']"}, 'parser_func': service_parser_naive},
    'isolation': {'API_Info': {'Isolation': "$['HostConfig']['Isolation']"}, 'parser_func': service_parser_naive},

    # Volumes
    # 'volumes:':{'API_Info':{''},'parser_func':service_parser_naive},

    # # NetworkingConfig
    # 'aliases':{'API_Info':'IPv4Address','parser_func':service_parser_naive},
    # 'ipv4_address':{'API_Info':'IPv6Address','parser_func':service_parser_naive},
    # 'ipv6_address':{'API_Info':'Aliases','parser_func':service_parser_naive}
}
