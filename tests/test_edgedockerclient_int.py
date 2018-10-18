# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import subprocess
import time
import unittest
import docker
from iotedgehubdev.errors import EdgeDeploymentError
from iotedgehubdev.edgedockerclient import EdgeDockerClient


class TestEdgeDockerClientSmoke(unittest.TestCase):
    IMAGE_NAME = 'microsoft/dotnet:2.0-runtime'
    NETWORK_NAME = 'ctl_int_test_network'
    CONTAINER_NAME = 'ctl_int_test_container'
    VOLUME_NAME = 'ctl_int_int_test_mnt'
    LABEL_NAME = 'ctl_int_test_label'

    def test_get_os_type(self):
        with EdgeDockerClient() as client:
            exception_raised = False
            try:
                os_type = client.get_os_type()
            except EdgeDeploymentError:
                exception_raised = True
            self.assertFalse(exception_raised)
            permitted_os_types = ['windows', 'linux']
            self.assertIn(os_type, permitted_os_types)

    def test_pull(self):
        with EdgeDockerClient() as client:
            exception_raised = False
            image_name = self.IMAGE_NAME
            try:
                local_sha_1 = client.get_local_image_sha_id(image_name)
                is_updated = client.pull(image_name, None, None)
                local_sha_2 = client.get_local_image_sha_id(image_name)
                if is_updated:
                    self.assertNotEqual(local_sha_1, local_sha_2)
                else:
                    self.assertEqual(local_sha_1, local_sha_2)
            except EdgeDeploymentError:
                exception_raised = True
            self.assertFalse(exception_raised)

    def _create_container(self, client):
        image_name = self.IMAGE_NAME
        os_type = client.get_os_type().lower()
        if os_type == 'linux':
            volume_path = '/{0}'.format(self.VOLUME_NAME)
        elif os_type == 'windows':
            volume_path = 'c:/{0}'.format(self.VOLUME_NAME)
        env_dict = {}
        env_dict['TEST_VOLUME_NAME'] = self.VOLUME_NAME
        client.pull(image_name, None, None)
        client.create_network(self.NETWORK_NAME)
        client.create_volume(self.VOLUME_NAME)
        host_config = client.create_host_config(
            mounts=[docker.types.Mount(volume_path, self.VOLUME_NAME)]
        )
        network_config = client.create_config_for_network(self.NETWORK_NAME)
        client.create_container(
            image_name,
            name=self.CONTAINER_NAME,
            networking_config=network_config,
            host_config=host_config,
            volumes=[volume_path],
            environment=env_dict,
            command="sleep 20s")
        client.copy_file_to_volume(self.CONTAINER_NAME,
                                   self.VOLUME_NAME,
                                   'test_file_name.txt',
                                   volume_path,
                                   __file__)

    def _destroy_container(self, client):
        client.stop(self.CONTAINER_NAME)
        status = client.status(self.CONTAINER_NAME)
        self.assertEqual('exited', status)
        client.remove(self.CONTAINER_NAME)
        status = client.status(self.CONTAINER_NAME)
        self.assertIsNone(status)
        client.remove_volume(self.VOLUME_NAME)
        client.destroy_network(self.NETWORK_NAME)

    def _reset_host_network(self, client):
        os_type = client.get_os_type().lower()
        if (os_type == 'windows'):
            subprocess.Popen('powershell.exe Remove-NetNat -Confirm:$False')
            subprocess.Popen('powershell.exe Restart-Service hns')

    def test_create(self):
        with EdgeDockerClient() as client:
            exception_raised = False
            try:
                self._reset_host_network(client)
                status = client.status(self.CONTAINER_NAME)
                if status is not None:
                    self._destroy_container(client)
                self._create_container(client)
                status = client.status(self.CONTAINER_NAME)
                self.assertEqual('created', status)
                client.start(self.CONTAINER_NAME)
                status = client.status(self.CONTAINER_NAME)
                self.assertEqual('running', status)
                time.sleep(5)
                self._destroy_container(client)
            except EdgeDeploymentError as ex:
                print(ex)
                exception_raised = True
            self.assertFalse(exception_raised)
