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
* [#5](https://github.com/Azure/iotedgehubdev/issues/5) Python 3.7 is not supported yet because Python Docker SDK does not support Python 3.7
