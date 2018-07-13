
# Azure IoT EdgeHub Dev Tool [![Build Status](https://travis-ci.com/Azure/iotedgehubdev.svg?token=KySEv4A21JkyzbCKjpFW&branch=master)](https://travis-ci.com/Azure/iotedgehubdev)
The Azure IoT EdgeHub Dev Tool provides a simulated EdgeHub environment for developing edge moduls and solutions.
- The edge solution could be run with the simulated EdgeHub locally without pushing image and creating deployment
- It helps to debug the module on the host (not in container) with the EdgeHub

## Quickstart
### Prerequisite
#### 1. **Install Docker**
- Note: On windows, please make sure the docker is in **linux mode**.
#### 2. **Install python (2.7/3.6)**
#### 3. **Install iotedgehubdev**

### Run Tool
#### Setup
- iotedgehubdev setup `<edge-device-connection-string>`

#### Run an IoT Edge Solution in Simulator
- iotedgehubdev start -d `<deployment-manifest>`
- iotedgehubdev stop

#### Run/Debug a module locally
- iotedgehubdev start -i `<module-inputs>`. For example:

    iotedgehubdev start -i "input1,input2"
- iotedgehubdev modulecred

  It will output the module credential environment variables.

- Start the module locally with the environment variables got from previous step
- Send message to the module through restful api. For example:

    curl --header "Content-Type: application/json" --request POST --data '{"inputName": "input1","data": "hello world"}' http://localhost:53000/api/v1/messages
 