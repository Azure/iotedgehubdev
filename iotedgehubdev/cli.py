# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import json
import os
import sys
import re
from functools import wraps

import click

from . import configs, decorators, telemetry
from .constants import EdgeConstants
from .edgecert import EdgeCert
from .edgemanager import EdgeManager
from .hostplatform import HostPlatform
from .output import Output
from .utils import Utils
from .errors import EdgeError, InvalidConfigError

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], max_content_width=120)
output = Output()

CONN_STR = 'connectionString'
CERT_PATH = 'certPath'
GATEWAY_HOST = 'gatewayhost'
DOCKER_HOST = 'DOCKER_HOST'
HUB_CONN_STR = 'iothubConnectionString'

# a set of parameters whose value should be logged as given
PARAMS_WITH_VALUES = {'edge_runtime_version'}

@decorators.suppress_all_exceptions()
def _parse_params(*args, **kwargs):
    params = []
    for key, value in kwargs.items():
        if (value is None) or (key in PARAMS_WITH_VALUES):
            params.append('{0}={1}'.format(key, value))
        else:
            params.append('{0}!=None'.format(key))
    return params


def _send_failed_telemetry(e):
    output.error(str(e))
    telemetry.fail(str(e), 'Command failed')
    telemetry.flush()


def _with_telemetry(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        configs.check_firsttime()
        params = _parse_params(*args, **kwargs)
        telemetry.start(func.__name__, params)
        try:
            value = func(*args, **kwargs)
            telemetry.success()
            telemetry.flush()
            return value
        except InvalidConfigError as e:
            _send_failed_telemetry(e)
            sys.exit(2)
        except Exception as e:
            _send_failed_telemetry(e)
            sys.exit(1)

    return _wrapper


def _parse_config_json():
    try:
        config_file = HostPlatform.get_config_file_path()

        if not Utils.check_if_file_exists(config_file):
            raise ValueError('Cannot find config file. Please run `{0}` first.'.format(_get_setup_command()))

        with open(config_file) as f:
            try:
                config_json = json.load(f)

                connection_str = config_json[CONN_STR]
                cert_path = config_json[CERT_PATH]
                gatewayhost = config_json[GATEWAY_HOST]
                hub_conn_str = config_json.get(HUB_CONN_STR)
                return EdgeManager(connection_str, gatewayhost, cert_path, hub_conn_str)

            except (ValueError, KeyError):
                raise ValueError('Invalid config file. Please run `{0}` again.'.format(_get_setup_command()))
    except Exception as e:
        raise InvalidConfigError(str(e))


def _get_setup_command():
    return '{0}iotedgehubdev setup -c "<edge-device-connection-string>"'.format('' if os.name == 'nt' else 'sudo ')


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
def main():
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


@click.command(context_settings=CONTEXT_SETTINGS,
               help='Setup the IoT Edge Simulator. This must be done before starting.')
@click.option('--connection-string',
              '-c',
              required=True,
              help='Set Azure IoT Edge device connection string. Note: Use double quotes when supplying this input.')
@click.option('--gateway-host',
              '-g',
              required=False,
              default=Utils.get_hostname(),
              show_default=True,
              help='GatewayHostName value for the module to connect.')
@click.option('--iothub-connection-string',
              '-i',
              required=False,
              help='Set Azure IoT Hub connection string. Note: Use double quotes when supplying this input.')
@_with_telemetry
def setup(connection_string, gateway_host, iothub_connection_string):
    try:
        gateway_host = gateway_host.lower()
        certDir = HostPlatform.get_default_cert_path()
        Utils.parse_connection_strs(connection_string, iothub_connection_string)
        if iothub_connection_string is None:
            configDict = {
                CONN_STR: connection_string,
                CERT_PATH: certDir,
                GATEWAY_HOST: gateway_host
            }
        else:
            configDict = {
                CONN_STR: connection_string,
                CERT_PATH: certDir,
                GATEWAY_HOST: gateway_host,
                HUB_CONN_STR: iothub_connection_string
            }

        fileType = 'edgehub.config'
        Utils.mkdir_if_needed(certDir)
        edgeCert = EdgeCert(certDir, gateway_host)
        edgeCert.generate_self_signed_certs()
        configFile = HostPlatform.get_config_file_path()
        Utils.delete_file(configFile, fileType)
        Utils.mkdir_if_needed(HostPlatform.get_config_path())
        configJson = json.dumps(configDict, indent=2, sort_keys=True)
        Utils.create_file(configFile, configJson, fileType)

        dataDir = HostPlatform.get_share_data_path()
        Utils.mkdir_if_needed(dataDir)
        os.chmod(dataDir, 0o755)

        with open(EdgeManager.COMPOSE_FILE, 'w') as f:
            f.write('version: \'3.6\'')
        os.chmod(EdgeManager.COMPOSE_FILE, 0o777)
        output.info('Setup IoT Edge Simulator successfully.')
    except Exception as e:
        raise e


@click.command(context_settings=CONTEXT_SETTINGS,
               # short_help hack to prevent Click truncating help text (https://github.com/pallets/click/issues/486)
               short_help='Get the module credentials such as connection string and certificate file path.',
               help='Get the module credentials such as connection string and certificate file path.')
@click.option('--modules',
              '-m',
              required=False,
              default='target',
              show_default=True,
              help='Specify the vertical-bar-separated ("|") module names to get credentials for, e.g., "module1|module2". '
                   'Note: Use double quotes when supplying this input.')
@click.option('--local',
              '-l',
              required=False,
              is_flag=True,
              default=False,
              show_default=True,
              help='Set `localhost` to `GatewayHostName` for module to run on host natively.')
@click.option('--output-file',
              '-o',
              required=False,
              show_default=True,
              help='Specify the output file to save the connection string. If the file exists, the content will be overwritten.')
@_with_telemetry
def modulecred(modules, local, output_file):
    edge_manager = _parse_config_json()

    if edge_manager:
        modules = [module.strip() for module in modules.strip().split('|')]
        credential = edge_manager.outputModuleCred(modules, local, output_file)
        output.info(credential[0])
        output.info(credential[1])


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Start the IoT Edge Simulator.")
@click.option('--inputs',
              '-i',
              required=False,
              help='Start IoT Edge Simulator in single module mode '
                   'using the specified comma-separated inputs of the target module, e.g., `input1,input2`.')
@click.option('--port',
              '-p',
              required=False,
              default=53000,
              show_default=True,
              help='Port of the service for sending message.')
@click.option('--deployment',
              '-d',
              required=False,
              help='Start IoT Edge Simulator in solution mode using the specified deployment manifest.')
@click.option('--verbose',
              '-v',
              required=False,
              is_flag=True,
              default=False,
              show_default=True,
              help='Show the solution container logs.')
@click.option('--host',
              '-H',
              required=False,
              help='Docker daemon socket to connect to.')
@click.option('--environment',
              '-e',
              required=False,
              multiple=True,
              help='Environment variables for single module mode, e.g., `-e "Env1=Value1" -e "Env2=Value2"`.')
@click.option('--edge-runtime-version',
              '-er',
              required=False,
              multiple=False,
              default='1.2',
              show_default=True,
              help='EdgeHub image version. Currently supported tags 1.0x, 1.1x, or 1.2x')
@_with_telemetry
def start(inputs, port, deployment, verbose, host, environment, edge_runtime_version):
    edge_manager = _parse_config_json()

    if edge_manager:
        if host is not None:
            os.environ[DOCKER_HOST] = str(host)

        hostname_hash, suffix = Utils.hash_connection_str_hostname(edge_manager.hostname)
        telemetry.add_extra_props({'iothubhostname': hostname_hash, 'iothubhostnamesuffix': suffix})

        if inputs is None and deployment is not None:
            if len(environment) > 0:
                output.info('Environment variables are ignored in solution mode.')

            if len(edge_runtime_version) > 0:
                output.info('edgeHub image version is ignored in solution mode.')

            with open(deployment) as json_file:
                json_data = json.load(json_file)
                if 'modulesContent' in json_data:
                    module_content = json_data['modulesContent']
                elif 'moduleContent' in json_data:
                    module_content = json_data['moduleContent']
            edge_manager.start_solution(module_content, verbose, output)
            if not verbose:
                output.info('IoT Edge Simulator has been started in solution mode.')
        else:
            if edge_runtime_version is not None:
                # The only validated versions are 1.0, 1.1, and 1.2 variants, hence the current limitation
                if re.match(r'^(1\.0)|(1\.1)|(1\.2)', edge_runtime_version) is None:
                    raise ValueError('-edge-runtime-version `{0}` is not valid.'.format(edge_runtime_version))

            if deployment is not None:
                output.info('Deployment manifest is ignored when inputs are present.')
            if inputs is None:
                input_list = ['input1']
            else:
                input_list = [input_.strip() for input_ in inputs.strip().split(',')]

            for env in environment:
                if re.match(r'^[a-zA-Z][a-zA-Z0-9_]*?=.*$', env) is None:
                    raise ValueError('Environment variable: `{0}` is not valid.'.format(env))

            edge_manager.start_singlemodule(input_list, port, environment, edge_runtime_version)

            data = '--data \'{{"inputName": "{0}","data":"hello world"}}\''.format(input_list[0])
            url = 'http://localhost:{0}/api/v1/messages'.format(port)
            curl_msg = '        curl --header "Content-Type: application/json" --request POST {0} {1}'.format(data, url)
            output.info('IoT Edge Simulator has been started in single module mode.')
            output.info('Please run `iotedgehubdev modulecred` to get credential to connect your module.')
            output.info('And send message through:')
            output.line()
            output.echo(curl_msg, 'green')
            output.line()
            output.info(
                'Please refer to https://github.com/Azure/iot-edge-testing-utility/blob/master/swagger.json'
                ' for detail schema')


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Stop the IoT Edge Simulator.")
@click.option('--host',
              '-H',
              required=False,
              help='Docker daemon socket to connect to')
@_with_telemetry
def stop(host):
    if host is not None:
        os.environ[DOCKER_HOST] = str(host)
    EdgeManager.stop()
    output.info('IoT Edge Simulator has been stopped successfully.')


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Determine whether config file is valid.")
@_with_telemetry
def validateconfig():
    _parse_config_json()
    output.info('Config file is valid.')

@click.command(context_settings=CONTEXT_SETTINGS,
               help="Create IoT Edge device CA")
@click.option('--output-dir',
              '-o',
              required=False,
              default=".",
              help='The output folder of generated certs. '
              'The tool will create a certs folder under given path to store the certs.')
@click.option('--valid-days',
              '-d',
              required=False,
              default=90,
              show_default=True,
              help='Days before cert expires.')
@click.option('--force',
              '-f',
              required=False,
              is_flag=True,
              default=False,
              show_default=True,
              help='Whether overwrite existing cert files.')
@click.option('--trusted-ca',
              '-c',
              required=False,
              help='Path of your own trusted ca used to sign IoT Edge device ca. '
              'Please also provide trsuted ca private key and related passphase (if have).'
              )
@click.option('--trusted-ca-key',
              '-k',
              required=False,
              help='Path of your own trusted ca private key used to sign IoT Edge device ca. '
              'Please also provide trusted ca and related passphase (if have).')
@click.option('--trusted-ca-key-passphase',
              '-p',
              required=False,
              help='Passphase of your own trusted ca private key.')
@_with_telemetry
def generatedeviceca(output_dir, valid_days, force, trusted_ca, trusted_ca_key, trusted_ca_key_passphase):
    try:
        output_dir = os.path.abspath(os.path.join(output_dir, EdgeConstants.CERT_FOLDER))
        if trusted_ca_key_passphase:
            trusted_ca_key_passphase = trusted_ca_key_passphase.encode()  # crypto requires byte string
        # Check whether create new trusted CA and generate files to be created
        output_files = list(Utils.get_device_ca_file_paths(output_dir, EdgeConstants.DEVICE_CA_ID).values())
        if trusted_ca and trusted_ca_key:
            output.info('Trusted CA (certification authority) and trusted CA key were provided.'
                        ' Load trusted CA from given files.')
        else:
            output.info('Trusted CA (certification authority) and Trusted CA key were not provided.'
                        ' Will create new trusted CA.')
            root_ca_files = Utils.get_device_ca_file_paths(output_dir, EdgeConstants.ROOT_CA_ID)
            output_files.append(root_ca_files[EdgeConstants.CERT_SUFFIX])
            output_files.append(root_ca_files[EdgeConstants.KEY_SUFFIX])
        # Check whether the output files exist
        existing_files = []
        for file in output_files:
            if os.path.exists(file):
                existing_files.append(file)
        if len(existing_files) > 0:
            if force:
                output.info('Following cert files already exist and will be overwritten: %s' % existing_files)
            else:
                raise EdgeError('Following cert files already exist. '
                                'You can use --force option to overwrite existing files: %s' % existing_files)
        # Generate certs
        edgeCert = EdgeCert(output_dir, '')
        edgeCert.generate_device_ca(valid_days, force, trusted_ca, trusted_ca_key, trusted_ca_key_passphase)
        output.info('Successfully generated device CA. Please find the generated certs at %s' % output_dir)
    except Exception as e:
        raise e


main.add_command(setup)
main.add_command(modulecred)
main.add_command(start)
main.add_command(stop)
main.add_command(validateconfig)
main.add_command(generatedeviceca)

if __name__ == "__main__":
    main()
