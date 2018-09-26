# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import shutil
import unittest
from iotedgehubdev.edgecert import EdgeCert

WORKINGDIRECTORY = os.getcwd()


class TestEdgeCertAPICreateSelfSignedCerts(unittest.TestCase):

    def tearDown(self):
        shutil.rmtree(os.path.join(WORKINGDIRECTORY, 'edge-agent-ca'))
        shutil.rmtree(os.path.join(WORKINGDIRECTORY, 'edge-chain-ca'))
        shutil.rmtree(os.path.join(WORKINGDIRECTORY, 'edge-device-ca'))
        shutil.rmtree(os.path.join(WORKINGDIRECTORY, 'edge-hub-server'))

    def test_get_self_signed_certs(self):
        edge_cert = EdgeCert(WORKINGDIRECTORY, 'testhostname')
        edge_cert.generate_self_signed_certs()
        assert edge_cert.get_cert_file_path('edge-agent-ca')
        assert edge_cert.get_cert_file_path('edge-chain-ca')
        assert edge_cert.get_cert_file_path('edge-device-ca')
        assert edge_cert.get_cert_file_path('edge-hub-server')
        assert edge_cert.get_pfx_file_path('edge-hub-server')
