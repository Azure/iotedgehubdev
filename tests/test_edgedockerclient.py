# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import unittest
from unittest import mock
import docker
from iotedgehubdev.errors import EdgeError, EdgeDeploymentError
from iotedgehubdev.edgedockerclient import EdgeDockerClient


class TestEdgeDockerClientGetOSType(unittest.TestCase):
    @mock.patch('docker.DockerClient', autospec=True)
    def test_get_os_valid(self, mock_docker_client):
        # arrange
        os_type = 'TEST_OS'
        mock_docker_client.info.return_value = {'OSType': os_type}
        client = EdgeDockerClient.create_instance(mock_docker_client)
        result = client.get_os_type()
        mock_docker_client.info.assert_called_with()
        self.assertEqual(result, os_type.lower())

    @mock.patch('docker.DockerClient', autospec=True)
    def test_get_os_fails(self, mock_docker_client):
        # arrange
        mock_docker_client.info.side_effect = docker.errors.APIError('info fails')
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeError):
            client.get_os_type()


class TestEdgeDockerClientGetLocalImageSHAId(unittest.TestCase):
    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_get_local_image_sha_id_valid(self, mock_docker_client, mock_docker_api_client):
        # arrange
        test_id = '1234'
        mock_docker_api_client.inspect_image.return_value = {'Id': test_id}
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'

        # act
        result = client.get_local_image_sha_id(image)

        # assert
        mock_docker_api_client.inspect_image.assert_called_with(image)
        self.assertEqual(result, test_id)

    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_get_local_image_sha_id_fails(self, mock_docker_client, mock_docker_api_client):
        # arrange
        mock_docker_api_client.inspect_image.side_effect = docker.errors.APIError('inspect fails')
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'

        # act
        result = client.get_local_image_sha_id(image)

        # assert
        mock_docker_api_client.inspect_image.assert_called_with(image)
        self.assertEqual(result, None)


class TestEdgeDockerClientPull(unittest.TestCase):
    @mock.patch('iotedgehubdev.edgedockerclient.EdgeDockerClient.get_local_image_sha_id')
    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_pull_image_exists_locally_with_no_newer_image_valid(self,
                                                                 mock_docker_client,
                                                                 mock_docker_api_client,
                                                                 mock_get_local_id):
        # arrange
        test_id = '1234'
        mock_get_local_id.return_value = test_id
        mock_docker_api_client.inspect_image.return_value = {'Id': test_id}
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'
        username = "test_user"
        password = "test_password"
        auth_dict = {'username': username, 'password': password}

        # act
        result = client.pull(image, username, password)

        # assert
        mock_get_local_id.assert_called_with(image)
        mock_docker_api_client.inspect_image.assert_called_with(image)
        mock_docker_client.images.pull.assert_called_with(image, auth_config=auth_dict)
        self.assertFalse(result)

    @mock.patch('iotedgehubdev.edgedockerclient.EdgeDockerClient.get_local_image_sha_id')
    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_pull_image_exists_locally_with_newer_image_valid(self,
                                                              mock_docker_client,
                                                              mock_docker_api_client,
                                                              mock_get_local_id):
        # arrange
        test_id = '1234'
        mock_get_local_id.return_value = '1000'
        mock_docker_api_client.inspect_image.return_value = {'Id': test_id}
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'
        username = "test_user"
        password = "test_password"
        auth_dict = {'username': username, 'password': password}

        # act
        result = client.pull(image, username, password)

        # assert
        mock_get_local_id.assert_called_with(image)
        mock_docker_api_client.inspect_image.assert_called_with(image)
        mock_docker_client.images.pull.assert_called_with(image, auth_config=auth_dict)
        self.assertTrue(result)

    @mock.patch('iotedgehubdev.edgedockerclient.EdgeDockerClient.get_local_image_sha_id')
    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_pull_image_exists_locally_with_newer_image_no_credentials_valid(self,
                                                                             mock_docker_client,
                                                                             mock_docker_api_client,
                                                                             mock_get_local_id):
        # arrange
        test_id = '1234'
        mock_get_local_id.return_value = '1000'
        mock_docker_api_client.inspect_image.return_value = {'Id': test_id}
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'
        auth_dict = None

        # act
        result = client.pull(image, None, None)

        # assert
        mock_get_local_id.assert_called_with(image)
        mock_docker_api_client.inspect_image.assert_called_with(image)
        mock_docker_client.images.pull.assert_called_with(image, auth_config=auth_dict)
        self.assertTrue(result)

    @mock.patch('iotedgehubdev.edgedockerclient.EdgeDockerClient.get_local_image_sha_id')
    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_pull_image_no_image_exists_locally(self,
                                                mock_docker_client,
                                                mock_docker_api_client,
                                                mock_get_local_id):
        # arrange
        test_id = '1234'
        mock_get_local_id.return_value = None
        mock_docker_api_client.inspect_image.return_value = {'Id': test_id}
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'
        username = "test_user"
        password = "test_password"
        auth_dict = {'username': username, 'password': password}

        # act
        result = client.pull(image, username, password)

        # assert
        mock_get_local_id.assert_called_with(image)
        mock_docker_api_client.inspect_image.assert_not_called()
        mock_docker_client.images.pull.assert_called_with(image, auth_config=auth_dict)
        self.assertTrue(result)

    @mock.patch('iotedgehubdev.edgedockerclient.EdgeDockerClient.get_local_image_sha_id')
    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_pull_raises_exception(self,
                                   mock_docker_client,
                                   mock_docker_api_client,
                                   mock_get_local_id):
        # arrange
        test_id = '1234'
        mock_get_local_id.return_value = None
        mock_docker_api_client.inspect_image.return_value = {'Id': test_id}
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        mock_docker_client.images.pull.side_effect = docker.errors.APIError('docker unavailable')
        client = EdgeDockerClient.create_instance(mock_docker_client)
        image = 'test_image'
        username = "test_user"
        password = "test_password"

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.pull(image, username, password)


class TestContainerSpec(docker.models.containers.Container):
    """
        Class used in mock autospec for containers
    """
    name = 'name'
    status = 'status'

    def stop(self, **kwargs):
        pass

    def start(self, **kwargs):
        pass

    def remove(self, **kwargs):
        pass


class TestEdgeDockerContainerOps(unittest.TestCase):
    """
        Unit tests for APIs
            EdgeDockerClient.start
            EdgeDockerClient.stop
            EdgeDockerClient.remove
            EdgeDockerClient.status
            EdgeDockerClient.stop_remove_by_label
            EdgeDockerClient.create
    """
    TEST_CONTAINER_NAME = 'test_name'
    TEST_LABEL = 'test_label'

    @mock.patch('docker.models.containers.Container', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_start_valid(self, mock_docker_client, mock_container):
        # arrange
        mock_docker_client.containers.get.return_value = mock_container
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act
        client.start(self.TEST_CONTAINER_NAME)

        # assert
        mock_docker_client.containers.get.assert_called_with(self.TEST_CONTAINER_NAME)
        mock_container.start.assert_called_with()

    @mock.patch('docker.models.containers.Container', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_start_fails_raises_exception(self, mock_docker_client, mock_container):
        # arrange
        mock_container.start.side_effect = docker.errors.APIError('start failure')
        mock_docker_client.containers.get.return_value = mock_container
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.start(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.DockerClient', autospec=True)
    def test_start_invalid_container_raises_exception(self, mock_docker_client):
        # arrange
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound('invalid image')
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.start(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.models.containers.Container', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_stop_valid(self, mock_docker_client, mock_container):
        # arrange
        mock_docker_client.containers.get.return_value = mock_container
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act
        client.stop(self.TEST_CONTAINER_NAME)

        # assert
        mock_docker_client.containers.get.assert_called_with(self.TEST_CONTAINER_NAME)
        mock_container.stop.assert_called_with()

    @mock.patch('docker.models.containers.Container', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_stop_fails_raises_exception(self, mock_docker_client, mock_container):
        # arrange
        mock_container.stop.side_effect = docker.errors.APIError('stop failure')
        mock_docker_client.containers.get.return_value = mock_container
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.stop(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.DockerClient', autospec=True)
    def test_stop_invalid_container_raises_exception(self, mock_docker_client):
        # arrange
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound('invalid image')
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.stop(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.models.containers.Container', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_remove_valid(self, mock_docker_client, mock_container):
        # arrange
        mock_docker_client.containers.get.return_value = mock_container
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act
        client.remove(self.TEST_CONTAINER_NAME)

        # assert
        mock_docker_client.containers.get.assert_called_with(self.TEST_CONTAINER_NAME)
        mock_container.remove.assert_called_with()

    @mock.patch('docker.models.containers.Container', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_remove_fails_raises_exception(self, mock_docker_client, mock_container):
        # arrange
        mock_container.remove.side_effect = docker.errors.APIError('remove failure')
        mock_docker_client.containers.get.return_value = mock_container
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.remove(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.DockerClient', autospec=True)
    def test_remove_invalid_container_raises_exception(self, mock_docker_client):
        # arrange
        mock_docker_client.containers.get.side_effect = docker.errors.NotFound('invalid image')
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.remove(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.models.containers.Container', autospec=TestContainerSpec)
    @mock.patch('docker.models.containers.Container', autospec=TestContainerSpec)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_status_valid(self, mock_docker_client, mock_container, mock_non_match_container):
        # @note when setting the container object using autospec=True, it could not
        # set the properties name and status of the mock object.
        # Thus we resort to using TestContainerSpec as the autospec where these are
        # settable. It should be noted that for the status test it was sufficient to use
        # @mock.patch('docker.models.containers.Container') directly but we are using
        # TestContainerSpec for consistency

        # arrange
        test_status = 'running'
        type(mock_container).status = mock.PropertyMock(return_value=test_status)
        type(mock_container).name = mock.PropertyMock(return_value=self.TEST_CONTAINER_NAME)
        type(mock_non_match_container).status = mock.PropertyMock(return_value='running')
        type(mock_non_match_container).name = mock.PropertyMock(return_value='blah')
        mock_docker_client.containers.list.return_value = [mock_non_match_container, mock_container]
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act
        result = client.status(self.TEST_CONTAINER_NAME)

        # assert
        mock_docker_client.containers.list.assert_called_with(all=True)
        self.assertEqual(test_status, result)

    @mock.patch('docker.DockerClient', autospec=True)
    def test_status_raises_exception(self, mock_docker_client):
        # arrange
        mock_docker_client.containers.list.side_effect = docker.errors.APIError('list failure')
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.status(self.TEST_CONTAINER_NAME)

    @mock.patch('docker.models.containers.Container', autospec=TestContainerSpec)
    @mock.patch('docker.models.containers.Container', autospec=TestContainerSpec)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_stop_by_label_valid(self, mock_docker_client,
                                 mock_container1, mock_container2):
        # @note when setting multiple container mocks autospec=True failed which is
        # why we resort to using TestContainerSpec as the autospec class

        # arrange
        mock_docker_client.containers.list.return_value = [mock_container1, mock_container2]
        client = EdgeDockerClient.create_instance(mock_docker_client)
        filter_dict = {'label': self.TEST_LABEL}

        # act
        client.stop_remove_by_label(self.TEST_LABEL)

        # assert
        mock_docker_client.containers.list.assert_called_with(all=True, filters=filter_dict)
        mock_container1.stop.assert_called_with()
        mock_container2.stop.assert_called_with()

    @mock.patch('docker.DockerClient', autospec=True)
    def test_stop_by_label_raises_exception(self, mock_docker_client):
        # arrange
        mock_docker_client.containers.list.side_effect = docker.errors.APIError('list failure')
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            client.stop_remove_by_label(self.TEST_LABEL)

    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_create_valid(self, mock_docker_client, mock_docker_api_client):
        # arrange
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        image = 'test_image'
        container_name = 'test_name'
        detach_bool = True
        env_dict = {'test_key_env': 'test_val_env'}
        ports_dict = {'test_key_ports': 'test_val_ports'}
        volume_dict = {'test_key_volume': {'bind': 'test_val_bind', 'mode': 'test_val_mode'}}
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act
        client.create_container(
            image,
            name=container_name,
            detach=detach_bool,
            environment=env_dict,
            ports=ports_dict,
            volumes=volume_dict)

        # assert
        mock_docker_client.api.create_container.assert_called_with(
            image,
            detach=detach_bool,
            environment=env_dict,
            name=container_name,
            ports=ports_dict,
            volumes=volume_dict)

    def _create_common_invocation(self, client):
        image = 'test_image'
        container_name = 'test_name'
        detach_bool = True
        env_dict = {'test_key_env': 'test_val_env'}
        ports_dict = {'test_key_ports': 'test_val_ports'}
        volume_dict = {'test_key_volume': {'bind': 'test_val_bind', 'mode': 'test_val_mode'}}

        # act
        client.create_container(
            image,
            name=container_name,
            detach=detach_bool,
            environment=env_dict,
            ports=ports_dict,
            volumes=volume_dict)

    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_create_raises_except_when_containerError_is_raised(self,
                                                                mock_docker_client,
                                                                mock_docker_api_client):
        # arrange
        mock_docker_api_client.create_container.side_effect = docker.errors.ContainerError(
            'container', 1, 'cmd', 'image', 'stderr')
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            self._create_common_invocation(client)

    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_create_raises_except_when_ImageNotFound_is_raised(self,
                                                               mock_docker_client,
                                                               mock_docker_api_client):
        # arrange
        mock_docker_api_client.create_container.side_effect = docker.errors.ImageNotFound('image error')
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            self._create_common_invocation(client)

    @mock.patch('docker.APIClient', autospec=True)
    @mock.patch('docker.DockerClient', autospec=True)
    def test_create_raises_except_when_APIError_is_raised(self,
                                                          mock_docker_client,
                                                          mock_docker_api_client):
        # arrange
        mock_docker_api_client.create_container.side_effect = docker.errors.APIError('image error')
        type(mock_docker_client).api = mock.PropertyMock(return_value=mock_docker_api_client)
        client = EdgeDockerClient.create_instance(mock_docker_client)

        # act, assert
        with self.assertRaises(EdgeDeploymentError):
            self._create_common_invocation(client)
