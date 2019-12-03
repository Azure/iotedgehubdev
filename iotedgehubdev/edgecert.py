# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
from .certutils import EdgeCertUtil
from .constants import EdgeConstants
from .errors import EdgeError
from .output import Output


class EdgeCert(object):
    def __init__(self, certs_dir, hostname):
        self.certs_dir = certs_dir
        self.hostname = hostname
        self.output = Output()

    def generate_self_signed_certs(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert(EdgeConstants.EDGE_DEVICE_CA,
                                      validity_days_from_now=365,
                                      subject_dict=EdgeConstants.CERT_DEFAULT_DICT,
                                      passphrase=None)
        cert_util.export_cert_artifacts_to_dir(EdgeConstants.EDGE_DEVICE_CA, self.certs_dir)

        cert_util.create_intermediate_ca_cert(EdgeConstants.EDGE_AGENT_CA,
                                              EdgeConstants.EDGE_DEVICE_CA,
                                              validity_days_from_now=365,
                                              common_name='Edge Agent CA',
                                              set_terminal_ca=False,
                                              passphrase=None)
        cert_util.export_cert_artifacts_to_dir(EdgeConstants.EDGE_AGENT_CA, self.certs_dir)

        cert_util.create_server_cert(EdgeConstants.EDGE_HUB_SERVER,
                                     EdgeConstants.EDGE_AGENT_CA,
                                     validity_days_from_now=365,
                                     hostname=self.hostname)
        cert_util.export_cert_artifacts_to_dir(EdgeConstants.EDGE_HUB_SERVER, self.certs_dir)
        cert_util.export_pfx_cert(EdgeConstants.EDGE_HUB_SERVER, self.certs_dir)

        prefixes = [EdgeConstants.EDGE_AGENT_CA, EdgeConstants.EDGE_DEVICE_CA]
        cert_util.chain_ca_certs(EdgeConstants.EDGE_CHAIN_CA, prefixes, self.certs_dir)

    # Generate IoT Edge device CA to be configured in IoT Edge runtime
    def generate_device_ca(self, valid_days, overwrite_existing, trusted_ca, trusted_ca_key, trusted_ca_key_passphase):
        # Function level variables
        root_ca_cert_path = os.path.join(self.certs_dir, EdgeConstants.ROOT_CA_ID + EdgeConstants.CERT_SUFFIX)
        root_ca_key_path = os.path.join(self.certs_dir, EdgeConstants.ROOT_CA_ID + EdgeConstants.KEY_SUFFIX)
        device_ca_cert_path = os.path.join(self.certs_dir, EdgeConstants.DEVICE_CA_ID + EdgeConstants.CERT_SUFFIX)
        device_ca_key_path = os.path.join(self.certs_dir, EdgeConstants.DEVICE_CA_ID + EdgeConstants.KEY_SUFFIX)
        device_ca_cert_chain_path = os.path.join(self.certs_dir, EdgeConstants.DEVICE_CA_ID + EdgeConstants.FULLCHAIN_CERT_SUFFIX)
        create_root_ca = not (trusted_ca and trusted_ca_key)
        # Check existing cert files
        existing_files = self.__get_existing_files__(device_ca_cert_path, device_ca_key_path, device_ca_cert_chain_path)
        if create_root_ca:
            existing_files.extend(self.__get_existing_files__(root_ca_cert_path, root_ca_key_path))

        if len(existing_files) > 0:
            if overwrite_existing:
                self.output.info('Following cert files already exist and will be overwritten: %s' % existing_files)
            else:
                raise EdgeError(
                    'Following cert files already exist. '
                    'You can use --force option to overwrite existing files: %s' % existing_files)

        # Generate certs
        cert_util = EdgeCertUtil()
        if create_root_ca:
            self.output.info('Generating root ca %s' % EdgeConstants.ROOT_CA_ID)
            cert_util.create_root_ca_cert(EdgeConstants.ROOT_CA_ID,
                                          validity_days_from_now=valid_days,
                                          subject_dict=EdgeConstants.CERT_DEFAULT_DICT,
                                          passphrase=None)
            cert_util.dump_cert(EdgeConstants.ROOT_CA_ID, root_ca_cert_path, root_ca_key_path, overwrite_existing)
            self.output.info('Saving generated root ca %s to folder %s' % (EdgeConstants.ROOT_CA_ID, self.certs_dir))
        else:
            self.output.info('--trusted-ca and --trusted-ca-key are provided, loading root ca from file %s' % trusted_ca)
            cert_util.load_cert_from_file(EdgeConstants.ROOT_CA_ID, trusted_ca, trusted_ca_key, trusted_ca_key_passphase)

        self.output.info('Generating device ca %s' % EdgeConstants.DEVICE_CA_ID)
        cert_util.create_intermediate_ca_cert(EdgeConstants.DEVICE_CA_ID, EdgeConstants.ROOT_CA_ID,
                                              validity_days_from_now=valid_days,
                                              common_name='Edge Device CA',
                                              set_terminal_ca=False,
                                              passphrase=None)
        cert_util.dump_cert(EdgeConstants.DEVICE_CA_ID, device_ca_cert_path, device_ca_key_path, overwrite_existing)
        cert_util.dump_cert_chain(device_ca_cert_chain_path, overwrite_existing,
                                  EdgeConstants.DEVICE_CA_ID, EdgeConstants.ROOT_CA_ID)
        self.output.info('Saving generated device ca %s to folder %s' % (EdgeConstants.DEVICE_CA_ID, self.certs_dir))

    def get_cert_file_path(self, id_str):
        return EdgeCertUtil.get_cert_file_path(id_str, self.certs_dir)

    def get_pfx_file_path(self, id_str):
        return EdgeCertUtil.get_pfx_file_path(id_str, self.certs_dir)

    def __get_existing_files__(self, *files):
        existing_files = []
        for file in files:
            if os.path.exists(file):
                existing_files.append(file)
        return existing_files
