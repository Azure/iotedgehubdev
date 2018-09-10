# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


import os

from six.moves import configparser
from . import decorators
from .hostplatform import HostPlatform

PRIVACY_STATEMENT = """
Welcome to iotedgehubdev!
-------------------------
Telemetry
---------
The iotedgehubdev collects usage data in order to improve your experience.
The data is anonymous and does not include commandline argument values.
The data is collected by Microsoft.

You can change your telemetry settings by updating 'collect_telemetry' to 'no' in {0}
"""


class ProductConfig(object):
    def __init__(self):
        self.config = configparser.ConfigParser({
            'firsttime': 'yes'
        })
        self.setup_config()

    @decorators.suppress_all_exceptions()
    def setup_config(self):
        try:
            configPath = HostPlatform.get_config_path()
            iniFilePath = HostPlatform.get_setting_ini_path()
            if not os.path.exists(configPath):
                os.makedirs(configPath)
            if not os.path.exists(iniFilePath):
                with open(iniFilePath, 'w') as iniFile:
                    self.config.write(iniFile)
            else:
                with open(iniFilePath, 'r') as iniFile:
                    self.config.readfp(iniFile)
                with open(iniFilePath, 'w') as iniFile:
                    self.config.write(iniFile)
        except Exception:
            pass

    @decorators.suppress_all_exceptions()
    def update_config(self):
        with open(HostPlatform.get_setting_ini_path(), 'w') as iniFile:
            self.config.write(iniFile)

    @decorators.suppress_all_exceptions()
    def set_val(self, direct, section, val):
        if val is not None:
            self.config.set(direct, section, val)
            self.update_config()


_prod_config = ProductConfig()


@decorators.suppress_all_exceptions()
def get_ini_config():
    return _prod_config.config


@decorators.suppress_all_exceptions()
def update_ini():
    _prod_config.update_config()


@decorators.suppress_all_exceptions()
def check_firsttime():
    if 'no' != _prod_config.config.get('DEFAULT', 'firsttime'):
        config = _prod_config.config
        config.set('DEFAULT', 'firsttime', 'no')
        print(PRIVACY_STATEMENT.format(HostPlatform.get_setting_ini_path()))
        config.set('DEFAULT', 'collect_telemetry', 'yes')
        _prod_config.update_config()
