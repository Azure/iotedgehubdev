# Changelog

[![PyPI version](https://badge.fury.io/py/iotedgehubdev.svg)](https://badge.fury.io/py/iotedgehubdev)

## 0.14.10 - 2021-10-20
* Update Python Docker package version to latest

## 0.14.9 - 2021-08-05
* Use 1.2 as default for edgeRuntime in single module mode.

## 0.14.8 - 2021-04-22
* Drop PY 2 suport.
* Update status from Beta to Production.

## 0.14.7 - 2021-04-02
### Changed
* Use 1.1 as default for edgeRuntime in single module mode.

## 0.14.6 - 2021-03-26
### Changed
* Rename edgeHub version command line parameter to '--edge-runtime-version/-er'
* Limit support for edge runtime 1.0x and 1.1x

## 0.14.5 - 2021-03-19
### Changed
* Dependency upgrades to address vulnerability issues
* Add vulnerability scanner Bandit
* Revert default edgeHub to v1.0

## 0.14.4 - 2021-03-16
### Changed
* Default to v1.1 of EdgeHub image

## 0.14.2 - 2020-09-29
### Added
* Support for running on specific version of EdgeHub image

## 0.14.1 - 2020-05-29
### Fixed
* Fix false alarm issue of Windows Defender

## 0.14.0 - 2020-05-25
### Added
* Support new route schema

## 0.13.0 - 2019-12-13
### Added
* Add command to generate cert

## 0.12.0 - 2019-12-05
### Changed
* Support Python 3.8
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
