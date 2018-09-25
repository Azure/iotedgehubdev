# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import unittest
from iotedgehubdev.edgecert import EdgeCert

WORKINGDIRECTORY = os.getcwd()


class TestEdgeCertAPICreateSelfSignedCerts(unittest.TestCase):

    def test_get_self_signed_certs(self):
        edge_cert = EdgeCert(WORKINGDIRECTORY, 'testhostname')
        edge_cert.generate_self_signed_certs()
        assert edge_cert.get_cert_file_path('edge-agent-ca')
        assert edge_cert.get_cert_file_path('edge-chain-ca')
        assert edge_cert.get_cert_file_path('edge-device-ca')
        assert edge_cert.get_cert_file_path('edge-hub-server')
        assert edge_cert.get_pfx_file_path('edge-hub-server')
