# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

from .certutils import EdgeCertUtil
from .constants import EdgeConstants


class EdgeCert(object):
    def __init__(self, certs_dir, hostname):
        self.certs_dir = certs_dir
        self.hostname = hostname

    def generate_self_signed_certs(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert(EdgeConstants.EDGE_DEVICE_CA,
                                      validity_days_from_now=365,
                                      subject_dict=EdgeConstants.CERT_DEFAULT_DICT,
                                      passphrase=None)
        cert_util.export_simulator_cert_artifacts_to_dir(EdgeConstants.EDGE_DEVICE_CA, self.certs_dir)

        cert_util.create_intermediate_ca_cert(EdgeConstants.EDGE_AGENT_CA,
                                              EdgeConstants.EDGE_DEVICE_CA,
                                              validity_days_from_now=365,
                                              common_name='Edge Agent CA',
                                              set_terminal_ca=False,
                                              passphrase=None)
        cert_util.export_simulator_cert_artifacts_to_dir(EdgeConstants.EDGE_AGENT_CA, self.certs_dir)

        cert_util.create_server_cert(EdgeConstants.EDGE_HUB_SERVER,
                                     EdgeConstants.EDGE_AGENT_CA,
                                     validity_days_from_now=365,
                                     hostname=self.hostname)
        cert_util.export_simulator_cert_artifacts_to_dir(EdgeConstants.EDGE_HUB_SERVER, self.certs_dir)
        cert_util.export_pfx_cert(EdgeConstants.EDGE_HUB_SERVER, self.certs_dir)

        prefixes = [EdgeConstants.EDGE_AGENT_CA, EdgeConstants.EDGE_DEVICE_CA]
        cert_util.chain_simulator_ca_certs(EdgeConstants.EDGE_CHAIN_CA, prefixes, self.certs_dir)

    # Generate IoT Edge device CA to be configured in IoT Edge runtime
    def generate_device_ca(self, valid_days, overwrite_existing, trusted_ca, trusted_ca_key, trusted_ca_key_passphase):
        # Function level variables
        create_root_ca = not (trusted_ca and trusted_ca_key)
        # Generate certs
        cert_util = EdgeCertUtil()
        if create_root_ca:
            cert_util.create_root_ca_cert(EdgeConstants.ROOT_CA_ID,
                                          validity_days_from_now=valid_days,
                                          subject_dict=EdgeConstants.CERT_DEFAULT_DICT,
                                          passphrase=None)
            cert_util.export_device_ca_cert_artifacts_to_dir(EdgeConstants.ROOT_CA_ID, self.certs_dir)
        else:
            cert_util.load_cert_from_file(EdgeConstants.ROOT_CA_ID, trusted_ca, trusted_ca_key, trusted_ca_key_passphase)

        cert_util.create_intermediate_ca_cert(EdgeConstants.DEVICE_CA_ID, EdgeConstants.ROOT_CA_ID,
                                              validity_days_from_now=valid_days,
                                              common_name='Edge Device CA',
                                              set_terminal_ca=False,
                                              passphrase=None)
        cert_util.export_device_ca_cert_artifacts_to_dir(EdgeConstants.DEVICE_CA_ID, self.certs_dir)
        cert_util.chain_device_ca_certs(EdgeConstants.DEVICE_CA_ID,
                                        [EdgeConstants.DEVICE_CA_ID, EdgeConstants.ROOT_CA_ID],
                                        self.certs_dir)

    def get_cert_file_path(self, id_str):
        return EdgeCertUtil.get_cert_file_path(id_str, self.certs_dir)

    def get_pfx_file_path(self, id_str):
        return EdgeCertUtil.get_pfx_file_path(id_str, self.certs_dir)
