# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import os
from OpenSSL import crypto
from shutil import copy2
from datetime import datetime
from .errors import EdgeValueError, EdgeFileAccessError
from .constants import EdgeConstants as EC
from .utils import Utils


class EdgeCertUtil(object):

    TYPE_RSA = 0
    MIN_VALIDITY_DAYS = 1
    MAX_VALIDITY_DAYS = 1095  # 3 years
    MIN_PASSPHRASE_LENGTH = 4
    MAX_PASSPHRASE_LENGTH = 1023
    CA_KEY_LEN = 4096
    CA_INT_KEY_LEN = 4096
    SERVER_KEY_LEN = 2048
    MIN_COMMON_NAME_LEN = 1
    MAX_COMMON_NAME_LEN = 64
    DIGEST = 'sha256'
    _type_dict = {TYPE_RSA: crypto.TYPE_RSA}
    _subject_validation_dict = {
        EC.SUBJECT_COUNTRY_KEY: {'MIN': 2, 'MAX': 2},
        EC.SUBJECT_STATE_KEY: {'MIN': 0, 'MAX': 128},
        EC.SUBJECT_LOCALITY_KEY: {'MIN': 0, 'MAX': 128},
        EC.SUBJECT_ORGANIZATION_KEY: {'MIN': 0, 'MAX': 64},
        EC.SUBJECT_ORGANIZATION_UNIT_KEY: {'MIN': 0, 'MAX': 64},
        EC.SUBJECT_COMMON_NAME_KEY: {'MIN': MIN_COMMON_NAME_LEN,
                                     'MAX': MAX_COMMON_NAME_LEN}
    }

    def __init__(self, serial_num=1000):
        self._cert_chain = {}
        self._serial_number = serial_num

    def create_root_ca_cert(self, id_str, **kwargs):
        if id_str in list(self._cert_chain.keys()):
            msg = 'Duplicate root CA certificate ID: {0}'.format(id_str)
            raise EdgeValueError(msg)

        validity_days_from_now = self._get_kwargs_validity(**kwargs)
        subj_dict = None
        if 'subject_dict' in kwargs:
            subj_dict = kwargs['subject_dict']
            if self.is_valid_certificate_subject(subj_dict) is False:
                msg = 'Certificate subject dictionary is invalid.'
                raise EdgeValueError(msg)
        else:
            msg = 'Certificate subject dictionary is required'
            raise EdgeValueError(msg)
        passphrase = self._get_kwargs_passphrase(**kwargs)

        key_obj = self._create_key_pair(EdgeCertUtil.TYPE_RSA,
                                        EdgeCertUtil.CA_KEY_LEN)
        csr_obj = self._create_csr(key_obj,
                                   C=subj_dict[EC.SUBJECT_COUNTRY_KEY],
                                   ST=subj_dict[EC.SUBJECT_STATE_KEY],
                                   L=subj_dict[EC.SUBJECT_LOCALITY_KEY],
                                   O=subj_dict[EC.SUBJECT_ORGANIZATION_KEY],
                                   OU=subj_dict[EC.SUBJECT_ORGANIZATION_KEY],
                                   CN=subj_dict[EC.SUBJECT_COMMON_NAME_KEY])

        validity_secs_from_now = validity_days_from_now * 24 * 60 * 60
        cert_obj = self._create_ca_cert(csr_obj,
                                        csr_obj,
                                        key_obj,
                                        (0, validity_secs_from_now),
                                        False)
        self._serial_number += 1
        cert_dict = {}
        cert_dict['key_pair'] = key_obj
        cert_dict['csr'] = csr_obj
        cert_dict['cert'] = cert_obj
        cert_dict['issuer_id'] = id_str
        cert_dict['passphrase'] = passphrase
        self._cert_chain[id_str] = cert_dict

    def create_intermediate_ca_cert(self, id_str, issuer_id_str, **kwargs):
        if id_str in list(self._cert_chain.keys()):
            msg = 'Duplicate intermediate CA certificate ID: {0}'.format(id_str)
            raise EdgeValueError(msg)

        if issuer_id_str not in list(self._cert_chain.keys()):
            msg = 'Invalid issuer certificate ID: {0}'.format(issuer_id_str)
            raise EdgeValueError(msg)

        validity_days_from_now = self._get_kwargs_validity(**kwargs)
        passphrase = self._get_kwargs_passphrase(**kwargs)

        min_length = self._subject_validation_dict[EC.SUBJECT_COMMON_NAME_KEY]['MIN']
        max_length = self._subject_validation_dict[EC.SUBJECT_COMMON_NAME_KEY]['MAX']
        common_name = self._get_kwargs_string('common_name', min_length, max_length, **kwargs)
        if common_name is None:
            msg = 'Invalid common name: {0}'.format(common_name)
            raise EdgeValueError(msg)

        set_terminal_ca = True
        if 'set_terminal_ca' in kwargs:
            set_terminal_ca = kwargs['set_terminal_ca']

        try:
            issuer_cert_dict = self._cert_chain[issuer_id_str]
            issuer_cert = issuer_cert_dict['cert']

            not_after_ts = issuer_cert.get_notAfter()
            valid_days = self._get_maximum_validity_days(not_after_ts,
                                                         validity_days_from_now)

            issuer_key = issuer_cert_dict['key_pair']
            key_obj = self._create_key_pair(EdgeCertUtil.TYPE_RSA, EdgeCertUtil.CA_KEY_LEN)
            csr_obj = self._create_csr(key_obj,
                                       C=issuer_cert.get_subject().countryName,
                                       ST=issuer_cert.get_subject().stateOrProvinceName,
                                       L=issuer_cert.get_subject().localityName,
                                       O=issuer_cert.get_subject().organizationName,
                                       OU=issuer_cert.get_subject().organizationalUnitName,
                                       CN=common_name)

            validity_secs_from_now = valid_days * 24 * 60 * 60
            cert_obj = self._create_ca_cert(csr_obj,
                                            issuer_cert,
                                            issuer_key,
                                            (0, validity_secs_from_now),
                                            set_terminal_ca)
            self._serial_number += 1
            cert_dict = {}
            cert_dict['key_pair'] = key_obj
            cert_dict['csr'] = csr_obj
            cert_dict['cert'] = cert_obj
            cert_dict['issuer_id'] = issuer_id_str
            cert_dict['passphrase'] = passphrase
            self._cert_chain[id_str] = cert_dict
        except EdgeValueError:
            msg = 'Could not create intermediate certificate for {0}'.format(id_str)
            raise EdgeValueError(msg)

    def create_server_cert(self, id_str, issuer_id_str, **kwargs):
        if id_str in list(self._cert_chain.keys()):
            msg = 'Duplicate intermediate CA certificate ID: {0}'.format(id_str)
            raise EdgeValueError(msg)

        if issuer_id_str not in list(self._cert_chain.keys()):
            msg = 'Invalid issuer certificate ID: {0}'.format(issuer_id_str)
            raise EdgeValueError(msg)

        validity_days_from_now = self._get_kwargs_validity(**kwargs)

        passphrase = self._get_kwargs_passphrase(**kwargs)

        max_length = self._subject_validation_dict[EC.SUBJECT_COMMON_NAME_KEY]['MAX']
        hostname = kwargs.get('hostname', None)
        if hostname is None:
            msg = 'Invalid hostname: {0}'.format(hostname)
            raise EdgeValueError(msg)
        # CN length is limited to 64. Since the certificate is used internally so just cut to 64.
        common_name = hostname if len(hostname) <= max_length else hostname[:max_length]

        try:
            issuer_cert_dict = self._cert_chain[issuer_id_str]
            issuer_cert = issuer_cert_dict['cert']
            issuer_key = issuer_cert_dict['key_pair']
            key_obj = self._create_key_pair(EdgeCertUtil.TYPE_RSA, EdgeCertUtil.SERVER_KEY_LEN)
            csr_obj = self._create_csr(key_obj,
                                       C=issuer_cert.get_subject().countryName,
                                       ST=issuer_cert.get_subject().stateOrProvinceName,
                                       L=issuer_cert.get_subject().localityName,
                                       O=issuer_cert.get_subject().organizationName,
                                       OU=issuer_cert.get_subject().organizationalUnitName,
                                       CN=common_name)
            not_after_ts = issuer_cert.get_notAfter()
            valid_days = self._get_maximum_validity_days(not_after_ts,
                                                         validity_days_from_now)
            validity_secs_from_now = valid_days * 24 * 60 * 60
            cert_obj = self._create_server_cert(csr_obj,
                                                issuer_cert,
                                                issuer_key,
                                                (0, validity_secs_from_now),
                                                hostname)
            self._serial_number += 1
            cert_dict = {}
            cert_dict['key_pair'] = key_obj
            cert_dict['csr'] = csr_obj
            cert_dict['cert'] = cert_obj
            cert_dict['issuer_id'] = issuer_id_str
            cert_dict['passphrase'] = passphrase
            self._cert_chain[id_str] = cert_dict
        except EdgeValueError:
            msg = 'Could not create server certificate for {0}'.format(id_str)
            raise EdgeValueError(msg)

    def export_pfx_cert(self, id_str, dir_path):
        if id_str not in self._cert_chain:
            msg = 'Invalid cert ID: {0}'.format(id_str)
            raise EdgeValueError(msg)

        try:
            cert_dict = self._cert_chain[id_str]
            cert_obj = cert_dict['cert']
            key_obj = cert_dict['key_pair']
            pfx = crypto.PKCS12()
            pfx.set_privatekey(key_obj)
            pfx.set_certificate(cert_obj)
            pfx_data = pfx.export('')
            prefix = id_str
            path = os.path.realpath(dir_path)
            path = os.path.join(path, prefix)
            cert_dir = os.path.join(path, 'cert')
            pfx_output_file_name = os.path.join(cert_dir, prefix + EC.PFX_SUFFIX)
            with open(pfx_output_file_name, 'wb') as pfx_file:
                pfx_file.write(pfx_data)
        except IOError as ex:
            msg = 'IO Error when exporting PFX cert ID: {0}.' \
                  ' Errno: {1} Error: {2}'.format(id_str, str(ex.errno), ex.strerror)
            raise EdgeFileAccessError(msg, pfx_output_file_name)

    @staticmethod
    def get_cert_file_path(id_str, dir_path):
        return os.path.join(dir_path, id_str, 'cert', id_str + EC.CERT_SUFFIX)

    @staticmethod
    def get_pfx_file_path(id_str, dir_path):
        return os.path.join(dir_path, id_str, 'cert', id_str + EC.PFX_SUFFIX)

    def export_cert_artifacts_to_dir(self, id_str, dir_path):
        if Utils.check_if_directory_exists(dir_path) is False:
            msg = 'Invalid export directory {0}'.format(dir_path)
            raise EdgeValueError(msg)

        if id_str not in list(self._cert_chain.keys()):
            msg = 'Certificate not in chain. ID: {0}'.format(id_str)
            raise EdgeValueError(msg)

        cert_dict = self._cert_chain[id_str]
        prefix = id_str
        try:
            path = os.path.realpath(dir_path)
            path = os.path.join(path, prefix)
            Utils.delete_dir(path)
            Utils.mkdir_if_needed(path)
            priv_dir = os.path.join(path, 'private')
            Utils.mkdir_if_needed(priv_dir)
            os.chmod(priv_dir, 0o700)
            cert_dir = os.path.join(path, 'cert')
            Utils.mkdir_if_needed(cert_dir)

            # export the private key
            priv_key_file_name = prefix + '.key.pem'
            priv_key_file = os.path.join(priv_dir, priv_key_file_name)
            if 'key_file' in cert_dict:
                key_file_path = cert_dict['key_file']
                copy2(key_file_path, priv_key_file)
            else:
                key_obj = cert_dict['key_pair']
                key_passphrase = cert_dict['passphrase']
                passphrase = None
                if key_passphrase and key_passphrase != '':
                    passphrase = key_passphrase.encode('utf-8')
                with open(priv_key_file, 'w') as ip_file:
                    cipher = None
                    if passphrase:
                        cipher = 'aes256'
                    ip_file.write(crypto.dump_privatekey(crypto.FILETYPE_PEM,
                                                         key_obj,
                                                         cipher=cipher,
                                                         passphrase=passphrase).decode('utf-8'))

            # export the cert
            cert_obj = cert_dict['cert']
            cert_file_name = prefix + EC.CERT_SUFFIX
            cert_file = os.path.join(cert_dir, cert_file_name)
            current_cert_file_path = cert_file
            with open(cert_file, 'w') as ip_file:
                ip_file.write(crypto.dump_certificate(crypto.FILETYPE_PEM,
                                                      cert_obj).decode('utf-8'))

            # export any chain certs
            if 'ca_chain' in list(cert_dict.keys()):
                src_chain_cert_file = cert_dict['ca_chain']
                cert_file_name = prefix + '-chain.cert.pem'
                cert_file = os.path.join(cert_dir, cert_file_name)
                copy2(src_chain_cert_file, cert_file)

            # check if this is the root cert in the chain, i.e. issuer is itself
            if cert_dict['issuer_id'] == id_str:
                cert_file_name = prefix + '-root.cert.pem'
                cert_file = os.path.join(cert_dir, cert_file_name)
                if 'ca_root' in list(cert_dict.keys()):
                    src_root_cert_file = cert_dict['ca_root']
                else:
                    src_root_cert_file = current_cert_file_path
                copy2(src_root_cert_file, cert_file)
        except IOError as ex:
            msg = 'IO Error when exporting certs for ID: {0}.\n' \
                  ' Error seen when copying/exporting file {1}.' \
                  ' Errno: {2} Error: {3}'.format(id_str, ex.filename, str(ex.errno), ex.strerror)
            raise EdgeFileAccessError(msg, path)

    def chain_ca_certs(self, output_prefix, prefixes, certs_dir):
        file_names = []
        for prefix in prefixes:
            if prefix not in list(self._cert_chain.keys()):
                msg = 'Invalid cert ID: {0}'.format(prefix)
                raise EdgeValueError(msg)
            else:
                cert_dict = self._cert_chain[prefix]
                if 'ca_chain' in list(cert_dict.keys()):
                    # this cert contains an existing certificate chain
                    # pick the chain instead of the actual cert
                    cert_file_name = prefix + '-chain.cert.pem'
                else:
                    cert_file_name = prefix + EC.CERT_SUFFIX
                cert_file = os.path.join(certs_dir, prefix, 'cert', cert_file_name)
                path = os.path.realpath(cert_file)
                file_names.append(path)
        try:
            output_dir = os.path.join(certs_dir, output_prefix)
            Utils.delete_dir(output_dir)
            Utils.mkdir_if_needed(output_dir)
            output_dir = os.path.join(output_dir, 'cert')
            Utils.mkdir_if_needed(output_dir)
            output_file_name = os.path.join(output_dir, output_prefix + EC.CERT_SUFFIX)
            with open(output_file_name, 'wb') as op_file:
                for file_name in file_names:
                    with open(file_name, 'rb') as ip_file:
                        op_file.write(ip_file.read())
        except IOError as ex:
            msg = 'IO Error when creating chain cert: {0}.' \
                  ' Errno: {1} Error: {2}'.format(output_file_name, str(ex.errno), ex.strerror)
            raise EdgeFileAccessError(msg, output_file_name)

    def is_valid_certificate_subject(self, subject_dict):
        result = True
        for key in list(EdgeCertUtil._subject_validation_dict.keys()):
            try:
                field = subject_dict[key]
                if field is not None:
                    length_field = len(field)
                    min_len = EdgeCertUtil._subject_validation_dict[key]['MIN']
                    max_len = EdgeCertUtil._subject_validation_dict[key]['MAX']
                    if length_field < min_len or length_field > max_len:
                        result = False
                else:
                    result = False
            except KeyError:
                result = False

            if result is False:
                break
        return result

    def _create_csr(self, key_pair, **kwargs):
        csr = crypto.X509Req()
        subj = csr.get_subject()
        for key, value in list(kwargs.items()):
            if value:
                setattr(subj, key, value)
        csr.set_pubkey(key_pair)
        csr.sign(key_pair, EdgeCertUtil.DIGEST)
        return csr

    def _create_cert_common(self,
                            csr,
                            issuer_cert,
                            validity_period):
        not_before, not_after = validity_period
        cert = crypto.X509()
        cert.set_serial_number(self._serial_number)
        cert.gmtime_adj_notBefore(not_before)
        cert.gmtime_adj_notAfter(not_after)
        cert.set_issuer(issuer_cert.get_subject())
        cert.set_subject(csr.get_subject())
        cert.set_pubkey(csr.get_pubkey())
        cert.set_version(2)
        return cert

    def _create_ca_cert(self,
                        csr,
                        issuer_cert,
                        issuer_key_pair,
                        validity_period,
                        path_len_zero):
        cert = self._create_cert_common(csr, issuer_cert, validity_period)
        val = b'CA:TRUE'
        if path_len_zero:
            val += b', pathlen:0'
        extensions = []
        extensions.append(crypto.X509Extension(b'basicConstraints',
                                               critical=True, value=val))
        cert.add_extensions(extensions)
        cert.sign(issuer_key_pair, EdgeCertUtil.DIGEST)
        return cert

    def _create_server_cert(self,
                            csr,
                            issuer_cert,
                            issuer_key_pair,
                            validity_period,
                            hostname):
        cert = self._create_cert_common(csr,
                                        issuer_cert,
                                        validity_period)

        extensions = []
        extensions.append(crypto.X509Extension(b'basicConstraints',
                                               critical=False,
                                               value=b'CA:FALSE'))
        altDns = ','.join(['DNS:localhost', 'DNS:{0}'.format(hostname)]).encode('utf-8')
        extensions.append(crypto.X509Extension(b'subjectAltName',
                                               critical=False,
                                               value=altDns))
        cert.add_extensions(extensions)
        cert.sign(issuer_key_pair, EdgeCertUtil.DIGEST)
        return cert

    def _create_key_pair(self, private_key_type, key_bit_len):
        key_pair = crypto.PKey()
        key_pair.generate_key(EdgeCertUtil._type_dict[private_key_type], key_bit_len)
        return key_pair

    def _get_maximum_validity_days(self, not_after_ts_asn1, validity_days_from_now):
        result = 0
        try:
            expiration_date = datetime.strptime(not_after_ts_asn1.decode('utf-8'), "%Y%m%d%H%M%SZ")
            expires_in = expiration_date - datetime.now()
            if expires_in.days > 0:
                result = min(expires_in.days, validity_days_from_now)
            return result
        except Exception:
            msg = 'Certificate date format incompatible {0}'.format(not_after_ts_asn1)
            raise EdgeValueError(msg)

    def _get_kwargs_validity(self, **kwargs):
        validity_days_from_now = 365
        min_validity = EdgeCertUtil.MIN_VALIDITY_DAYS
        max_validity = EdgeCertUtil.MAX_VALIDITY_DAYS
        kwarg_key = 'validity_days_from_now'
        if kwarg_key in kwargs:
            validity_days_from_now = kwargs[kwarg_key]

        if validity_days_from_now < min_validity or validity_days_from_now > max_validity:
            msg = 'Certificate validity days needs to be greater than or equal to {0} ' \
                  'and less than {1} days. Value provided: {2}'. format(min_validity,
                                                                        max_validity,
                                                                        validity_days_from_now)
            raise EdgeValueError(msg)

        return validity_days_from_now

    def _validate_string_length(self, test_string, min_length, max_length):
        length = len(test_string)
        if min_length > length or length > max_length:
            return False
        return True

    def _get_kwargs_passphrase(self, **kwargs):
        passphrase = None
        min_length = EdgeCertUtil.MIN_PASSPHRASE_LENGTH
        max_length = EdgeCertUtil.MAX_PASSPHRASE_LENGTH
        kwarg_key = 'passphrase'
        if kwarg_key in kwargs:
            passphrase = kwargs[kwarg_key]
        if passphrase is not None:
            if self._validate_string_length(passphrase, min_length, max_length) is False:
                msg = 'Private key passphrase needs to greater than or equal to {0} and less ' \
                      'than {1} characters.'.format(min_length, max_length)
                raise EdgeValueError(msg)
        return passphrase

    def _get_kwargs_string(self, kwarg_key, min_length, max_length, default_str=None, **kwargs):
        result_str = default_str
        if kwarg_key in kwargs:
            result_str = kwargs[kwarg_key]
        if result_str is not None:
            if self._validate_string_length(result_str, min_length, max_length) is False:
                msg = 'KWarg[{0}]:{1} string length needs to greater than or equal to {2} and ' \
                      'less than {3} characters.'.format(kwarg_key, result_str,
                                                         min_length, max_length)
                raise EdgeValueError(msg)
        return result_str
