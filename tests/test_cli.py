# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import pytest
import platform
import re
import subprocess
import shutil
import time
from click.testing import CliRunner
from iotedgehubdev import cli
from iotedgehubdev import configs
from iotedgehubdev.edgedockerclient import EdgeDockerClient
from iotedgehubdev.hostplatform import HostPlatform

workingdirectory = os.getcwd()
docker_client = EdgeDockerClient()

tests_dir = os.path.join(workingdirectory, "tests")
test_config_dir = os.path.join(tests_dir, "assets", "config")
test_resources_dir = os.path.join(tests_dir, 'test_compose_resources')

VALID_IOTHUBCONNECTIONSTRING = os.environ['IOTHUB_CONNECTION_STRING']
VALID_DEVICECONNECTIONSTRING = os.environ[platform.system().upper() + '_DEVICE_CONNECTION_STRING']
VALID_CONTAINERREGISTRYSERVER = os.environ['CONTAINER_REGISTRY_SERVER']
VALID_CONTAINERREGISTRYUSERNAME = os.environ['CONTAINER_REGISTRY_USERNAME']
VALID_CONTAINERREGISTRYPASSWORD = os.environ['CONTAINER_REGISTRY_PASSWORD']


device_id = re.findall(".*DeviceId=(.*);SharedAccessKey.*", VALID_DEVICECONNECTIONSTRING)[0]
iothub_name = re.findall(".*HostName=(.*);DeviceId.*", VALID_DEVICECONNECTIONSTRING)[0].split('.')[0]


@pytest.fixture
def runner():
    return CliRunner()


def get_docker_os_type():
    return docker_client.get_os_type().lower()


def docker_login(username, password, server):
    start_process(['docker', 'login', '-u', username, '-p', password, server], False)


def docker_logout(server_name):
    start_process(['docker', 'logout', server_name], False)


def docker_pull_image(image_name):
    start_process(['docker', 'pull', image_name], False)


def docker_tag_image(original_tag_name, new_tag_name):
    start_process(['docker', 'tag', original_tag_name, new_tag_name], False)


def docker_push_image(image_name):
    start_process(['docker', 'push', image_name], False)


def get_platform_type():
    if get_docker_os_type() == 'windows':
        platform_type = 'windows-amd64'
    else:
        platform_type = 'amd64'
    return platform_type


def update_setting_ini_as_firsttime():
    config = configs._prod_config.config
    config.set('DEFAULT', 'firsttime', 'yes')
    configs._prod_config.update_config()


def clean_config_files():
    iniFile = HostPlatform.get_setting_ini_path()
    jsonFile = HostPlatform.get_config_file_path()
    update_setting_ini_as_firsttime()
    if os.path.exists(iniFile):
        os.remove(iniFile)
    if os.path.exists(jsonFile):
        os.remove(jsonFile)


def cli_setup(runner):
    result = runner.invoke(cli.setup, ['-c', VALID_DEVICECONNECTIONSTRING, '-g', 'iotedgetestingnow'])
    if 'Setup IoT Edge Simulator successfully' not in result.output.strip():
        raise Exception(result.stdout)


def cli_setup_with_hub(runner):
    device_connstr = 'HostName=testhub.azure-devices.net;DeviceId=mylaptop2;SharedAccessKey=XXXXX'
    hub_connstr = 'HostName=testhub.azure-devices.net;SharedAccessKeyName=iothubowner;SharedAccessKey=XXXXX'
    result = runner.invoke(cli.setup, ['-c', device_connstr, '-i', hub_connstr])
    if 'Setup IoT Edge Simulator successfully' not in result.output.strip():
        raise Exception(result.stdout)


def start_process(command, is_shell):
    process = subprocess.Popen(command, shell=is_shell,
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    output, error = process.communicate()
    if process.returncode == 0:
        return str(output)
    else:
        command = command.replace(VALID_IOTHUBCONNECTIONSTRING, '******')
        raise Exception(error)


def cli_start_with_deployment(runner, deployment_json_file_path):
    result = runner.invoke(cli.start, ['-d', deployment_json_file_path])
    if 'IoT Edge Simulator has been started in solution mode' not in result.output.strip():
        raise Exception(result.stdout)


def invoke_module_method():
    invoke_module_method_cmd = 'az iot hub invoke-module-method --device-id "' + device_id + \
        '" --method-name "reset" --module-id "tempSensor" --hub-name "' + \
        iothub_name + '" --login "' + VALID_IOTHUBCONNECTIONSTRING + '"'
    output = start_process(invoke_module_method_cmd, True)
    if '"status": 200' not in str(output):
        raise Exception('Failed to invoke module method.')


def monitor_d2c_message():
    invoke_monitor_events_cmd = 'az iot hub monitor-events -n "' + iothub_name + \
        '" -d "' + device_id + '" --login "' + VALID_IOTHUBCONNECTIONSTRING + '" -y -t 5'
    output = start_process(invoke_monitor_events_cmd, True)
    return output


def cli_stop(runner):
    result = runner.invoke(cli.stop)
    if result.exit_code == 0:
        return result
    else:
        raise Exception(result.stdout)


def verify_docker_output(docker_cmd, expect_values, use_shell):
    result = start_process(docker_cmd, use_shell)
    print('Process result is: \n %s \n' % (result))
    for expect_value in expect_values:
        if expect_value in result:
            print('%s is in process result.\n' % (expect_value))
        else:
            print('%s is not in process result.\n' % (expect_value))
            return False
    return True


def wait_verify_docker_output(docker_cmd, expect_values, use_shell=False):
    times = 0
    while (not verify_docker_output(docker_cmd, expect_values, use_shell)):
        print("Waiting until docker command is ready... ...\n")
        time.sleep(10)
        times += 1
        if times > 360:
            raise Exception('Timeout to wait until it appears expected value ' + str(expect_values))


def get_all_docker_volumes():
    output = start_process(['docker', 'volume', 'ls'], False)
    return output


def remove_docker_volumes(volumes):
    all_volumes = get_all_docker_volumes()
    for volume in volumes:
        if volume in all_volumes:
            start_process(['docker', 'volume', 'rm', volume, '-f'], False)


def get_all_docker_images():
    output = start_process(['docker', 'image', 'ls'], False)
    return output


def remove_docker_images(images):
    all_images = get_all_docker_images()
    for image in images:
        image_without_tag = image.split(':')[0]
        if image_without_tag in all_images:
            start_process(['docker', 'rmi', '-f', image], False)


def get_all_docker_networks():
    output = start_process(['docker', 'network', 'ls'], False)
    return output


def remove_docker_networks(networks):
    all_networks = get_all_docker_networks()
    for network in networks:
        if network in all_networks:
            start_process(['docker', 'network', 'rm', network], False)


def update_file_content(file_path, actual_value, expected_value):
    with open(file_path, "r+") as f:
        stream_data = f.read()
        ret = re.sub(actual_value, expected_value, stream_data)
        f.seek(0)
        f.truncate()
        f.write(ret)


def test_cli(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert not result.exception
    assert 'Usage: main' in result.output.strip()


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='It does not support windows container')
def test_cli_start_with_deployment(runner):
    try:
        cli_setup(runner)
        deployment_json_file_path = os.path.join(test_resources_dir, 'deployment_without_custom_module.json')
        cli_start_with_deployment(runner, deployment_json_file_path)
        wait_verify_docker_output(['docker', 'logs', 'edgeHubDev'], ['Opened link'])
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Sending message'])
        invoke_module_method()
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Received direct method'])
        output = monitor_d2c_message()
        assert 'device: ' + device_id in str(output)
        # TODO improve this test case due to unstable
        # assert 'machine' in str(output)
        # assert 'temperature' in str(output)
    finally:
        result = cli_stop(runner)
        assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()
        remove_docker_networks(['azure-iot-edge-dev'])
        remove_docker_images(['mcr.microsoft.com/azureiotedge-simulated-temperature-sensor:1.0',
                              'mcr.microsoft.com/azureiotedge-hub:1.0',
                              'hello-world'])


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='Windows container is not yet supported')
def test_pre_setup(runner):
    json_file = HostPlatform.get_config_file_path()
    if os.path.exists(json_file):
        os.remove(json_file)

    instruction = ('ERROR: Cannot find config file. Please run `iotedgehubdev setup -c "<edge-device-connection-string>"` first.'
                   if platform.system().lower() == 'windows'
                   else 'ERROR: Cannot find config file. '
                   'Please run `sudo iotedgehubdev setup -c "<edge-device-connection-string>"` first.')

    result = runner.invoke(cli.start, ['-i', 'input1'])
    assert result.exception
    assert result.exit_code != 0
    assert instruction in result.output.strip()

    result = runner.invoke(cli.start, ['-d', 'dummy_deployment.json'])
    assert result.exception
    assert result.exit_code != 0
    assert instruction in result.output.strip()

    result = runner.invoke(cli.modulecred)
    assert result.exception
    assert result.exit_code != 0
    assert instruction in result.output.strip()


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='Windows container is not yet supported')
def test_corrupt_edge_hub_config(runner):
    json_file = HostPlatform.get_config_file_path()

    base_dir = os.path.dirname(json_file)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    if os.path.exists(json_file):
        os.remove(json_file)

    # Create an empty edgehub.json file
    open(json_file, 'a').close()

    instruction = ('ERROR: Invalid config file. Please run `iotedgehubdev setup -c "<edge-device-connection-string>"` again.'
                   if platform.system().lower() == 'windows'
                   else 'ERROR: Invalid config file. '
                   'Please run `sudo iotedgehubdev setup -c "<edge-device-connection-string>"` again.')

    result = runner.invoke(cli.start, ['-i', 'input1'])
    assert result.exception
    assert result.exit_code != 0
    assert instruction in result.output.strip()

    result = runner.invoke(cli.start, ['-d', 'dummy_deployment.json'])
    assert result.exception
    assert result.exit_code != 0
    assert instruction in result.output.strip()

    result = runner.invoke(cli.modulecred)
    assert result.exception
    assert result.exit_code != 0
    assert instruction in result.output.strip()


def test_cli_setup_during_first_time(runner):
    clean_config_files()
    cli_setup(runner)
    ini_file = HostPlatform.get_setting_ini_path()
    json_file = HostPlatform.get_config_file_path()
    assert os.path.exists(ini_file)
    assert os.path.exists(json_file)


def test_cli_setup_with_hub_during_first_time(runner):
    clean_config_files()
    cli_setup_with_hub(runner)
    iniFile = HostPlatform.get_setting_ini_path()
    jsonFile = HostPlatform.get_config_file_path()
    assert os.path.exists(iniFile)
    assert os.path.exists(jsonFile)


def test_cli_modulecred(runner):
    cli_setup(runner)
    result = runner.invoke(cli.modulecred)
    assert not result.exception
    assert result.exit_code == 0
    assert 'EdgeHubConnectionString=HostName=' + iothub_name in result.output.strip()
    assert 'EdgeModuleCACertificateFile' in result.output.strip()
    assert 'edge-device-ca.cert.pem' in result.output.strip()


def test_cli_output_modulecred_file(runner):
    try:
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


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='It does not support windows container')
def test_cli_create_options_for_custom_volume(runner):
    try:
        deployment_json_file_path = os.path.join(test_resources_dir, 'deployment_with_custom_volume.json')
        temp_config_folder = os.path.join(tests_dir, 'config_tmp')
        os.makedirs(temp_config_folder)

        config_file_path = os.path.join(temp_config_folder, 'deployment_with_custom_volume.json')
        shutil.copy(deployment_json_file_path, config_file_path)

        if get_docker_os_type() == "windows":
            update_file_content(config_file_path, '/mnt_test', 'C:/mnt_test')

        cli_setup(runner)
        remove_docker_volumes(['testVolume', 'testvolume'])
        cli_start_with_deployment(runner, config_file_path)

        if get_docker_os_type() == 'linux':
            expected_volumes = (['testVolume', 'edgemoduledev', 'edgehubdev'])
            expected_tempsensor_volumes = (['"Source": "testVolume"',
                                            '"Target": "/mnt_test"',
                                            '"Source": "edgemoduledev"',
                                            '"Target": "/mnt/edgemodule"'])
            expected_edgehubdev_volumes = (['"Source": "edgehubdev"', '"Target": "/mnt/edgehub"'])
        elif get_docker_os_type() == 'windows':
            expected_volumes = (['testvolume', 'edgemoduledev', 'edgehubdev'])
            expected_tempsensor_volumes = (['"Source": "testVolume"',
                                            '"Target": "C:/mnt_test"',
                                            '"Source": "edgemoduledev"',
                                            '"Target": "c:/mnt/edgemodule"'])
            expected_edgehubdev_volumes = (['"Source": "edgehubdev"',
                                            '"Target": "c:/mnt/edgehub"'])

        wait_verify_docker_output(['docker', 'volume', 'ls'], expected_volumes)
        wait_verify_docker_output(['docker', 'inspect', 'tempSensor'], expected_tempsensor_volumes)
        wait_verify_docker_output(['docker', 'inspect', 'edgeHubDev'], expected_edgehubdev_volumes)
    finally:
        shutil.rmtree(temp_config_folder, ignore_errors=True)
        result = cli_stop(runner)
        assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()
        remove_docker_networks(['azure-iot-edge-dev'])
        remove_docker_images(['mcr.microsoft.com/azureiotedge-simulated-temperature-sensor:1.0',
                              'mcr.microsoft.com/azureiotedge-hub:1.0',
                              'hello-world'])
        remove_docker_volumes(['testVolume', 'testvolume'])


def test_cli_modulecred_for_multiple_modules(runner):
    cli_setup(runner)
    result = runner.invoke(cli.modulecred, ['-m', 'tempSensor|edgeHubDev'])
    assert '|HostName=' in result.output.strip()
    assert 'ModuleId=tempSensor' in result.output.strip()
    assert 'ModuleId=edgeHubDev' in result.output.strip()


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='It does not support windows container')
def test_cli_start_with_chunked_create_options(runner):
    try:
        cli_setup(runner)
        deployment_json_file_path = os.path.join(test_resources_dir, 'deployment_with_create_options.json')
        cli_start_with_deployment(runner, deployment_json_file_path)
        wait_verify_docker_output(['docker', 'logs', 'edgeHubDev'], ['Opened link'])
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Sending message'])
        expect_createoptions = ['FOO1=bar1', 'FOO2=bar2', 'FOO3=bar3',
                                'FOO4=bar4', 'FOO5=bar5', 'FOO6=bar6', 'FOO7=bar7']
        wait_verify_docker_output(['docker', 'inspect', 'tempSensor'], expect_createoptions)
    finally:
        result = cli_stop(runner)
        assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()
        remove_docker_networks(['azure-iot-edge-dev'])
        remove_docker_images(['mcr.microsoft.com/azureiotedge-simulated-temperature-sensor:1.0',
                              'mcr.microsoft.com/azureiotedge-hub:1.0',
                              'hello-world'])


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='The base image of edgeHubDev image is 1809 but agent is 1803.'
                    'So it does not support windows container.')
def test_cli_start_with_input(runner):
    try:
        result = runner.invoke(cli.start, ['-i', 'input1'])
        output = result.output.strip()
        if result.exit_code == 0:
            assert 'IoT Edge Simulator has been started in single module mode' in output
            assert 'curl --header' in output
        else:
            raise Exception(result.stdout)
    finally:
        result = cli_stop(runner)
        assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()
        remove_docker_networks(['azure-iot-edge-dev'])
        remove_docker_images(['mcr.microsoft.com/azureiotedge-hub:1.0',
                              'mcr.microsoft.com/azureiotedge-testing-utility:1.0.0-rc1'])


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='The base image of edgeHubDev image is 1809 but agent is 1803.'
                    'So it does not support windows container.')
def test_cli_start_with_create_options_for_bind(runner):
    try:
        deployment_json_file_path = os.path.join(test_resources_dir, 'deployment_with_create_options_for_bind.json')
        temp_config_folder = os.path.join(tests_dir, 'tmp_config')
        os.makedirs(temp_config_folder)

        config_file_path = os.path.join(temp_config_folder, 'deployment_with_create_options_for_bind.json')
        shutil.copy(deployment_json_file_path, config_file_path)

        if get_docker_os_type() == "windows":
            update_file_content(config_file_path, '/usr:/home/moduleuser/test',
                                r'C:\\\\\\\\Users:C:/moduleuser/test')

        cli_setup(runner)
        cli_start_with_deployment(runner, config_file_path)

        wait_verify_docker_output(['docker', 'logs', 'edgeHubDev'], ['Opened link'])
        wait_verify_docker_output(['docker', 'logs', 'tempSensor'], ['Sending message'])
        if get_docker_os_type() == "windows":
            wait_verify_docker_output('echo dir | docker exec -i -w c:/moduleuser/test/ tempSensor cmd', ['Public'], True)
        else:
            wait_verify_docker_output(['docker', 'exec', 'tempSensor', 'ls', '/home/moduleuser/test'], ["share"])
    finally:
        shutil.rmtree(temp_config_folder, ignore_errors=True)
        result = cli_stop(runner)
        assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()
        remove_docker_networks(['azure-iot-edge-dev'])
        remove_docker_images(['mcr.microsoft.com/azureiotedge-simulated-temperature-sensor:1.0',
                              'mcr.microsoft.com/azureiotedge-hub:1.0',
                              'hello-world'])


@pytest.mark.skipif(get_docker_os_type() == 'windows', reason='The base image of edgeHubDev image is 1809 but agent is 1803.'
                    'So it does not support windows container.')
def test_cli_start_with_registry(runner):
    temp_config_folder = os.path.join(tests_dir, 'deployment_config')
    os.makedirs(temp_config_folder)
    try:
        old_tag = '1.0.0-rc1'
        new_tag = '1.0.0-rc1.test'
        image_name = 'azureiotedge-testing-utility'
        old_image_name = image_name + ':' + old_tag
        new_image_name = image_name + ':' + new_tag
        old_tag_name = ('{0}/{1}').format('mcr.microsoft.com', old_image_name)
        new_tag_name = ('{0}/{1}').format(VALID_CONTAINERREGISTRYSERVER, new_image_name)

        docker_pull_image(old_tag_name)
        docker_tag_image(old_tag_name, new_tag_name)
        docker_login(VALID_CONTAINERREGISTRYUSERNAME, VALID_CONTAINERREGISTRYPASSWORD, VALID_CONTAINERREGISTRYSERVER)
        docker_push_image(new_tag_name)

        config_file_path = os.path.join(temp_config_folder, 'deployment.json')
        deployment_file_path = os.path.join(test_config_dir, "deployment.json")
        shutil.copy(deployment_file_path, config_file_path)

        module_image_name = ('"image": "{0}/{1}"').format(VALID_CONTAINERREGISTRYSERVER, new_image_name)
        update_file_content(config_file_path, '"image": ""', module_image_name)

        update_file_content(config_file_path, '"username": ""',
                            '"username": "' + VALID_CONTAINERREGISTRYUSERNAME + '"')
        update_file_content(config_file_path, '"password": ""',
                            '"password": "' + VALID_CONTAINERREGISTRYPASSWORD + '"')
        update_file_content(config_file_path, '"address": ""',
                            '"address": "' + VALID_CONTAINERREGISTRYSERVER + '"')

        remove_docker_images([old_tag_name, new_tag_name])
        docker_logout(VALID_CONTAINERREGISTRYSERVER)

        cli_start_with_deployment(runner, config_file_path)
        wait_verify_docker_output(['docker', 'ps'], ['azureiotedge-testing-utility', new_tag])
    finally:
        shutil.rmtree(temp_config_folder, ignore_errors=True)

        result = cli_stop(runner)
        assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()

        remove_docker_networks(['azure-iot-edge-dev'])
        remove_docker_images([new_tag_name,
                              old_tag_name,
                              'mcr.microsoft.com/azureiotedge-hub:1.0',
                              'hello-world'])


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
