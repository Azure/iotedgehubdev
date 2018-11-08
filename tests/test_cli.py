# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import pytest
import re
import subprocess
import time
from click.testing import CliRunner
from dotenv import load_dotenv
from iotedgehubdev import cli

filename = os.path.join(os.getcwd(), '.env')
if os.path.exists(filename):
    load_dotenv(filename)
VALID_DEVICECONNECTIONSTRING = ('HostName=iothubautotest01.azure-devices.net;'
                                'DeviceId=iotdeviceautotest01;'
                                'SharedAccessKey=ROKkS5m0yX/woTmcCGKhRG36RDyZfot5rLzEGLVmTb8=')


@pytest.fixture
def runner():
    return CliRunner()


def _cli_setup(runner):
    result = runner.invoke(cli.setup, ['-c', VALID_DEVICECONNECTIONSTRING, '-g', 'iotedgetestingnow'])
    assert 'Setup IoT Edge Simulator successfully' in result.output.strip()


def _cli_start_with_deployment(runner):
    test_resources_dir = os.path.join('tests', 'test_compose_resources')
    deployment_json_file_path = os.path.join(test_resources_dir, "deployment_without_custom_module.json")
    result = runner.invoke(cli.start, ['-d', deployment_json_file_path])
    time.sleep(20)
    assert 'IoT Edge Simulator has been started in solution mode' in result.output.strip()


def _invoke_module_method():
    iot_hub_name = re.findall(".*HostName=(.*);DeviceId.*", VALID_DEVICECONNECTIONSTRING)[0].split('.')[0]
    device_id = re.findall(".*DeviceId=(.*);Shared.*", VALID_DEVICECONNECTIONSTRING)[0]
    invoke_module_method_cmd = 'powershell.exe az iot hub invoke-module-method --device-id ' + \
        device_id + ' --method-name "reset" --module-id "tempSensor" --hub-name ' + iot_hub_name
    process = subprocess.Popen(invoke_module_method_cmd, stdout=subprocess.PIPE)
    process.wait()


def _cli_stop(runner):
    result = runner.invoke(cli.stop)
    assert not result.exception
    assert result.exit_code == 0
    assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()


def _reset_docker_environment():
    process = subprocess.Popen("docker system prune -a -f", stdout=subprocess.PIPE)
    process.wait()


def _verify_container_logs(container_name, expect_value):
    process = subprocess.Popen(['docker', 'logs', container_name], stdout=subprocess.PIPE)
    output = process.communicate()[0]
    assert expect_value in str(output)


def test_cli(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert not result.exception
    assert 'Usage: main' in result.output.strip()


def test_cli_deploy_successfully(runner):
    _cli_setup(runner)
    _cli_start_with_deployment(runner)
    _verify_container_logs('edgeHubDev', 'Opened link')
    _invoke_module_method()
    _verify_container_logs('tempSensor', 'Sending message')
    _verify_container_logs('tempSensor', 'Received direct method call to reset temperature sensor')
    _cli_stop(runner)
    _reset_docker_environment()


# def test_cli_with_option(runner):
#     result = runner.invoke(cli.main, ['--as-cowboy'])
#     assert not result.exception
#     assert result.exit_code == 0
#     assert result.output.strip() == 'Howdy, world.'


# def test_cli_with_arg(runner):
#     result = runner.invoke(cli.main, ['iotedgehubdev'])
#     assert result.exit_code == 0
#     assert not result.exception
#     assert result.output.strip() == 'Hello, iotedgehubdev.'
