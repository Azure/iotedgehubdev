# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import errno
import os
import shutil
import socket
import stat
import subprocess
from base64 import b64decode, b64encode
from hashlib import sha256
from hmac import HMAC
from time import time

from six.moves.urllib.parse import quote_plus, urlencode

from .constants import EdgeConstants as EC
from .decorators import suppress_all_exceptions
from .errors import EdgeFileAccessError


class Utils(object):
    @staticmethod
    def parse_connection_strs(device_conn_str, hub_conn_str=None):
        data = Utils._parse_device_connection_str(device_conn_str)
        data[EC.DEVICE_ACCESS_KEY_KEY] = data.pop(EC.ACCESS_KEY_KEY)
        if hub_conn_str is not None:
            hub_data = Utils._parse_hub_connection_str(hub_conn_str, data[EC.HOSTNAME_KEY])
            data[EC.HUB_ACCESS_KEY_KEY] = hub_data[EC.ACCESS_KEY_KEY]
            data[EC.ACCESS_KEY_NAME] = hub_data[EC.ACCESS_KEY_NAME]
        return data

    @staticmethod
    def _parse_device_connection_str(connection_string):
        data = Utils._split_connection_string(connection_string)
        if len(data) > 0:
            if EC.HOSTNAME_KEY not in data or EC.DEVICE_ID_KEY not in data or EC.ACCESS_KEY_KEY not in data:
                if EC.ACCESS_KEY_NAME in data:
                    raise KeyError('Please make sure you are using a device connection string '
                                   'instead of an IoT Hub connection string')
                else:
                    raise KeyError('Error parsing connection string. '
                                   'Please make sure you wrap the connection string with double quotes when supplying it via CLI')
            return data
        else:
            raise KeyError('Error parsing connection string')

    @staticmethod
    def _parse_hub_connection_str(hub_connection_string, host_name):
        hub_data = Utils._split_connection_string(hub_connection_string)
        if len(hub_data) > 0:
            if EC.HOSTNAME_KEY not in hub_data or EC.ACCESS_KEY_NAME not in hub_data or EC.ACCESS_KEY_KEY not in hub_data:
                if EC.DEVICE_ID_KEY in hub_data:
                    raise KeyError('Please make sure you are using a IoT Hub connection string '
                                   'instead of an device connection string')
                else:
                    raise KeyError('Error parsing connection string. '
                                   'Please make sure you wrap the connection string with double quotes when supplying it via CLI')
            elif hub_data[EC.HOSTNAME_KEY] != host_name:
                raise KeyError('Please make sure the device belongs to the IoT Hub')
            return hub_data
        else:
            raise KeyError('Error parsing IoT Hub connection string')

    @staticmethod
    def _split_connection_string(connection_string):
        data = dict()
        if connection_string is not None:
            parts = connection_string.split(';')
            for part in parts:
                if "=" in part:
                    subparts = [s.strip() for s in part.split("=", 1)]
                    data[subparts[0]] = subparts[1]
        return data

    @staticmethod
    def get_hostname():
        try:
            return socket.getfqdn()
        except IOError as ex:
            raise ex

    @staticmethod
    def check_if_file_exists(file_path):
        if file_path is None \
           or os.path.exists(file_path) is False \
           or os.path.isfile(file_path) is False:
            return False
        return True

    @staticmethod
    def check_if_directory_exists(dir_path):
        if dir_path is None \
           or os.path.exists(dir_path) is False \
           or os.path.isdir(dir_path) is False:
            return False
        return True

    @staticmethod
    def delete_dir(dir_path):
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path, onerror=Utils._remove_readonly_callback)
        except OSError as ex:
            raise ex

    @staticmethod
    def mkdir_if_needed(dir_path):
        try:
            os.makedirs(dir_path)
        except OSError as ex:
            if ex.errno != errno.EEXIST:
                raise ex

    @staticmethod
    def delete_file(file_path, file_type_diagnostic):
        try:
            if os.path.exists(file_path):
                os.unlink(file_path)
        except OSError as ex:
            msg = 'Error deleteing {0}: {1}. ' \
                  'Errno: {2}, Error: {3}'.format(file_type_diagnostic,
                                                  file_path, str(ex.errno), ex.strerror)
            raise EdgeFileAccessError(msg, file_path)

    @staticmethod
    def create_file(file_path, data, file_type_diagnostic, mode=0o644):
        try:
            fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, mode)
            with os.fdopen(fd, 'w') as output_file:
                output_file.write(data)
        except OSError as ex:
            msg = 'Error creating {0}: {1}. ' \
                  'Errno: {2}, Error: {3}'.format(file_type_diagnostic,
                                                  file_path, str(ex.errno), ex.strerror)
            raise EdgeFileAccessError(msg, file_path)

    @staticmethod
    def get_iot_hub_sas_token(uri, key, policy_name, expiry=3600):
        ttl = time() + expiry
        sign_key = "%s\n%d" % ((quote_plus(uri)), int(ttl))
        signature = b64encode(
            HMAC(b64decode(key), sign_key.encode("utf-8"), sha256).digest())

        rawtoken = {
            "sr": uri,
            "sig": signature,
            "se": str(int(ttl))
        }

        if policy_name is not None:
            rawtoken["skn"] = policy_name

        return "SharedAccessSignature " + urlencode(rawtoken)

    @staticmethod
    def copy_files(src_path, dst_path):
        try:
            shutil.copy2(src_path, dst_path)
        except OSError as ex:
            raise ex

    @staticmethod
    def _remove_readonly_callback(func, path, excinfo):
        del func, excinfo
        os.chmod(path, stat.S_IWRITE)
        os.unlink(path)

    @staticmethod
    def exe_proc(params, shell=False, cwd=None, suppress_out=False):
        try:
            subprocess.check_call(params, shell=shell, cwd=cwd)
        except KeyboardInterrupt:
            raise
        except Exception as e:
            raise Exception("Error while executing command: {0}. {1}".format(' '.join(params), str(e)))

    @staticmethod
    @suppress_all_exceptions()
    def hash_connection_str_hostname(hostname):
        """Hash connection string hostname to count distint IoT Hub number"""
        if not hostname:
            return ("", "")

        # get hostname suffix (e.g., azure-devices.net) to distinguish national clouds
        if "." in hostname:
            hostname_suffix = hostname[hostname.index(".") + 1:]
        else:
            hostname_suffix = ""

        return (Utils.get_sha256_hash(hostname), hostname_suffix)

    @staticmethod
    def get_sha256_hash(val):
        hash_object = sha256(val.encode('utf-8'))

        return str(hash_object.hexdigest()).lower()
