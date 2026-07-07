# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import unittest
import shutil
import tempfile
from unittest import mock
from cryptography import x509
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.serialization import pkcs12
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

    def tearDown(self):
        test_data_folder = os.path.join(WORKINGDIRECTORY, 'root')
        if os.path.exists(test_data_folder):
            shutil.rmtree(test_data_folder)

    @mock.patch('iotedgehubdev.utils.Utils.check_if_directory_exists')
    def test_export_cert_artifacts_to_dir_incorrect_id_invalid(self, mock_chk_dir):
        cert_util = EdgeCertUtil()
        with self.assertRaises(EdgeValueError):
            mock_chk_dir.return_value = True
            cert_util.export_simulator_cert_artifacts_to_dir('root', 'some_dir')

    @mock.patch('iotedgehubdev.utils.Utils.check_if_directory_exists')
    def test_export_cert_artifacts_to_dir_invalid_dir_invalid(self, mock_chk_dir):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        with self.assertRaises(EdgeValueError):
            mock_chk_dir.return_value = False
            cert_util.export_simulator_cert_artifacts_to_dir('root', 'some_dir')

    def test_get_cert_artifacts_file_path(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.export_simulator_cert_artifacts_to_dir('root', WORKINGDIRECTORY)
        assert cert_util.get_cert_file_path('root', WORKINGDIRECTORY)

    def test_get_chain_ca_certs(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.chain_simulator_ca_certs('root', {'root'}, WORKINGDIRECTORY)
        assert cert_util.get_cert_file_path('root', WORKINGDIRECTORY)

    def test_get_pfx_cert_file_path(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.chain_simulator_ca_certs('root', {'root'}, WORKINGDIRECTORY)
        cert_util.export_pfx_cert('root', WORKINGDIRECTORY)
        assert cert_util.get_cert_file_path('root', WORKINGDIRECTORY)


class TestEdgeCertUtilContentParity(unittest.TestCase):
    """Tier 2 content-parity tests: parse the exported artifacts back and assert on
    their contents (extensions, PEM format, PFX, validity clamping) to guard the
    pyOpenSSL -> cryptography migration against on-disk format regressions."""

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.tmp_dir):
            shutil.rmtree(self.tmp_dir)

    def _key_path(self, id_str):
        return os.path.join(self.tmp_dir, id_str, 'private', id_str + EC.KEY_SUFFIX)

    def _load_cert(self, id_str):
        with open(EdgeCertUtil.get_cert_file_path(id_str, self.tmp_dir), 'rb') as cert_file:
            return x509.load_pem_x509_certificate(cert_file.read())

    def test_dumped_cert_and_key_round_trip(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.export_simulator_cert_artifacts_to_dir('root', self.tmp_dir)

        # Loading the dumped cert + key back must not raise (exercises 'rb' + bytes passphrase path).
        loader = EdgeCertUtil()
        loader.load_cert_from_file('root',
                                   EdgeCertUtil.get_cert_file_path('root', self.tmp_dir),
                                   self._key_path('root'),
                                   None)

    def test_dumped_private_key_is_pkcs1_pem(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.export_simulator_cert_artifacts_to_dir('root', self.tmp_dir)

        with open(self._key_path('root'), 'r') as key_file:
            content = key_file.read()
        # TraditionalOpenSSL/PKCS#1 header, not PKCS#8.
        assert content.startswith('-----BEGIN RSA PRIVATE KEY-----')

    def test_dumped_private_key_with_passphrase_is_encrypted(self):
        passphrase = 'secretpass'
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT, passphrase=passphrase)
        cert_util.export_simulator_cert_artifacts_to_dir('root', self.tmp_dir)

        with open(self._key_path('root'), 'rb') as key_file:
            content = key_file.read()
        assert content.startswith(b'-----BEGIN RSA PRIVATE KEY-----')
        assert b'ENCRYPTED' in content
        # Decrypts with the correct passphrase ...
        serialization.load_pem_private_key(content, password=passphrase.encode('utf-8'))
        # ... and fails with the wrong one.
        with self.assertRaises(ValueError):
            serialization.load_pem_private_key(content, password=b'wrongpass')

    def test_root_ca_cert_extensions(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.export_simulator_cert_artifacts_to_dir('root', self.tmp_dir)

        cert = self._load_cert('root')
        basic_constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints).value
        assert basic_constraints.ca is True

        key_usage = cert.extensions.get_extension_for_class(x509.KeyUsage).value
        assert key_usage.key_cert_sign is True
        assert key_usage.crl_sign is True
        assert key_usage.digital_signature is True

        # Subject and Authority Key Identifier extensions must both be present.
        cert.extensions.get_extension_for_class(x509.SubjectKeyIdentifier)
        cert.extensions.get_extension_for_class(x509.AuthorityKeyIdentifier)

    def test_server_cert_extensions(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.create_server_cert('server', 'root', hostname='myhost')
        cert_util.export_simulator_cert_artifacts_to_dir('server', self.tmp_dir)

        cert = self._load_cert('server')
        basic_constraints = cert.extensions.get_extension_for_class(x509.BasicConstraints).value
        assert basic_constraints.ca is False

        san = cert.extensions.get_extension_for_class(x509.SubjectAlternativeName).value
        dns_names = san.get_values_for_type(x509.DNSName)
        assert 'localhost' in dns_names
        assert 'myhost' in dns_names

    def test_pfx_round_trip(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT)
        cert_util.chain_simulator_ca_certs('root', {'root'}, self.tmp_dir)
        cert_util.export_pfx_cert('root', self.tmp_dir)

        with open(EdgeCertUtil.get_pfx_file_path('root', self.tmp_dir), 'rb') as pfx_file:
            pfx_data = pfx_file.read()
        # Password is None to match NoEncryption() used on export.
        key, cert, _ = pkcs12.load_key_and_certificates(pfx_data, None)
        assert key is not None
        assert cert is not None

    def test_intermediate_validity_clamped_to_issuer(self):
        cert_util = EdgeCertUtil()
        cert_util.create_root_ca_cert('root', subject_dict=VALID_SUBJECT_DICT,
                                      validity_days_from_now=2)
        cert_util.create_intermediate_ca_cert('int', 'root', common_name='intname',
                                              validity_days_from_now=365)
        cert_util.export_simulator_cert_artifacts_to_dir('root', self.tmp_dir)
        cert_util.export_simulator_cert_artifacts_to_dir('int', self.tmp_dir)

        root_cert = self._load_cert('root')
        int_cert = self._load_cert('int')
        # The intermediate requested 365 days but must be clamped to the issuer's expiry.
        assert int_cert.not_valid_after_utc <= root_cert.not_valid_after_utc
