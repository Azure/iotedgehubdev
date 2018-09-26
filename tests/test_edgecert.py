# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import shutil
import unittest
from iotedgehubdev.edgecert import EdgeCert

WORKINGDIRECTORY = os.getcwd()


class TestEdgeCertAPICreateSelfSignedCerts(unittest.TestCase):

    def tearDown(self):
        self._delete_directory(WORKINGDIRECTORY, 'edge-agent-ca')
        self._delete_directory(WORKINGDIRECTORY, 'edge-chain-ca')
        self._delete_directory(WORKINGDIRECTORY, 'edge-device-ca')
        self._delete_directory(WORKINGDIRECTORY, 'edge-hub-server')

    def _delete_directory(self, folder_path, foldername):
        data_path = os.path.join(folder_path, foldername)
        if os.path.exists(data_path):
            shutil.rmtree(data_path)

    def test_get_self_signed_certs(self):
        edge_cert = EdgeCert(WORKINGDIRECTORY, 'testhostname')
        edge_cert.generate_self_signed_certs()
        assert edge_cert.get_cert_file_path('edge-agent-ca')
        assert edge_cert.get_cert_file_path('edge-chain-ca')
        assert edge_cert.get_cert_file_path('edge-device-ca')
        assert edge_cert.get_cert_file_path('edge-hub-server')
        assert edge_cert.get_pfx_file_path('edge-hub-server')
