# Azure IoT EdgeHub Dev Tool [![Build Status](https://travis-ci.com/Azure/iotedgehubdev.svg?token=KySEv4A21JkyzbCKjpFW&branch=master)](https://travis-ci.com/Azure/iotedgehubdev)
The Azure IoT EdgeHub Dev Tool provide a local development experience with a simulator for creating, developing, testing, running, and debugging Azure IoT Edge modules and solutions.
- The Edge solution could be run with the simulator locally without pushing image and creating deployment
- It helps to debug the module on the host (not in container) with the EdgeHub

## Installing
1. Install [Docker CE](https://www.docker.com/community-edition) on Windows, macOS or Linux.
2. Install [Python (2.7/3.6) and Pip](https://www.python.org/)
3. Install iotedgehubdev by running below command in your terminal
    ```
    pip install --upgrade iotedgehubdev
    ```

## Quickstart
1. Setup
    ```
    iotedgehubdev setup -c <edge-device-connection-string>
    ```

2. Start/stop an IoT Edge solution in simulator
    ```
    iotedgehubdev start -d <path/to/deployment manifest>
    iotedgehubdev stop
    ```

3. Start and debug a single module natively
    1. Start the module with specific input(s)
        ```
        iotedgehubdev start -i <module-inputs>
        ```

        For example: `iotedgehubdev start -i "input1,input2"`
    
    2. Output the module credential environment variables

        ```
        iotedgehubdev modulecred
        ```

    3. Start the module natively with the environment variables got from previous step
    4. Send message to the module through RESTful API. 

        For example:
        `curl --header "Content-Type: application/json" --request POST --data '{"inputName": "input1","data": "hello world"}' http://localhost:53000/api/v1/messages`
 
## Other resources
- [Azure IoT Edge for Visual Studio Code](https://github.com/microsoft/vscode-azure-iot-edge)
- [Azure IoT Edge Dev CLI Tool](https://github.com/azure/iotedgedev)

## Data/Telemetry
This project collects usage data and sends it to Microsoft to help improve our products and services. Read our [privacy statement](http://go.microsoft.com/fwlink/?LinkId=521839) to learn more. 
If you don’t wish to send usage data to Microsoft, you can change your telemetry settings by updating `collect_telemetry` to `no` in the ini file.