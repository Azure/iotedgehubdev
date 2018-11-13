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
from iotedgehubdev import configs
from iotedgehubdev.edgedockerclient import EdgeDockerClient
from iotedgehubdev.hostplatform import HostPlatform

workingdirectory = os.getcwd()
filename = os.path.join(workingdirectory, '.env')
if os.path.exists(filename):
    load_dotenv(filename)
docker_client = EdgeDockerClient()

VALID_DEVICECONNECTIONSTRING = os.environ['DEVICE_CONNECTION_STRING']
VALID_IOTHUBCONNECTIONSTRING = os.environ['IOTHUB_CONNECTION_STRING']


@pytest.fixture
def runner():
    return CliRunner()


def start_process(command, is_shell):
    process = subprocess.Popen(command, shell=is_shell,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode == 0:
        print('Process Output Message:\n' + str(output))
    else:
        print('Process Error Message:\n' + str(error))
    return str(output)


def cli_setup(runner):
    result = runner.invoke(cli.setup, ['-c', VALID_DEVICECONNECTIONSTRING, '-g', 'iotedgetestingnow'])
    assert 'Setup IoT Edge Simulator successfully' in result.output.strip()


def cli_start_with_deployment(runner, deployment_file):
    test_resources_dir = os.path.join('tests', 'test_compose_resources')
    deployment_json_file_path = os.path.join(test_resources_dir, deployment_file)
    result = runner.invoke(cli.start, ['-d', deployment_json_file_path])
    assert 'IoT Edge Simulator has been started in solution mode' in result.output.strip()


def get_device_id_from_device_connection_string():
    device_id = re.findall(".*DeviceId=(.*);SharedAccessKey.*", VALID_DEVICECONNECTIONSTRING)[0]
    return device_id


def get_iothub_name_from_device_connection_string():
    iothub_name = re.findall(".*HostName=(.*);DeviceId.*", VALID_DEVICECONNECTIONSTRING)[0].split('.')[0]
    return iothub_name


def invoke_module_method():
    device_id = get_device_id_from_device_connection_string()
    iothub_name = get_iothub_name_from_device_connection_string()
    invoke_module_method_cmd = 'az iot hub invoke-module-method --device-id "' + device_id + \
        '" --method-name "reset" --module-id "tempSensor" --hub-name "' + \
        iothub_name + '" --login "' + VALID_IOTHUBCONNECTIONSTRING + '"'
    output = start_process(invoke_module_method_cmd, True)
    if '"status": 200' not in output:
        raise "Failed to invoke module method."


def monitor_d2c_message():
    device_id = get_device_id_from_device_connection_string()
    iothub_name = get_iothub_name_from_device_connection_string()
    invoke_monitor_events_cmd = 'az iot hub monitor-events -n "' + iothub_name + \
        '" -d "' + device_id + '" --login "' + VALID_IOTHUBCONNECTIONSTRING + '" -y -t 5'
    output = start_process(invoke_monitor_events_cmd, True)
    return output


def cli_stop(runner):
    result = runner.invoke(cli.stop)
    assert not result.exception
    assert result.exit_code == 0
    assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()


def reset_docker_environment():
    start_process(['docker', 'network', 'rm', 'azure-iot-edge-dev'], False)
    start_process(['docker', 'rmi', '-f', 'mcr.microsoft.com/azureiotedge-simulated-temperature-sensor:1.0'], False)
    start_process(['docker', 'rmi', '-f', 'mcr.microsoft.com/azureiotedge-hub:1.0'], False)
    start_process(['docker', 'rmi', '-f', 'hello-world'], False)


def verify_docker_output(docker_cmd, expect_values):
    result = start_process(docker_cmd, False)
    print('Process result is: \n %s \n' % (result))
    for expect_value in expect_values:
        if expect_value in result:
            print('%s is in process result.\n' % (expect_value))
        else:
            print('%s is not in process result.\n' % (expect_value))
            return False
    return True


def wait_verify_docker_output(docker_cmd, expect_values):
    times = 0
    while (not verify_docker_output(docker_cmd, expect_values)):
        print("Waiting until docker command is ready... ...\n")
        time.sleep(10)
        times += 1
        if times > 360:
            raise "timeout to wait until it appears expected value " + expect_values + "... ...\n"


def remove_docker_volume(volume_name):
    start_process(['docker', 'volume', 'rm', volume_name, '-f'], False)


def update_setting_ini_as_firsttime():
    config = configs._prod_config.config
    config.set('DEFAULT', 'firsttime', 'yes')
    configs._prod_config.update_config()


def test_cli(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert not result.exception
    assert 'Usage: main' in result.output.strip()


@pytest.mark.skipif(docker_client.get_os_type().lower() == 'windows', reason='It does not support windows container')
def test_cli_start_with_deployment(runner):
    try:
        cli_setup(runner)
        cli_start_with_deployment(runner, 'deployment_without_custom_module.json')
        wait_verify_docker_output(['docker', 'logs', 'edgeHubDev'], ['Opened link'])
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Sending message'])
        invoke_module_method()
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Received direct method'])
        output = monitor_d2c_message()
        device_id = get_device_id_from_device_connection_string()
        assert 'origin: ' + device_id in str(output)
        assert '{"machine":{"temperature":' in str(output)
    finally:
        cli_stop(runner)
        reset_docker_environment()


def test_cli_setup_during_first_time(runner):
    iniFile = HostPlatform.get_setting_ini_path()
    jsonFile = HostPlatform.get_config_file_path()
    update_setting_ini_as_firsttime()
    if os.path.exists(iniFile):
        os.remove(iniFile)
    if os.path.exists(jsonFile):
        os.remove(jsonFile)
    cli_setup(runner)
    assert os.path.exists(iniFile)
    assert os.path.exists(jsonFile)


def test_cli_modulecred(runner):
    iothub_name = get_iothub_name_from_device_connection_string()
    cli_setup(runner)
    result = runner.invoke(cli.modulecred)
    assert not result.exception
    assert result.exit_code == 0
    assert 'EdgeHubConnectionString=HostName=' + iothub_name in result.output.strip()
    assert 'EdgeModuleCACertificateFile' in result.output.strip()
    assert 'edge-device-ca.cert.pem' in result.output.strip()


def test_cli_output_modulecred_file(runner):
    try:
        iothub_name = get_iothub_name_from_device_connection_string()
        cli_setup(runner)
        modulered_output_file = 'modulecred_output.txt'
        result = runner.invoke(cli.modulecred, ['-o', modulered_output_file])
        output_file_path = os.path.join(workingdirectory, modulered_output_file)
        assert not result.exception
        assert result.exit_code == 0
        assert os.path.exists(output_file_path)
        with open(output_file_path) as f:
            content = f.readlines()
            assert 'EdgeHubConnectionString=HostName=' + iothub_name in str(content)
            assert 'EdgeModuleCACertificateFile' in str(content)
            assert 'edge-device-ca.cert.pem' in result.output.strip()
    finally:
        if os.path.exists(output_file_path):
            os.remove(output_file_path)


@pytest.mark.skipif(docker_client.get_os_type().lower() == 'windows', reason='It does not support windows container')
def test_cli_create_options_for_custom_volume(runner):
    try:
        cli_setup(runner)
        remove_docker_volume('testVolume')
        cli_start_with_deployment(runner, 'deployment_with_custom_volume.json')
        wait_verify_docker_output(['docker', 'volume', 'ls'], ['testVolume'])
        expected_volumes = (['"Source": "testVolume"',
                             '"Destination": "/mnt_test"',
                             '"Source": "edgemoduledev"',
                             '"Destination": "/mnt/edgemodule"'])
        wait_verify_docker_output(['docker', 'inspect', 'tempSensor'], expected_volumes)
    finally:
        cli_stop(runner)
        reset_docker_environment()
        remove_docker_volume('testVolume')


def test_cli_modulecred_for_multiple_modules(runner):
    cli_setup(runner)
    result = runner.invoke(cli.modulecred, ['-m', 'tempSensor|edgeHubDev'])
    assert '|HostName=' in result.output.strip()
    assert 'ModuleId=tempSensor' in result.output.strip()
    assert 'ModuleId=edgeHubDev' in result.output.strip()


@pytest.mark.skipif(docker_client.get_os_type().lower() == 'windows', reason='It does not support windows container')
def test_cli_start_with_chunked_create_options(runner):
    try:
        cli_setup(runner)
        cli_start_with_deployment(runner, 'deployment_with_create_options.json')
        wait_verify_docker_output(['docker', 'logs', 'edgeHubDev'], ['Opened link'])
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Sending message'])
        expect_createoptions = ['FOO1=bar1', 'FOO2=bar2', 'FOO3=bar3', 'FOO4=bar4', 'FOO5=bar5', 'FOO6=bar6', 'FOO7=bar7']
        wait_verify_docker_output(['docker', 'inspect', 'tempSensor'], expect_createoptions)
    finally:
        cli_stop(runner)
        reset_docker_environment()


def test_cli_start_with_input(runner):
    try:
        result = runner.invoke(cli.start, ['-i', 'input1'])
        assert not result.exception
        assert result.exit_code == 0
        assert 'IoT Edge Simulator has been started in single module mode' in result.output.strip()
        assert 'curl --header' in result.output.strip()
    finally:
        cli_stop(runner)
        reset_docker_environment()


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
