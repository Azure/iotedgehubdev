import requests
import json
import docker
import os
from .constants import EdgeConstants as EC
from .utils import Utils
from .errors import ResponseError
from .edgedockerclient import EdgeDockerClient
from .edgecert import EdgeCert
from .composeproject import ComposeProject


class EdgeManager(object):
    HOST_PREFIX = 'HostName='
    DEVICE_PREFIX = 'DeviceId='
    KEY_PREFIX = 'SharedAccessKey='
    LABEL = 'iotedgehubdev'
    EDGEHUB_IMG = 'mcr.microsoft.com/azureiotedge-hub:1.0'
    TESTUTILITY_IMG = 'mcr.microsoft.com/azureiotedge-testing-utility:1.0.0-rc1'
    EDGEHUB_MODULE = '$edgeHub'
    EDGEHUB = 'edgeHubDev'
    INPUT = 'input'
    NW_NAME = 'azure-iot-edge-dev'
    HUB_VOLUME = 'edgehubdev'
    HUB_MOUNT = '/mnt/edgehub'
    MODULE_VOLUME = 'edgemoduledev'
    MODULE_MOUNT = '/mnt/edgemodule'
    HUB_CA_ENV = 'EdgeModuleHubServerCAChainCertificateFile=/mnt/edgehub/edge-chain-ca.cert.pem'
    HUB_CERT_ENV = 'EdgeModuleHubServerCertificateFile=/mnt/edgehub/edge-hub-server.cert.pfx'
    HUB_SRC_ENV = 'configSource=local'
    MODULE_CA_ENV = "EdgeModuleCACertificateFile=/mnt/edgemodule/edge-device-ca.cert.pem"
    HUB_SSLPATH_ENV = 'SSL_CERTIFICATE_PATH=/mnt/edgehub/'
    HUB_SSLCRT_ENV = 'SSL_CERTIFICATE_NAME=edge-hub-server.cert.pfx'
    CERT_HELPER = 'cert_helper'
    HELPER_IMG = 'hello-world:latest'

    def __init__(self, connectionStr, gatewayhost, certPath):
        values = connectionStr.split(';')
        self.hostname = ''
        self.deviceId = ''
        self.key = ''

        for val in values:
            stripped = val.strip()
            if stripped.startswith(EdgeManager.HOST_PREFIX):
                self.hostname = stripped[len(EdgeManager.HOST_PREFIX):]
            elif stripped.startswith(EdgeManager.DEVICE_PREFIX):
                self.deviceId = stripped[len(EdgeManager.DEVICE_PREFIX):]
            elif stripped.startswith(EdgeManager.KEY_PREFIX):
                self.key = stripped[len(EdgeManager.KEY_PREFIX):]

        self.gatewayhost = gatewayhost
        self.deviceUri = '{0}/devices/{1}'.format(self.hostname, self.deviceId)
        self.certPath = certPath
        self.edgeCert = EdgeCert(self.certPath, self.gatewayhost)

    @staticmethod
    def stop():
        edgedockerclient = EdgeDockerClient()
        edgedockerclient.stop_by_label(EdgeManager.LABEL)

    def startForSingleModule(self, inputs, port):
        edgeHubConnStr = self.getOrAddModule(EdgeManager.EDGEHUB_MODULE, False)
        inputConnStr = self.getOrAddModule(EdgeManager.INPUT, False)
        edgedockerclient = EdgeDockerClient()

        EdgeManager.stop()
        status = edgedockerclient.status(EdgeManager.EDGEHUB)
        if status is not None:
            edgedockerclient.stop(EdgeManager.EDGEHUB)
            edgedockerclient.remove(EdgeManager.EDGEHUB)
        status = edgedockerclient.status(EdgeManager.INPUT)
        if status is not None:
            edgedockerclient.stop(EdgeManager.INPUT)
            edgedockerclient.remove(EdgeManager.INPUT)

        self._prepare(edgedockerclient)

        routes = self._generateRoutesEnvFromInputs(inputs)
        self._start_edge_hub(edgedockerclient, edgeHubConnStr, routes)

        edgedockerclient.pullIfNotExist(EdgeManager.TESTUTILITY_IMG, None, None)
        network_config = edgedockerclient.create_config_for_network(EdgeManager.NW_NAME)
        inputEnv = [EdgeManager.MODULE_CA_ENV, "EdgeHubConnectionString={0}".format(inputConnStr)]
        input_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(EdgeManager.MODULE_MOUNT, EdgeManager.MODULE_VOLUME)],
            port_bindings={
                '3000': port
            }
        )
        inputContainer = edgedockerclient.create_container(
            EdgeManager.TESTUTILITY_IMG,
            name=EdgeManager.INPUT,
            volumes=[EdgeManager.MODULE_MOUNT],
            host_config=input_host_config,
            networking_config=network_config,
            environment=inputEnv,
            labels=[EdgeManager.LABEL],
            ports=[(3000, 'tcp')]
        )

        edgedockerclient.copy_file_to_volume(
            EdgeManager.INPUT, self._device_cert(),
            EdgeManager.MODULE_MOUNT,
            self.edgeCert.get_cert_file_path(EC.EDGE_DEVICE_CA))
        edgedockerclient.start(inputContainer.get('Id'))

    def start_solution(self, deployment_config):
        edgedockerclient = EdgeDockerClient()

        EdgeManager.stop()
        status = edgedockerclient.status(EdgeManager.EDGEHUB)
        if status is not None:
            edgedockerclient.stop(EdgeManager.EDGEHUB)
            edgedockerclient.remove(EdgeManager.EDGEHUB)

        self._prepare(edgedockerclient)
        self._prepare_cert(edgedockerclient)

        module_names = [EdgeManager.EDGEHUB_MODULE]
        custom_modules = deployment_config['moduleContent']['$edgeAgent']['properties.desired']['modules']
        for module_name in custom_modules:
            module_names.append(module_name)

        ConnStr_info = {}
        for module_name in module_names:
            # TODO: In futrue PR $ escape will be done before yaml file dump.
            # Replace $ by $$ to escape $ in yaml file
            ConnStr_info[module_name] = self.getOrAddModule(module_name, False).replace('$', '$$')

        env_info = {
            'hub_env': {
                'HUB_CA_ENV': EdgeManager.HUB_CA_ENV.replace('$', '$$'),
                'HUB_CERT_ENV': EdgeManager.HUB_CERT_ENV.replace('$', '$$'),
                'HUB_SRC_ENV': EdgeManager.HUB_SRC_ENV.replace('$', '$$'),
                'HUB_SSLPATH_ENV': EdgeManager.HUB_SSLPATH_ENV.replace('$', '$$'),
                'HUB_SSLCRT_ENV': EdgeManager.HUB_SSLCRT_ENV.replace('$', '$$')
            },
            'module_env': {
                'MODULE_CA_ENV': EdgeManager.MODULE_CA_ENV.replace('$', '$$')
            }
        }

        volume_info = {
            'HUB_MOUNT': EdgeManager.HUB_MOUNT.replace('$', '$$'),
            'HUB_VOLUME': EdgeManager.HUB_VOLUME.replace('$', '$$'),
            'MODULE_VOLUME': EdgeManager.MODULE_VOLUME.replace('$', '$$'),
            'MODULE_MOUNT': EdgeManager.MODULE_MOUNT.replace('$', '$$')
        }

        network_info = {
            'NW_NAME': EdgeManager.NW_NAME.replace('$', '$$'),
            'ALIASES': self.gatewayhost.replace('$', '$$')
        }

        compose_project = ComposeProject(deployment_config)
        compose_project.set_edge_info({
            'ConnStr_info': ConnStr_info,
            'env_info': env_info,
            'volume_info': volume_info,
            'network_info': network_info,
            'hub_name': EdgeManager.EDGEHUB
        })

        compose_project.compose()
        compose_project.dump('docker-compose.yml')

    def _prepare_cert(self, edgedockerclient):
        status = edgedockerclient.status(EdgeManager.CERT_HELPER)
        if status is not None:
            edgedockerclient.stop(EdgeManager.CERT_HELPER)
            edgedockerclient.remove(EdgeManager.CERT_HELPER)

        helper_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(EdgeManager.HUB_MOUNT, EdgeManager.HUB_VOLUME),
                    docker.types.Mount(EdgeManager.MODULE_MOUNT, EdgeManager.MODULE_VOLUME)]
        )

        edgedockerclient.pull(EdgeManager.HELPER_IMG, None, None)

        # Ignore flake8 local variable 'cert_helper' is assigned to but never used error
        cert_helper = edgedockerclient.create_container(  # noqa: F841
            EdgeManager.HELPER_IMG,
            name=EdgeManager.CERT_HELPER,
            volumes=[EdgeManager.HUB_MOUNT, EdgeManager.MODULE_MOUNT],
            host_config=helper_host_config,
            labels=[EdgeManager.LABEL]
        )

        edgedockerclient.copy_file_to_volume(
            EdgeManager.CERT_HELPER, EdgeManager._chain_cert(),
            EdgeManager.HUB_MOUNT, self.edgeCert.get_cert_file_path(EC.EDGE_CHAIN_CA))
        edgedockerclient.copy_file_to_volume(
            EdgeManager.CERT_HELPER, EdgeManager._hubserver_pfx(),
            EdgeManager.HUB_MOUNT, self.edgeCert.get_pfx_file_path(EC.EDGE_HUB_SERVER))
        edgedockerclient.copy_file_to_volume(
            EdgeManager.CERT_HELPER, self._device_cert(),
            EdgeManager.MODULE_MOUNT, self.edgeCert.get_cert_file_path(EC.EDGE_DEVICE_CA))

    def start(self, modulesDict, routes):
        return

    def getOrAddModule(self, name, islocal):
        try:
            return self.getModule(name, islocal)
        except ResponseError as geterr:
            if geterr.status_code == 404:
                try:
                    return self.addModule(name, islocal)
                except ResponseError as adderr:
                    raise adderr
            else:
                raise geterr

    def outputModuleCred(self, name, islocal, output_file):
        connstrENV = 'EdgeHubConnectionString={0}'.format(self.getOrAddModule(name, islocal))
        if islocal:
            deviceCAEnv = 'EdgeModuleCACertificateFile={0}'.format(self.edgeCert.get_cert_file_path(EC.EDGE_DEVICE_CA))
        else:
            deviceCAEnv = EdgeManager.MODULE_CA_ENV
        cred = [connstrENV, deviceCAEnv]

        if output_file is not None:
            dir = os.path.dirname(output_file)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(output_file, 'w+') as envFile:
                envFile.writelines(['\n', cred[0], '\n', cred[1]])
        return cred

    def getModule(self, name, islocal):
        moduleUri = "https://{0}/devices/{1}/modules/{2}?api-version=2017-11-08-preview".format(
            self.hostname, self.deviceId, name)
        sas = Utils.get_iot_hub_sas_token(self.deviceUri, self.key, None)
        res = requests.get(
            moduleUri,
            headers={
                'Authorization': sas,
                'Content-Type': 'application/json'
            }
        )
        if res.ok is not True:
            raise ResponseError(res.status_code, res.text)
        return self._generateModuleConnectionStr(res, islocal)

    def addModule(self, name, islocal):
        moduleUri = "https://{0}/devices/{1}/modules/{2}?api-version=2017-11-08-preview".format(
            self.hostname, self.deviceId, name)
        sas = Utils.get_iot_hub_sas_token(self.deviceUri, self.key, None)
        res = requests.put(
            moduleUri,
            headers={
                "Authorization": sas,
                "Content-Type": "application/json"
            },
            data=json.dumps({
                'moduleId': name,
                'deviceId': self.deviceId
            })
        )
        if res.ok is not True:
            raise ResponseError(res.status_code, res.text)
        return self._generateModuleConnectionStr(res, islocal)

    def _generateModuleConnectionStr(self, response, islocal):
        jsonObj = json.loads(response.content)
        moduleId = jsonObj['moduleId']
        deviceId = jsonObj['deviceId']
        sasKey = jsonObj['authentication']['symmetricKey']['primaryKey']
        hubTemplate = 'HostName={0};DeviceId={1};ModuleId={2};SharedAccessKey={3}'
        moduleTemplate = 'HostName={0};GatewayHostName={1};DeviceId={2};ModuleId={3};SharedAccessKey={4}'
        gatewayhost = self.gatewayhost
        if (islocal):
            gatewayhost = 'localhost'
        if (moduleId == '$edgeHub'):
            return hubTemplate.format(self.hostname, deviceId, moduleId, sasKey)
        else:
            return moduleTemplate.format(self.hostname, gatewayhost, deviceId, moduleId, sasKey)

    def _generateRoutesEnvFromInputs(self, inputs):
        routes = [
            'routes__output=FROM /messages/modules/target/outputs/* INTO BrokeredEndpoint("/modules/input/inputs/print")'
        ]
        template = 'routes__r{0}=FROM /messages/modules/input/outputs/{1} INTO BrokeredEndpoint("/modules/target/inputs/{2}")'
        inputSet = set(inputs)
        for (idx, input) in enumerate(inputSet):
            routes.append(template.format(idx + 1, input, input))
        return routes

    def _prepare(self, edgedockerclient):
        edgedockerclient.create_network(EdgeManager.NW_NAME)
        edgedockerclient.create_volume(EdgeManager.HUB_VOLUME)
        edgedockerclient.create_volume(EdgeManager.MODULE_VOLUME)

    def _start_edge_hub(self, edgedockerclient, edgeHubConnStr, routes):
        edgedockerclient.pullIfNotExist(EdgeManager.EDGEHUB_IMG, None, None)
        network_config = edgedockerclient.create_config_for_network(EdgeManager.NW_NAME, aliases=[self.gatewayhost])
        hub_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(EdgeManager.HUB_MOUNT, EdgeManager.HUB_VOLUME)],
            port_bindings={
                '8883': 8883,
                '443': 443,
                '5671': 5671
            }
        )
        hubEnv = [
            EdgeManager.HUB_CA_ENV,
            EdgeManager.HUB_CERT_ENV,
            EdgeManager.HUB_SRC_ENV,
            EdgeManager.HUB_SSLPATH_ENV,
            EdgeManager.HUB_SSLCRT_ENV,
            'IotHubConnectionString={0}'.format(edgeHubConnStr)]
        hubEnv.extend(routes)
        hubContainer = edgedockerclient.create_container(
            EdgeManager.EDGEHUB_IMG,
            name=EdgeManager.EDGEHUB,
            volumes=[EdgeManager.HUB_MOUNT],
            host_config=hub_host_config,
            networking_config=network_config,
            environment=hubEnv,
            labels=[EdgeManager.LABEL],
            ports=[(8883, 'tcp'), (443, 'tcp'), (5671, 'tcp')]
        )

        edgedockerclient.copy_file_to_volume(
            EdgeManager.EDGEHUB, EdgeManager._chain_cert(),
            EdgeManager.HUB_MOUNT, self.edgeCert.get_cert_file_path(EC.EDGE_CHAIN_CA))
        edgedockerclient.copy_file_to_volume(
            EdgeManager.EDGEHUB, EdgeManager._hubserver_pfx(),
            EdgeManager.HUB_MOUNT, self.edgeCert.get_pfx_file_path(EC.EDGE_HUB_SERVER))
        edgedockerclient.start(hubContainer.get('Id'))

    @staticmethod
    def _chain_cert():
        return EC.EDGE_CHAIN_CA + EC.CERT_SUFFIX

    @staticmethod
    def _hubserver_pfx():
        return EC.EDGE_HUB_SERVER + EC.PFX_SUFFIX

    @staticmethod
    def _device_cert():
        return EC.EDGE_DEVICE_CA + EC.CERT_SUFFIX
