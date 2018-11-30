# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.


class EdgeConstants():
    HOSTNAME_KEY = 'HostName'
    DEVICE_ID_KEY = 'DeviceId'
    ACCESS_KEY_KEY = 'SharedAccessKey'

    SUBJECT_COUNTRY_KEY = 'countryCode'
    SUBJECT_STATE_KEY = 'state'
    SUBJECT_LOCALITY_KEY = 'locality'
    SUBJECT_ORGANIZATION_KEY = 'organization'
    SUBJECT_ORGANIZATION_UNIT_KEY = 'organizationUnit'
    SUBJECT_COMMON_NAME_KEY = 'commonName'

    EDGE_CHAIN_CA = 'edge-chain-ca'
    EDGE_HUB_SERVER = 'edge-hub-server'
    EDGE_DEVICE_CA = 'edge-device-ca'
    EDGE_AGENT_CA = 'edge-agent-ca'
    CERT_SUFFIX = '.cert.pem'
    PFX_SUFFIX = '.cert.pfx'

    CERT_DEFAULT_DICT = {
        SUBJECT_COUNTRY_KEY: 'US',
        SUBJECT_STATE_KEY: 'Washington',
        SUBJECT_LOCALITY_KEY: 'Redmond',
        SUBJECT_ORGANIZATION_KEY: 'Default Edge Organization',
        SUBJECT_ORGANIZATION_UNIT_KEY: 'Edge Unit',
        SUBJECT_COMMON_NAME_KEY: 'Edge Test Device CA'
    }

    # Port of Docker daemon
    # https://github.com/docker/docker-ce/blob/f9756bfb29877236a83979170ef2c0aa35eb57c6/components/engine/volume/mounts/windows_parser.go#L19-L76
    MOUNT_HOST_DIR_REGEX = r'(?:\\\\\?\\)?[a-z]:[\\/](?:[^\\/:*?"<>|\r\n]+[\\/]?)*'
    MOUNT_NAME_REGEX = r'[^\\/:*?"<>|\r\n]+'
    MOUNT_PIPE_REGEX = r'[/\\]{2}.[/\\]pipe[/\\][^:*?"<>|\r\n]+'
    MOUNT_SOURCE_REGEX = r'((?P<source>((' + MOUNT_HOST_DIR_REGEX + r')|(' + \
        MOUNT_NAME_REGEX + r')|(' + MOUNT_PIPE_REGEX + r'))):)?'
    MOUNT_MODE_REGEX = r'(:(?P<mode>(?i)ro|rw))?'
    MOUNT_WIN_DEST_REGEX = r'(?P<destination>((?:\\\\\?\\)?([a-z]):((?:[\\/][^\\/:*?"<>\r\n]+)*[\\/]?))|(' + \
        MOUNT_PIPE_REGEX + r'))'
    MOUNT_LCOW_DEST_REGEX = r'(?P<destination>/(?:[^\\/:*?"<>\r\n]+[/]?)*)'
    MOUNT_WIN_REGEX = r'^' + MOUNT_SOURCE_REGEX + MOUNT_WIN_DEST_REGEX + MOUNT_MODE_REGEX + r'$'
    MOUNT_LCOW_REGEX = r'^' + MOUNT_SOURCE_REGEX + MOUNT_LCOW_DEST_REGEX + MOUNT_MODE_REGEX + r'$'
