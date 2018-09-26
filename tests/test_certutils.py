# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import unittest
from unittest import mock
from iotedgehubdev.certutils import EdgeCertUtil
from iotedgehubdev.constants import EdgeConstants as EC
from iotedgehubdev.errors import EdgeValueError

VALID_SUBJECT_DICT = {
    EC.SUBJECT_COUNTRY_KEY: 'TC',
    EC.SUBJECT_STATE_KEY: 'Test State',
    EC.SUBJECT_LOCALITY_KEY: 'Test Locality',
    EC.SUBJECT_ORGANIZATION_KEY: 'Test Organization',
    EC.SUBJECT_ORGANIZATION_UNIT_KEY: 'Test Unit',
    EC.SUBJECT_COMMON_NAME_KEY: 'Test CommonName'
}

WORKINGDIRECTORY = os.getcwd()


class TestEdgeCertUtilAPICreateRootCACert(unittest.TestCase):

    def test_create_root_ca_cert_duplicate_ids_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)

    def test_create_root_ca_cert_validity_days_invalid(self):
        cert_util = EdgeCertUtil()
        for validity in [-1, 0, 1096]:
            with self.assertRaises(EdgeValueError):
                cert_util.create_root_ca_cert('root',
                                              subject_dict=VALID_SUBJECT_DICT,
                                              validity_days_from_now=validity)

    def test_create_root_ca_cert_subject_dict_invalid(self):
        cert_util = EdgeCertUtil()
        with mock.patch('iotedgehubdev.certutils.EdgeCertUtil.is_valid_certificate_subject',
                        mock.MagicMock(return_value=False)):
            with self.assertRaises(EdgeValueError):
                cert_util.create_root_ca_cert('root',
                                              subject_dict=VALID_SUBJECT_DICT)

    def test_create_root_ca_cert_without_subject_dict(self):
        cert_util = EdgeCertUtil()
        with mock.patch('iotedgehubdev.certutils.EdgeCertUtil.is_valid_certificate_subject',
                        mock.MagicMock(return_value=False)):
            with self.assertRaises(EdgeValueError):
                cert_util.create_root_ca_cert('root')

    def test_create_root_ca_cert_passphrase_invalid(self):
        cert_util = EdgeCertUtil()
        with self.assertRaises(EdgeValueError):
            cert_util.create_root_ca_cert('root',
                                          subject_dict=VALID_SUBJECT_DICT,
                                          passphrase='')
        with self.assertRaises(EdgeValueError):
            cert_util.create_root_ca_cert('root',
                                          subject_dict=VALID_SUBJECT_DICT,
                                          passphrase='123')
        bad_pass_1024 = 'a' * 1024
        with self.assertRaises(EdgeValueError):
            cert_util.create_root_ca_cert('root',
                                          subject_dict=VALID_SUBJECT_DICT,
                                          passphrase=bad_pass_1024)


class TestEdgeCertUtilAPICreateIntCACert(unittest.TestCase):
    def test_create_intermediate_ca_cert_duplicate_ids_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('root', 'root', common_name='name')

    def test_create_intermediate_ca_cert_validity_days_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        for validity in [-1, 0, 1096]:
            with self.assertRaises(EdgeValueError):
                cert_util.create_intermediate_ca_cert('int', 'root', common_name='name',
                                                      validity_days_from_now=validity)

    def test_create_intermediate_ca_cert_passphrase_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root', common_name='name',
                                                  passphrase='')

        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root', common_name='name',
                                                  passphrase='123')

        bad_pass_1024 = 'a' * 1024
        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root', common_name='name',
                                                  passphrase=bad_pass_1024)

    def test_create_intermediate_ca_cert_common_name_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root')

        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root', common_name=None)

        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root', common_name='')

        bad_common_name = 'a' * 65
        with self.assertRaises(EdgeValueError):
            cert_util.create_intermediate_ca_cert('int', 'root', common_name=bad_common_name)

    def test_create_intermediate_ca_cert_successfully(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)

        valid_common_name = 'testcommonname'
        assert not cert_util.create_intermediate_ca_cert('int', 'root', common_name=valid_common_name)


class TestEdgeCertUtilAPICreateServerCert(unittest.TestCase):
    def test_create_server_cert_duplicate_ids_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('root', 'root', host_name='name')

    def test_create_server_cert_validity_days_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        for validity in [-1, 0, 1096]:
            with self.assertRaises(EdgeValueError):
                cert_util.create_server_cert('server', 'root', host_name='name',
                                             validity_days_from_now=validity)

    def test_create_server_cert_passphrase_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('server', 'root', host_name='name', passphrase='')

        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('server', 'root', host_name='name', passphrase='123')

        bad_pass = 'a' * 1024
        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('server', 'root', host_name='name', passphrase=bad_pass)

    def test_create_server_cert_hostname_invalid(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('int', 'root')

        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('int', 'root', host_name=None)

        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('int', 'root', host_name='')

        bad_hostname = 'a' * 65
        with self.assertRaises(EdgeValueError):
            cert_util.create_server_cert('int', 'root', host_name=bad_hostname)

    def test_create_server_cert_successfully(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)

        valid_hostname = 'testhostname'
        assert not cert_util.create_server_cert('int', 'root', hostname=valid_hostname)


class TestEdgeCertUtilAPIExportCertArtifacts(unittest.TestCase):

    @mock.patch('iotedgehubdev.utils.Utils.check_if_directory_exists')
    def test_export_cert_artifacts_to_dir_incorrect_id_invalid(self, mock_chk_dir):
        cert_util = EdgeCertUtil()
        with self.assertRaises(EdgeValueError):
            mock_chk_dir.return_value = True
            cert_util.export_cert_artifacts_to_dir('root', 'some_dir')

    @mock.patch('iotedgehubdev.utils.Utils.check_if_directory_exists')
    def test_export_cert_artifacts_to_dir_invalid_dir_invalid(self, mock_chk_dir):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            mock_chk_dir.return_value = False
            cert_util.export_cert_artifacts_to_dir('root', 'some_dir')

    def test_get_cert_artifacts_file_path(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.export_cert_artifacts_to_dir('root', WORKINGDIRECTORY)
        assert cert_util.get_cert_file_path('root', WORKINGDIRECTORY)

    def test_get_chain_ca_certs(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.chain_ca_certs('root', {'root'}, WORKINGDIRECTORY)
        assert cert_util.get_cert_file_path('root', WORKINGDIRECTORY)

    def test_get_pfx_cert_file_path(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.export_pfx_cert('root', WORKINGDIRECTORY)
        assert cert_util.get_cert_file_path('root', WORKINGDIRECTORY)
