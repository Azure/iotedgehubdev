# Changelog

[![PyPI version](https://badge.fury.io/py/iotedgehubdev.svg)](https://badge.fury.io/py/iotedgehubdev)
## 0.12.0 - 2019-11-xx
### Changed
* Add python version requirement in README and setup.py (Now we are only support python 2.7/3.5/3.6/3.7)
* Make python version consistent between pip and standalone
* Update cert generation logic

## 0.11.1 - 2019-10-25
### Fixed
* Fix telemetry issue

## 0.11.0 - 2019-10-09
### Added
* Support host network for modules
* Standalone binaries of iotedgehubdev for Windows is available

## 0.10.0 - 2019-08-02
### Added
* Support environment variables for single module ([#193](https://github.com/Azure/iotedgehubdev/issues/193))
* Add validateconfig command to check whether configuration is valid

### Changed
* Use error code 2 for invalid configuration

## 0.9.0 - 2019-06-14
### Changed
* Use range version for dependences to avoid incompatible issue

## 0.8.0 - 2019-04-01
### Added
* Add module twin support

### Changed
* Upgrade docker-py dependency to support connect remote Docker engine with ssh://
* Output errors to stderr

## 0.7.0 - 2019-01-29
### Added
* Allow specifying Docker daemon socket to connect to with the `--host/-H` option
* docker-compose as a pip dependency
* Partially support `on-unhealthy` restart policy by falling back to `always`
* Provide more friendly information when starting without setting up

### Changed
* Update testing utility image version to 1.0.0

## 0.6.0 - 2018-12-05
### Added
* Support parsing `Binds` in `createOptions`
* Log in registries with credentials in deployment manifest

### Changed
* Fix authentication error when hostname is longer than 64

## 0.5.0 - 2018-10-31
### Added
* Support extended `createOptions`

### Changed
* Update REST API version
* Fix "Error getting device scope result from IoTHub, HttpStatusCode: Unauthorized" issue after starting ([#95](https://github.com/Azure/iotedgehubdev/issues/95))

## 0.4.0 - 2018-10-12
### Changed
* Fix "Error: 'environment'" when starting ([#87](https://github.com/Azure/iotedgehubdev/issues/87))

## 0.3.0 - 2018-09-21
### Added
* Support environment variables set in the `env` section of a module
* Support getting credentials of multiple modules

### Changed
* Always pull the EdgeHub image before starting
* Fix "the JSON object must be str, not 'bytes'" when starting on Python 3.5

## 0.2.0 - 2018-08-03
### Added
* Support networks and volumes in `createOptions`
* Support Windows container

### Changed
* Remove requirement of `sudo` for `iotedgehubdev start` and `iotedgehubdev modulecred` command
* Rename EdgeHub runtime to IoT Edge simulator
* Fix a issue which causes duplicate D2C messages

### Known Issues
* [#67](https://github.com/Azure/iotedgehubdev/issues/67) Running Python and C modules which relies on SDK's support is not ready yet 
* [#62](https://github.com/Azure/iotedgehubdev/issues/62) Debugging C# modules may fail with Windows container due to incorrect timestamp
* [#30](https://github.com/Azure/iotedgehubdev/issues/30) Debugging C# modules locally on macOS requires manually adding edge-device-ca.cert.pem to Keychain, and removing the EdgeModuleCACertificateFile environment variable
