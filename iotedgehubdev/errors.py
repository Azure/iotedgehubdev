# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class EdgeError(Exception):
    def __init__(self, msg, ex=None):
        if ex:
            msg += ' : {0}'.format(str(ex))
        super(EdgeError, self).__init__(msg)
        self._ex = ex


class EdgeInvalidArgument(EdgeError):
    def __init__(self, msg, ex=None):
        super(EdgeInvalidArgument, self).__init__(msg, ex)


class EdgeValueError(EdgeError):
    def __init__(self, msg, ex=None):
        super(EdgeValueError, self).__init__(msg, ex)


class EdgeFileAccessError(EdgeError):
    def __init__(self, msg, file_name, ex=None):
        msg += ': {0}'.format(file_name)
        super(EdgeFileAccessError, self).__init__(msg, ex)
        self.file_name = file_name


class EdgeFileParseError(EdgeError):
    def __init__(self, msg, file_name, ex=None):
        msg += ': {0}'.format(file_name)
        super(EdgeFileParseError, self).__init__(msg, ex)
        self.file_name = file_name


class EdgeDeploymentError(EdgeError):
    def __init__(self, msg, ex=None):
        super(EdgeDeploymentError, self).__init__(msg, ex)


class ResponseError(Exception):
    def __init__(self, status_code, value):
        self.value = value
        self.status_code = status_code

    def message(self):
        return ('Code:{0}. Detail:{1}').format(self.status_code, self.value)

    def status(self):
        return self.status_code


class RegistriesLoginError(Exception):
    def __init__(self, registries, errmsg):
        self._registries = registries
        self._errmsg = errmsg

    def message(self):
        return ('Fail to login {0}. Detail: {1}').format(self._registries, self._errmsg)

    def registries(self):
        return self._registries
