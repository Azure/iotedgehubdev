import sys
import click
import json
from .output import Output
from .hostplatform import HostPlatform
from .edgecert import EdgeCert
from .edgemanager import EdgeManager
from .utils import Utils
from functools import wraps
from . import configs
from . import telemetry

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], max_content_width=120)
output = Output()

CONN_STR = 'connectionString'
CERT_PATH = 'certPath'
GATEWAY_HOST = 'gatewayhost'


def _with_telemetry(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        configs.check_firsttime()
        telemetry.start(func.__name__)
        value = None
        try:
            value = func(*args, **kwargs)
            telemetry.success()
            telemetry.flush()
            return value
        except Exception as e:
            output.error('Error: {0}'.format(str(e)))
            telemetry.fail(str(e), 'Command failed')

    return _wrapper


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
def main():
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


@click.command(context_settings=CONTEXT_SETTINGS,
               help='Setup the EdgeHub runtime. This must be done before starting.')
@click.option('--connection-string',
              '-c',
              required=True,
              help='Set the connection string of the Edge device. Note: Use double quotes when supplying this input.')
@click.option('--gateway-host',
              '-g',
              required=False,
              default=Utils.get_hostname(),
              show_default=True,
              help='GatewayHostName value for the module to connect.')
@_with_telemetry
def setup(connection_string, gateway_host):
    fileType = 'edgehub.config'
    certDir = HostPlatform.get_default_cert_path()
    Utils.mkdir_if_needed(certDir)
    edgeCert = EdgeCert(certDir, gateway_host)
    edgeCert.generate_self_signed_certs()
    configFile = HostPlatform.get_config_file_path()
    Utils.delete_file(configFile, fileType)
    Utils.mkdir_if_needed(HostPlatform.get_config_path())
    configDict = {
        CONN_STR: connection_string,
        CERT_PATH: certDir,
        GATEWAY_HOST: gateway_host
    }
    configJson = json.dumps(configDict, indent=2, sort_keys=True)
    Utils.create_file(configFile, configJson, fileType)
    output.info('Setup EdgeHub runtime successfully.')


@click.command(context_settings=CONTEXT_SETTINGS,
               # short_help hack to prevent Click truncating help text (https://github.com/pallets/click/issues/486)
               short_help='Get the credentials of target module such as connection string and certificate file path.',
               help='Get the credentials of target module such as connection string and certificate file path.')
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
              help='Specify the output file to save the connection string.')
@_with_telemetry
def modulecred(local, output_file):
    configFile = HostPlatform.get_config_file_path()
    if Utils.check_if_file_exists(configFile) is not True:
        output.error('Cannot find config file. Please setup first')
        sys.exit(1)
    try:
        with open(configFile) as f:
            jsonObj = json.load(f)
            if CONN_STR in jsonObj and CERT_PATH in jsonObj and GATEWAY_HOST in jsonObj:
                connectionString = jsonObj[CONN_STR]
                certPath = jsonObj[CERT_PATH]
                gatewayhost = jsonObj[GATEWAY_HOST]
                edgeManager = EdgeManager(connectionString, gatewayhost, certPath)
                connstr = edgeManager.getOrAddModule('target', local)
                output.info('Target module connection string is {0}'.format(connstr))
            else:
                output.error('Missing keys in config file. Please run `iotedgehubdev setup` again.')
                sys.exit(1)
    except Exception as e:
        output.error('Error: {0}.'.format(str(e)))
        sys.exit(1)


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Start the EdgeHub runtime.")
@click.option('--inputs',
              '-i',
              required=False,
              help='Start EdgeHub runtime in single module mode '
                   'using the specified comma-separated inputs of the target module, e.g., `input1,input2`.')
# @click.option('--deployment',
#               '-d',
#               required=False,
#               help='Start EdgeHub runtime in Docker Compose mode using the specified deployment manifest.')
@_with_telemetry
def start(inputs):
    deployment = None
    if inputs is None and deployment is not None:
        pass
    else:
        if deployment is not None:
            output.info('Deployment manifest is ignored when inputs are present.')

        configFile = HostPlatform.get_config_file_path()
        if Utils.check_if_file_exists(configFile) is not True:
            output.error('Cannot find config file. Please run `iotedgehubdev setup` first.')
            sys.exit(1)

        try:
            with open(configFile) as f:
                jsonObj = json.load(f)
                if CONN_STR in jsonObj and CERT_PATH in jsonObj and GATEWAY_HOST in jsonObj:
                    if inputs is None:
                        input_list = ['input1']
                    else:
                        input_list = [input_.strip() for input_ in inputs.strip().split(',')]
                    connectionString = jsonObj[CONN_STR]
                    certPath = jsonObj[CERT_PATH]
                    gatewayhost = jsonObj[GATEWAY_HOST]
                    edgeManager = EdgeManager(connectionString, gatewayhost, certPath)
                    edgeManager.startForSingleModule(input_list)
                    output.info('EdgeHub runtime has been started in single module mode.'
                                'Please connect your module as target and test.')
                else:
                    output.error('Missing keys in config file. Please run `iotedgehubdev setup` again.')
                    sys.exit(1)
        except Exception as e:
            output.error('Error: {0}.'.format(str(e)))
            sys.exit(1)


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Stop the EdgeHub runtime")
@_with_telemetry
def stop():
    try:
        EdgeManager.stop()
        output.info('EdgeHub runtime has been stopped successfully')
    except Exception as e:
        output.error('Error: {0}.'.format(str(e)))
        sys.exit(1)


main.add_command(setup)
main.add_command(modulecred)
main.add_command(start)
main.add_command(stop)

if __name__ == "__main__":
    main()
