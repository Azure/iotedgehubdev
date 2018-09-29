# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import os
import pytest
from click.testing import CliRunner
from iotedgehubdev import cli

VALID_DEVICECONNECTIONSTRING = os.environ['DEVICE_CONNECTION_STRING']


@pytest.fixture
def runner():
    return CliRunner()


def test_cli(runner):
    result = runner.invoke(cli.main)
    assert result.exit_code == 0
    assert not result.exception
    assert 'Usage: main' in result.output.strip()


def test_cli_setup(runner):
    result = runner.invoke(cli.setup, ['-c', VALID_DEVICECONNECTIONSTRING, '-g', 'localhost'])
    assert not result.exception
    assert result.exit_code == 0
    assert 'Setup IoT Edge Simulator successfully' in result.output.strip()


def test_cli_modulecred(runner):
    result = runner.invoke(cli.modulecred)
    assert not result.exception
    assert result.exit_code == 0
    assert 'EdgeHubConnectionString' in result.output.strip()


def test_cli_start(runner):
    result = runner.invoke(cli.start, ['-i', 'input1'])
    assert not result.exception
    assert result.exit_code == 0
    assert 'IoT Edge Simulator has been started in single module mode' in result.output.strip()


def test_cli_stop(runner):
    result = runner.invoke(cli.stop)
    assert not result.exception
    assert result.exit_code == 0
    assert 'IoT Edge Simulator has been stopped successfully' in result.output.strip()

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
