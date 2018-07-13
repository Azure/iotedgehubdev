from iotedgehubdev.constants import EdgeConstants as EC
from iotedgehubdev.utils import Utils

empty_string = ""
valid_connectionstring = "HostName=testhub.azure-devices.net;DeviceId=testdevice;SharedAccessKey=othergibberish="
invalid_connectionstring = "HostName=testhub.azure-devices.net;SharedAccessKey=othergibberish="


def test_empty_connectionstring():
    connection_str_dict = Utils.parse_connection_str(empty_string)
    assert not connection_str_dict


def test_valid_connectionstring():
    connection_str_dict = Utils.parse_connection_str(valid_connectionstring)
    assert connection_str_dict[EC.HOSTNAME_KEY] == "testhub.azure-devices.net"
    assert connection_str_dict[EC.DEVICE_ID_KEY] == "testdevice"
    assert connection_str_dict[EC.ACCESS_KEY_KEY] == "othergibberish="


def test_invalid_connectionstring():
    connection_str_dict = Utils.parse_connection_str(invalid_connectionstring)
    assert connection_str_dict[EC.HOSTNAME_KEY] == "testhub.azure-devices.net"
    assert EC.DEVICE_ID_KEY not in connection_str_dict
    assert connection_str_dict[EC.ACCESS_KEY_KEY] == "othergibberish="
