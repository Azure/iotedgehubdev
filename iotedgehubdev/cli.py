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

# @click.command()
# @click.option('--as-cowboy', '-c', is_flag=True, help='Greet as a cowboy.')
# @click.argument('name', default='world', required=False)
# def main(name, as_cowboy):
#     """My Tool does one thing, and one thing well."""
#     greet = 'Howdy' if as_cowboy else 'Hello'
#     click.echo('{0}, {1}.'.format(greet, name))


@click.group(context_settings=CONTEXT_SETTINGS, invoke_without_command=True)
@click.version_option()
def main():
    ctx = click.get_current_context()
    if ctx.invoked_subcommand is None:
        click.echo(ctx.get_help())
        sys.exit(0)


@click.command(context_settings=CONTEXT_SETTINGS,
               help='Setup edgeHub. This must be done before starting.')
@click.option('--connectionstring',
              required=True,
              help='Provide the connection string of the edge device.')
@click.option('--gatewayhost',
              required=False,
              help='GatewayHostName value for the module to connect. Default is the FQDN of the device')
def setup(connectionstring, gatewayhost):
    if gatewayhost is None:
        gatewayhost = Utils.get_hostname()
    fileType = 'edgehub.config'
    certDir = HostPlatform.get_default_cert_path()
    Utils.mkdir_if_needed(certDir)
    edgeCert = EdgeCert(certDir, gatewayhost)
    edgeCert.generate_self_signed_certs()
    configFile = HostPlatform.get_config_file_path()
    Utils.delete_file(configFile, fileType)
    Utils.mkdir_if_needed(HostPlatform.get_config_path())
    configDict = {
        CONN_STR: connectionstring,
        CERT_PATH: certDir,
        GATEWAY_HOST: gatewayhost
    }
    configJson = json.dumps(configDict, indent=2, sort_keys=True)
    Utils.create_file(configFile, configJson, fileType)
    output.info('Setup edgeHub successfully')


@click.command(context_settings=CONTEXT_SETTINGS,
               help='get the connection string of target module')
@click.option('--outputfile',
              required=False,
              default=None,
              help='use `--outputfile` to specify the output file to save the connection string')
def targetconnstr(outputfile):
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
                connstr = edgeManager.getOrAddModule('target')
                output.info('Target module connection string is {0}'.format(connstr))
            else:
                output.error('Missing keys in config file. Please setup again')
    except Exception as e:
        output.error('Error: {0}'.format(str(e)))


@click.command(context_settings=CONTEXT_SETTINGS,
               help="start the edgeHub in single module test mode")
@click.option('--inputs',
              required=False,
              default=None,
              help='use `--inputs` to specify the input array of the target module')
def singlemoduletest(inputs):
    configFile = HostPlatform.get_config_file_path()
    if Utils.check_if_file_exists(configFile) is not True:
        output.error('Cannot find config file. Please setup first')
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
                output.info('EdgeHub has been started in single mode. Please connect your module as target and test')
            else:
                output.error('Missing keys in config file. Please setup again')
    except Exception as e:
        output.error('Error: {0}'.format(str(e)))


@click.command(context_settings=CONTEXT_SETTINGS,
               help="stop the edgeHub runtime")
def stop():
    try:
        EdgeManager.stop()
        output.info('EdgeHub has been stopped successfully')
    except Exception as e:
        output.error('Error: {0}'.format(str(e)))


main.add_command(setup)
main.add_command(targetconnstr)
main.add_command(singlemoduletest)
main.add_command(stop)

if __name__ == "__main__":
    main()
