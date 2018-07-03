import sys
import click
import json
from .output import Output
from .hostplatform import HostPlatform
from .edgecert import EdgeCert
from .edgemanager import EdgeManager
from .utils import Utils

CONTEXT_SETTINGS = dict(help_option_names=['-h', '--help'], max_content_width=120)
output = Output()

CONN_STR = 'connectionString'
CERT_PATH = 'certPath'
GATEWAY_HOST = 'gatewayhost'


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
    output.info('Setup EdgeHub runtime successfully')


@click.command(context_settings=CONTEXT_SETTINGS,
               help='Get the connection string of target module.')
@click.option('--local',
              '-l',
              required=False,
              is_flag=True,
              default=False,
              show_default=True,
              help='Set `localhost` to `GatewayHostName` for module to run on host natively.')
@click.option('--output',
              '-o',
              'output_file',  # non-user-facing alias to prevent conflict with the other variable named `output`
              required=False,
              show_default=True,
              help='Specify the output file to save the connection string.')
#   TODO: better naming or shorter
def targetconnstr(local, output_file):
    configFile = HostPlatform.get_config_file_path()
    if Utils.check_if_file_exists(configFile) is not True:
        output.error('Cannot find config file. Please setup first')
        return
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
                output.error('Missing keys in config file. Please setup again')
    except Exception as e:
        output.error('Error: {0}'.format(str(e)))


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Start the EdgeHub runtime.")
@click.option('--compose',
              '-c',
              required=False,
              is_flag=True,
              default=False,
              show_default=True,
              help='Start EdgeHub runtime in Docker Compose mode.')
@click.option('--inputs',
              '-i',
              required=False,
              default=None,
              help='Specify the inputs of the target module, separated by commas.')
#   TODO: Use multi?
def start(compose, inputs):
    print(single_mode)
    configFile = HostPlatform.get_config_file_path()
    if Utils.check_if_file_exists(configFile) is not True:
        output.error('Cannot find config file. Please run `iotedgehubdev setup` first.')
        return

    try:
        with open(configFile) as f:
            jsonObj = json.load(f)
            if CONN_STR in jsonObj and CERT_PATH in jsonObj and GATEWAY_HOST in jsonObj:
                if inputs is None:
                    inputs = ['input1']
                connectionString = jsonObj[CONN_STR]
                certPath = jsonObj[CERT_PATH]
                gatewayhost = jsonObj[GATEWAY_HOST]
                edgeManager = EdgeManager(connectionString, gatewayhost, certPath)
                edgeManager.startForSingleModule(inputs)
                output.info('EdgeHub runtime has been started in single mode. Please connect your module as target and test.')
            else:
                output.error('Missing keys in config file. Please run `iotedgehubdev setup` again.')
    except Exception as e:
        output.error('Error: {0}'.format(str(e)))


@click.command(context_settings=CONTEXT_SETTINGS,
               help="Stop the EdgeHub runtime.")
def stop():
    try:
        EdgeManager.stop()
        output.info('EdgeHub runtime has been stopped successfully')
    except Exception as e:
        output.error('Error: {0}'.format(str(e)))


main.add_command(setup)
main.add_command(targetconnstr)
main.add_command(start)
main.add_command(stop)

if __name__ == "__main__":
    main()
