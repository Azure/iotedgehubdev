
# Azure IoT EdgeHub Dev Tool [![Build Status](https://dev.azure.com/mseng/VSIoT/_apis/build/status/Azure%20IoT%20Edge/iotedgehubdev?branchName=main)](https://dev.azure.com/mseng/VSIoT/_build/latest?definitionId=7735&branchName=main)

## Announcement
The Azure IoT EdgeHub Dev Tool is in a maintenance mode. Please see [this announcement](https://github.com/Azure/iotedgehubdev/issues/396) for more details. We recommend using VM, Physical devices or [EFLOW](https://github.com/Azure/iotedge-eflow).

## Introduction
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
3. Install [Python (3.5/3.6/3.7/3.8/3.9) and Pip](https://www.python.org/)
4. Install **iotedgehubdev** by running the following command in your terminal:
    ```
    pip install --upgrade iotedgehubdev
    ```
5. Ensure the user is a member of **docker** user group (**Linux / MacOS only**):
    ```
    sudo usermod -aG docker $USER
    ```

**Please make sure there is no Azure IoT Edge runtime running on the same machine as iotedgehubdev since they require the same ports.**

## Quickstart
### 1. Setup

  ```
  iotedgehubdev setup -c "<edge-device-connection-string>"
  ```

### 2. Start/Stop an IoT Edge solution in simulator

  ```
  iotedgehubdev start -d <path/to/deployment-manifest>
  iotedgehubdev stop
  ```

### 3. Start and debug a single module natively

  1. Start the module with specific input(s) and/or environment variable(s)

      ```
      iotedgehubdev start -i "<module-inputs>"

      // OR

      iotedgehubdev start -i "<module-inputs>" -e "<environment-variable>"
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

      ```
      iotedgehubdev stop
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
