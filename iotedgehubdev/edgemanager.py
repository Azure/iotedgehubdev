import requests
import json
import docker
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
    LABEL = 'edgehublocaltest'
    EDGEHUB_IMG = 'mcr.microsoft.com/azureiotedge-hub:1.0'
    TESTUTILITY_IMG = 'adashen/iot-edge-testing-utility:0.0.1'
    EDGEHUB_MODULE = '$edgeHub'
    EDGEHUB = 'edgeHubTest'
    INPUT = 'input'
    NW_NAME = 'azure-iot-edge-test'
    HUB_VOLUME = 'edgehubtest'
    HUB_MOUNT = '/mnt/edgehub'
    MODULE_VOLUME = 'edgemoduletest'
    MODULE_MOUNT = '/mnt/edgemodule'
    HUB_CA_ENV = 'EdgeModuleHubServerCAChainCertificateFile=/mnt/edgehub/edge-chain-ca.cert.pem'
    HUB_CERT_ENV = 'EdgeModuleHubServerCertificateFile=/mnt/edgehub/edge-hub-server.cert.pfx'
    HUB_SRC_ENV = 'configSource=local'
    MODULE_CA_ENV = "EdgeModuleCACertificateFile=/mnt/edgemodule/edge-device-ca.cert.pem"
    HUB_SSLPATH_ENV = 'SSL_CERTIFICATE_PATH=/mnt/edgehub/'
    HUB_SSLCRT_ENV = 'SSL_CERTIFICATE_NAME=edge-hub-server.cert.pfx'

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

    def startForSingleModule(self, inputs):
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
                '3000': 3000
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
        status = edgedockerclient.status(EdgeManager.INPUT)
        if status is not None:
            edgedockerclient.stop(EdgeManager.INPUT)
            edgedockerclient.remove(EdgeManager.INPUT)

        self._prepare(edgedockerclient)
        self._prepare_cert(edgedockerclient)

        module_names = [EdgeManager.EDGEHUB_MODULE]
        custom_modules = deployment_config['moduleContent']['$edgeAgent']['properties.desired']['modules']
        for module_name in custom_modules:
            module_names.append(module_name)

        ConnStr_info = {}
        for module_name in module_names:
            # Replace $ by $$ to escape $ in yaml file
            ConnStr_info[module_name] = self.getOrAddModule(module_name, False).replace('$', '$$')

        env_info = {
            'hub_env': {
                'HUB_CA_ENV': EdgeManager.HUB_CA_ENV,
                'HUB_CERT_ENV': EdgeManager.HUB_CERT_ENV,
                'HUB_SRC_ENV': EdgeManager.HUB_SRC_ENV,
                'HUB_SSLPATH_ENV': EdgeManager.HUB_SSLPATH_ENV,
                'HUB_SSLCRT_ENV': EdgeManager.HUB_SSLCRT_ENV
            },
            'module_env': {
                'MODULE_CA_ENV': EdgeManager.MODULE_CA_ENV
            }
        }

        volume_info = {
            'HUB_MOUNT': EdgeManager.HUB_MOUNT,
            'HUB_VOLUME': EdgeManager.HUB_VOLUME,
            'MODULE_VOLUME': EdgeManager.MODULE_VOLUME,
            'MODULE_MOUNT': EdgeManager.MODULE_MOUNT
        }

        network_info = {
            'NW_NAME': EdgeManager.NW_NAME,
            'ALIASES': self.gatewayhost
        }

        compose_project = ComposeProject(deployment_config)
        compose_project.get_edge_info({
            'ConnStr_info': ConnStr_info,
            'env_info': env_info,
            'volume_info': volume_info,
            'network_info': network_info
        })

        compose_project.compose()
        compose_project.dump('docker-compose.yml')

    def _prepare_cert(self, edgedockerclient):
        status = edgedockerclient.status('cert_helper')
        if status is not None:
            edgedockerclient.stop('cert_helper')
            edgedockerclient.remove('cert_helper')

        helper_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(EdgeManager.HUB_MOUNT, EdgeManager.HUB_VOLUME),
                    docker.types.Mount(EdgeManager.MODULE_MOUNT, EdgeManager.MODULE_VOLUME)]
        )

        # Ignore flake8 local variable 'cert_helper' is assigned to but never used error
        cert_helper = edgedockerclient.create_container(  # noqa: F841
            'busybox:latest',
            name='cert_helper',
            volumes=[EdgeManager.HUB_MOUNT, EdgeManager.MODULE_MOUNT],
            host_config=helper_host_config,
            labels=[EdgeManager.LABEL]
        )

        edgedockerclient.copy_file_to_volume(
            'cert_helper', EdgeManager._chain_cert(),
            EdgeManager.HUB_MOUNT, self.edgeCert.get_cert_file_path(EC.EDGE_CHAIN_CA))
        edgedockerclient.copy_file_to_volume(
            'cert_helper', EdgeManager._hubserver_pfx(),
            EdgeManager.HUB_MOUNT, self.edgeCert.get_pfx_file_path(EC.EDGE_HUB_SERVER))
        edgedockerclient.copy_file_to_volume(
            'cert_helper', self._device_cert(),
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
        for (idx, input) in enumerate(inputs):
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
                '443': 443
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
            ports=[(8883, 'tcp'), (443, 'tcp')]
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
