# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import docker
import os
import time
import tarfile
from io import BytesIO
from .errors import EdgeDeploymentError
from .utils import Utils


class EdgeDockerClient(object):
    _DOCKER_INFO_OS_TYPE_KEY = 'OSType'

    def __init__(self, docker_client=None):
        if docker_client is not None:
            self._client = docker_client
        else:
            try:
                self._client = docker.DockerClient.from_env(version='auto')
            except Exception as ex:
                msg = 'Could not connect to Docker daemon. Please make sure Docker is running'
                raise EdgeDeploymentError(msg, ex)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._client is not None:
            self._client.api.close()

    def stop_remove_by_label(self, label):
        try:
            filter_dict = {'label': label}
            containers = self._client.containers.list(all=True, filters=filter_dict)
            for container in containers:
                container.stop()
                self.remove(container.name)
        except docker.errors.APIError as ex:
            msg = 'Could not stop and remove containers by label: {0}'.format(label)
            raise EdgeDeploymentError(msg, ex)

    def get_local_image_sha_id(self, image):
        local_id = None
        try:
            inspect_dict = self._client.api.inspect_image(image)
            local_id = inspect_dict['Id']
        except docker.errors.APIError:
            local_id = None
        return local_id

    def pull(self, image, username, password):
        old_id = self.get_local_image_sha_id(image)
        try:
            is_updated = True
            auth_dict = None
            if username is not None:
                auth_dict = {'username': username, 'password': password}
            self._client.images.pull(image, auth_config=auth_dict)
            if old_id is not None:
                inspect_dict = self._client.api.inspect_image(image)
                new_id = inspect_dict['Id']
                if new_id == old_id:
                    is_updated = False

            return is_updated
        except docker.errors.APIError as ex:
            msg = 'Error during pull for image {0}'.format(image)
            raise EdgeDeploymentError(msg, ex)

    def pullIfNotExist(self, image, username, password):
        imageId = self.get_local_image_sha_id(image)
        if imageId is None:
            return self.pull(image, username, password)

    def status(self, container_name):
        try:
            containers = self._client.containers.list(all=True)
            for container in containers:
                if container_name == container.name:
                    return container.status
            return None
        except docker.errors.APIError as ex:
            msg = 'Error while checking status for: {0}'.format(container_name)
            raise EdgeDeploymentError(msg, ex)

    def stop(self, container_name):
        self._exec_container_method(container_name, 'stop')

    def start(self, container_name):
        self._exec_container_method(container_name, 'start')

    def remove(self, container_name):
        self._exec_container_method(container_name, 'remove')

    def create_network(self, network_name):
        create_network = False
        try:
            networks = self._client.networks.list(names=[network_name])
            if networks:
                num_networks = len(networks)
                if num_networks == 0:
                    create_network = True
            else:
                create_network = True
            if create_network is True:
                os_name = self.get_os_type()
                if os_name == 'windows':
                    return self._client.networks.create(network_name, driver='nat')
                else:
                    return self._client.networks.create(network_name, driver='bridge')
        except docker.errors.APIError as ex:
            msg = 'Could not create docker network: {0}'.format(network_name)
            raise EdgeDeploymentError(msg, ex)

    def create_volume(self, volume_name):
        try:
            volume = self._get_volume_if_exists(volume_name)
            if volume is None:
                return self._client.volumes.create(volume_name)
        except docker .errors.APIError as ex:
            msg = 'Docker volume create failed for: {0}'.format(volume_name)
            raise EdgeDeploymentError(msg, ex)

    def create_config_for_network(self, nw_name, *args, **kwargs):
        return self._client.api.create_networking_config({
            nw_name: self._client.api.create_endpoint_config(*args, **kwargs)
        })

    def create_container(self, image, **kwargs):
        try:
            return self._client.api.create_container(image, **kwargs)
        except docker.errors.ContainerError as ex_ctr:
            msg = 'Container exited with errors: {0}'.format(kwargs.get('name', None))
            raise EdgeDeploymentError(msg, ex_ctr)
        except docker.errors.ImageNotFound as ex_img:
            msg = 'Docker create failed. Image not found: {0}'.format(image)
            raise EdgeDeploymentError(msg, ex_img)
        except docker.errors.APIError as ex:
            msg = 'Docker create failed for image: {0}'.format(image)
            raise EdgeDeploymentError(msg, ex)

    def create_host_config(self, *args, **kwargs):
        try:
            return self._client.api.create_host_config(*args, **kwargs)
        except Exception as ex:
            msg = 'docker create host config failed'
            raise EdgeDeploymentError(msg, ex)

    def copy_file_to_volume(self,
                            container_name,
                            volume_name,
                            volume_dest_file_name,
                            volume_dest_dir_path,
                            host_src_file):
        if self.get_os_type() == 'windows':
            self._insert_file_in_volume_mount(volume_name, host_src_file, volume_dest_file_name)
        else:
            self._insert_file_in_container(container_name,
                                           volume_dest_file_name,
                                           volume_dest_dir_path,
                                           host_src_file)

    def get_os_type(self):
        try:
            info = self._client.info()
            return info[EdgeDockerClient._DOCKER_INFO_OS_TYPE_KEY].lower()
        except docker.errors.APIError as ex:
            msg = 'Docker daemon returned error'
            raise EdgeDeploymentError(msg, ex)

    def destroy_network(self, network_name):
        try:
            networks = self._client.networks.list(names=[network_name])
            if networks is not None:
                for network in networks:
                    if network.name == network_name:
                        network.remove()
        except docker.errors.APIError as ex:
            msg = 'Could not remove docker network: {0}'.format(network_name)
            raise EdgeDeploymentError(msg, ex)

    def remove_volume(self, volume_name, force=False):
        try:
            volume = self._get_volume_if_exists(volume_name)
            if volume is not None:
                volume.remove(force)
        except docker.errors.APIError as ex:
            msg = 'Docker volume remove failed for: {0}, force flag: {1}'.format(volume_name, force)
            raise EdgeDeploymentError(msg, ex)

    def _get_volume_if_exists(self, name):
        try:
            return self._client.volumes.get(name)
        except docker.errors.NotFound:
            return None
        except docker.errors.APIError as ex:
            msg = 'Docker volume get failed for: {0}'.format(name)
            raise EdgeDeploymentError(msg, ex)

    def _exec_container_method(self, container_name, method, **kwargs):
        container = self._get_container_by_name(container_name)
        try:
            getattr(container, method)(**kwargs)
        except docker.errors.APIError as ex:
            msg = 'Could not {0} container: {1}'.format(method, container_name)
            raise EdgeDeploymentError(msg, ex)

    def _get_container_by_name(self, container_name):
        try:
            return self._client.containers.get(container_name)
        except docker.errors.NotFound as nf_ex:
            msg = 'Could not find container by name {0}'.format(container_name)
            raise EdgeDeploymentError(msg, nf_ex)
        except docker.errors.APIError as ex:
            msg = 'Error getting container by name: {0}'.format(container_name)
            raise EdgeDeploymentError(msg, ex)

    def _insert_file_in_volume_mount(self, volume_name, host_src_file, volume_dest_file_name):
        try:
            volume_info = self._client.api.inspect_volume(volume_name)
            Utils.copy_files(host_src_file.replace('\\\\', '\\'),
                             os.path.join(volume_info['Mountpoint'].replace('\\\\', '\\'), volume_dest_file_name))
        except docker.errors.APIError as docker_ex:
            msg = 'Docker volume inspect failed for: {0}'.format(volume_name)
            raise EdgeDeploymentError(msg, docker_ex)
        except (OSError, IOError) as ex_os:
            msg = 'File IO error seen copying files to volume: {0}. ' \
                  'Errno: {1}, Error {2}'.format(volume_name, str(ex_os.errno), ex_os.strerror)
            raise EdgeDeploymentError(msg, ex_os)

    def _insert_file_in_container(self,
                                  container_name,
                                  volume_dest_file_name,
                                  volume_dest_dir_path,
                                  host_src_file):
        try:
            (tar_stream, dest_archive_info, container_tar_file) = \
                EdgeDockerClient.create_tar_objects(volume_dest_file_name)
            file_data = open(host_src_file, 'rb').read()
            dest_archive_info.size = len(file_data)
            dest_archive_info.mtime = time.time()
            dest_archive_info.mode = 0o444
            container_tar_file.addfile(dest_archive_info, BytesIO(file_data))
            container_tar_file.close()
            tar_stream.seek(0)
            container = self._get_container_by_name(container_name)
            container.put_archive(volume_dest_dir_path, tar_stream)
        except docker.errors.APIError as docker_ex:
            msg = 'Container put_archive failed for container: {0}'.format(container_name)
            raise EdgeDeploymentError(msg, docker_ex)
        except (OSError, IOError) as ex_os:
            msg = 'File IO error seen during put archive for container: {0}. ' \
                  'Errno: {1}, Error {2}'.format(container_name, str(ex_os.errno), ex_os.strerror)
            raise EdgeDeploymentError(msg, ex_os)

    @staticmethod
    def create_tar_objects(container_dest_file_name):
        tar_stream = BytesIO()
        dest_archive_info = tarfile.TarInfo(name=container_dest_file_name)
        container_tar_file = tarfile.TarFile(fileobj=tar_stream, mode='w')
        return (tar_stream, dest_archive_info, container_tar_file)

    @classmethod
    def create_instance(cls, docker_client):
        """
        Factory method useful in testing.
        """
        return cls(docker_client)
