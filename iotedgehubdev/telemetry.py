import os
import uuid
import datetime
import platform
import subprocess
import sys
import json

from collections import defaultdict
from six.moves import configparser
from functools import wraps
from . import decorators
from .hostplatform import HostPlatform
from . import telemetry_upload as telemetry_core
from . import configs

PRODUCT_NAME = 'iotedgehubdev'

class TelemetrySession(object):
    def __init__(self, correlation_id=None):
        self.start_time = None
        self.end_time = None
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.command = 'command_name'
        self.parameters = []
        self.result = 'None'
        self.result_summary = None
        self.exception = None
        self.extra_props = {}
        self.machineId = self._get_hash_mac_address()
        self.events = defaultdict(list)

    def generate_payload(self):
        props = {
            'EventId': str(uuid.uuid4()),
            'CorrelationId': self.correlation_id,
            'MachineId': self.machineId,
            'ProductName': PRODUCT_NAME,
            'ProductVersion': _get_core_version(),
            'CommandName': self.command,
            'OS.Type': platform.system().lower(),
            'OS.Version': platform.version().lower(),
            'Result': self.result,
            'StartTime': self.start_time,
            'EndTime': self.end_time
        }

        if self.result_summary:
            props['ResultSummary'] = self.result_summary

        if self.exception:
            props['Exception'] = self.exception

        self.events[_get_AI_key()].append({
            'name': '{}/command'.format(PRODUCT_NAME),
            'properties': props
        })

        payload = json.dumps(self.events)
        return _remove_symbols(payload)
    
    @decorators.suppress_all_exceptions()
    @decorators.hash256_result
    def _get_hash_mac_address(self):
        s = ''
        for index, c in enumerate(hex(uuid.getnode())[2:].upper()):
            s += c
            if index % 2:
                s += '-'

        s = s.strip('-')
        return s


_session = TelemetrySession()

def _user_agrees_to_telemetry(func):
    @wraps(func)
    def _wrapper(*args, **kwargs):
        if not configs.get_ini_config().getboolean('core', 'collect_telemetry', fallback=True):
            return None
        return func(*args, **kwargs)

    return _wrapper

@decorators.suppress_all_exceptions()
def start(cmdname):
    _session.command = cmdname
    _session.start_time = datetime.datetime.utcnow()

@decorators.suppress_all_exceptions()
def success():
    _session.result = 'Success'

@decorators.suppress_all_exceptions()
def fail(exception, summary):
    _session.exception = exception
    _session.result = 'Fail'
    _session.result_summary = summary

@_user_agrees_to_telemetry
@decorators.suppress_all_exceptions()
def flush():
    # flush out current information
    _session.end_time = datetime.datetime.utcnow()

    payload = _session.generate_payload()
    if payload:
        _upload_telemetry_with_user_agreement(payload)

    # reset session fields, retaining correlation id and application
    _session.__init__(correlation_id=_session.correlation_id)


@decorators.suppress_all_exceptions(fallback_return=None)
def _get_core_version():
    from iotedgehubdev import __version__ as core_version
    return core_version

@decorators.suppress_all_exceptions()
def _get_AI_key():
    from iotedgehubdev import __AIkey__ as key
    return key

# This includes a final user-agreement-check; ALL methods sending telemetry MUST call this.
@_user_agrees_to_telemetry
@decorators.suppress_all_exceptions()
def _upload_telemetry_with_user_agreement(payload, **kwargs):
    subprocess.Popen([sys.executable, os.path.realpath(telemetry_core.__file__), payload], **kwargs)

def _remove_symbols(s):
    if isinstance(s, str):
        for c in '$%^&|':
            s = s.replace(c, '_')
    return s