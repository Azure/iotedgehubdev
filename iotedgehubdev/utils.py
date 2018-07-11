import os
import shutil
import stat
import errno
import socket
import sys
import subprocess
from base64 import b64encode, b64decode
from hashlib import sha256
from hmac import HMAC
from time import time
from .output import Output
from .errors import EdgeFileAccessError
if sys.version_info.major >= 3:
    from urllib.parse import quote_plus, urlencode
else:
    from urllib import quote_plus, urlencode

output = Output()


class Utils(object):
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
    def create_file(file_path, data, file_type_diagnostic):
        try:
            fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
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
        except KeyboardInterrupt as ki:
            return
        except Exception as e:
            output.error("Error while executing command: {0}. {1}".format(' '.join(params), str(e)))
