# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import json
import os

import docker
import requests

from .composeproject import ComposeProject
from .constants import EdgeConstants as EC
from .edgecert import EdgeCert
from .edgedockerclient import EdgeDockerClient
from .errors import ResponseError, RegistriesLoginError
from .hostplatform import HostPlatform
from .utils import Utils


class EdgeManager(object):
    LABEL = 'iotedgehubdev'
    EDGEHUB_IMG = 'mcr.microsoft.com/azureiotedge-hub:1.0'
    TESTUTILITY_IMG = 'mcr.microsoft.com/azureiotedge-testing-utility:1.0.0-rc1'
    EDGEHUB_MODULE = '$edgeHub'
    EDGEHUB = 'edgeHubDev'
    INPUT = 'input'
    NW_NAME = 'azure-iot-edge-dev'
    MOUNT_BASE = 'mnt'
    HUB_VOLUME = 'edgehubdev'
    HUB_MOUNT = '{0}/edgehub'
    MODULE_VOLUME = 'edgemoduledev'
    MODULE_MOUNT = '{0}/edgemodule'
    HUB_CA_ENV = 'EdgeModuleHubServerCAChainCertificateFile={0}/edgehub/edge-chain-ca.cert.pem'
    HUB_CERT_ENV = 'EdgeModuleHubServerCertificateFile={0}/edgehub/edge-hub-server.cert.pfx'
    HUB_SRC_ENV = 'configSource=local'
    MODULE_CA_ENV = "EdgeModuleCACertificateFile={0}/edgemodule/edge-device-ca.cert.pem"
    HUB_SSLPATH_ENV = 'SSL_CERTIFICATE_PATH={0}/edgehub/'
    HUB_SSLCRT_ENV = 'SSL_CERTIFICATE_NAME=edge-hub-server.cert.pfx'
    CERT_HELPER = 'cert_helper'
    HELPER_IMG = 'hello-world:latest'
    COMPOSE_FILE = os.path.join(HostPlatform.get_share_data_path(), 'docker-compose.yml')

    def __init__(self, connection_str, gatewayhost, cert_path):
        connection_str_dict = Utils.parse_device_connection_str(connection_str)
        self.hostname = connection_str_dict[EC.HOSTNAME_KEY]
        self.device_id = connection_str_dict[EC.DEVICE_ID_KEY]
        self.access_key = connection_str_dict[EC.ACCESS_KEY_KEY]
        self.compose_file = None
        self.gatewayhost = gatewayhost
        self.device_uri = '{0}/devices/{1}'.format(self.hostname, self.device_id)
        self.cert_path = cert_path
        self.edge_cert = EdgeCert(self.cert_path, self.gatewayhost)

    @staticmethod
    def stop(edgedockerclient=None):
        if edgedockerclient is None:
            edgedockerclient = EdgeDockerClient()

        compose_err = None
        label_err = None
        try:
            if os.path.exists(EdgeManager.COMPOSE_FILE):
                cmd = "docker-compose -f {0} down".format(EdgeManager.COMPOSE_FILE)
                Utils.exe_proc(cmd.split())
        except Exception as e:
            compose_err = e

        try:
            edgedockerclient.stop_remove_by_label(EdgeManager.LABEL)
        except Exception as e:
            label_err = e

        if compose_err or label_err:
            raise Exception('{0}{1}'.format(
                '' if compose_err is None else str(compose_err),
                '' if label_err is None else str(label_err)))

    def start_singlemodule(self, inputs, port):
        edgedockerclient = EdgeDockerClient()
        mount_base = self._obtain_mount_path(edgedockerclient)
        if mount_base is None:
            raise Exception("OS Type is not supported")

        EdgeManager.stop(edgedockerclient)
        self._prepare(edgedockerclient)

        edgeHubConnStr = self.getOrAddModule(EdgeManager.EDGEHUB_MODULE, False)
        inputConnStr = self.getOrAddModule(EdgeManager.INPUT, False)
        routes = self._generateRoutesEnvFromInputs(inputs)
        self._start_edge_hub(edgedockerclient, edgeHubConnStr, routes, mount_base)

        module_mount = EdgeManager.MODULE_MOUNT.format(mount_base)
        edgedockerclient.pullIfNotExist(EdgeManager.TESTUTILITY_IMG, None, None)
        network_config = edgedockerclient.create_config_for_network(EdgeManager.NW_NAME)
        inputEnv = [EdgeManager.MODULE_CA_ENV.format(mount_base), "EdgeHubConnectionString={0}".format(inputConnStr)]
        input_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(module_mount, EdgeManager.MODULE_VOLUME)],
            port_bindings={
                '3000': port
            },
            restart_policy={
                'MaximumRetryCount': 3,
                'Name': 'on-failure'
            }
        )
        inputContainer = edgedockerclient.create_container(
            EdgeManager.TESTUTILITY_IMG,
            name=EdgeManager.INPUT,
            volumes=[module_mount],
            host_config=input_host_config,
            networking_config=network_config,
            environment=inputEnv,
            labels=[EdgeManager.LABEL],
            ports=[(3000, 'tcp')]
        )

        edgedockerclient.copy_file_to_volume(
            EdgeManager.INPUT, EdgeManager.MODULE_VOLUME, self._device_cert(),
            module_mount,
            self.edge_cert.get_cert_file_path(EC.EDGE_DEVICE_CA))
        edgedockerclient.start(inputContainer.get('Id'))

    def config_solution(self, module_content, target, mount_base):
        module_names = [EdgeManager.EDGEHUB_MODULE]
        custom_modules = module_content['$edgeAgent']['properties.desired']['modules']
        for module_name in custom_modules:
            module_names.append(module_name)

        ConnStr_info = {}
        for module_name in module_names:
            ConnStr_info[module_name] = self.getOrAddModule(module_name, False)

        env_info = {
            'hub_env': [
                EdgeManager.HUB_CA_ENV.format(mount_base),
                EdgeManager.HUB_CERT_ENV.format(mount_base),
                EdgeManager.HUB_SRC_ENV,
                EdgeManager.HUB_SSLPATH_ENV.format(mount_base),
                EdgeManager.HUB_SSLCRT_ENV
            ],
            'module_env': [
                EdgeManager.MODULE_CA_ENV.format(mount_base)
            ]
        }

        volume_info = {
            'HUB_MOUNT': EdgeManager.HUB_MOUNT.format(mount_base),
            'HUB_VOLUME': EdgeManager.HUB_VOLUME,
            'MODULE_VOLUME': EdgeManager.MODULE_VOLUME,
            'MODULE_MOUNT': EdgeManager.MODULE_MOUNT.format(mount_base)
        }

        network_info = {
            'NW_NAME': EdgeManager.NW_NAME,
            'ALIASES': self.gatewayhost
        }

        compose_project = ComposeProject(module_content)
        compose_project.set_edge_info({
            'ConnStr_info': ConnStr_info,
            'env_info': env_info,
            'volume_info': volume_info,
            'network_info': network_info,
            'hub_name': EdgeManager.EDGEHUB,
            'labels': EdgeManager.LABEL
        })

        compose_project.compose()
        compose_project.dump(target)

    def start_solution(self, module_content, verbose):
        edgedockerclient = EdgeDockerClient()
        mount_base = self._obtain_mount_path(edgedockerclient)
        if not mount_base:
            raise Exception("OS Type is not supported")

        EdgeManager.stop(edgedockerclient)
        self._prepare(edgedockerclient)
        self._prepare_cert(edgedockerclient, mount_base)

        self.config_solution(module_content, EdgeManager.COMPOSE_FILE, mount_base)

        cmd_pull = ['docker-compose', '-f', EdgeManager.COMPOSE_FILE, 'pull', EdgeManager.EDGEHUB]
        Utils.exe_proc(cmd_pull)
        if verbose:
            cmd_up = ['docker-compose', '-f', EdgeManager.COMPOSE_FILE, 'up']
        else:
            cmd_up = ['docker-compose', '-f', EdgeManager.COMPOSE_FILE, 'up', '-d']
        Utils.exe_proc(cmd_up)

    @staticmethod
    def login_registries(module_content):
        registryCredentials = module_content.get('$edgeAgent', {}).get('properties.desired', {}).get(
            'runtime', {}).get('settings', {}).get('registryCredentials')
        if not registryCredentials:
            return
        failLogin = []
        errMsg = ''
        for key in registryCredentials:
            value = registryCredentials[key]
            try:
                cmd_login = ['docker', 'login', '-u', value['username'], '-p', value['password'], value['address']]
                Utils.exe_proc(cmd_login)
            except Exception as e:
                failLogin.append(key)
                errMsg += '{0}\n'.format(str(e))
        if failLogin:
            raise RegistriesLoginError(failLogin, errMsg)

    def _prepare_cert(self, edgedockerclient, mount_base):
        status = edgedockerclient.status(EdgeManager.CERT_HELPER)
        if status is not None:
            edgedockerclient.stop(EdgeManager.CERT_HELPER)
            edgedockerclient.remove(EdgeManager.CERT_HELPER)

        hub_mount = EdgeManager.HUB_MOUNT.format(mount_base)
        module_mount = EdgeManager.MODULE_MOUNT.format(mount_base)

        helper_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(hub_mount, EdgeManager.HUB_VOLUME),
                    docker.types.Mount(module_mount, EdgeManager.MODULE_VOLUME)]
        )

        edgedockerclient.pull(EdgeManager.HELPER_IMG, None, None)

        edgedockerclient.create_container(
            EdgeManager.HELPER_IMG,
            name=EdgeManager.CERT_HELPER,
            volumes=[hub_mount, module_mount],
            host_config=helper_host_config,
            labels=[EdgeManager.LABEL]
        )

        edgedockerclient.copy_file_to_volume(
            EdgeManager.CERT_HELPER, EdgeManager.HUB_VOLUME, EdgeManager._chain_cert(),
            hub_mount, self.edge_cert.get_cert_file_path(EC.EDGE_CHAIN_CA))
        edgedockerclient.copy_file_to_volume(
            EdgeManager.CERT_HELPER, EdgeManager.HUB_VOLUME, EdgeManager._hubserver_pfx(),
            hub_mount, self.edge_cert.get_pfx_file_path(EC.EDGE_HUB_SERVER))
        edgedockerclient.copy_file_to_volume(
            EdgeManager.CERT_HELPER, EdgeManager.MODULE_VOLUME, self._device_cert(),
            module_mount, self.edge_cert.get_cert_file_path(EC.EDGE_DEVICE_CA))

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

    def outputModuleCred(self, names, islocal, output_file):
        connstrENV = 'EdgeHubConnectionString={0}'.format('|'.join([self.getOrAddModule(name, islocal) for name in names]))
        deviceCAEnv = 'EdgeModuleCACertificateFile={0}'.format(self.edge_cert.get_cert_file_path(EC.EDGE_DEVICE_CA))
        cred = [connstrENV, deviceCAEnv]

        if output_file is not None:
            output_path = os.path.abspath(output_file)
            dir = os.path.dirname(output_path)
            if not os.path.exists(dir):
                os.makedirs(dir)
            with open(output_path, 'w+') as envFile:
                envFile.writelines(['\n', cred[0], '\n', cred[1]])
        return cred

    def getModule(self, name, islocal):
        moduleUri = self._getModuleReqUri(name)
        sas = Utils.get_iot_hub_sas_token(self.device_uri, self.access_key, None)
        res = requests.get(
            moduleUri,
            headers={
                'Authorization': sas,
                'Content-Type': 'application/json'
            }
        )
        if res.ok is not True:
            raise ResponseError(res.status_code, res.text)
        else:
            jsonObj = res.json()
            auth = jsonObj['authentication']
            if auth is not None:
                authType = auth['type']
                authKey = auth['symmetricKey']
                if authType == 'sas' and authKey is not None and authKey['primaryKey'] is not None:
                    return self._generateModuleConnectionStr(res, islocal)
            return self.updateModule(name, jsonObj['etag'], islocal)

    def updateModule(self, name, etag, islocal):
        moduleUri = self._getModuleReqUri(name)
        sas = Utils.get_iot_hub_sas_token(self.device_uri, self.access_key, None)
        res = requests.put(
            moduleUri,
            headers={
                'Authorization': sas,
                'Content-Type': "application/json",
                'If-Match': '"*"'
            },
            data=json.dumps({
                'moduleId': name,
                'deviceId': self.device_id,
                'authentication': {
                    'type': 'sas'
                }
            })
        )
        if res.ok is not True:
            raise ResponseError(res.status_code, res.text)
        return self._generateModuleConnectionStr(res, islocal)

    def addModule(self, name, islocal):
        moduleUri = self._getModuleReqUri(name)
        sas = Utils.get_iot_hub_sas_token(self.device_uri, self.access_key, None)
        res = requests.put(
            moduleUri,
            headers={
                "Authorization": sas,
                "Content-Type": "application/json"
            },
            data=json.dumps({
                'moduleId': name,
                'deviceId': self.device_id
            })
        )
        if res.ok is not True:
            raise ResponseError(res.status_code, res.text)
        return self._generateModuleConnectionStr(res, islocal)

    def _getModuleReqUri(self, name):
        return "https://{0}/devices/{1}/modules/{2}?api-version=2018-06-30".format(
            self.hostname, self.device_id, name)

    def _generateModuleConnectionStr(self, response, islocal):
        jsonObj = response.json()
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

    def _start_edge_hub(self, edgedockerclient, edgeHubConnStr, routes, mount_base):
        edgedockerclient.pull(EdgeManager.EDGEHUB_IMG, None, None)
        network_config = edgedockerclient.create_config_for_network(EdgeManager.NW_NAME, aliases=[self.gatewayhost])
        hub_mount = EdgeManager.HUB_MOUNT.format(mount_base)
        hub_host_config = edgedockerclient.create_host_config(
            mounts=[docker.types.Mount(hub_mount, EdgeManager.HUB_VOLUME)],
            port_bindings={
                '8883': 8883,
                '443': 443,
                '5671': 5671
            }
        )
        hubEnv = [
            EdgeManager.HUB_CA_ENV.format(mount_base),
            EdgeManager.HUB_CERT_ENV.format(mount_base),
            EdgeManager.HUB_SRC_ENV,
            EdgeManager.HUB_SSLPATH_ENV.format(mount_base),
            EdgeManager.HUB_SSLCRT_ENV,
            'IotHubConnectionString={0}'.format(edgeHubConnStr)]
        hubEnv.extend(routes)
        hubContainer = edgedockerclient.create_container(
            EdgeManager.EDGEHUB_IMG,
            name=EdgeManager.EDGEHUB,
            volumes=[hub_mount],
            host_config=hub_host_config,
            networking_config=network_config,
            environment=hubEnv,
            labels=[EdgeManager.LABEL],
            ports=[(8883, 'tcp'), (443, 'tcp'), (5671, 'tcp')]
        )

        edgedockerclient.copy_file_to_volume(
            EdgeManager.EDGEHUB, EdgeManager.HUB_VOLUME, EdgeManager._chain_cert(),
            hub_mount, self.edge_cert.get_cert_file_path(EC.EDGE_CHAIN_CA))
        edgedockerclient.copy_file_to_volume(
            EdgeManager.EDGEHUB, EdgeManager.HUB_VOLUME, EdgeManager._hubserver_pfx(),
            hub_mount, self.edge_cert.get_pfx_file_path(EC.EDGE_HUB_SERVER))
        edgedockerclient.start(hubContainer.get('Id'))

    def _obtain_mount_path(self, edgedockerclient):
        os_type = edgedockerclient.get_os_type().lower()
        if os_type == 'linux':
            return '/{0}'.format(EdgeManager.MOUNT_BASE)
        elif os_type == 'windows':
            return 'c:/{0}'.format(EdgeManager.MOUNT_BASE)

    @staticmethod
    def _chain_cert():
        return EC.EDGE_CHAIN_CA + EC.CERT_SUFFIX

    @staticmethod
    def _hubserver_pfx():
        return EC.EDGE_HUB_SERVER + EC.PFX_SUFFIX

    @staticmethod
    def _device_cert():
        return EC.EDGE_DEVICE_CA + EC.CERT_SUFFIX
