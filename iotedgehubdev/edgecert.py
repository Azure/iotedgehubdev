# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .certutils import EdgeCertUtil
from .constants import EdgeConstants
from .output import Output


class EdgeCert(object):
    def __init__(self, certs_dir, hostname):
        self.certs_dir = certs_dir
        self.hostname = hostname
        self.cert_util = EdgeCertUtil()
        self.output = Output()

    def generate_self_signed_certs(self):
        self.cert_util.create_root_ca_cert(EdgeConstants.EDGE_DEVICE_CA,
                                           validity_days_from_now=365,
                                           subject_dict=EdgeConstants.CERT_DEFAULT_DICT,
                                           passphrase=None)
        self.cert_util.export_cert_artifacts_to_dir(EdgeConstants.EDGE_DEVICE_CA, self.certs_dir)

        self.cert_util.create_intermediate_ca_cert(EdgeConstants.EDGE_AGENT_CA,
                                                   EdgeConstants.EDGE_DEVICE_CA,
                                                   validity_days_from_now=365,
                                                   common_name='Edge Agent CA',
                                                   set_terminal_ca=False,
                                                   passphrase=None)
        self.cert_util.export_cert_artifacts_to_dir(EdgeConstants.EDGE_AGENT_CA, self.certs_dir)

        self.cert_util.create_server_cert(EdgeConstants.EDGE_HUB_SERVER,
                                          EdgeConstants.EDGE_AGENT_CA,
                                          validity_days_from_now=365,
                                          hostname=self.hostname)
        self.cert_util.export_cert_artifacts_to_dir(EdgeConstants.EDGE_HUB_SERVER, self.certs_dir)
        self.cert_util.export_pfx_cert(EdgeConstants.EDGE_HUB_SERVER, self.certs_dir)

        prefixes = [EdgeConstants.EDGE_AGENT_CA, EdgeConstants.EDGE_DEVICE_CA]
        self.cert_util.chain_ca_certs(EdgeConstants.EDGE_CHAIN_CA, prefixes, self.certs_dir)

    # Generate IoT Edge device CA to be configured in IoT Edge runtime
    def generate_device_ca(self, cert_name, valid_days, overwrite_existing):
        root_ca_id = EdgeConstants.ROOT_CA_ID
        device_ca_id = EdgeConstants.DEVICE_CA_ID_PREFIX + cert_name
        root_ca_exists = self.cert_util.check_cert_existence(root_ca_id)
        # Generate certs
        if not root_ca_exists:
            self.output.info('Generating root ca %s' % root_ca_id)
            self.cert_util.create_root_ca_cert(root_ca_id,
                                               validity_days_from_now=valid_days,
                                               subject_dict=EdgeConstants.CERT_DEFAULT_DICT,
                                               passphrase=None)
            self.cert_util.dump_cert(root_ca_id, self.certs_dir, overwrite_existing)
            self.output.info('Saving generated root ca %s to folder %s' % (root_ca_id, self.certs_dir))

        self.output.info('Generating device ca %s' % device_ca_id)
        self.cert_util.create_intermediate_ca_cert(device_ca_id, root_ca_id,
                                                   validity_days_from_now=valid_days,
                                                   common_name='Edge Device CA',
                                                   set_terminal_ca=False,
                                                   passphrase=None)
        self.cert_util.dump_cert(device_ca_id, self.certs_dir, overwrite_existing)
        self.cert_util.dump_cert_chain(self.certs_dir, overwrite_existing, device_ca_id, root_ca_id)
        self.output.info('Saving generated device ca %s to folder %s' % (device_ca_id, self.certs_dir))

    def get_cert_file_path(self, id_str):
        return EdgeCertUtil.get_cert_file_path(id_str, self.certs_dir)

    def get_pfx_file_path(self, id_str):
        return EdgeCertUtil.get_pfx_file_path(id_str, self.certs_dir)

    def load_cert_from_file(self, id_str, cert_path, key_path, key_passphase):
        self.cert_util.load_cert_from_file(id_str, cert_path, key_path, key_passphase)
