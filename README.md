# Azure IoT EdgeHub Dev Tool [![Build Status](https://travis-ci.org/Azure/iotedgehubdev.svg?branch=master)](https://travis-ci.org/Azure/iotedgehubdev)
The Azure IoT EdgeHub Dev Tool provides a local development experience with a simulator for creating, developing, testing, running, and debugging Azure IoT Edge modules and solutions.

The simulator allows you to run, test and debug your own custom IoT Edge modules locally, without the IoT Edge Runtime, and with the following benefits:
- Your custom Edge module code is the **same** whether running on the simulator or the full IoT Edge Runtime.
- Your Edge solution can be run locally **without the need** to push new images or create IoT Edge deployment manifests.
- The only credential required to run your Edge solution on the simulator is the **IoT Edge Device Connection String**. The IoT Hub Connection String is not needed.
- It helps you debug your custom Edge modules on the host and not just in the container.

The following table compares the requirements to run your solution on the IoT Edge Runtime and iotedgehubdev tool:

  |                               | IoT Edge Runtime | iotedgehubdev |
  | ----------------------------- |:----------------:|:-------------:|
  | Device Credential Needed      | YES              | YES           |
  | IoT Hub Credential Needed     | YES              | **NO**        |
  | Build Image                   | YES              | YES           |
  | Push Image                    | YES              | **NO**        |
  | Create Deployment             | YES              | **NO**        |
  | Support native debug scenario | NO               | **YES**       |

## Installing
1. Install [Docker CE (18.02.0+)](https://www.docker.com/community-edition) on
[Windows](https://docs.docker.com/docker-for-windows/install/), [macOS](https://docs.docker.com/docker-for-mac/install/) or [Linux](https://docs.docker.com/install/linux/docker-ce/ubuntu/#install-docker-ce)

2. Install [Docker Compose (1.20.0+)](https://docs.docker.com/compose/install/#install-compose) (***Linux only***. *Compose has already been included in Windows/macOS Docker CE installation*)
3. Install [Python (2.7/3.5/3.6/3.7/3.8) and Pip](https://www.python.org/)
4. Install **iotedgehubdev** by running the following command in your terminal:
    ```
    pip install --upgrade iotedgehubdev
    ```
    **Note**: Please install iotedgehubdev to **root** on Linux/macOS (*Don't use '--user' option in the 'pip install' command*).

**Please make sure there is no Azure IoT Edge runtime running on the same machine as iotedgehubdev since they require the same ports.**

## Quickstart
### 1. Setup

  ##### Windows
  ```
  iotedgehubdev setup -c "<edge-device-connection-string>"
  ```

  ##### Linux/macOS
  ```
  sudo iotedgehubdev setup -c "<edge-device-connection-string>"
  ```

### 2. Start/Stop an IoT Edge solution in simulator

  ##### Windows
  ```
  iotedgehubdev start -d <path/to/deployment-manifest>
  iotedgehubdev stop
  ```

  ##### Linux/macOS
  ```
  sudo iotedgehubdev start -d <path/to/deployment-manifest>
  sudo iotedgehubdev stop
  ```

### 3. Start and debug a single module natively
  1. Start the module with specific input(s) and/or environment variable(s)

      ##### Windows
      ```
      iotedgehubdev start -i "<module-inputs>"

      // OR

      iotedgehubdev start -i "<module-inputs>" -e "<environment-variable>"
      ```

      ##### Linux/macOS
      ```
      sudo iotedgehubdev start -i "<module-inputs>"

      // OR

      sudo iotedgehubdev start -i "<module-inputs>" -e "<environment-variable>"
      ```

      **For example**:  
      `iotedgehubdev start -i "input1,input2" -e "TestEnv1=Value1" -e "TestEnv2=Value2"`

  2. Output the module credential environment variables

      ```
      iotedgehubdev modulecred
      ```

  3. Start your module natively with the environment variables from the previous step

  4. Send a message to your module through the RESTful API

      **For example**:  
      `curl --header "Content-Type: application/json" --request POST --data '{"inputName": "input1","data": "hello world"}' http://localhost:53000/api/v1/messages`

  5. Stop the simulator

      ##### Windows
      ```
      iotedgehubdev stop
      ```

      ##### Linux/macOS
      ```
      sudo iotedgehubdev stop
      ```

## Other resources
- [Azure IoT Edge for Visual Studio Code](https://github.com/microsoft/vscode-azure-iot-edge)
- [Azure IoT Edge Dev CLI Tool](https://github.com/azure/iotedgedev)

# Data/Telemetry
This project collects usage data and sends it to Microsoft to help improve our products and services. Read our [privacy statement](http://go.microsoft.com/fwlink/?LinkId=521839) to learn more.
If you don’t wish to send usage data to Microsoft, you can change your telemetry settings by updating `collect_telemetry` to `no` in the ini file.

# Contributing

This project welcomes contributions and suggestions. Most contributions require you to
agree to a Contributor License Agreement (CLA) declaring that you have the right to,
and actually do, grant us the rights to use your contribution. For details, visit
https://cla.microsoft.com.

When you submit a pull request, a CLA-bot will automatically determine whether you need
to provide a CLA and decorate the PR appropriately (e.g., label, comment). Simply follow the
instructions provided by the bot. You will only need to do this once across all repositories using our CLA.

This project has adopted the [Microsoft Open Source Code of Conduct](https://opensource.microsoft.com/codeofconduct/).
For more information see the [Code of Conduct FAQ](https://opensource.microsoft.com/codeofconduct/faq/)
or contact [opencode@microsoft.com](mailto:opencode@microsoft.com) with any additional questions or comments.
